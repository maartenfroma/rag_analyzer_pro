import csv
from datetime import datetime
from io import StringIO

#
# Helper class to export chat history to CSV format
class CsvExporter:
    
    # Static method to export chat history to a CSV file
    @staticmethod
    def export(chat_history, doc_title=None, chunk_count=None, file_size=None):
        
        if not chat_history:
            return
        
        rows=[]

        for entry in chat_history:
            
            rows.append(
                {
                    "timestamp": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "question": entry.get("query", ""),
                    "answer": entry.get("response", ""),
                    "source_count": len(
                        entry.get("metadata", [])
                    ),
                }
            )
        
        output = StringIO()
        # Create a CSV DictWriter with the specified fieldnames
        dict_writer = csv.DictWriter(output, fieldnames=["timestamp", "question", 
                                                          "answer", "source_count"])
        dict_writer.writeheader()
        dict_writer.writerows(rows)

        return output.getvalue()
    