from app.core.config import Settings


def test_settings_defaults_to_local_environment() -> None:
    assert Settings(_env_file=None).environment == "local"


def test_api_prefix_is_versioned() -> None:
    assert Settings(_env_file=None).api_prefix == "/v1"


def test_jobs_settings_have_local_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.jobs_queue_name == "market-hub-jobs"
    assert settings.jobs_dlq_name == "market-hub-jobs-dlq"
    assert settings.reconcile_page_size == 50
    assert settings.jobs_max_receive_count == 3
    assert settings.aws_endpoint_url == "http://localhost:4566"
