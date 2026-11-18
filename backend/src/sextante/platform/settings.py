"""Application settings, read from SEXTANTE_ environment variables (02-arquitectura.md §10)."""

from collections.abc import Mapping
from pathlib import Path
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError

ENV_PREFIX: Final = "SEXTANTE_"
SETTING_TEXT_MAX_LENGTH: Final = 512


class StartupConfigurationError(RuntimeError):
    """Raised when the application cannot start with the configuration it was given."""


class Settings(BaseModel):
    """Mandatory configuration. No defaults: a missing value refuses startup (SEC-02, REQ-PLT-007).

    Example:
        settings = Settings.from_environment(os.environ)
    """

    anthropic_api_key: SecretStr = Field(max_length=SETTING_TEXT_MAX_LENGTH)
    catalog_path: Path
    database_url: SecretStr = Field(max_length=SETTING_TEXT_MAX_LENGTH)
    target_entity_name: str = Field(min_length=1, max_length=SETTING_TEXT_MAX_LENGTH)
    target_entity_nif: str = Field(min_length=1, max_length=SETTING_TEXT_MAX_LENGTH)

    # A plain model, not pydantic-settings: the environment is always passed in explicitly,
    # so a stray variable in the process cannot silently fill a missing setting.
    model_config = ConfigDict(frozen=True, extra="ignore")

    @classmethod
    def from_environment(cls, environ: Mapping[str, str]) -> "Settings":
        """Build settings from an explicit environment mapping, never from implicit globals.

        Raises:
            StartupConfigurationError: naming each offending variable, never its value.
        """
        values = {
            name.removeprefix(ENV_PREFIX).lower(): value
            for name, value in environ.items()
            if name.startswith(ENV_PREFIX)
        }
        try:
            return cls.model_validate(values)
        except ValidationError as error:
            raise StartupConfigurationError(_describe_invalid_settings(error)) from None


def _describe_invalid_settings(error: ValidationError) -> str:
    # Only the variable name and the kind of problem are reported. The input value is
    # left out on purpose, because it may be a secret (SEC-02, SEC-15).
    problems = [
        f"{ENV_PREFIX}{str(issue['loc'][0]).upper()}: {issue['type']}"
        for issue in error.errors(include_input=False, include_url=False)
    ]
    return "Invalid or missing configuration. " + "; ".join(problems)
