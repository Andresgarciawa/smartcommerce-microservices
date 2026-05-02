from pydantic import BaseModel
from typing import Optional

class BookInput(BaseModel):
    title: Optional[str]
    author: Optional[str]
    publisher: Optional[str]
    published_date: Optional[str]
    description: Optional[str]
    cover_url: Optional[str]

class NormalizedOutput(BaseModel):
    title: str
    author: str
    publisher: str
    year: int
    description: str
    cover_url: Optional[str]