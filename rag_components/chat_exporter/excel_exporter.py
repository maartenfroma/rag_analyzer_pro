from io import BytesIO
from datetime import datetime

import openpyxl
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter


class ExcelExporter:

    @staticmethod
    def export(
        chat_history,
        doc_title=None,
        chunk_count=None,
        file_size=None
    ):

        if not chat_history:
            return None

        workbook = openpyxl.Workbook()

        # =====================================================
        # SUMMARY SHEET
        # =====================================================

        summary_sheet = workbook.active
        summary_sheet.title = "Summary"

        summary_sheet.append(["Metric", "Value"])

        summary_sheet["A1"].font = Font(bold=True)
        summary_sheet["B1"].font = Font(bold=True)

        summary_sheet.append(
            ["Document", doc_title or "Unknown"]
        )

        summary_sheet.append(
            ["Chunks Indexed", chunk_count or 0]
        )

        summary_sheet.append(
            ["File Size (Bytes)", file_size or 0]
        )

        summary_sheet.append(
            ["Questions Analysed", len(chat_history)]
        )

        summary_sheet.append(
            ["Export Date",
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        )

        # Calculate the total number of sources used across all chat entries
        total_sources = 0
        
        # Iterate over each chat entry to count the total number of sources used
        for entry in chat_history:
            if not isinstance(entry, dict):
                continue
            
            # Extract the metadata from the chat entry
            metadata = entry.get("metadata", [])
            
            # Ensure metadata is a list before counting its length
            if isinstance(metadata, list):
                total_sources += len(metadata)

        # Append the total sources used to the summary sheet
        summary_sheet.append(
            ["Total Sources Used", total_sources]
        )

        # =====================================================
        # AVERAGE SOURCES PER QUESTION
        # =====================================================
        # Append the average sources per question to the summary sheet
        summary_sheet.append(
            [
                "Average Sources Per Question",
                round(
                    total_sources /
                    max(len(chat_history), 1),
                    2
                )
            ]
        )

        # =====================================================
        # ADJUST COLUMN WIDTHS
        # ===================================================== 
        summary_sheet.column_dimensions["A"].width = 35
        summary_sheet.column_dimensions["B"].width = 50

        # =====================================================
        # CHAT HISTORY SHEET
        # =====================================================
        
        # Create a new sheet for chat history
        chat_sheet = workbook.create_sheet(
            title="Chat History"
        )

        # Define the headers for the chat history sheet
        headers = [
            "Timestamp",
            "Question",
            "Source Count"
        ]

        # Append the headers to the chat history sheet
        chat_sheet.append(headers)

        for cell in chat_sheet[1]:
            cell.font = Font(bold=True)

        # Append each chat entry to the chat history sheet
        for entry in chat_history:

            chat_sheet.append(
                [
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    entry.get("query", ""),
                    len(entry.get("metadata", []))
                ]
            )

        chat_sheet.column_dimensions["A"].width = 22
        chat_sheet.column_dimensions["B"].width = 100
        chat_sheet.column_dimensions["C"].width = 15

        # =====================================================
        # ANSWERS SHEET
        # =====================================================

        answers_sheet = workbook.create_sheet(
            title="Answers"
        )

        answers_sheet.append(
            ["Question", "Answer"]
        )

        for cell in answers_sheet[1]:
            cell.font = Font(bold=True)

        for entry in chat_history:

            answers_sheet.append(
               [
                   entry.get("query", ""),
                   entry.get("response", ""),
                   ", ".join(entry.get("metadata", []))
               ]
            )

        answers_sheet.column_dimensions["A"].width = 50
        answers_sheet.column_dimensions["B"].width = 120

        # =====================================================
        # SOURCES SHEET
        # =====================================================

        # Create a new sheet for sources
        sources_sheet = workbook.create_sheet(
            title="Sources"
        )

        # Define the headers for the sources sheet
        sources_sheet.append(
            [
                "Question",
                "Source Count"
            ]
        )

        # Apply bold font to the header row of the sources sheet
        for cell in sources_sheet[1]:
            cell.font = Font(bold=True)

        # Append each source entry to the sources sheet 
        for entry in chat_history:

            # Append each source entry to the sources sheet
            sources_sheet.append(
                [
                    entry.get("query", ""),
                    len(entry.get("metadata", []))
                ]
            )

        sources_sheet.column_dimensions["A"].width = 70
        sources_sheet.column_dimensions["B"].width = 20

        # =====================================================
        # WRAP TEXT FOR ALL SHEETS
        # =====================================================

        # Apply text wrapping to all cells in all sheets
        for sheet in workbook.worksheets:

            for row in sheet.iter_rows():

                for cell in row:

                    cell.alignment = Alignment(
                        wrap_text=True,
                        vertical="top"
                    )

        # =====================================================
        # EXPORT
        # =====================================================

        buffer = BytesIO()

        workbook.save(buffer)

        buffer.seek(0)

        return buffer.getvalue()