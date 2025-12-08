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
"""Tests for the config.py module."""

import os
import unittest
from unittest import mock

import pydantic
from socialpulse_common import config


class ConfigTest(unittest.TestCase):
  def setUp(self):
    super().setUp()

    # Reset the singleton Settings object for atomic tests
    config.Settings._instance = None
    config.Settings._initialized = False

    self.mock_os_envs = {
        "CLOUD__PROJECT_ID": "123456789",
        "API__YOUTUBE__KEY": "dummy_key",
        "DB__PASSWORD": "dummy_db_password",
        "CLOUD__REGION": "us-central1",
        "CLOUD__DATASET_NAME": "social_pulse_sentiment_data",
        "APP_ENV": "development"
    }
    self.setup_os_environment()

  def setup_os_environment(self):
    self.env_patcher = mock.patch.dict(
        os.environ,
        self.mock_os_envs,
        clear=True
    )
    self.env_patcher.start()

  def tearDown(self):
    super().tearDown()
    self.env_patcher.stop()

  @mock.patch("socialpulse_common.config._load_all_gcp_secrets_to_env")
  @mock.patch("dotenv.find_dotenv", side_effect=IOError)
  def test_dynamic_api_url_is_generated_correctly(
      self,
      mocked_find_dotenv,
      mocked_secrets_loader
  ):
    """Verifies the dynamic API URL is built correctly from other settings.

    Given the CLOUD__PROJECT_ID environment variable is set
    When the Settings object is initialized
    Then the workflow_runner_api_url is generated with the correct format

    Args:
      mocked_find_dotenv: Mocked find_dotenv to prevent loading a .env file.
      mocked_secrets_loader: Mocked secrets loader to isolate URL logic.
    """
    del mocked_find_dotenv
    settings = config.Settings()

    expected_url = (
        "https://sp-analysis-runner-123456789.us-central1.run.app"
    )
    self.assertEqual(settings.cloud.workflow_runner_api_url, expected_url)
    mocked_secrets_loader.assert_called_once_with("123456789")

  @mock.patch("socialpulse_common.config._load_all_gcp_secrets_to_env")
  @mock.patch("dotenv.find_dotenv", side_effect=IOError)
  def test_dynamic_api_url_is_overridden_by_env_var(
      self,
      mocked_find_dotenv,
      mocked_secrets_loader
  ):
    """Ensures an explicit environment variable overrides the dynamic API URL.

    Given an explicit CLOUD__WORKFLOW_RUNNER_API_URL is set
    When the Settings object is initialized
    Then the dynamic URL is not used and the explicit one is kept

    Args:
      mocked_find_dotenv: Mocked find_dotenv to prevent loading a .env file.
      mocked_secrets_loader: Mocked secrets loader, not used in this test.
    """
    del mocked_find_dotenv
    del mocked_secrets_loader

    self.mock_os_envs["CLOUD__WORKFLOW_RUNNER_API_URL"] = (
        "http://my-override-url.com"
    )
    self.setup_os_environment()

    settings = config.Settings()

    self.assertEqual(
        settings.cloud.workflow_runner_api_url,
        "http://my-override-url.com"
    )

  @mock.patch(
      "socialpulse_common.config.secretmanager.SecretManagerServiceClient"
  )
  @mock.patch("dotenv.find_dotenv", side_effect=IOError)
  def test_secrets_are_loaded_and_used_as_config(
      self,
      mocked_find_dotenv,
      mock_sm_client
  ):
    """Tests that secrets from GCP are loaded and used by the settings model.

    Given the Secret Manager has a value for the database password
    And the secret ID is store under the DB-PASSWORD ID
    When the Settings object is initialized
    Then the value of the mocked secret is correctly populated in the settings

    Args:
      mocked_find_dotenv: Mocked find_dotenv to prevent loading a .env file.
      mock_sm_client: Mocked SecretManagerServiceClient to simulate API calls.
    """
    del mocked_find_dotenv

    mock_client_instance = mock.Mock()
    mock_sm_client.return_value = mock_client_instance

    mock_secret = mock.Mock()
    mock_secret.name = "projects/gcp-project/secrets/DB-PASSWORD"
    mock_client_instance.list_secrets.return_value = [mock_secret]

    mock_version_response = mock.Mock()
    mock_version_response.payload.data = b"password-from-secret"
    mock_client_instance.access_secret_version.return_value = (
        mock_version_response
    )

    with mock.patch.dict(os.environ, {"API__YOUTUBE.KEY": "dummy"}):
      settings = config.Settings()

      self.assertEqual(settings.db.password, "password-from-secret")
      mock_client_instance.list_secrets.assert_called_once()
      mock_client_instance.access_secret_version.assert_called_once()

  @mock.patch("socialpulse_common.config._load_all_gcp_secrets_to_env")
  @mock.patch("dotenv.find_dotenv")
  @mock.patch("dotenv.load_dotenv")
  def test_fatal_error_if_required_bootstrap_params_not_set(
      self,
      mocked_load_dotenv,
      mocked_find_dotenv,
      mocked_secrets_loader
  ):
    """Fatal error is raised if required bootstrap params are not set.

    Given the GCP Project ID is not set
    When the config module is imported
    Then a fatal error is raised

    Args:
      mocked_load_dotenv: mocked load_dotenv function, not used.
      mocked_find_dotenv: mocked find_dotenv function, not used.
      mocked_secrets_loader: mocked secrets_loader function, not used.
    """
    del mocked_find_dotenv
    del mocked_load_dotenv
    del mocked_secrets_loader

    self.mock_os_envs.pop("CLOUD__PROJECT_ID")
    self.setup_os_environment()

    with self.assertRaises(pydantic.ValidationError):
      settings = config.Settings()  # pylint: disable=unused-variable

  @mock.patch("socialpulse_common.config._load_all_gcp_secrets_to_env")
  @mock.patch("dotenv.find_dotenv")
  @mock.patch("dotenv.load_dotenv")
  def test_development_mode_is_true_if_app_env_set_to_dev(
      self,
      mocked_load_dotenv,
      mocked_find_dotenv,
      mocked_secrets_loader
  ):
    """Development mode flag is true if app env is set to development.

    Given the app_env env variable is set to "dev"
    When is_development() is called
    Then the return value is True

    Args:
      mocked_load_dotenv: mocked load_dotenv function, not used.
      mocked_find_dotenv: mocked find_dotenv function, not used.
      mocked_secrets_loader: mocked secrets_loader function, not used.
    """
    del mocked_find_dotenv
    del mocked_load_dotenv
    del mocked_secrets_loader

    with mock.patch.dict(os.environ, {"APP_ENV": "dev"}):
      self.assertTrue(config.is_development())

  @mock.patch("socialpulse_common.config._load_all_gcp_secrets_to_env")
  @mock.patch("dotenv.find_dotenv")
  @mock.patch("dotenv.load_dotenv")
  def test_env_vars_override_default_values(
      self,
      mocked_load_dotenv,
      mocked_find_dotenv,
      mocked_secrets_loader
  ):
    """Environment variables override default values.

    Given a setting var with a default value
    When an env var is set
    Then the env var value is used over the default value

    Args:
      mocked_load_dotenv: mocked load_dotenv function, not used.
      mocked_find_dotenv: mocked find_dotenv function, not used.
      mocked_secrets_loader: mocked secrets_loader function, not used.
    """
    del mocked_find_dotenv
    del mocked_load_dotenv
    del mocked_secrets_loader

    with mock.patch.dict(os.environ, {"DB__USERNAME": "fizz"}):
      settings = config.Settings()
      self.assertEqual(settings.db.username, "fizz")


if __name__ == "__main__":
  unittest.main()
