"""SQL for model calls, encoded lines and lexical scores. Joins the caller's transaction."""

from sqlalchemy.ext.asyncio import AsyncConnection

from sextante.matching.application.records import EncodedLineRecord, ModelCallRecord
from sextante.matching.infrastructure.tables import (
    ENCODED_LINE_TABLE,
    LEXICAL_SCORE_TABLE,
    MODEL_CALL_TABLE,
)


class MatchingRepository:
    """Implements MatchingRepositoryPort with SQLAlchemy Core.

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
        catalog_item = record.choice.catalog_item
        await connection.execute(
            ENCODED_LINE_TABLE.insert().values(
                id=record.encoded_line_id,
                invoice_line_id=record.invoice_line_id,
                target_sheet=record.target_sheet,
                item_number=catalog_item.item_number.value if catalog_item else None,
                catalog_description=catalog_item.description_pt if catalog_item else None,
                choice_outcome=record.choice.outcome.value,
                candidate_index=record.choice.candidate_index,
                catalog_digest=record.catalog_digest,
                model_call_id=record.model_call_id,
                encoded_at=record.encoded_at.isoformat(),
            )
        )
        await connection.execute(
            LEXICAL_SCORE_TABLE.insert(),
            [
                {
                    "invoice_line_id": record.invoice_line_id,
                    "item_number": score.item_number,
                    "score": score.score,
                    "rank": score.rank,
                }
                for score in record.scores
            ],
        )
