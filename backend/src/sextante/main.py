"""Application factory. Started with ``uvicorn --factory sextante.main:create_app``."""

import os
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager

from fastapi import FastAPI

from sextante.api.health import health_router
from sextante.catalog.application.load_catalog import load_catalog
from sextante.catalog.domain.catalog_builder import BuiltCatalog
from sextante.catalog.domain.errors import CatalogFileError, CatalogValidationError
from sextante.catalog.infrastructure.xlsx_catalog_reader import XlsxCatalogWorkbookReader
from sextante.platform.database import apply_migrations, create_database_engine
from sextante.platform.settings import Settings, StartupConfigurationError
from sextante.platform.structured_logging import configure_logging


def create_app(environ: Mapping[str, str] | None = None) -> FastAPI:
    """Build the application, failing fast when configuration or catalog is invalid.

    Everything that can refuse startup runs here, before the server accepts a request.

    Example:
        app = create_app({"SEXTANTE_CATALOG_PATH": "...", ...})

    Raises:
        StartupConfigurationError: naming the offending setting or catalog condition.
    """
    configure_logging()
    settings = Settings.from_environment(os.environ if environ is None else environ)
    built_catalog = _load_catalog_or_refuse(settings)
    database_url = settings.database_url.get_secret_value()
    apply_migrations(database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.database_engine = create_database_engine(database_url)
        try:
            yield
        finally:
            await app.state.database_engine.dispose()

    app = FastAPI(title="Sextante", lifespan=lifespan)
    app.state.catalog = built_catalog.catalog
    app.include_router(health_router)
    return app


def _load_catalog_or_refuse(settings: Settings) -> BuiltCatalog:
    try:
        return load_catalog(settings.catalog_path, XlsxCatalogWorkbookReader())
    except CatalogFileError as error:
        raise StartupConfigurationError(f"SEXTANTE_CATALOG_PATH: {error}") from None
    except CatalogValidationError as error:
        raise StartupConfigurationError(f"Invalid catalog. {error}") from None
