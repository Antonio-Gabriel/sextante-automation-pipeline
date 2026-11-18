"""SQL for model calls, encoded lines and lexical scores. Joins the caller's transaction."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.matching.application.records import EncodedLineRecord, LineCoding, ModelCallRecord
from sextante.matching.infrastructure.tables import (
    ENCODED_LINE_TABLE,
    LEXICAL_SCORE_TABLE,
    MODEL_CALL_TABLE,
)


class MatchingRepository:
    """Implements MatchingRepositoryPort and CodingsReader with SQLAlchemy Core.

    Example:
        await MatchingRepository().record_model_call(connection, record)
    """

    async def record_model_call(self, connection: AsyncConnection, record: ModelCallRecord) -> None:
        """Insert the model call row."""
        await connection.execute(
            MODEL_CALL_TABLE.insert().values(
                id=record.call_id,
                invoice_id=record.invoice_id,
                model_id=record.response.model_id,
                prompt_version=record.response.prompt_version,
                input_tokens=record.response.input_tokens,
                output_tokens=record.response.output_tokens,
                called_at=record.called_at.isoformat(),
            )
        )

    async def record_encoded_line(
        self, connection: AsyncConnection, record: EncodedLineRecord
    ) -> None:
        """Insert the encoded line and one score row per item of the target sheet."""
        await connection.execute(ENCODED_LINE_TABLE.insert().values(**_encoded_line_row(record)))
        await connection.execute(
            LEXICAL_SCORE_TABLE.insert(),
            [
                {
                    "invoice_line_id": record.invoice_line_id,
                    "item_number": s.item_number,
                    "score": s.score,
                    "rank": s.rank,
                }
                for s in record.scores
            ],
        )

    async def read_codings(
        self, connection: AsyncConnection, line_ids: Sequence[str]
    ) -> dict[str, LineCoding]:
        """Return the coding of each given line that has one, keyed by invoice line id."""
        table = ENCODED_LINE_TABLE
        query = select(
            table.c.invoice_line_id,
            table.c.target_sheet,
            table.c.item_number,
            table.c.catalog_description,
        ).where(table.c.invoice_line_id.in_(list(line_ids)))
        rows = (await connection.execute(query)).all()
        return {str(r[0]): LineCoding(str(r[1]), r[2], r[3]) for r in rows}


def _encoded_line_row(record: EncodedLineRecord) -> dict[str, object]:
    catalog_item = record.choice.catalog_item
    return {
        "id": record.encoded_line_id,
        "invoice_line_id": record.invoice_line_id,
        "target_sheet": record.target_sheet.value,
        "item_number": catalog_item.item_number.value if catalog_item else None,
        "catalog_description": catalog_item.description_pt if catalog_item else None,
        "choice_outcome": record.choice.outcome.value,
        "candidate_index": record.choice.candidate_index,
        "catalog_digest": record.catalog_digest,
        "model_call_id": record.model_call_id,
        "encoded_at": record.encoded_at.isoformat(),
    }
