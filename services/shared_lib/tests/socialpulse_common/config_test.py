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

    # Reset the singleton Settings object, so tests can be atomic, since they
    # all do share the same global space.
    config.Settings._instance = None
    config.Settings._initialized = False

  @mock.patch("dotenv.find_dotenv")
  @mock.patch("dotenv.load_dotenv")
  def test_fatal_error_if_required_bootstrap_params_not_set(
      self,
      mocked_load_dotenv,
      mocked_find_dotenv
  ):
    """Fatal error is raised if required bootstrap params are not set.

    Given the GCP Project ID is not set
    When the config module is imported
    Then a fatal error is raised

    Args:
      mocked_load_dotenv: mocked load_dotenv function, not used.
      mocked_find_dotenv: mocked find_dotenv function, not used.
    """
    del mocked_find_dotenv
    del mocked_load_dotenv

    with self.assertRaises(pydantic.ValidationError):
      settings = config.Settings()  # pylint: disable=unused-variable

  @mock.patch.dict(
      os.environ, {
          "CLOUD.PROJECT_ID": "foo-project",
          "API.YOUTUBE.KEY": "bar-key",
          "DB.PASSWORD": "fizz-password",
          "DB.NAME": "test-db",
      },
      clear=True
  )
  @mock.patch("dotenv.find_dotenv")
  @mock.patch("dotenv.load_dotenv")
  def test_is_development_mode_is_one_if_app_evn_set_to_dev(
      self,
      mocked_load_dotenv,
      mocked_find_dotenv
  ):
    """Development mode flag is true if app env is set to development.

    Given the app_env env variable is set to "development"
    When is_development is called
    Then the return value is True

    Args:
      mocked_load_dotenv: mocked load_dotenv function, not used.
      mocked_find_dotenv: mocked find_dotenv function, not used.
    """
    del mocked_find_dotenv
    del mocked_load_dotenv

    with mock.patch.dict(os.environ, {"APP_ENV": "development"}):
      settings = config.Settings()
      self.assertTrue(settings.is_development)

  @mock.patch.dict(
      os.environ, {
          "CLOUD.PROJECT_ID": "foo-project",
          "API.YOUTUBE.KEY": "bar-key",
          "DB.PASSWORD": "fizz-password",
          "DB.NAME": "test-db",
      },
      clear=True
  )
  @mock.patch("dotenv.find_dotenv")
  @mock.patch("dotenv.load_dotenv")
  def test_env_vars_override_default_values(
      self,
      mocked_load_dotenv,
      mocked_find_dotenv
  ):
    """Environment variables override default values.

    Given a setting var with a default value
    When an env var is set
    Then the env var value is used over the default value

    Args:
      mocked_load_dotenv: mocked load_dotenv function, not used.
      mocked_find_dotenv: mocked find_dotenv function, not used.
    """
    del mocked_find_dotenv
    del mocked_load_dotenv

    with mock.patch.dict(os.environ, {"DB.USERNAME": "fizz"}):
      settings = config.Settings()
      self.assertEqual(settings.db.username, "fizz")


if __name__ == "__main__":
  unittest.main()
