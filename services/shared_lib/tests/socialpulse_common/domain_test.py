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

import datetime
import unittest
from unittest import mock
import uuid

from socialpulse_common import domain as entity_lib


class EntityTest(unittest.TestCase):

  @mock.patch.object(datetime, 'datetime', autospec=True)
  def test_created_is_generated_if_entity_not_given_during_init(
      self, mock_datetime
  ):
    """Entity generates a new created timestamp if none is provided during init.

    When an entity is initiated with no created timestamp
    Then the entity autogenerates its own created timestamp

    Args:
      mock_datetime: Mock datetime generator.
    """
    now = datetime.datetime(2024, 1, 1)
    mock_datetime.now.return_value = now

    entity = entity_lib.Entity()

    self.assertEqual(entity.created, now)

  @mock.patch.object(datetime, 'datetime', autospec=True)
  def test_last_updated_is_generated_if_entity_not_given_during_init(
      self, mock_datetime
  ):
    """Entity generates a new last_updated timestamp if none is provided during init.

    When an entity is initiated with no last_updated timestamp
    Then the entity autogenerates its own last_updated timestamp

    Args:
      mock_datetime: Mock datetime generator.
    """
    now = datetime.datetime(2024, 1, 1)
    mock_datetime.now.return_value = now

    entity = entity_lib.Entity()

    self.assertEqual(entity.last_updated, now)

  def test_passed_in_uuid_is_used_by_entity_during_init(self):
    """Entity uses the provided UUID during init.

    Given an entity exists in the DB with a UUID
    When an entity is initiated with the UUID
    Then it uses the provided UUID
    """
    existing_uuid = 'existing_uuid'
    entity = entity_lib.Entity(entity_id=existing_uuid)

    self.assertEqual(entity.entity_id, existing_uuid)

  def test_passed_in_created_is_used_by_entity_during_init(self):
    """Entity uses the provided created timestamp during init.

    Given an entity exists in the DB with a created timestamp
    When an entity is initiated with the created timestamp
    Then it uses the provided created timestamp
    """
    existing_created = datetime.datetime(2024, 1, 1)
    entity = entity_lib.Entity(created=existing_created)

    self.assertEqual(entity.created, existing_created)

  def test_passed_in_last_updated_is_used_by_entity_during_init(self):
    """Entity uses the provided last_updated timestamp during init.

    Given an entity exists in the DB with a last_updated timestamp
    When an entity is initiated with the last_updated timestamp
    Then it uses the provided last_updated timestamp
    """
    existing_last_updated = datetime.datetime(2024, 1, 1)
    entity = entity_lib.Entity(last_updated=existing_last_updated)

    self.assertEqual(entity.last_updated, existing_last_updated)

  def test_last_updated_cannot_be_before_created_during_init(self):
    """Entity raises an error if last_updated is before created during init.

    Given an entity exists in the DB with a last_updated timestamp
    When an entity is initiated with a last_updated timestamp before created
    Then it raises an error
    """
    existing_created = datetime.datetime(2024, 1, 1)
    existing_last_updated = datetime.datetime(2023, 12, 31)

    with self.assertRaises(ValueError) as e:
      entity_lib.Entity(
          created=existing_created, last_updated=existing_last_updated
      )

    self.assertIn(
        'last_updated cannot be before created.',
        str(e.exception),
    )


if __name__ == '__main__':
  unittest.main()
