import asyncio
import time

from passlib.context import CryptContext
from sqlalchemy import (update, NullPool, Boolean, func, insert, Table, Column, Integer, String, MetaData, select, delete, desc)
from sqlalchemy.ext.asyncio import create_async_engine


class DatabaseConnector:
    """
    Class that implements methods for interacting with the database using sqlalchemy
    """
    meta = MetaData()
    users = Table(
        "users",
        meta,
        Column("id", Integer, primary_key=True),
        Column("login", String, nullable=False, unique=True),
        Column("password", String, nullable=False),
    )

    applications = Table(
        "applications",
        meta,
        Column("id", Integer, primary_key=True),
        Column("bundle_id", String, unique=True),
        Column("allow_execution", Boolean),
        Column("last_access_time", Integer)
    )

    def __init__(self, db_conn_string: str):
        self.engine = create_async_engine(db_conn_string, poolclass=NullPool)
        asyncio.run(self.__create_meta())

    async def __create_meta(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(self.meta.create_all)

    async def create_user(self, login: str, password: str) -> None:
        """
        Create user for bot in database.
        Args:
            login (str): new user login.
            password (str): new user password.
        """
        async with self.engine.connect() as conn:
            query = insert(self.users).values(login=login, password=self.__get_password_hash(password))
            await conn.execute(query)
            await conn.commit()

    async def validate_user(self, login: str, password: str) -> bool:
        """
        Validate user by user credentials.
        Args:
            login (str): user login.
            password (str): user password.
        Returns:
            bool: Is valid credentials.
        """
        async with self.engine.connect() as conn:
            query = select(self.users.c.password).where(self.users.c.login == login)
            result = await conn.execute(query)
            pass_hash = result.fetchall()
            if len(pass_hash) > 0:
                return self.__verify_password(password, pass_hash[0][0])
            else:
                return False

    async def is_bundle_exists(self, bundle_id: str) -> bool:
        """
        Check is application exists in database.
        Args:
            bundle_id (str): Application identifier e.g. com.example.app.
        Returns:
            bool: Is bundle exists in database.
        """
        async with self.engine.connect() as conn:
            query = select(self.applications.c.id).where(self.applications.c.bundle_id == bundle_id)
            result = await conn.execute(query)
            bundle = result.fetchall()
            return len(bundle) > 0

    async def check_or_create_bundle(self, bundle_id: str, ping_time: int = None) -> bool:
        """
        Check if the application launch is allowed.
        If the application exists, return its launch status.
        If not, create the application in the database and allow its launch.
        Also updates the last launch permission check time.

        Args:
            bundle_id (str): Application identifier (e.g., com.example.app).
            ping_time (int): Timestamp of the check.

        Returns:
            bool: Whether the application launch is allowed.
        """

        if ping_time is None:
            ping_time = int(time.time())

        async with self.engine.connect() as conn:
            if await self.is_bundle_exists(bundle_id):
                query = select(self.applications.c.allow_execution).where(self.applications.c.bundle_id == bundle_id)
                result = await conn.execute(query)
                allowance = result.fetchall()
                query = (
                    update(self.applications)
                    .values(last_access_time=ping_time)
                    .where(self.applications.c.bundle_id == bundle_id)
                )
                await conn.execute(query)
                await conn.commit()
                return allowance[0][0]
            else:
                query = (
                    insert(self.applications)
                    .values(bundle_id=bundle_id, allow_execution=True, last_access_time=ping_time)
                )
                await conn.execute(query)
                await conn.commit()
                return True

    async def change_execution_for_bundle(self, bundle_id: str, execution_status: bool) -> None:
        """
        Set launch allowance for application.
        Args:
            bundle_id (str): Application identifier e.g. com.example.app.
            execution_status (bool): launch allowance.
        """
        async with self.engine.connect() as conn:
            if await self.is_bundle_exists(bundle_id):
                query = (
                    update(self.applications)
                    .values(allow_execution=execution_status)
                    .where(self.applications.c.bundle_id == bundle_id)
                )
                await conn.execute(query)
                await conn.commit()
            else:
                await self.check_or_create_bundle(bundle_id)
                query = (
                    update(self.applications)
                    .values(allow_execution=execution_status)
                    .where(self.applications.c.bundle_id == bundle_id)
                )
                await conn.execute(query)
                await conn.commit()

    async def remove_bundle(self, bundle_id: str) -> None:
        """
        Remove application from database.
        Args:
            bundle_id (str): Application identifier e.g. com.example.app.
        """
        async with self.engine.connect() as conn:
            query = delete(self.applications).where(self.applications.c.bundle_id == bundle_id)
            await conn.execute(query)
            await conn.commit()

    async def get_bundles_list(self, limit: int, offset: int) -> tuple[int, list[list[str, bool]]]:
        """
        Get the list of applications with a specified offset and limit on the number of rows.

        Args:
            limit (int): Maximum number of rows to return.
            offset (int): Number of rows to skip before starting to return rows.

        Returns:
            int: Total number of applications in the database.

            list[list[str, bool]]: A list of lists, where each inner list contains:
                - str: Application identifier.
                - bool: Launch status.
        """
        async with self.engine.connect() as conn:
            count_query = select(func.count()).select_from(self.applications)
            result = await conn.execute(count_query)
            count = result.fetchall()[0][0]
            if count == 0:
                return 0, []
            else:
                data = (
                    select(self.applications.c.bundle_id, self.applications.c.allow_execution)
                    .limit(limit)
                    .offset(offset)
                    .order_by(desc(self.applications.c.last_access_time))
                )
                result = await conn.execute(data)
                data = result.fetchall()
                return count, data

    async def get_bundle_info(self, bundle_id: str) -> tuple[bool, int]:
        """
        Get application info by application id.
        Args:
            bundle_id (str): Limit rows.
        Returns:
            bool: Launch allowance.

            int: Last application launch allowance check timestamp.
        """
        async with self.engine.connect() as conn:
            bundle_status = (
                select(self.applications.c.allow_execution, self.applications.c.last_access_time)
                .where(self.applications.c.bundle_id == bundle_id)
            )
            result = await conn.execute(bundle_status)
            result = result.fetchall()
            bundle_status = result[0][0]
            bundle_last_ping = result[0][1]
            return bundle_status, bundle_last_ping

    async def is_exists(self, username: str) -> bool:
        """
        Check is user exists in database.
        Args:
            username (str): Username to check.
        Returns:
            bool: Is user exists in database.
        """
        async with self.engine.connect() as conn:
            query = select(self.users.c.password).where(self.users.c.login == username)
            result = await conn.execute(query)
            pass_hash = result.fetchall()
            return len(pass_hash) > 0

    @staticmethod
    def __get_password_hash(password: str) -> str:
        """
        Generate password hash from string.
        Args:
            password (str): password for hashing
        Returns:
            str: bcrypt hash
        """
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)

    @staticmethod
    def __verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify password for specific hash.
        Args:
            plain_password (str): password for verify
            hashed_password (str): hash for verify
        Returns:
            bool: is hash matched to password
        """
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(plain_password, hashed_password)

    async def get_usernames(self) -> list[str]:
        """
        Get users list.
        Args:

        Returns:
            list[str]: List with usernames
        """
        async with self.engine.connect() as conn:
            query = select(self.users.c.login)
            result = await conn.execute(query)
            users = []
            for row in result:
                users.append(row[0])
            return users

    async def remove_user(self, username: str) -> None:
        """
        Remove user from database
        Args:
            username (str): User for removing from database
        """
        async with self.engine.connect() as conn:
            query = delete(self.users).where(self.users.c.login == username)
            await conn.execute(query)
            await conn.commit()

    async def change_password(self, username: str, password: str) -> None:
        """
        Change password for specific user
        Args:
            username (str): User for changing password.
            password (str): New password.
        """
        async with self.engine.connect() as conn:
            query = (
                update(self.users)
                .values(password=self.__get_password_hash(password))
                .where(self.users.c.login == username)
            )
            await conn.execute(query)
            await conn.commit()

    async def search_by_bundle_id(self, search_query: str, limit: int = 50) -> list[list[str, bool, int]]:
        """
        Search for applications by the substring that is inside the application identifier.
        Args:
            search_query (str): Substring for search.
            limit (int): Maximum number of rows to return.
        Returns:
            list[list[Union[str, bool, int]]]: list of lists, where each inner list contains:
                - str: application id.
                - bool: execution status.
                - int: last access time.
        """
        async with self.engine.connect() as conn:
            query = (
                select(
                    self.applications.c.bundle_id,
                    self.applications.c.allow_execution,
                    self.applications.c.last_access_time
                )
                .where(self.applications.c.bundle_id.like(f"%{search_query}%"))
                .limit(limit))
            data = await conn.execute(query)
            return data.fetchall()
