#  Copyright 2026 Google LLC
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

# pylint: disable=no-member

"""Tests for the logging.py module."""

import io
import logging

import unittest
from unittest import mock

from socialpulse_common import logging as sp_logging


class LoggingTest(unittest.TestCase):
  """Unit tests for the logging module."""

  def setUp(self):
    super().setUp()
    # Reset the execution ID before each test.
    sp_logging.set_execution_id(None)
    # Reset root logger handlers.
    logging.getLogger().handlers = []

  def tearDown(self):
    super().tearDown()
    # Reset root logger handlers again to be safe.
    logging.getLogger().handlers = []

  def test_setup_logging_dev_mode_logs_to_stdout(self):
    """Verifies all logs go to stdout in DEV mode.

    Given running in development mode
    When setup_logging is called with is_dev=True
    Then all logs go to stdout regardless of level.
    """
    mock_stdout = io.StringIO()

    with mock.patch("sys.stdout", mock_stdout):
      sp_logging.setup_logging(log_level="DEBUG")

      logger = logging.getLogger("test_logger")
      logger.debug("debug message")
      logger.info("info message")
      logger.warning("warning message")
      logger.error("error message")

    stdout_output = mock_stdout.getvalue()

    self.assertIn("DEBUG: debug message", stdout_output)
    self.assertIn("INFO: info message", stdout_output)
    self.assertIn("WARNING: warning message", stdout_output)
    self.assertIn("ERROR: error message", stdout_output)

  def test_execution_id_injected_when_set(self):
    """Verifies that execution ID is injected into log messages when set.

    Given an execution ID is set in the context
    When a log message is generated
    Then the message includes the execution ID in the format [id].
    """
    mock_stdout = io.StringIO()

    with mock.patch("sys.stdout", mock_stdout):
      sp_logging.setup_logging(log_level="INFO")
      sp_logging.set_execution_id("test_exec_123")

      logger = logging.getLogger("test_logger")
      logger.info("hello with id")

    output = mock_stdout.getvalue()
    self.assertIn("[test_exec_123] INFO: hello with id", output)

  def test_execution_id_not_injected_when_not_set(self):
    """Verifies that execution ID is NOT injected when not set.

    Given NO execution ID is set in the context
    When a log message is generated
    Then the message does NOT include the execution ID prefix.
    """
    mock_stdout = io.StringIO()

    with mock.patch("sys.stdout", mock_stdout):
      sp_logging.setup_logging(log_level="INFO")
      sp_logging.set_execution_id(None)

      logger = logging.getLogger("test_logger")
      logger.info("hello without id")

    output = mock_stdout.getvalue()
    self.assertIn("INFO: hello without id", output)
    self.assertNotIn("[]", output)


if __name__ == "__main__":
  unittest.main()
