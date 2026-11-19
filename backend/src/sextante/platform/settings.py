"""Application settings, read from SEXTANTE_ environment variables (02-arquitectura.md §10)."""

from collections.abc import Mapping
from pathlib import Path
from typing import Final

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    ValidationError,
    field_validator,
    model_validator,
)

ENV_PREFIX: Final = "SEXTANTE_"
SETTING_TEXT_MAX_LENGTH: Final = 512
# The SQLite pragmas of D-3.5 assume SQLite; another engine is refused until the
# PostgreSQL migration path of 00-decisoes-e-lacunas.md §6 is taken.
DATABASE_URL_PREFIX: Final = "sqlite+aiosqlite:///"
CSV_SEPARATORS: Final = frozenset({",", ";", "|"})
# A key a person could guess is refused at startup.
API_KEY_MIN_LENGTH: Final = 16
RATE_LIMIT_MAXIMUM: Final = 100_000
SESSION_HOURS_MAXIMUM: Final = 24
MODEL_CALL_WINDOW_MAXIMUM_SECONDS: Final = 86_400
PDF_MIN_CHARS_DEFAULT: Final = 100
PDF_MIN_CHARS_MAXIMUM: Final = 10_000
REVIEWER_ID_MAX_LENGTH: Final = 128
REVIEWER_ID_PATTERN: Final = r"^[A-Za-z0-9._@-]+$"


class StartupConfigurationError(RuntimeError):
    """Raised when the application cannot start with the configuration it was given."""


class ModelCallSettings(BaseModel):
    """Settings of the model call, shared by the application and the manual golden run.

    Example:
        ModelCallSettings.model_validate({"anthropic_api_key": "..."}).model_id
    """

    anthropic_api_key: SecretStr = Field(max_length=SETTING_TEXT_MAX_LENGTH)
    # Items that fit any expense; choosing one is always LOW and flagged (D-3.16).
    # Comma-separated item numbers; tuning, not a secret, so it has a default.
    generic_items: tuple[str, ...] = ("O00052",)
    # Attempts per model call, the first included, for transient failures (REQ-PLT-003).
    model_max_attempts: int = Field(default=3, ge=1, le=10)
    # Claude model of the item choice: Sonnet by default, for cost (D-3.22, revised).
    model_id: str = Field(default="claude-sonnet-5-5", pattern=r"^[a-z0-9.-]{1,64}$")

    @field_validator("generic_items", mode="before")
    @classmethod
    def _split_items(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(part.strip() for part in value.split(",") if part.strip())
        return value


class Settings(ModelCallSettings):
    """Mandatory configuration. No defaults: a missing value refuses startup (SEC-02, REQ-PLT-007).

    Example:
        settings = Settings.from_environment({"SEXTANTE_CATALOG_PATH": "catalog.xlsx", ...})
    """

    catalog_path: Path
    database_url: SecretStr = Field(max_length=SETTING_TEXT_MAX_LENGTH)
    target_entity_name: str = Field(max_length=SETTING_TEXT_MAX_LENGTH)
    target_entity_nif: str = Field(max_length=SETTING_TEXT_MAX_LENGTH)
    upload_dir: Path
    # Key every /api call but health must carry in X-API-Key (L-07, revised 2026-11-19).
    api_key: SecretStr = Field(min_length=API_KEY_MIN_LENGTH, max_length=SETTING_TEXT_MAX_LENGTH)
    # Token a person types to open a browser session (SEC-06, frontend ticket 01).
    access_token: SecretStr = Field(
        min_length=API_KEY_MIN_LENGTH, max_length=SETTING_TEXT_MAX_LENGTH
    )
    # Life of a session, absolute from login, and whether its cookie is Secure.
    session_hours: int = Field(default=8, ge=1, le=SESSION_HOURS_MAXIMUM)
    session_cookie_secure: bool = True
    # The interactive API documentation (/docs, /redoc, /openapi.json). Open by default
    # for local use; off where the server is public (docs/02 §6, SEC-15, decision 3.27).
    api_docs_enabled: bool = True
    # The release this process runs, set in the image by the release pipeline; shown by
    # the health check so a deploy can be confirmed (decision 3.27).
    release_version: str = Field(default="dev", max_length=64, pattern=r"^[0-9A-Za-z.+-]+$")
    entity_denylist_path: Path
    # Author of every review action in the audit trail: there is no login in this
    # version (L-07), so the identity comes from configuration (REQ-REV-004).
    reviewer_id: str = Field(max_length=REVIEWER_ID_MAX_LENGTH, pattern=REVIEWER_ID_PATTERN)
    # CSV separator, comma by default (REQ-EXP-005).
    csv_separator: str = ","
    # Rate limits per caller (SEC-12). Defaults are the table of SEC-12.
    rate_limit_upload_per_minute: int = Field(default=10, ge=1, le=RATE_LIMIT_MAXIMUM)
    rate_limit_reprocess_per_hour: int = Field(default=20, ge=1, le=RATE_LIMIT_MAXIMUM)
    rate_limit_export_per_hour: int = Field(default=30, ge=1, le=RATE_LIMIT_MAXIMUM)
    rate_limit_correction_per_minute: int = Field(default=120, ge=1, le=RATE_LIMIT_MAXIMUM)
    rate_limit_general_per_minute: int = Field(default=300, ge=1, le=RATE_LIMIT_MAXIMUM)
    rate_limit_login_per_minute: int = Field(default=10, ge=1, le=RATE_LIMIT_MAXIMUM)
    # Ceiling on model calls per window, in the worker: over it invoices wait queued
    # (SEC-12). Provisional default, to calibrate with the real volume (L-02).
    model_call_ceiling: int = Field(default=200, ge=1, le=RATE_LIMIT_MAXIMUM)
    model_call_window_seconds: int = Field(default=3600, ge=1, le=MODEL_CALL_WINDOW_MAXIMUM_SECONDS)
    # Limits of reading one PDF in its own process (SEC-16): address space and time.
    pdf_extraction_memory_mib: int = Field(default=512, ge=128, le=8192)
    pdf_extraction_timeout_seconds: int = Field(default=30, ge=1, le=600)
    # Characters per page below which a PDF counts as scanned (REQ-ING-002, L-01).
    pdf_min_chars_per_page: int = Field(
        default=PDF_MIN_CHARS_DEFAULT, ge=1, le=PDF_MIN_CHARS_MAXIMUM
    )

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

    @field_validator("csv_separator")
    @classmethod
    def _known_separator(cls, value: str) -> str:
        if value not in CSV_SEPARATORS:
            raise ValueError(
                f"unsupported separator {value!r}. Expected one of {sorted(CSV_SEPARATORS)}"
            )
        return value

    @model_validator(mode="after")
    def _token_apart_from_key(self) -> "Settings":
        # A person's token and a program's key are two credentials; one value for both
        # would hand the key to everyone who logs in.
        if self.access_token.get_secret_value() == self.api_key.get_secret_value():
            raise ValueError(
                "SEXTANTE_ACCESS_TOKEN equals SEXTANTE_API_KEY. Expected two different values"
            )
        return self

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
    # A rule across settings has no single variable: its message names the variables.
    problems = [
        f"{ENV_PREFIX}{str(issue['loc'][0]).upper()}: {issue['msg']}"
        if issue["loc"]
        else issue["msg"]
        for issue in error.errors(include_input=False, include_url=False, include_context=False)
    ]
    return "Invalid or missing configuration. " + "; ".join(problems)
