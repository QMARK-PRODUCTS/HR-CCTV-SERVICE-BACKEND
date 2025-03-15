from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class FunctionsCreateSchema(BaseModel):
    name: str
    description: str
    type: str
    timeSlot: str
    camerasAssigned: dict
    saveRecordings: bool
    notify: bool

    class Config:
        from_attributes = True