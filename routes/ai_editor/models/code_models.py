from pydantic import BaseModel


class CodePart(BaseModel):
    """Модель для части кода, сгенерированной разработчиком"""
    type: str  # "html" | "css" | "javascript"
    code: str
    step_name: str


class CombinedCodeResult(BaseModel):
    """Результат объединения кода"""
    content: str
    parts_count: int
    total_length: int

