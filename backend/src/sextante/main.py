"""Application factory. Started with ``uvicorn --factory sextante.main:create_app``."""

import asyncio
import contextlib
import os
from collections.abc import AsyncIterator, Callable, Mapping
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from sextante.catalog.application.load_catalog import CatalogFileError, load_catalog
from sextante.catalog.contracts import Catalog
from sextante.catalog.domain.catalog_builder import BuiltCatalog
from sextante.catalog.domain.errors import CatalogValidationError
from sextante.catalog.infrastructure.xlsx_catalog_reader import XlsxCatalogWorkbookReader
from sextante.ingestion.api.routes import ingestion_router
from sextante.ingestion.application.read_job_status import JobNotFoundError, ReadJobStatus
from sextante.ingestion.application.upload_invoices import (
    FileTooLargeError,
    UnsupportedFileTypeError,
    UploadInvoices,
)
from sextante.ingestion.contracts import InvoiceExtractor
from sextante.ingestion.infrastructure.local_file_store import LocalInvoiceFileStore
from sextante.ingestion.infrastructure.repository import IngestionRepository
from sextante.ingestion.infrastructure.unconfigured_extractor import UnconfiguredInvoiceExtractor
from sextante.matching.application.encode_invoice import EncodeInvoice, EncodingCollaborators
from sextante.matching.contracts import ItemClassifier
from sextante.matching.infrastructure.rapidfuzz_scorer import RapidfuzzLexicalScorer
from sextante.matching.infrastructure.repository import MatchingRepository
from sextante.matching.infrastructure.unconfigured_classifier import UnconfiguredItemClassifier
from sextante.platform.audit import AuditEventRepository
from sextante.platform.clock import Clock, IdentifierGenerator, SystemClock, UuidIdentifierGenerator
from sextante.platform.correlation import CorrelationIdMiddleware
from sextante.platform.database import apply_migrations, create_database_engine
from sextante.platform.health import health_router
from sextante.platform.http_errors import install_error_handlers
from sextante.platform.settings import Settings, StartupConfigurationError
from sextante.platform.structured_logging import configure_logging
from sextante.review.api.routes import review_router
from sextante.review.application.list_job_results import ListJobResults
from sextante.worker import EncodingWorker, WorkerCollaborators

HTTP_STATUS_BY_ERROR = {
    JobNotFoundError: 404,
    UnsupportedFileTypeError: 415,
    FileTooLargeError: 413,
}


@dataclass(frozen=True)
class AppDependencies:
    """The adapters behind the ports. Tests replace the extractor and the classifier.

    The defaults refuse to extract or classify with an explicit reason, until the PDF
    extractor (ticket 12) and the Claude adapter (ticket 11) are wired.
    """

    extractor: InvoiceExtractor = field(default_factory=UnconfiguredInvoiceExtractor)
    classifier: ItemClassifier = field(default_factory=UnconfiguredItemClassifier)
    clock: Clock = field(default_factory=SystemClock)
    identifiers: IdentifierGenerator = field(default_factory=UuidIdentifierGenerator)
    worker_poll_seconds: float = 1.0


def create_app(
    environ: Mapping[str, str] | None = None, dependencies: AppDependencies | None = None
) -> FastAPI:
    """Build the application, failing fast when configuration or catalog is invalid.

    Everything that can refuse startup runs here, before the server accepts a request.

    Example:
        app = create_app({"SEXTANTE_CATALOG_PATH": "...", ...})

    Raises:
        StartupConfigurationError: naming the offending setting or catalog condition.
    """
    configure_logging()
    settings = Settings.from_environment(os.environ if environ is None else environ)
    catalog = _load_catalog_or_refuse(settings).catalog
    apply_migrations(settings.database_url.get_secret_value())
    app = FastAPI(
        title="Sextante", lifespan=_lifespan(settings, catalog, dependencies or AppDependencies())
    )
    app.state.catalog = catalog
    app.add_middleware(CorrelationIdMiddleware)
    install_error_handlers(app, HTTP_STATUS_BY_ERROR)
    for router in (health_router, ingestion_router, review_router):
        app.include_router(router)
    return app


def _lifespan(
    settings: Settings, catalog: Catalog, adapters: AppDependencies
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_database_engine(settings.database_url.get_secret_value())
        app.state.database_engine = engine
        _wire_use_cases(app, engine, settings, catalog, adapters)
        worker_task = asyncio.create_task(app.state.worker.run_forever())
        try:
            yield
        finally:
            worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await worker_task
            await engine.dispose()

    return lifespan


def _wire_use_cases(
    app: FastAPI,
    engine: AsyncEngine,
    settings: Settings,
    catalog: Catalog,
    adapters: AppDependencies,
) -> None:
    store = LocalInvoiceFileStore(Path(settings.upload_dir))
    ingestion = IngestionRepository()
    app.state.upload_invoices = UploadInvoices(
        engine, ingestion, store, adapters.clock, adapters.identifiers
    )
    app.state.read_job_status = ReadJobStatus(engine, ingestion)
    app.state.list_job_results = ListJobResults(
        engine, app.state.read_job_status, ingestion, MatchingRepository()
    )
    app.state.worker = _build_worker(engine, settings, catalog, adapters, store)


def _build_worker(
    engine: AsyncEngine,
    settings: Settings,
    catalog: Catalog,
    adapters: AppDependencies,
    store: LocalInvoiceFileStore,
) -> EncodingWorker:
    return EncodingWorker(
        WorkerCollaborators(
            engine=engine,
            repository=IngestionRepository(),
            store=store,
            extractor=adapters.extractor,
            encoder=_build_encoder(engine, catalog, adapters),
            clock=adapters.clock,
            identifiers=adapters.identifiers,
            target_entity_name=settings.target_entity_name,
            poll_seconds=adapters.worker_poll_seconds,
        )
    )


def _build_encoder(
    engine: AsyncEngine, catalog: Catalog, adapters: AppDependencies
) -> EncodeInvoice:
    return EncodeInvoice(
        EncodingCollaborators(
            engine=engine,
            catalog=catalog,
            scorer=RapidfuzzLexicalScorer(),
            classifier=adapters.classifier,
            repository=MatchingRepository(),
            audit=AuditEventRepository(),
            clock=adapters.clock,
            identifiers=adapters.identifiers,
        )
    )


def _load_catalog_or_refuse(settings: Settings) -> BuiltCatalog:
    try:
        return load_catalog(settings.catalog_path, XlsxCatalogWorkbookReader())
    except CatalogFileError as error:
        raise StartupConfigurationError(f"SEXTANTE_CATALOG_PATH: {error}") from None
    except CatalogValidationError as error:
        raise StartupConfigurationError(f"Invalid catalog. {error}") from None
