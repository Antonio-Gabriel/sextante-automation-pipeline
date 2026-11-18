"""Application settings, read from SEXTANTE_ environment variables (02-arquitectura.md §10)."""

from collections.abc import Mapping
from pathlib import Path
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError, field_validator

ENV_PREFIX: Final = "SEXTANTE_"
SETTING_TEXT_MAX_LENGTH: Final = 512
# The SQLite pragmas of D-3.5 assume SQLite; another engine is refused until the
# PostgreSQL migration path of 00-decisoes-e-lacunas.md §6 is taken.
DATABASE_URL_PREFIX: Final = "sqlite+aiosqlite:///"
CSV_SEPARATORS: Final = frozenset({",", ";", "|"})


class StartupConfigurationError(RuntimeError):
    """Raised when the application cannot start with the configuration it was given."""


class Settings(BaseModel):
    """Mandatory configuration. No defaults: a missing value refuses startup (SEC-02, REQ-PLT-007).

    Example:
        settings = Settings.from_environment({"SEXTANTE_CATALOG_PATH": "catalog.xlsx", ...})
    """

    anthropic_api_key: SecretStr = Field(max_length=SETTING_TEXT_MAX_LENGTH)
    catalog_path: Path
    database_url: SecretStr = Field(max_length=SETTING_TEXT_MAX_LENGTH)
    target_entity_name: str = Field(max_length=SETTING_TEXT_MAX_LENGTH)
    target_entity_nif: str = Field(max_length=SETTING_TEXT_MAX_LENGTH)
    upload_dir: Path
    entity_denylist_path: Path
    # Items that fit any expense; choosing one is always LOW and flagged (D-3.16).
    # Comma-separated item numbers; tuning, not a secret, so it has a default.
    generic_items: tuple[str, ...] = ("O00052",)
    # CSV separator, comma by default (REQ-EXP-005).
    csv_separator: str = ","
    # Attempts per model call, the first included, for transient failures (REQ-PLT-003).
    model_max_attempts: int = Field(default=3, ge=1, le=10)

    # A plain model, not pydantic-settings: the environment is always passed in explicitly,
    # so a stray variable in the process cannot silently fill a missing setting.
    model_config = ConfigDict(frozen=True, extra="ignore")

    @field_validator("*", mode="before")
    @classmethod
    def _refuse_blank(cls, value: object) -> object:
        # An empty or whitespace-only value is as missing as an absent one (REQ-PLT-007).
        if isinstance(value, str) and not value.strip():
            raise ValueError("value is blank. Expected a non-empty value")
        return value.strip() if isinstance(value, str) else value

    @field_validator("generic_items", mode="before")
    @classmethod
    def _split_items(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(part.strip() for part in value.split(",") if part.strip())
        return value

    @field_validator("csv_separator")
    @classmethod
    def _known_separator(cls, value: str) -> str:
        if value not in CSV_SEPARATORS:
            raise ValueError(
                f"unsupported separator {value!r}. Expected one of {sorted(CSV_SEPARATORS)}"
            )
        return value

    @field_validator("database_url")
    @classmethod
    def _require_sqlite(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().startswith(DATABASE_URL_PREFIX):
            raise ValueError(f"unsupported database. Expected a URL starting {DATABASE_URL_PREFIX}")
        return value

    @classmethod
    def from_environment(cls, environ: Mapping[str, str]) -> "Settings":
        """Build settings from an explicit environment mapping, never from implicit globals.

        Example:
            settings = Settings.from_environment(os.environ)

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
        f"{ENV_PREFIX}{str(issue['loc'][0]).upper()}: {issue['msg']}"
        for issue in error.errors(include_input=False, include_url=False, include_context=False)
    ]
    return "Invalid or missing configuration. " + "; ".join(problems)
