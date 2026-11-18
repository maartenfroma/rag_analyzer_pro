from rag_components.chat_exporter import csv_exporter, docx_exporter, excel_exporter, pdf_exporter, json_exporter

# Helper class to export chat history to the Streamlit session state
class MainExporter:
    
    # Dictionary mapping export formats to their respective exporter classes
    EXPORTERS={
        
        "csv": csv_exporter.CsvExporter,
        "docx": docx_exporter.DocxExporter,
        "excel": excel_exporter.ExcelExporter,
        "pdf": pdf_exporter.PdfExporter,
        "json": json_exporter.JsonExporter,
    }
    
    # Static method to export chat history using the appropriate exporter based on the format
    # Passing the format as the first argument determines which exporter to use
    # Second argument and beyond are passed to the exporter's export method
    
    @staticmethod
    def export(format, *args, **kwargs):
        
        exporter=MainExporter.EXPORTERS.get(format.lower())
        if not exporter:
            raise ValueError(f"Unsupported export format: {format}")
        
        return exporter.export(*args, **kwargs)