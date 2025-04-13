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
"""Tests for the services.py module."""

import unittest

from socialpulse_common import service


class SomeAbstractService(service.RegisterableService):
  pass


class SomeConcreteService(SomeAbstractService):
  pass


class ServicesTest(unittest.TestCase):

  def test_returns_reference_to_registered_service(self):
    """Returns a reference to a registered service.

    Given a service is registered
    When the registry is asked for the service
    The registered service is returned.
    """
    service_instance = SomeConcreteService()
    service.registry.register(SomeConcreteService, service_instance)
    self.assertEqual(
        service.registry.get(SomeConcreteService), service_instance
    )

  def test_raises_error_if_service_isnt_registered(self):
    """Raises an error if a service is not registered beforehand.

    Given a service isn't registered
    When the registry is asked for the service
    Then an error is raised
    """
    with self.assertRaises(ValueError) as raised:
      service.registry.get(SomeConcreteService)

    error = raised.exception
    self.assertIn("SomeConcreteService", str(error))

  def test_should_handle_registering_child_service_as_parent_service(self):
    """Should handle registering child service as parent service.

    Given a child service is registered as its parent
    When the registry is asked for the parent service
    Then the child service is returned
    """
    concrete_service_instance = SomeConcreteService()
    service.registry.register(SomeAbstractService, concrete_service_instance)

    registered_service = service.registry.get(SomeAbstractService)

    self.assertEqual(registered_service, concrete_service_instance)


if __name__ == "__main__":
  unittest.main()
