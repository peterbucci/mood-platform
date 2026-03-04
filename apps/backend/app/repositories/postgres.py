import psycopg


class PostgresRepository:
    def check_connection(self, database_url: str) -> str:
        try:
            with psycopg.connect(database_url, connect_timeout=3) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            return "ok"
        except Exception as exc:
            return f"postgres check failed: {exc}"
