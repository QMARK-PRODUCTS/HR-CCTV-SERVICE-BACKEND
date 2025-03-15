from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional, Dict
from datetime import datetime

class FunctionRecordings(SQLModel, table=True):
    
    __tablename__ = "function_recordings"
    
    id: int = Field(primary_key=True)
    function_id: int = Field(foreign_key="functions.id")
    timestamp: str
    recording: str
    people_count: int
    created_at: datetime = Field(default=datetime.now())
    
    def __repr__(self):
        return f"FunctionRecordings(id={self.id}, function_id={self.function_id}, timestamp={self.timestamp}, recording={self.recording}, people_count={self.people_count}, created_at={self.created_at})"
    
    def __str__(self):
        return f"FunctionRecordings(id={self.id}, function_id={self.function_id}, timestamp={self.timestamp}, recording={self.recording}, people_count={self.people_count}, created_at={self.created_at})"
    
    def __eq__(self, other):
        if not isinstance(other, FunctionRecordings):
            return False
        return self.id == other.id and self.function_id == other.function_id and self.timestamp == other.timestamp and self.recording == other.recording and self.people_count == other.people_count and self.created_at == other.created_at