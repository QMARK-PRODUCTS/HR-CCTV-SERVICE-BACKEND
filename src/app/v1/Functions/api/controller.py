from src.database.db import get_session
from fastapi import Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from sqlmodel import Session, select
from typing import Annotated
from src.app.v1.Functions.models.models import *
from sqlalchemy.sql.expression import cast
from sqlalchemy.types import String
from ..schemas import *

SessionDep = Annotated[Session, Depends(get_session)]


def AddNewFunction(
    function_data: FunctionsCreateSchema, session: SessionDep
) -> JSONResponse:
    try:
        # Convert Pydantic schema to SQLAlchemy model
        function = Functions(
            name=function_data.name,
            description=function_data.description,
            type="DETECT",  # Override type
            timeSlot=function_data.timeSlot,
            camerasAssigned=function_data.camerasAssigned,
            saveRecordings=function_data.saveRecordings,
            notify=function_data.notify
        )

        session.add(function)
        session.commit()
        session.refresh(function)

        return JSONResponse(content={"message": "Function added successfully"}, status_code=201)
    
    except Exception as e:
        print(e)
        session.rollback()
        return JSONResponse(content={"message": "An error occurred while adding the function"}, status_code=500)
    
def GetFunctions(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> JSONResponse:
    try:
        functions = session.exec(select(Functions).offset(offset).limit(limit)).all()
        
        functions_data = [
            {
                **function.model_dump(),
                "created_at": function.created_at.isoformat()  # Convert datetime to string
            }
            for function in functions
        ]

        return JSONResponse(content={"result": functions_data}, status_code=200)
    
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "An error occurred while fetching the functions"}, status_code=500)
    
    finally:
        session.close()
        
        
def UpdateFunction(
    functionId: int,
    updated_data: FunctionsCreateSchema,
    session: SessionDep
) -> JSONResponse:
    
    try:
        function = session.query(Functions).filter(Functions.id == functionId).first()
        
        if not function:
            raise HTTPException(status_code=404, detail="Function not found")
        
        function.name = updated_data.name
        function.description = updated_data.description
        function.timeSlot = updated_data.timeSlot
        function.camerasAssigned = updated_data.camerasAssigned
        function.saveRecordings = updated_data.saveRecordings
        function.notify = updated_data.notify
        
        session.commit()
        session.refresh(function)
        
        return JSONResponse(content={"message": "Function updated successfully"}, status_code=200)
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "An error occurred while updating the function"}, status_code=500)
    finally:
        session.close()
        
        
def DeleteFunction(
    functionId: int,
    session: SessionDep
    ) -> JSONResponse:
    
    try:
        function = session.query(Functions).filter(Functions.id == functionId).first()
        
        if not function:
            raise HTTPException(status_code=404, detail="Function not found")
        
        session.delete(function)
        session.commit()
        
        return JSONResponse(content={"message": "Function deleted successfully"}, status_code=200)
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "An error occurred while deleting the function"}, status_code=500)
    finally:
        session.close()