"""Read one invoice as a reviewer sees it (frontend ticket 05, SEC-18)."""

from sqlalchemy.ext.asyncio import AsyncEngine

from sextante.ingestion.application.errors import InvoiceNotFoundError
from sextante.ingestion.application.ports import InvoiceViewReader
from sextante.ingestion.application.records import InvoiceView


class ReadInvoice:
    """Return an invoice's state, extracted header, entity resolution and earlier copy.

    Example:
        view = await ReadInvoice(engine, IngestionRepository()).execute("3f2a...")
    """

    def __init__(self, engine: AsyncEngine, reader: InvoiceViewReader) -> None:
        self._engine = engine
        self._reader = reader

    async def execute(self, invoice_id: str) -> InvoiceView:
        """Return the invoice.

        Example:
            (await read_invoice.execute("3f2a...")).state.status  # InvoiceStatus.ENCODED

        Raises:
            InvoiceNotFoundError: when no invoice has this identifier.
        """
        async with self._engine.connect() as connection:
            view = await self._reader.read_invoice_view(connection, invoice_id)
        if view is None:
            raise InvoiceNotFoundError(f"Invoice {invoice_id!r} does not exist.")
        return view
