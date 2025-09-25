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
"""Module providing the routing for the web app root."""

from core import models
import mesop as me


@me.page(
    path="/",
    stylesheets=[
        "https://cdn.jsdelivr.net/npm/"
        "bootstrap@5.3.3/dist/css/bootstrap.min.css",
    ],
)
def main_app():
  """Main application page."""
  header()

  with me.box(classes="container px-4 py-5"):
    with me.box(classes="pb-2"):
      me.text("Body", type="headline-5")

    footer()


def header():
  """Responsible for creating the application header."""
  state = me.state(models.AppState)

  with me.box(classes="container"):
    with me.box(
        classes=("d-flex flex-wrap justify-content-between py-3 mb-4 "
                 "border-bottom"),
    ):
      with me.box(
          classes=("d-flex align-items-center mb-3 mb-md-0 me-md-auto "
                   "link-body-emphasis text-decoration-none fs-4"),
      ):
        me.text(f"Social Pulse - {state.current_route}")

      with me.box(classes="nav nav-pills"):
        with me.box(classes="nav-item"):
          with me.box(classes="nav-link active"):
            me.text("Dashboard")

        with me.box(classes="nav-item"):
          with me.box(classes="nav-link"):
            me.text("Create Report")


def footer():
  """Responsible for creating the application footer."""
  with me.box(
      classes=("d-flex flex-wrap justify-content-between align-items-center "
               "py-3 my-4 border-top")
  ):
    with me.box(classes="col-md-4 mb-0 text-body-secondary"):
      me.text("Social Pulse")
