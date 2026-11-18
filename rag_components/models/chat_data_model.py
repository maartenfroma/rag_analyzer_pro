from dataclasses import dataclass
from datetime import datetime   


@dataclass

class ChatData:
    question: str = ""
    answer: str = ""
    created_at: datetime | None = None