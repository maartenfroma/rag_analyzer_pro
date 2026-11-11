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

    #
    @staticmethod
    def format(metadata:dict):

        # Determine the source type from metadata
        source=metadata.get("source")

        # If source is not specified, default to unknown
        if source == "pdf":
             return (
                f"📄 {metadata.get('file_name')} | "
                f"Page: {metadata.get('page_number')} | "
                f"Chunk: {metadata.get('chunk_index')}"
            )

        elif source == "docx":
            return (
                f"📄 {metadata.get('file_name')} | "
                f"Chunk: {metadata.get('chunk_index')}"
            ) 

        elif source == "csv":
            return (
                f"📈 {metadata.get('file_name')} | "
                f"Index: {metadata.get('index')} | "
                f"Chunk: {metadata.get('chunk_index')}"
                    )
        elif source == "pptx":

            return (
                f"📊 {metadata.get('file_name')} | "
                f"Slide: {metadata.get('slide')} | "
                f"Chunk: {metadata.get('chunk_index')}"
            )

        elif source=="xlsx":
            return (
                f"📊 {metadata.get('file_name')} | "
                f"Sheet: {metadata.get('sheet')} | "
                f"Chunk: {metadata.get('chunk_index')}"
            )
        elif source in ["mp3", "wav"]:

            file_name = metadata.get('file_name', 'unknown')
            return (
                f"🎙️ {file_name} | "
                f"Start: {MetaDisplayHelper.format_time(metadata.get('start_time', 0))} | "
                f"End: {MetaDisplayHelper.format_time(metadata.get('end_time', 0))}"
            )

        elif source == "mp4":

            file_name = metadata.get('file_name', 'unknown')
            
            return (
                f"🎥 {file_name} | "
                f"Start: {MetaDisplayHelper.format_time(metadata.get('start_time', 0))} | "
                f"End: {MetaDisplayHelper.format_time(metadata.get('end_time', 0))}"
            )

        # If source type is not recognized, display generic metadata information
        file_name = metadata.get('file_name', 'unknown')
        return (f"📄 {file_name} | "
                  f"{metadata}"
                                   )





            
    