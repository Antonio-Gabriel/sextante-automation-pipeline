"""Application factory. Started with ``uvicorn --factory sextante.main:create_app``."""

import asyncio
import contextlib
import os
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path

from anthropic import AsyncAnthropic
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from sextante.catalog.application.load_catalog import CatalogFileError, load_catalog
from sextante.catalog.contracts import FALLBACK_ITEM_NUMBER, Catalog, CatalogItem, ItemNumber
from sextante.catalog.domain.catalog_builder import BuiltCatalog
from sextante.catalog.domain.errors import CatalogValidationError
from sextante.catalog.infrastructure.xlsx_catalog_reader import XlsxCatalogWorkbookReader
from sextante.export.api.routes import export_router
from sextante.export.application.build_job_export import BuildJobExport
from sextante.export.application.export_job import ExportJob
from sextante.export.infrastructure.spreadsheet_writers import SpreadsheetExportWriter
from sextante.ingestion.api.routes import ingestion_router
from sextante.ingestion.application.read_job_status import JobNotFoundError, ReadJobStatus
from sextante.ingestion.application.reprocess_invoice import (
    InvoiceNotFoundError,
    InvoiceNotReprocessableError,
    ReprocessInvoice,
)
from sextante.ingestion.application.resolve_entity import (
    InvoiceNotAmbiguousError,
    ResolutionCollaborators,
    ResolveEntity,
)
from sextante.ingestion.application.upload_invoices import (
    FileTooLargeError,
    UnsupportedFileTypeError,
    UploadInvoices,
)
from sextante.ingestion.contracts import InvoiceExtractor
from sextante.ingestion.infrastructure.local_file_store import LocalInvoiceFileStore
from sextante.ingestion.infrastructure.pdf_invoice_extractor import PdfInvoiceExtractor
from sextante.ingestion.infrastructure.repository import IngestionRepository
from sextante.matching.application.encode_invoice import EncodeInvoice, EncodingCollaborators
from sextante.matching.application.line_coding import CodingRules, LineCoder
from sextante.matching.contracts import EntityDenylist, ItemClassifier, TargetEntity
from sextante.matching.infrastructure.claude_classifier import (
    ClaudeItemClassifier,
    create_model_client,
)
from sextante.matching.infrastructure.denylist_file import DenylistFileError, read_entity_denylist
from sextante.matching.infrastructure.rapidfuzz_scorer import RapidfuzzLexicalScorer
from sextante.matching.infrastructure.repository import MatchingRepository
from sextante.platform.audit import AuditEventRepository
from sextante.platform.clock import Clock, IdentifierGenerator, SystemClock, UuidIdentifierGenerator
from sextante.platform.correlation import CorrelationIdMiddleware
from sextante.platform.database import apply_migrations, create_database_engine
from sextante.platform.health import health_router
from sextante.platform.http_errors import install_error_handlers
from sextante.platform.idempotency import (
    PURGE_INTERVAL_SECONDS,
    IdempotencyKeyRequiredError,
    IdempotencyKeyReusedError,
    IdempotentExecutor,
    purge_periodically,
)
from sextante.platform.retry import RetryPolicy, Sleep
from sextante.platform.settings import Settings, StartupConfigurationError
from sextante.platform.structured_logging import configure_logging
from sextante.review.api.routes import review_router
from sextante.review.application.codings_in_force import CodingsInForce
from sextante.review.application.list_job_results import ListJobResults
from sextante.review.application.read_job_progress import ReadJobProgress
from sextante.review.application.read_line_candidates import (
    InvoiceLineNotFoundError,
    ReadLineCandidates,
)
from sextante.review.application.review_line import (
    EncodedLineNotFoundError,
    ReviewCollaborators,
    ReviewLine,
)
from sextante.review.domain.review_state import (
    ItemNotInSheetError,
    LineWithoutSheetError,
    ReviewNotPendingError,
)
from sextante.review.infrastructure.repository import ReviewRepository
from sextante.worker import EncodingWorker, WorkerCollaborators

# The first retry waits 1 s, the next 2 s, and so on (REQ-PLT-003).
MODEL_RETRY_BASE_SECONDS = 1.0


@dataclass(frozen=True)
class ReferenceData:
    """Data loaded once at startup and read by every coding (NFR-PRF-003)."""

    catalog: Catalog
    denylist: EntityDenylist
    target_entity: TargetEntity


HTTP_STATUS_BY_ERROR = {
    InvoiceNotFoundError: 404,
    InvoiceNotReprocessableError: 409,
    InvoiceNotAmbiguousError: 409,
    JobNotFoundError: 404,
    EncodedLineNotFoundError: 404,
    InvoiceLineNotFoundError: 404,
    LineWithoutSheetError: 409,
    ReviewNotPendingError: 409,
    ItemNotInSheetError: 422,
    IdempotencyKeyRequiredError: 422,
    IdempotencyKeyReusedError: 422,
    UnsupportedFileTypeError: 415,
    FileTooLargeError: 413,
}


