"""Export a job as a file, from the persisted state (REQ-EXP-001 to REQ-EXP-005)."""

from sextante.export.application.build_job_export import BuildJobExport
from sextante.export.application.ports import ExportFile, ExportFormat, SpreadsheetWriter


class ExportJob:
    """Build the job's rows and write them in the requested format.

    Example:
        export_file = await ExportJob(build_export, writer).execute(job_id, ExportFormat.CSV)
    """

    def __init__(self, build_export: BuildJobExport, writer: SpreadsheetWriter) -> None:
        self._build_export = build_export
        self._writer = writer

    async def execute(self, job_id: str, export_format: ExportFormat) -> ExportFile:
        """Return the export file.

        Example:
            (await export_job.execute("3f2a...", ExportFormat.XLSX)).extension  # "xlsx"

        Raises:
            JobNotFoundError: when no job has this identifier.
        """
        rows = await self._build_export.execute(job_id)
        return self._writer.write(rows, export_format)
