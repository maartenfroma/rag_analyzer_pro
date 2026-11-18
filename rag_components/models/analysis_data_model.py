from dataclasses import dataclass

@dataclass
class AnalysisResult:
    summary: str
    document_count: int
    chunk_count: int
    model_used: str