from app.core.config import Settings


def test_settings_defaults_to_local_environment() -> None:
    assert Settings(_env_file=None).environment == "local"


def test_api_prefix_is_versioned() -> None:
    assert Settings(_env_file=None).api_prefix == "/v1"
