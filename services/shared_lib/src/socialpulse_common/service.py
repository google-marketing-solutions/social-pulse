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
"""Module for a service registry.

Any type of service should extend the abstract RegisterableService class.  Then
a concrete implementation of the abstract service class can be registered
by the application/bootstrap layer, and used by any client of the service.  This
way, there's a layter of abstraction between higher level code (ie, domain
classes) and lower level code (ie, scripts executed at the command line).

For example:

# Domain Layer
class SomeDomainService(services.RegisterableService):
  @abc.abstractmethod
  def do_something():
    pass

class SomeDomain(Entity):
  def domain_function():
    my_service = services.registry.get(services.SomeDomainService)
    my_service.do_something()


# Application Layer
class SomeDomainServiceImplementation(SomeDomainService):
  def do_something():
    # Concrete code

impl = SomeDomainServiceImplementation()
services.registry.register(SomeDomainService, impl)
"""

import abc
from typing import TypeVar


class RegisterableService(abc.ABC):
  """Represents a domain service that can be registered."""


T = TypeVar('T')


class ServiceRegistry:
  """A registry of services used by service clients.

  A simple registry where service clients can get instances of the services
  they need, without being coupled to the implementation.  This way an entity
  can get the functionality it needs (ie, looking up if an email is correct)
  without having to know about the underlying implementation (ie, sending
  an RPC call to a 3rd party email verification API).
  """

  _instance = None
  _initialized: bool = False

  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      cls._instance = super(ServiceRegistry, cls).__new__(cls)
    return cls._instance

  def __init__(self):
    if self._initialized:
      return

    self._registered_services: dict[str, RegisterableService] = {}
    self._initialized = True

  def register(
      self,
      service_class: type[RegisterableService],
      service_instance: RegisterableService,
  ):
    """Register an service object bound to its type.

    Args:
      service_class: The type of service to register.
      service_instance: The service instance to register.
    """
    self._registered_services[service_class.__name__] = service_instance

  def get(self, service_type: type[T]) -> T:
    """Retrieves service instance by its type.

    Args:
      service_type: The type of service to retrieve.

    Returns:
      The service instance of the given type, casted to the provided type.

    Raises:
      ValueError: If the service type is not registered.
    """
    key = service_type.__name__
    if key not in self._registered_services:
      raise ValueError(f'Service type {service_type} not registered.')
    return self._registered_services.get(key)


registry = ServiceRegistry()
