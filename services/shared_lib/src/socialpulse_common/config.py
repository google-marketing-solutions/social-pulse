# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module for configuration parameters access."""
import logging
import os
import re
from typing import Any

import dotenv
from google.api_core import exceptions
from google.cloud import secretmanager
import pydantic
import pydantic_settings


ENV_DEVELOPMENT = "dev"
ENV_PRODUCTION = "prod"

NESTED_CONFIG_SETTING_DELIMITER = "__"

WORKFLOW_RUNNER_DEPLOY_NAME = "sp-analysis-run"
WORKFLOW_EXECUTOR_DEPLOY_NAME = "sp-analysis-executor"
REPORT_BACKEND_DEPLOY_NAME = "sp-reporting-api"


def _load_all_gcp_secrets_to_env(project_id: str):
  """Loads the latest version of all secrets into an environment variable.

  Args:
    project_id: GCP Project ID.
  """
  if not project_id:
    logging.warning("GCP Project ID not provided. Skipping secret loading.")
    return

  logging.info("Starting to load secrets from GCP project: %s", project_id)
  client = secretmanager.SecretManagerServiceClient()
  parent = f"projects/{project_id}"

  try:
    secrets_list = client.list_secrets(request={"parent": parent})
  except exceptions.PermissionDenied:
    logging.error(
        "Permission Denied: Ensure the principal has "
        "'secretmanager.secrets.list' permission on the project."
    )
    return
  except Exception:  # pylint: disable=broad-except
    logging.exception("An unexpected error occurred while listing secrets:  ")
    return

  loaded_count = 0
  for secret in secrets_list:
    secret_id = secret.name.split("/")[-1]

    # Unfortunately, some cloud secret managers don't allow dot notation ('.')
    # in secret ID names. In the secrets manager we use a dash ('-') to
    # separate property levels, but convert them to '__' when adding to the
    # env.
    env_var_name = re.sub(
        r"-", NESTED_CONFIG_SETTING_DELIMITER, secret_id.upper()
    )

    try:
      version_name = f"{secret.name}/versions/latest"
      response = client.access_secret_version(request={"name": version_name})
      payload = response.payload.data.decode("UTF-8")

      os.environ[env_var_name] = payload
      logging.debug("Loaded '%s' into env var '%s'", secret_id, env_var_name)
      loaded_count += 1
    except exceptions.NotFound:
      logging.warning("Skipping '%s': No versions found.", secret_id)
    except Exception:  # pylint: disable=broad-except
      logging.exception("An error occurred with secret '%s': ", secret_id)

  logging.info("Finished. Loaded a total of %s secrets.", loaded_count)


class _DbSettings(pydantic.BaseModel):
  host: str = pydantic.Field(default="localhost")
  port: int = pydantic.Field(default=5432)
  username: str = pydantic.Field(default="social_pulse_user")
  name: str = pydantic.Field(default="social_pulse_db")
  password: str = pydantic.Field(repr=False)


class _CloudSettings(pydantic.BaseModel):
  """Cloud-related settings."""
  project_id: str = pydantic.Field()
  region: str = pydantic.Field(default="us-central1")
  dataset_name: str = pydantic.Field(default="social_pulse_sentiment_data")
  task_scheduler_host: str = pydantic.Field(default="localhost")
  task_scheduler_port: int = pydantic.Field(default=7000)

  # This field will be computed dynamically
  workflow_runner_api_url: str | None = None
  workflow_executor_api_url: str | None = None
  report_backend_api_url: str | None = None

  @pydantic.model_validator(mode="before")
  @classmethod
  def set_dynamic_api_url(cls, data: Any) -> Any:
    """Dynamically builds the runner API URL if not provided.

    Args:
      data: The dictionary containing the model data.

    Returns:
      The modified dictionary with dynamic API URLs set if applicable.
    """
    logging.debug("Checking config for dynamic API URLs:  %s", data)
    if isinstance(data, dict) and not is_development():
      project_number = data.get("project_number")
      region = data.get("region", "us-central1")

      if project_number and region:
        data["workflow_runner_api_url"] = (
            f"https://{WORKFLOW_RUNNER_DEPLOY_NAME}-{project_number}.{region}"
            ".run.app"
        )
        data["workflow_executor_api_url"] = (
            f"https://{WORKFLOW_EXECUTOR_DEPLOY_NAME}-{project_number}.{region}"
            ".run.app"
        )
        data["report_backend_api_url"] = (
            f"https://{REPORT_BACKEND_DEPLOY_NAME}-{project_number}.{region}"
            ".run.app"
        )
        logging.debug("Added dynamic API URLs to config data:  %s", data)
    return data


class _YoutubeApiSettings(pydantic.BaseModel):
  key: str = pydantic.Field(..., repr=False)
  service_name: str = pydantic.Field(default="youtube")
  version: str = pydantic.Field(default="v3")
  scopes: list[str] = pydantic.Field(
      default=["https://www.googleapis.com/auth/youtube.force-ssl"]
  )


class _ApiSettings(pydantic.BaseModel):
  youtube: _YoutubeApiSettings


class _AppSettings(pydantic_settings.BaseSettings):
  """Internal class to hold the settings.

  This class is not meant to be used directly, use the Settings class instead.
  """
  _instance = None
  _initialized: bool = False

  app_env: str = pydantic.Field(default=ENV_DEVELOPMENT)

  db: _DbSettings
  api: _ApiSettings
  cloud: _CloudSettings

  model_config = pydantic_settings.SettingsConfigDict(
      env_nested_delimiter=NESTED_CONFIG_SETTING_DELIMITER,
      extra="ignore"
  )


class Settings:
  """Configuration settings for the application.

  A singleton that Loads settings from environment variables, which can either
  be set with a local .env file (see python-dotenv), or directly as environment
  variables.

  How to use:
    from socialpulse_common import config

    settings: Settings = config.Settings()

    # Access as as a read-only property
    print(settings.cloud_project_id)
  """
  _instance = None
  _initialized: bool = False
  _internal_settings: _AppSettings = None

  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      cls._instance = super(Settings, cls).__new__(cls)
    return cls._instance

  def __init__(self):
    if self._initialized:
      return

    if is_development():
      try:
        dotenv_file_location = dotenv.find_dotenv(
            usecwd=True,
            raise_error_if_not_found=True
        )
        logging.info(
            "Loading configuration from .env file: %s", dotenv_file_location)
        dotenv.load_dotenv(dotenv_path=dotenv_file_location)
      except IOError:
        logging.info(
            "No .env file found, proceeding with environment variables."
        )

    # if not is_development():
    #   gcp_project_id = os.getenv(
    #       f"CLOUD{NESTED_CONFIG_SETTING_DELIMITER}PROJECT_ID"
    #   )
    #   _load_all_gcp_secrets_to_env(gcp_project_id)

    self._internal_settings = _AppSettings()
    self._initialized = True

  def __getattr__(self, name):
    try:
      return getattr(self._internal_settings, name)
    except AttributeError:
      logging.error("Unknown configuration setting requested: %s", name)
      raise


def is_development() -> bool:
  """Flag idicating if the application is running in development mode.

  Returns:
    True if the application is running in development mode, False otherwise.
  """
  app_env = os.getenv("APP_ENV", ENV_PRODUCTION)
  logging.debug("Application environment: %s", app_env)
  return app_env == ENV_DEVELOPMENT
