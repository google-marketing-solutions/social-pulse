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
"""Module for managing connections to a PostgresDB."""

import logging

from psycopg2 import pool


MIN_OPEN_CONNS = 1
MAX_OPEN_CONNS = 5


logger = logging.getLogger(__name__)


class PostgresDbClient:
  """Client for interacting with a Postgres database.

  This class is implemented as a singleton to ensure only one connection pool
  is created.
  """

  _is_initialized: bool = False
  _instance = None

  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      cls._instance = super(PostgresDbClient, cls).__new__(cls)
    return cls._instance

  def __init__(
      self,
      host: str | None = None,
      port: str | None = None,
      user: str | None = None,
      password: str | None = None,
      database: str | None = None,
  ):
    if self._is_initialized:
      return

    self.host = host
    self.port = port
    self.user = user
    self.database = database
    self.password = password

    logger.debug(
        "Initializing PostgresDB connection pool with the following "
        "parameters: %s, %s, %s, %s",
        self.host,
        self.port,
        self.user,
        self.database,
    )
    self._connection_pool = self._init_connection_pool()
    self._is_initialized = True

  def _init_connection_pool(self) -> pool.ThreadedConnectionPool:
    """Initialize connection pool.

    Returns:
        psycopg2.pool.ThreadedConnectionPool: A connection pool object.

    Raises:
        psycopg2.Error: If there is an error connecting to the database.
    """

    return pool.ThreadedConnectionPool(
        minconn=MIN_OPEN_CONNS,
        maxconn=MAX_OPEN_CONNS,
        host=self.host,
        port=self.port,
        dbname=self.database,
        user=self.user,
        password=self.password,
    )

  def retrieve_row(
      self, query: str, params: tuple[any, ...] = None
  ) -> tuple[any, ...]:
    """Retrieves a single row from the database based on the given query.

    Args:
        query (str): The SQL query to execute.
        params (tuple, optional): Parameters to pass to the query. Defaults to
          None.

    Returns:
        A tuple with the row data or None if no row is found.

    Raises:
        psycopg2.Error: If there is an error executing the query.
    """

    result = None
    conn = None

    try:
      conn = self._connection_pool.getconn()
      with conn.cursor() as cursor:
        cursor.execute(query, params)
        result = cursor.fetchone()

      return result
    finally:
      if conn is not None:
        self._connection_pool.putconn(conn)

  def insert_row(self, query: str, params: tuple[any, ...] = None) -> str:
    """Inserts a single row into the database based on the given query.

    Args:
      query (str): The SQL INSERT query to execute.
      params (tuple, optional): Parameters to pass to the query. Defaults to
        None.

    Returns:
      str: The ID of the newly inserted row, assuming the query uses
      RETURNING clause to return the ID.

    Raises:
      psycopg2.Error: If there is an error executing the query.
    """
    conn = None
    new_id = None

    try:
      conn = self._connection_pool.getconn()
      with conn.cursor() as cursor:
        cursor.execute(query, params)
        new_id = cursor.fetchone()[0]
        conn.commit()

        return new_id
    except Exception:
      conn.rollback()
      raise
    finally:
      if conn is not None:
        self._connection_pool.putconn(conn)

  def update_row(self, query: str, params: tuple[any, ...] = None) -> None:
    """Updates a single row in the database based on the given query.

    Args:
      query (str): The SQL UPDATE query to execute.
      params (tuple, optional): Parameters to pass to the query. Defaults to
        None.

    Returns:
      None

    Raises:
      psycopg2.Error: If there is an error executing the query.
    """
    conn = None

    try:
      conn = self._connection_pool.getconn()
      with conn.cursor() as cursor:
        cursor.execute(query, params)
        conn.commit()
    except Exception:
      conn.rollback()
      raise
    finally:
      if conn is not None:
        self._connection_pool.putconn(conn)

  def retrieve_rows(
      self, query: str, params: tuple[any, ...] = None
  ) -> list[tuple[any, ...]]:
    """Retrieves multiple rows from the database based on the given query.

    Args:
        query (str): The SQL query to execute.
        params (tuple, optional): Parameters to pass to the query. Defaults to
          None.

    Returns:
        A list of tuples, where each tuple is a row. Returns an empty list
        if no rows are found.

    Raises:
        psycopg2.Error: If there is an error executing the query.
    """

    results = []
    conn = None

    try:
      conn = self._connection_pool.getconn()
      with conn.cursor() as cursor:
        cursor.execute(query, params)
        results = cursor.fetchall()

      return results
    finally:
      if conn is not None:
        self._connection_pool.putconn(conn)
