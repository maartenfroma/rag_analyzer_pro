from pathlib import Path

class MetadataHelper:

    @staticmethod
    def build_metadata(source:str, file_name:str, **extra) -> dict:
        
        metadata = {"source": source,
                    "file_name": file_name,
                    "file_type": Path(file_name).suffix.lower()}

        metadata.update({key: value
                         for key, value in extra.items() 
                         if value is not None})

        
       
        return metadata