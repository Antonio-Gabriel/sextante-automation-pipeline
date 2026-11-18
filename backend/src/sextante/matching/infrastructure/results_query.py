"""Read model of coded lines for one job, in document order (REQ-PLT-001, REQ-ING-004)."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.ingestion.contracts import INVOICE_HEADER_TABLE, INVOICE_LINE_TABLE, INVOICE_TABLE
from sextante.matching.infrastructure.tables import ENCODED_LINE_TABLE


@dataclass(frozen=True, slots=True)
class ResultLine:
    """One invoice line with its coding, as listed to the client."""

    invoice_number: str | None
    line_position: int
    line_description: str
    target_sheet: str | None
    item_number: str | None
    catalog_description: str | None


async def read_job_results(
    connection: AsyncConnection, job_id: str, limit: int, offset: int
) -> list[ResultLine]:
    """Return one page of the job's lines, ordered by invoice upload and document position.

    Example:
        page = await read_job_results(connection, job_id, limit=50, offset=0)
    """
    lines = INVOICE_LINE_TABLE
    query = (
        select(
            INVOICE_HEADER_TABLE.c.invoice_number,
            lines.c.position,
            lines.c.description,
            ENCODED_LINE_TABLE.c.target_sheet,
            ENCODED_LINE_TABLE.c.item_number,
            ENCODED_LINE_TABLE.c.catalog_description,
        )
        .select_from(lines)
        .join(INVOICE_TABLE, INVOICE_TABLE.c.id == lines.c.invoice_id)
        .join(INVOICE_HEADER_TABLE, INVOICE_HEADER_TABLE.c.invoice_id == lines.c.invoice_id)
        .outerjoin(ENCODED_LINE_TABLE, ENCODED_LINE_TABLE.c.invoice_line_id == lines.c.id)
        .where(INVOICE_TABLE.c.job_id == job_id)
        .order_by(INVOICE_TABLE.c.created_at, INVOICE_TABLE.c.id, lines.c.position)
        .limit(limit)
        .offset(offset)
    )
    return [
        ResultLine(
            invoice_number=row.invoice_number,
            line_position=int(row.position),
            line_description=str(row.description),
            target_sheet=row.target_sheet,
            item_number=row.item_number,
            catalog_description=row.catalog_description,
        )
        for row in (await connection.execute(query)).all()
    ]
