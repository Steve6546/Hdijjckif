# cache_manager.py
import redis
import logging
import os

logger = logging.getLogger(__name__)

class CacheManager:
    """Handles caching using Redis."""

    def __init__(self, host: str = None, port: int = 6379, db: int = 0):
        """
        Initializes the Redis connection.
        Reads connection details from environment variables if available,
        otherwise uses defaults.

        Args:
            host (str, optional): Redis server host. Defaults to REDIS_HOST env var or 'localhost'.
            port (int, optional): Redis server port. Defaults to REDIS_PORT env var or 6379.
            db (int, optional): Redis database number. Defaults to REDIS_DB env var or 0.
        """
        # Get Redis config from environment variables or use defaults
        self.redis_host = host or os.getenv('REDIS_HOST', 'localhost')
        try:
            self.redis_port = port or int(os.getenv('REDIS_PORT', 6379))
        except ValueError:
            logger.warning(f"Invalid REDIS_PORT environment variable. Using default 6379.")
            self.redis_port = 6379
        try:
            self.redis_db = db or int(os.getenv('REDIS_DB', 0))
        except ValueError:
             logger.warning(f"Invalid REDIS_DB environment variable. Using default 0.")
             self.redis_db = 0

        self.redis_connection = None
        try:
            # Establish connection pool
            logger.info(f"Attempting to connect to Redis at {self.redis_host}:{self.redis_port}, DB {self.redis_db}")
            # Using decode_responses=False to store bytes directly, handle decoding in get() if needed
            self.redis_connection = redis.StrictRedis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=False # Store raw bytes
            )
            # Test connection
            self.redis_connection.ping()
            logger.info("Successfully connected to Redis.")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Failed to connect to Redis at {self.redis_host}:{self.redis_port}. Caching will be disabled. Error: {e}")
            self.redis_connection = None # Disable caching if connection fails
        except Exception as e:
            logger.error(f"An unexpected error occurred during Redis initialization: {e}", exc_info=True)
            self.redis_connection = None

    def get(self, key: str) -> bytes | None:
        """
        Retrieves a value from the cache.

        Args:
            key (str): The key to retrieve.

        Returns:
            bytes | None: The cached value as bytes if found, otherwise None.
        """
        if not self.redis_connection:
            # logger.debug("Redis connection not available, skipping cache get.")
            return None
        try:
            value = self.redis_connection.get(key)
            if value:
                logger.debug(f"Cache hit for key: {key}")
            else:
                logger.debug(f"Cache miss for key: {key}")
            return value
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error getting key '{key}': {e}")
            return None

    def set(self, key: str, value: str | bytes, expire: int | None = None):
        """
        Stores a value in the cache.

        Args:
            key (str): The key to store the value under.
            value (str | bytes): The value to store. If str, it will be utf-8 encoded.
            expire (int | None, optional): Time-to-live in seconds. Defaults to None (no expiration).
        """
        if not self.redis_connection:
            # logger.debug("Redis connection not available, skipping cache set.")
            return

        try:
            # Ensure value is bytes
            if isinstance(value, str):
                value_bytes = value.encode('utf-8')
            else:
                value_bytes = value

            self.redis_connection.set(key, value_bytes, ex=expire)
            logger.debug(f"Cached value for key: {key}" + (f" with expiry {expire}s" if expire else ""))
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error setting key '{key}': {e}")

    def delete(self, key: str):
        """
        Deletes a key from the cache.

        Args:
            key (str): The key to delete.
        """
        if not self.redis_connection:
            # logger.debug("Redis connection not available, skipping cache delete.")
            return
        try:
            self.redis_connection.delete(key)
            logger.debug(f"Deleted key from cache: {key}")
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error deleting key '{key}': {e}")

# Example usage (optional, for testing)
if __name__ == "__main__":
    # Ensure Redis server is running locally on default port for this test
    print("Testing CacheManager...")
    cache = CacheManager()

    if cache.redis_connection:
        key = "test_key"
        value = "test_value_123"
        expiry_seconds = 10

        print(f"\nSetting key '{key}' with value '{value}' and expiry {expiry_seconds}s")
        cache.set(key, value, expire=expiry_seconds)

        print(f"Getting key '{key}'...")
        retrieved_value = cache.get(key)
        if retrieved_value:
            print(f"Retrieved value: {retrieved_value.decode()}") # Decode bytes for printing
        else:
            print("Value not found or expired.")

        print(f"\nGetting non-existent key 'missing_key'...")
        missing_value = cache.get("missing_key")
        print(f"Retrieved value for missing key: {missing_value}")

        print(f"\nDeleting key '{key}'...")
        cache.delete(key)
        retrieved_after_delete = cache.get(key)
        print(f"Value after delete: {retrieved_after_delete}")

        print("\nTesting storing bytes:")
        byte_key = "byte_test"
        byte_value = b'\x01\x02\x03\xff'
        cache.set(byte_key, byte_value)
        retrieved_bytes = cache.get(byte_key)
        print(f"Retrieved bytes: {retrieved_bytes}")

    else:
        print("\nCould not connect to Redis. Skipping tests.")

    print("\nCacheManager test finished.")