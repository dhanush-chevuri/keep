"""
PostgresProvider is a class that provides a way to read data from Postgres and write queries to Postgres.
"""

import dataclasses
import os

import psycopg2
import pydantic

from keep.providers.base.base_provider import BaseProvider
from keep.providers.models.provider_config import ProviderConfig


@pydantic.dataclasses.dataclass
class PostgresProviderAuthConfig:
    username: str = dataclasses.field(
        metadata={"required": True, "description": "Postgres username"}
    )
    password: str = dataclasses.field(
        metadata={"required": True, "description": "Postgres password"}
    )
    host: str = dataclasses.field(
        metadata={"required": True, "description": "Postgres hostname"}
    )
    database: str | None = dataclasses.field(
        metadata={"required": False, "description": "Postgres database name"}
    )
    port: str | None = dataclasses.field(
        default="5432", metadata={"required": False, "description": "Postgres port"}
    )


class PostgresProvider(BaseProvider):
    def __init__(self, provider_id: str, config: ProviderConfig):
        super().__init__(provider_id, config)
        self.conn = None

    def __init_connection(self):
        """
        Generates a Postgres connection.

        Returns:
            psycopg2 connection object
        """
        conn = psycopg2.connect(
            dbname=self.authentication_config.database,
            user=self.authentication_config.username,
            password=self.authentication_config.password,
            host=self.authentication_config.host,
            port=self.authentication_config.port,
        )
        self.conn = conn
        return conn

    def dispose(self):
        try:
            self.conn.close()
        except Exception:
            self.logger.exception("Error closing Postgres connection")

    def validate_config(self):
        """
        Validates required configuration for Postgres's provider.
        """
        self.authentication_config = PostgresProviderAuthConfig(
            **self.config.authentication
        )

    def query(self, **kwargs: dict) -> list | tuple:
        """
        Executes a query against the Postgres database.

        Returns:
            list | tuple: list of results or single result if single_row is True
        """
        query = kwargs.get("query")
        if not query:
            raise ValueError("Query is required")

        conn = self.__init_connection()
        try:
            with conn.cursor() as cur:
                # Open a cursor to perform database operations
                cur = conn.cursor()
                # Execute a simple query
                cur.execute(query)
                # Fetch the results
                results = cur.fetchall()
                # Close the cursor and connection
                cur.close()
                conn.close()
            return list(results)
        finally:
            # Close the database connection
            conn.close()

    def notify(self, **kwargs):
        """
        Notifies the Postgres database.
        """
        # notify and query are the same for Postgres
        query = kwargs.get("query")
        if not query:
            raise ValueError("Query is required")

        conn = self.__init_connection()
        try:
            with conn.cursor() as cur:
                # Open a cursor to perform database operations
                cur = conn.cursor()
                # Execute a simple query
                cur.execute(query)
                # Close the cursor and connection
                cur.close()
                conn.commit()
                conn.close()
        finally:
            # Close the database connection
            conn.close()


if __name__ == "__main__":
    config = ProviderConfig(
        authentication={
            "username": os.environ.get("POSTGRES_USER"),
            "password": os.environ.get("POSTGRES_PASSWORD"),
            "host": os.environ.get("POSTGRES_HOST"),
            "database": os.environ.get("POSTGRES_DATABASE"),
        }
    )
    postgres_provider = PostgresProvider("postgres-prod", config)
    results = postgres_provider.query(query="select * from disk")
    print(results)