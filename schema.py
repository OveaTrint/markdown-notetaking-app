from typing import List

from pydantic import BaseModel


class SavedNotes(BaseModel):
    count: int
    notes: List[dict[str, str]]
