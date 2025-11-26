import os

_ENV_TARGETS = {
    "demo": {
        "datagouv_api": "https://demo.data.gouv.fr/api/",
        "site": "https://demo.data.gouv.fr/",
        "tabular_api": "https://tabular-api.preprod.data.gouv.fr/api/",
        "metrics_api": "https://metric-api.data.gouv.fr/api/",  # No demo/preprod for Metrics API
    },
    "prod": {
        "datagouv_api": "https://www.data.gouv.fr/api/",
        "site": "https://www.data.gouv.fr/",
        "tabular_api": "https://tabular-api.data.gouv.fr/api/",
        "metrics_api": "https://metric-api.data.gouv.fr/api/",
    },
}


def get_current_environment() -> str:
    """
    Return the environment name selected via DATAGOUV_ENV (demo|prod), defaulting to prod.
    """
    value = os.getenv("DATAGOUV_ENV")
    if not value:
        return "prod"
    value = value.strip().lower()
    if value in _ENV_TARGETS:
        return value
    return "prod"


def get_env_config(env_name: str | None = None) -> dict[str, str]:
    """
    Get the configuration for a specific environment.

    Args:
        env_name: Environment name (demo|prod). If None, uses current environment.

    Returns:
        Dictionary with API endpoints for the environment.
    """
    if env_name is None:
        env_name = get_current_environment()
    return _ENV_TARGETS.get(env_name, _ENV_TARGETS["prod"])


def frontend_base_url() -> str:
    """
    Return the public site base URL matching the current environment (demo or prod).
    """
    config = get_env_config()
    return config["site"]
