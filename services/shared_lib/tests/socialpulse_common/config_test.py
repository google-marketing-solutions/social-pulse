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

  def test_fatal_error_if_required_boostrap_params_not_set(self):
    """Fatal error is raised if required bootstrap params are not set.

    Given the GCP Project ID is not set
    When the config module is imported
    Then a fatal error is raised
    """
    with self.assertRaises(pydantic.ValidationError):
      settings = config.Settings()  # pylint: disable=unused-variable

  @mock.patch.dict(
      os.environ, {"cloud_project_id": "foo", "cloud_api_key": "bar"}
  )
  def test_is_development_mode_is_one_if_app_evn_set_to_dev(self):
    """Development mode flag is true if app env is set to development.

    Given the app_env env variable is set to "development"
    When is_development is called
    Then the return value is True
    """
    with mock.patch.dict(os.environ, {"app_env": "development"}):
      settings = config.Settings()
      self.assertTrue(settings.is_development)

  @mock.patch.dict(
      os.environ, {"cloud_project_id": "foo", "cloud_api_key": "bar"}
  )
  def test_env_vars_override_default_values(self):
    """Environment variables override default values.

    Given a setting var with a default value
    When an env var is set
    Then the env var value is used over the default value
    """
    with mock.patch.dict(os.environ, {"gemini_pro_model_id": "fizz"}):
      settings = config.Settings()
      self.assertEqual(settings.gemini_pro_model_id, "fizz")


if __name__ == "__main__":
  unittest.main()