@dataclass(frozen=True)
class AppDependencies:
    """The adapters behind the ports. Tests replace the extractor and the classifier.

    Without an extractor, the native PDF extractor is built from the settings. The
    default classifier refuses with an explicit reason until the Claude adapter
    (ticket 11) is wired.
    """

    extractor: InvoiceExtractor | None = None
    classifier: ItemClassifier | None = None
    clock: Clock = field(default_factory=SystemClock)
    identifiers: IdentifierGenerator = field(default_factory=UuidIdentifierGenerator)
    worker_poll_seconds: float = 1.0
    sleep: Sleep = asyncio.sleep


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
    target_entity = TargetEntity(settings.target_entity_name, settings.target_entity_nif)
    denylist = _load_denylist_or_refuse(settings, target_entity)
    require_generic_items_in_catalog(settings.generic_items, catalog)
    apply_migrations(settings.database_url.get_secret_value())
    adapters = dependencies or AppDependencies()
    app = FastAPI(
        title="Sextante",
        lifespan=_lifespan(settings, ReferenceData(catalog, denylist, target_entity), adapters),
    )
    app.state.catalog = catalog
    app.add_middleware(CorrelationIdMiddleware)
    install_error_handlers(app, HTTP_STATUS_BY_ERROR)
    for router in (health_router, ingestion_router, review_router, export_router):
        app.include_router(router)
    return app


