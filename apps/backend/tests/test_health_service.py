from app.services.health_service import HealthService


class MockPostgresRepository:
    def __init__(self, result: str) -> None:
        self.result = result
        self.calls: list[str] = []

    def check_connection(self, database_url: str) -> str:
        self.calls.append(database_url)
        return self.result


class MockRedisRepository:
    def __init__(self, result: str) -> None:
        self.result = result
        self.calls: list[str] = []

    def check_connection(self, redis_url: str) -> str:
        self.calls.append(redis_url)
        return self.result


def test_get_liveness_returns_alive() -> None:
    service = HealthService(
        postgres_repository=MockPostgresRepository(result="ok"),
        redis_repository=MockRedisRepository(result="ok"),
    )

    assert service.get_liveness() == {"status": "alive"}


def test_get_readiness_returns_ready_when_checks_pass(monkeypatch) -> None:
    postgres_repo = MockPostgresRepository(result="ok")
    redis_repo = MockRedisRepository(result="ok")
    service = HealthService(
        postgres_repository=postgres_repo,
        redis_repository=redis_repo,
    )
    monkeypatch.setenv("DATABASE_URL", "postgresql://mood:mood@localhost:5432/mood")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

    is_ready, checks = service.get_readiness()

    assert is_ready is True
    assert checks == {"postgres": "ok", "redis": "ok"}
    assert postgres_repo.calls == ["postgresql://mood:mood@localhost:5432/mood"]
    assert redis_repo.calls == ["redis://localhost:6379/0"]


def test_get_readiness_reports_missing_environment_variables(monkeypatch) -> None:
    service = HealthService(
        postgres_repository=MockPostgresRepository(result="ok"),
        redis_repository=MockRedisRepository(result="ok"),
    )
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)

    is_ready, checks = service.get_readiness()

    assert is_ready is False
    assert checks == {
        "postgres": "DATABASE_URL is not set",
        "redis": "REDIS_URL is not set",
    }


def test_get_readiness_returns_not_ready_on_repository_errors(monkeypatch) -> None:
    service = HealthService(
        postgres_repository=MockPostgresRepository(result="postgres check failed: timeout"),
        redis_repository=MockRedisRepository(result="redis check failed: timeout"),
    )
    monkeypatch.setenv("DATABASE_URL", "postgresql://mood:mood@localhost:5432/mood")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

    is_ready, checks = service.get_readiness()

    assert is_ready is False
    assert checks == {
        "postgres": "postgres check failed: timeout",
        "redis": "redis check failed: timeout",
    }
