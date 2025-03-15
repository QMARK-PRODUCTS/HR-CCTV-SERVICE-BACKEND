from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional, Dict
from datetime import datetime

class Functions(SQLModel, table=True):
    
    __tablename__ = "functions"
    
    id: int = Field(primary_key=True)
    name: str = Field(max_length=50)
    description: str = Field(max_length=255)
    type: str = Field(max_length=50)
    timeSlot: str = Field(max_length=50)
    camerasAssigned: Dict = Field(sa_column=Column(JSON))
    saveRecordings: bool = Field(default=False)
    notify: bool = Field(default=False)
    created_at: datetime = Field(default=datetime.now())
    
    
class FunctionInfo(SQLModel, table=True):
    
    __tablename__ = "function_info"
    
    id: int = Field(primary_key=True)
    function_id: int = Field(foreign_key="functions.id")
    timestamp: datetime
    avg_people_count: int