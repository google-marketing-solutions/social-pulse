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
"""Module providing util functions for the web app."""

from core.models import AppState


def set_page(state: AppState, page_name: str):
  """Navigates to a different page."""
  state.current_page = page_name


def show_toast(state: AppState, message: str):
  """Displays a temporary toast message."""
  state.toast_message = message
  state.show_toast = True
