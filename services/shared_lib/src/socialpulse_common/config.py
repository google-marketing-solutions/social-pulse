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

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


ENV_DEVELOPMENT = "development"
ENV_PRODUCTION = "production"


# Load local .env overrides, so Settings can use local developmnet overrides.
load_dotenv()


class _PydanticSettingsRepo(BaseSettings):
  """Internal class to hold the settings.

  This class is not meant to be used directly, use the Settings class instead.
  """
  _instance = None
  _initialized: bool = False

  model_config = SettingsConfigDict(extra="ignore")

  app_env: str = Field(default=ENV_DEVELOPMENT)
  cloud_project_id: str = Field()
  cloud_api_key: str = Field()
  cloud_region: str = Field(default="us-central1")

  gemini_pro_model_id: str = Field(default="gemini-2.0-flash-001")
  sentiment_dataset_name: str = Field(default="social_pulse_sentiment")

  report_dataset_name: str = Field(default="social_pulse_reports")
  workflow_execution_table_name: str = Field(default="workflow_executions")

  yt_api_service_name: str = Field(default="youtube")
  yt_api_version: str = Field(default="v3")
  yt_api_scope: list[str] = Field(
      default=["https://www.googleapis.com/auth/youtube.force-ssl"]
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
  _internal_settings: _PydanticSettingsRepo = None

  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      cls._instance = super(Settings, cls).__new__(cls)
    return cls._instance

  def __init__(self):
    if self._initialized:
      return

    self._internal_settings = _PydanticSettingsRepo()
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
