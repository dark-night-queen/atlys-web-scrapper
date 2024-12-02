import json

import redis
from loguru import logger


class Cache:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0) -> None:
        """
        Initialize a Redis cache instance & clear the existing database
        :param host:
        :param port:
        :param db:
        """
        self.redis = redis.Redis(host=host, port=port, db=db)
        self.clear()

    def get(self, key: str) -> any:
        """
        Get the value from the Redis database
        :param key:
        :return:
        """
        return self.redis.get(key)

    def set(self, key: str, value: str) -> None:
        """
        Set the value in the Redis database
        :param key:
        :param value:
        :return:
        """
        self.redis.set(key, value)

    def clear(self) -> None:
        """
        Clear the Redis database
        :return:
        """
        logger.info("Current Redis database cleared!")
        self.redis.flushdb()

    def get_all_keys(self) -> list:
        """
        Get all keys from the Redis database
        :return:
        """
        cursor = 0
        keys = []

        while True:
            cursor, partial_keys = self.redis.scan(cursor)
            keys.extend(partial_keys)
            if cursor == 0:
                break

        return keys

    def export(self, filename: str, headers: list[str]) -> None:
        """
        Export the current state of the Redis database into csv file
        :return:
        """
        # Retrieve all keys using SCAN
        keys = self.get_all_keys()

        logger.info(f"Total keys in the database: {len(keys)}")
        # store the keys in csv file

        with open(f"export_{filename}.csv", "w") as f:
            title = ", ".join(headers)
            f.write(f"{title}\n")

            for key in keys:
                value = self.get(key).decode("utf-8")

                # check if the value is a json string
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    pass

                body = ", ".join(value[_key] for _key in headers)
                f.write(f"{body}\n")


cache = Cache()
