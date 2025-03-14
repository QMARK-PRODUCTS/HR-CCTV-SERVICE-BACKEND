from fastapi import Form
from typing import Dict
from pydantic import BaseModel

class PeopleCreateSerializer(BaseModel):
    name: str
    otherDetails: Dict[str, any]  # Ensure otherDetails is a dictionary

    class Config:
        from_attributes = True
        arbitrary_types_allowed=True