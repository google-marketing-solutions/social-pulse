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

# pylint: disable=no-member,import-self

"""Structured logging utility with contextual execution ID support."""

import contextvars
import logging
import sys


# Context variable to store the execution ID.
_execution_id_var = contextvars.ContextVar("execution_id", default=None)


class ExecutionIdFilter(logging.Filter):  # pylint: disable=too-few-public-methods
  """Filter that injects the execution ID into the log record."""

  def filter(self, record: logging.LogRecord) -> bool:
    """Injects execution ID into the log record.

    Args:
      record: The log record to inject the execution ID into.

    Returns:
      bool: Always True, as the filter always succeeds.
    """
    exec_id = _execution_id_var.get()
    record.execution_id = f"[{exec_id}] " if exec_id else ""
    return True


def setup_logging(log_level: str = "INFO") -> None:
  """Sets up logging based on the environment.

  Args:
    log_level: The log level to set.
  """
  level = getattr(logging, log_level.upper(), logging.INFO)
  root_logger = logging.getLogger()
  root_logger.setLevel(level)

  # Clear existing handlers to avoid duplicates.
  root_logger.handlers = []

  handler = logging.StreamHandler(sys.stdout)
  context_filter = ExecutionIdFilter()
  handler.addFilter(context_filter)

  formatter = logging.Formatter(
      "%(execution_id)s%(levelname)s: %(message)s"
  )
  handler.setFormatter(formatter)

  root_logger.addHandler(handler)


def set_execution_id(execution_id: str | None) -> None:
  """Sets the execution ID in the current context.

  Args:
    execution_id: The execution ID to set, or None to clear.
  """
  _execution_id_var.set(execution_id)
