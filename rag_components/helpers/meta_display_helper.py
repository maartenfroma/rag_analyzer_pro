from datetime import timedelta


# Helper class to format metadata for display purposes
class MetaDisplayHelper:

    # Helper class for displaying metadata in a human-readable format
    @staticmethod
    def format_time(seconds: float) -> str:

        # Convert the input seconds to an integer for processing

        total_seconds = int(seconds)

        td = timedelta(seconds=total_seconds)

        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours:02}:{minutes:02}:{seconds:02}"

        return f"{minutes:02}:{seconds:02}"

    # Helper method to format metadata for display based on source type
    # Returns a formatted string representation of the metadata based on the source type
    # If the source type is not recognized, it returns a generic representation
    @staticmethod
    def format(metadata: dict):

        # Determine the source type from metadata
        source = metadata.get("source")

        # If source is not specified, default to unknown
        if source == "pdf":

            return (
                f"📄 {metadata.get('file_name')}\n"
                f"📑 Page {metadata.get('page_number', '?')}\n"
                f"📂 PDF Document"
            )

        elif source == "docx":

            return f"📝 {metadata.get('file_name')}\n" f"📂 Word Document"

        elif source == "csv":

            return (
                f"📈 {metadata.get('file_name')}\n"
                f"🔢 Row {metadata.get('index', '?')}\n"
                f"📂 CSV Dataset"
            )

        elif source == "pptx":

            return (
                f"📽️ {metadata.get('file_name')}\n"
                f"📊 Slide {metadata.get('slide', '?')}\n"
                f"📂 PowerPoint Presentation"
            )

        elif source == "xlsx":

            return (
                f"📊 {metadata.get('file_name')}\n"
                f"📋 Sheet {metadata.get('sheet', '?')}\n"
                f"📂 Excel Workbook"
            )

        elif source in ["mp3", "wav"]:

            file_name = metadata.get("file_name", "unknown")

            return (
                f"🎧 {file_name}\n"
                f"⏱️ {MetaDisplayHelper.format_time(metadata.get('start_time', 0))}"
                f" - "
                f"{MetaDisplayHelper.format_time(metadata.get('end_time', 0))}\n"
                f"📂 Audio Recording"
            )

        elif source in ["video", "mp4"]:

            file_name = metadata.get("file_name", "unknown")

            return (
                f"📹 {file_name}\n"
                f"⏱️ {MetaDisplayHelper.format_time(metadata.get('start_time', 0))}"
                f" - "
                f"{MetaDisplayHelper.format_time(metadata.get('end_time', 0))}\n"
                f"📂 Video Recording"
            )

        # If source type is not recognized, display generic metadata information
        file_name = metadata.get("file_name", "Unknown")

        return f"📄 {file_name}\n" f"📂 Unknown Document Type"
