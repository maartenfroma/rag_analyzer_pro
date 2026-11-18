from dataclasses import dataclass
from datetime import datetime

@dataclass
class DocData:
    id: int | None = None
    file_name: str = ""
    file_size: int = 0
    chunk_count: int = 0
    uploaded_at: datetime | None = None
    embedding_model: str = ""
    status: str = ""
