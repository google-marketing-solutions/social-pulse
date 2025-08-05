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
"""Module level domain utilities and classes."""

import datetime
import uuid


def _generate_id() -> str:
  """Generates a unique universal ID."""
  return str(uuid.uuid4())


class Entity:
  """Base entity type that contains a unique UUID."""

  def __init__(
      self,
      entity_id: str | None = None,
      created: datetime.datetime | None = None,
      last_updated: datetime.datetime | None = None,
  ):
    """Instantiate a new entity.

    Args:
      entity_id: Optional.  Used as the entity ID, or if None is provided, a new
        UUID will be generated.
      created: Optional.  The creation timestamp of the entity.
      last_updated: Optional.  The last updated timestamp of the entity.
    """
    self.entity_id = entity_id if entity_id else _generate_id()

    if created and last_updated and last_updated < created:
      raise ValueError(
          'last_updated cannot be before created.  last_updated: %s,'
          ' created: %s' % (last_updated, created)
      )

    self.created = created if created else datetime.datetime.now()
    self.last_updated = (
        last_updated if last_updated else datetime.datetime.now()
    )
