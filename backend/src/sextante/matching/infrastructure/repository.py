"""SQL for model calls, encoded lines, flags and lexical scores. Joins the caller's transaction."""

from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Row, func, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.matching.application.records import (
    CodingsSummary,
    EncodedLineRecord,
    LineCandidates,
    LineCoding,
    ModelCallRecord,
    ScoredCandidate,
)
from sextante.matching.infrastructure.tables import (
    ENCODED_LINE_TABLE,
    LEXICAL_SCORE_TABLE,
    LINE_FLAG_TABLE,
    MODEL_CALL_TABLE,
)


class MatchingRepository:
    """Implements MatchingRepositoryPort, CodingsReader and TokenUsageReader.

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
                cache_creation_input_tokens=record.response.cache_creation_input_tokens,
                cache_read_input_tokens=record.response.cache_read_input_tokens,
                called_at=record.called_at.isoformat(),
            )
        )

    async def codings_in_force(
        self, connection: AsyncConnection, invoice_line_ids: Sequence[str]
    ) -> CodingsSummary:
        """What coded these lines until now: prompt versions, catalog digests, line count."""
        line, call = ENCODED_LINE_TABLE, MODEL_CALL_TABLE
        query = (
            select(line.c.catalog_digest, call.c.prompt_version)
            .select_from(line)
            .outerjoin(call, call.c.id == line.c.model_call_id)
            .where(
                line.c.invoice_line_id.in_(list(invoice_line_ids)), line.c.superseded_at.is_(None)
            )
        )
        rows = (await connection.execute(query)).all()
        return CodingsSummary(
            prompt_versions=tuple(sorted({str(r[1]) for r in rows if r[1] is not None})),
            catalog_digests=tuple(sorted({str(r[0]) for r in rows})),
            line_count=len(rows),
        )

    async def supersede_codings(
        self, connection: AsyncConnection, invoice_line_ids: Sequence[str], at: datetime
    ) -> None:
        """Mark the codings in force of these lines as superseded; nothing is overwritten."""
        table = ENCODED_LINE_TABLE
        await connection.execute(
            update(table)
            .where(
                table.c.invoice_line_id.in_(list(invoice_line_ids)), table.c.superseded_at.is_(None)
            )
            .values(superseded_at=at.isoformat())
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
                "encoded_line_id": record.encoded_line_id,
                "invoice_line_id": record.invoice_line_id,
                "item_number": s.item_number,
                "score": s.score,
                "rank": s.rank,
            }
            for s in record.scores
        ]
        if scores:
            await connection.execute(LEXICAL_SCORE_TABLE.insert(), scores)

    async def read_token_usage(
        self, connection: AsyncConnection, invoice_ids: Sequence[str]
    ) -> dict[str, tuple[int, int]]:
        """Return, by invoice, the input and output tokens of its model calls."""
        return await _token_usage(connection, invoice_ids)

    async def read_codings(
        self, connection: AsyncConnection, line_ids: Sequence[str]
    ) -> dict[str, LineCoding]:
        """Return the coding of each given line that has one, keyed by invoice line id."""
        table = ENCODED_LINE_TABLE
        rows = (
            await connection.execute(
                select(table).where(
                    table.c.invoice_line_id.in_(list(line_ids)), table.c.superseded_at.is_(None)
                )
            )
        ).all()
        flags = await _flags_of(connection, [str(r.id) for r in rows])
        return {str(r.invoice_line_id): _line_coding(r, flags[str(r.id)]) for r in rows}

    async def read_encoded_line(
        self, connection: AsyncConnection, encoded_line_id: str
    ) -> LineCoding | None:
        """Return one coding by its own identifier, or None."""
        table = ENCODED_LINE_TABLE
        query = select(table).where(table.c.id == encoded_line_id, table.c.superseded_at.is_(None))
        row = (await connection.execute(query)).first()
        if row is None:
            return None
        flags = await _flags_of(connection, [encoded_line_id])
        return _line_coding(row, flags[encoded_line_id])

    async def read_candidates(
        self, connection: AsyncConnection, invoice_line_id: str
    ) -> LineCandidates | None:
        """Return the scored items of the line's sheet, best first, and the model's choice."""
        table = ENCODED_LINE_TABLE
        query = select(table).where(
            table.c.invoice_line_id == invoice_line_id, table.c.superseded_at.is_(None)
        )
        row = (await connection.execute(query)).first()
        if row is None:
            return None
        scores = await _scores_of(connection, str(row.id))
        chosen = row.item_number if row.choice_outcome == "chosen" else None
        return LineCandidates(row.target_sheet, chosen, scores)


def _line_coding(row: Row[tuple[object, ...]], flags: list[str]) -> LineCoding:
    return LineCoding(
        encoded_line_id=str(row.id),
        invoice_line_id=str(row.invoice_line_id),
        target_sheet=row.target_sheet,
        item_number=row.item_number,
        catalog_description=row.catalog_description,
        confidence=str(row.confidence),
        review_status=str(row.review_status),
        flags=tuple(flags),
        note=row.note,
    )


async def _scores_of(
    connection: AsyncConnection, encoded_line_id: str
) -> tuple[ScoredCandidate, ...]:
    table = LEXICAL_SCORE_TABLE
    query = (
        select(table.c.item_number, table.c.score, table.c.rank)
        .where(table.c.encoded_line_id == encoded_line_id)
        .order_by(table.c.rank)
    )
    rows = (await connection.execute(query)).all()
    return tuple(ScoredCandidate(str(r[0]), float(r[1]), int(r[2])) for r in rows)


async def _token_usage(
    connection: AsyncConnection, invoice_ids: Sequence[str]
) -> dict[str, tuple[int, int]]:
    table = MODEL_CALL_TABLE
    query = (
        select(table.c.invoice_id, func.sum(table.c.input_tokens), func.sum(table.c.output_tokens))
        .where(table.c.invoice_id.in_(list(invoice_ids)))
        .group_by(table.c.invoice_id)
    )
    rows = (await connection.execute(query)).all()
    return {str(r[0]): (int(str(r[1])), int(str(r[2]))) for r in rows}


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
