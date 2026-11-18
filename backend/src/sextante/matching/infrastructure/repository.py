"""SQL for model calls, encoded lines, flags and lexical scores. Joins the caller's transaction."""

from collections import defaultdict
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.matching.application.records import EncodedLineRecord, LineCoding, ModelCallRecord
from sextante.matching.infrastructure.tables import (
    ENCODED_LINE_TABLE,
    LEXICAL_SCORE_TABLE,
    LINE_FLAG_TABLE,
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
        """Insert the encoded line, its flags, and the score of every item of its sheet."""
        await connection.execute(ENCODED_LINE_TABLE.insert().values(**_encoded_line_row(record)))
        flags = [
            {"encoded_line_id": record.encoded_line_id, "reason": f.value}
            for f in record.decision.flags
        ]
        if flags:
            await connection.execute(LINE_FLAG_TABLE.insert(), flags)
        scores = [
            {
                "invoice_line_id": record.invoice_line_id,
                "item_number": s.item_number,
                "score": s.score,
                "rank": s.rank,
            }
            for s in record.scores
        ]
        if scores:
            await connection.execute(LEXICAL_SCORE_TABLE.insert(), scores)

    async def read_codings(
        self, connection: AsyncConnection, line_ids: Sequence[str]
    ) -> dict[str, LineCoding]:
        """Return the coding of each given line that has one, keyed by invoice line id."""
        table = ENCODED_LINE_TABLE
        rows = (
            await connection.execute(
                select(table).where(table.c.invoice_line_id.in_(list(line_ids)))
            )
        ).all()
        flags = await _flags_of(connection, [str(r.id) for r in rows])
        return {
            str(r.invoice_line_id): LineCoding(
                target_sheet=r.target_sheet,
                item_number=r.item_number,
                catalog_description=r.catalog_description,
                confidence=str(r.confidence),
                review_status=str(r.review_status),
                flags=tuple(flags[str(r.id)]),
                note=r.note,
            )
            for r in rows
        }


async def _flags_of(
    connection: AsyncConnection, encoded_line_ids: list[str]
) -> dict[str, list[str]]:
    query = (
        select(LINE_FLAG_TABLE.c.encoded_line_id, LINE_FLAG_TABLE.c.reason)
        .where(LINE_FLAG_TABLE.c.encoded_line_id.in_(encoded_line_ids))
        .order_by(LINE_FLAG_TABLE.c.reason)
    )
    flags: dict[str, list[str]] = defaultdict(list)
    for encoded_line_id, reason in (await connection.execute(query)).all():
        flags[str(encoded_line_id)].append(str(reason))
    return flags


def _encoded_line_row(record: EncodedLineRecord) -> dict[str, object]:
    catalog_item = record.decision.catalog_item
    return {
        "id": record.encoded_line_id,
        "invoice_line_id": record.invoice_line_id,
        "target_sheet": record.target_sheet.value if record.target_sheet else None,
        "item_number": catalog_item.item_number.value if catalog_item else None,
        "catalog_description": catalog_item.description_pt if catalog_item else None,
        "choice_outcome": record.choice.outcome.value if record.choice else "not_coded",
        "candidate_index": record.choice.candidate_index if record.choice else None,
        "catalog_digest": record.catalog_digest,
        "model_call_id": record.model_call_id,
        "confidence": record.decision.confidence.value,
        "confidence_rule": record.decision.rule,
        "review_status": record.decision.review_status,
        "note": record.decision.note.value if record.decision.note else None,
        "encoded_at": record.encoded_at.isoformat(),
    }
