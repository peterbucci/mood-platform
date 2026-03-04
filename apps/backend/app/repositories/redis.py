from redis import Redis


class RedisRepository:
    def check_connection(self, redis_url: str) -> str:
        try:
            client = Redis.from_url(redis_url, socket_connect_timeout=3, socket_timeout=3)
            try:
                client.ping()
            finally:
                client.close()
            return "ok"
        except Exception as exc:
            return f"redis check failed: {exc}"
