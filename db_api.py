import contextlib
from typing import Optional, AsyncIterator

import asyncpg
from config_loader import config

class Database:

    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None

    # user queries
    async def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS users (
        id serial PRIMARY KEY,
        telegram_id BIGINT NOT NULL UNIQUE 
        );
        """
        await self.execute(sql, execute=True)

    async def add_user(self, telegram_id):
        sql = "INSERT INTO users (telegram_id) VALUES($1) returning *"
        return dict(await self.execute(sql, telegram_id, fetchrow=True))

    async def select_user(self, **kwargs):
        sql = "SELECT * FROM users WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return dict(await self.execute(sql, *parameters, fetchrow=True))
    
    async def select_users(self):
        sql = "SELECT * FROM users"
        return [dict(i) for i in list(await self.execute(sql, fetch=True))]
    
    # scripts queries
    async def create_scripts_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS scripts (
        id serial PRIMARY KEY,
        name VARCHAR NOT NULL,
        intervals_json VARCHAR NOT NULL
        );
        """
        return await self.execute(sql, execute=True)
    
    async def add_script(self, name: str, intervals_json: str):
        sql = "INSERT INTO scripts (name, intervals_json) VALUES($1, $2) returning *"
        return await self.execute(sql, name, intervals_json, execute=True)
    
    async def select_script(self, **kwargs):
        sql = "SELECT * FROM scripts WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return dict(await self.execute(sql, *parameters, fetchrow=True))
    
    async def search_script(self, name):
        sql = f"SELECT * FROM scripts WHERE name ILIKE {name}"
        return dict(await self.execute(sql, fetchrow=True))
    
    async def select_scripts(self):
        sql = "SELECT * FROM scripts"
        return [dict(i) for i in list(await self.execute(sql, fetch=True))]
    
    async def delete_script(self, **kwargs):
        sql = "DELETE FROM scripts WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, execute=True)
    
    async def update_script(self, id: int, intervals_json: str):
        sql = "UPDATE scripts SET intervals_json=$1 WHERE id=$2 RETURNING *"
        return await self.execute(sql, intervals_json, id, execute=True)

    async def execute(self, command, *args,
                      fetch: bool = False,
                      fetchval: bool = False,
                      fetchrow: bool = False,
                      execute: bool = False
                      ):
        result = None
        async with self._transaction() as connection:  # type: asyncpg.Connection
            if fetch:
                result = await connection.fetch(command, *args)
            elif fetchval:
                result = await connection.fetchval(command, *args)
            elif fetchrow:
                result = await connection.fetchrow(command, *args)
            elif execute:
                result = await connection.execute(command, *args)
        return result

    @contextlib.asynccontextmanager
    async def _transaction(self) -> AsyncIterator[asyncpg.Connection]:
        if self._pool is None:
            
            self._pool = await asyncpg.create_pool(
                user=config.postgres_user.get_secret_value(),
                password=config.postgres_password.get_secret_value(),
                host=config.host.get_secret_value(),
                database=config.postgres_db.get_secret_value(),
            )
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            async with conn.transaction():
                yield conn

    async def close(self) -> None:
        if self._pool is None:
            return None

        await self._pool.close()

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join([
            f"{item} = ${num}" for num, item in enumerate(parameters.keys(),
                                                          start=1)
        ])
        return sql, tuple(parameters.values())
    

db = Database()