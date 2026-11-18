from datetime import datetime
import json

# Helper class to export chat history to JSON format
class JsonExporter: 
    
    # Static method to export chat history to JSON format
    @staticmethod
    def export(chat_history, file_path=None, doc_title=None, chunk_count=None, file_size=None):
        
        if not chat_history:
            return

        export_data = {
            "report_info": {
                "generated": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "document": doc_title,
                "chunk_count": chunk_count,
                "file_size": file_size,
                "questions_analyzed": len(chat_history)
            },
            "chat_history": chat_history
        }

        # Convert the export data to a JSON string with indentation and UTF-8 encoding
        return json.dumps(export_data,
                                           indent=4,
                                            ensure_ascii=False
                                        ).encode("utf-8")
                                    