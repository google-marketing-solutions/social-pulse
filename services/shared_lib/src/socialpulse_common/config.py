#  Copyright 2025 Google LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""Module for configuration parameters access."""
import logging

import dotenv
import pydantic
import pydantic_settings


ENV_DEVELOPMENT = "development"
ENV_PRODUCTION = "production"


class _DbSettings(pydantic.BaseModel):
  host: str = pydantic.Field(default="localhost")
  port: int = pydantic.Field(default=5432)
  username: str = pydantic.Field(default="social_pulse_user")
  name: str = pydantic.Field(default="social_pulse_db")
  password: str = pydantic.Field(repr=False)


class _CloudSettings(pydantic.BaseModel):
  project_id: str = pydantic.Field()
  region: str = pydantic.Field(default="us-central1")


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
      env_nested_delimiter=".",
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
  _internal_settings: _ApiSettings = None

  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      cls._instance = super(Settings, cls).__new__(cls)
    return cls._instance

  def __init__(self):
    if self._initialized:
      return

    # Load local .env overrides, so Settings can use local developmnet
    # overrides.
    dotenv_file_location = dotenv.find_dotenv(
        usecwd=True,
        raise_error_if_not_found=True
    )
    dotenv.load_dotenv(dotenv_path=dotenv_file_location)

    self._internal_settings = _AppSettings()
    self._initialized = True

  def __getattr__(self, name):
    try:
      return getattr(self._internal_settings, name)
    except AttributeError:
      logging.error("Unknown configuration setting requested:  %s", name)
      raise

  @property
  def is_development(self) -> bool:
    return self.app_env == ENV_DEVELOPMENT