def _lifespan(
    settings: Settings, reference: ReferenceData, adapters: AppDependencies
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_database_engine(settings.database_url.get_secret_value())
        app.state.database_engine = engine
        classifier, model_client = _classifier(settings, adapters)
        _wire_use_cases(app, engine, settings, reference, adapters, classifier)
        tasks = [
            asyncio.create_task(app.state.worker.run_forever()),
            asyncio.create_task(purge_periodically(app.state.idempotency, PURGE_INTERVAL_SECONDS)),
        ]
        try:
            yield
        finally:
            await _stop(tasks)
            if model_client is not None:
                await model_client.close()
            await engine.dispose()

    return lifespan


async def _stop(tasks: list[asyncio.Task[None]]) -> None:
    for task in tasks:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


def _classifier(
    settings: Settings, adapters: AppDependencies
) -> tuple[ItemClassifier, AsyncAnthropic | None]:
    # An injected classifier (a test double) needs no API client.
    if adapters.classifier is not None:
        return adapters.classifier, None
    client = create_model_client(settings.anthropic_api_key.get_secret_value())
    return ClaudeItemClassifier(client, settings.model_id), client


def _wire_use_cases(
    app: FastAPI,
    engine: AsyncEngine,
    settings: Settings,
    reference: ReferenceData,
    adapters: AppDependencies,
    classifier: ItemClassifier,
) -> None:
    store = LocalInvoiceFileStore(Path(settings.upload_dir))
    ingestion = IngestionRepository()
    app.state.upload_invoices = UploadInvoices(
        engine, ingestion, store, adapters.clock, adapters.identifiers
    )
    app.state.read_job_status = ReadJobStatus(engine, ingestion)
    app.state.read_job_progress = ReadJobProgress(
        engine, app.state.read_job_status, MatchingRepository()
    )
    app.state.reprocess_invoice = ReprocessInvoice(
        ingestion, AuditEventRepository(), adapters.clock, adapters.identifiers
    )
    codings_in_force = CodingsInForce(MatchingRepository(), ReviewRepository())
    app.state.list_job_results = ListJobResults(
        engine, app.state.read_job_status, ingestion, codings_in_force
    )
    build_export = BuildJobExport(engine, app.state.read_job_status, ingestion, codings_in_force)
    app.state.export_job = ExportJob(build_export, SpreadsheetExportWriter(settings.csv_separator))
    _wire_review(app, engine, settings, reference.catalog, adapters)
    app.state.worker = _build_worker(engine, settings, reference, adapters, store, classifier)


def _wire_review(
    app: FastAPI,
    engine: AsyncEngine,
    settings: Settings,
    catalog: Catalog,
    adapters: AppDependencies,
) -> None:
    app.state.reviewer_id = settings.reviewer_id
    app.state.resolve_entity = _build_entity_resolution(settings, adapters)
    app.state.idempotency = IdempotentExecutor(engine, adapters.clock)
    app.state.read_line_candidates = ReadLineCandidates(
        engine, IngestionRepository(), MatchingRepository(), catalog
    )
    app.state.review_line = ReviewLine(
        ReviewCollaborators(
            codings=MatchingRepository(),
            reviews=ReviewRepository(),
            catalog=catalog,
            audit=AuditEventRepository(),
            clock=adapters.clock,
            identifiers=adapters.identifiers,
            reviewer_id=settings.reviewer_id,
        )
    )


def _build_entity_resolution(settings: Settings, adapters: AppDependencies) -> ResolveEntity:
    return ResolveEntity(
        ResolutionCollaborators(
            repository=IngestionRepository(),
            audit=AuditEventRepository(),
            clock=adapters.clock,
            identifiers=adapters.identifiers,
            reviewer_id=settings.reviewer_id,
        )
    )


def _build_worker(
    engine: AsyncEngine,
    settings: Settings,
    reference: ReferenceData,
    adapters: AppDependencies,
    store: LocalInvoiceFileStore,
    classifier: ItemClassifier,
) -> EncodingWorker:
    return EncodingWorker(
        WorkerCollaborators(
            engine=engine,
            repository=IngestionRepository(),
            store=store,
            extractor=adapters.extractor or PdfInvoiceExtractor(settings.pdf_min_chars_per_page),
            encoder=_build_encoder(engine, reference.catalog, settings, adapters, classifier),
            audit=AuditEventRepository(),
            clock=adapters.clock,
            identifiers=adapters.identifiers,
            target_entity=reference.target_entity,
            denylist=reference.denylist,
            poll_seconds=adapters.worker_poll_seconds,
        )
    )


def _build_encoder(
    engine: AsyncEngine,
    catalog: Catalog,
    settings: Settings,
    adapters: AppDependencies,
    classifier: ItemClassifier,
) -> EncodeInvoice:
    rules = coding_rules(
        catalog, classifier, settings.generic_items, settings.model_max_attempts, adapters.sleep
    )
    return EncodeInvoice(
        EncodingCollaborators(
            engine=engine,
            coder=LineCoder(rules),
            catalog=catalog,
            repository=MatchingRepository(),
            audit=AuditEventRepository(),
            clock=adapters.clock,
            identifiers=adapters.identifiers,
        )
    )


def coding_rules(
    catalog: Catalog,
    classifier: ItemClassifier,
    generic_items: Sequence[str],
    max_attempts: int,
    sleep: Sleep,
) -> CodingRules:
    """The rules a line is decided by, as the application builds them.

    Shared with the manual golden measurement, so it codes exactly as the application.

    Example:
        LineCoder(coding_rules(catalog, classifier, ("O00052",), 3, asyncio.sleep))

    Raises:
        StartupConfigurationError: when a generic item or O00999 is not in the catalog.
    """
    require_generic_items_in_catalog(generic_items, catalog)
    return CodingRules(
        catalog=catalog,
        scorer=RapidfuzzLexicalScorer(),
        classifier=classifier,
        fallback_item=_fallback_item(catalog),
        generic_items=frozenset(ItemNumber(n) for n in generic_items),
        retry_policy=RetryPolicy(max_attempts, MODEL_RETRY_BASE_SECONDS),
        sleep=sleep,
    )


def require_generic_items_in_catalog(generic_items: Sequence[str], catalog: Catalog) -> None:
    """Refuse generic items that the catalog does not have (D-3.16).

    Example:
        require_generic_items_in_catalog(("O00052",), catalog)

    Raises:
        StartupConfigurationError: naming the unknown items.
    """
    unknown = [n for n in generic_items if catalog.find(ItemNumber(n)) is None]
    if unknown:
        raise StartupConfigurationError(
            f"SEXTANTE_GENERIC_ITEMS: items {unknown} are not in the catalog. "
            "Expected item numbers of column No., for example O00052."
        )


def _fallback_item(catalog: Catalog) -> CatalogItem:
    # Startup validation already refused a catalog without O00999 (REQ-MAP-012).
    fallback = catalog.find(FALLBACK_ITEM_NUMBER)
    if fallback is None:
        raise StartupConfigurationError(
            f"Invalid catalog. No item {FALLBACK_ITEM_NUMBER}. Expected it in sheet OUTLAYSP."
        )
    return fallback


def _load_denylist_or_refuse(settings: Settings, target: TargetEntity) -> EntityDenylist:
    try:
        denylist = EntityDenylist.of(read_entity_denylist(settings.entity_denylist_path))
    except DenylistFileError as error:
        raise StartupConfigurationError(f"SEXTANTE_ENTITY_DENYLIST_PATH: {error}") from None
    # A denylist entry equal to the target, once normalized, would route every AMT
    # invoice to OUTLAYSP without anyone noticing (R2, REQ-ENT-003).
    if denylist.excludes(target.name):
        raise StartupConfigurationError(
            "SEXTANTE_ENTITY_DENYLIST_PATH: an entry is the target entity itself. Expected "
            "only sister companies, shipping lines and clients."
        )
    return denylist


def _load_catalog_or_refuse(settings: Settings) -> BuiltCatalog:
    try:
        return load_catalog(settings.catalog_path, XlsxCatalogWorkbookReader())
    except CatalogFileError as error:
        raise StartupConfigurationError(f"SEXTANTE_CATALOG_PATH: {error}") from None
    except CatalogValidationError as error:
        raise StartupConfigurationError(f"Invalid catalog. {error}") from None
