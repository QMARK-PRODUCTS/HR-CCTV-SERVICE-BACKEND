from src.database.db import get_session
from fastapi import Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from sqlmodel import Session, select
from typing import Annotated
from src.app.v1.CameraSources.models.camera_sources import *

SessionDep = Annotated[Session, Depends(get_session)]

def AddNewConnection(
    camera_source: CameraSources, 
    session: SessionDep
    ) -> CameraSources:
    
    try:
        if camera_source.type != "RTSP":
            raise HTTPException(status_code=400, detail="Only RTSP cameras are supported at the moment.")
        
        session.add(camera_source)
        session.commit()
        session.refresh(camera_source)
        return JSONResponse(content={"message": "Camera source added successfully"}, status_code=201)
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "An error occurred while adding the camera source"}, status_code=500)
    
def GetCameraSources(    
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    ) -> list[CameraSources]:
    
    camera_sources = session.exec(select(CameraSources).offset(offset).limit(limit)).all()
    
    camera_sources_data = [source.model_dump() for source in camera_sources]

    return JSONResponse(content={"result": camera_sources_data}, status_code=200)


def UpdateCameraSource(
    camera_id: int,
    updated_data: CameraSources,
    session: SessionDep
    ) -> JSONResponse:
    try:
        camera_source = session.query(CameraSources).filter(CameraSources.id == camera_id).first()
        
        if not camera_source:
            raise HTTPException(status_code=404, detail="Camera source not found")
        
        if updated_data.type != "RTSP":
            raise HTTPException(status_code=400, detail="Only RTSP cameras are supported at the moment.")
        
        camera_source.type = updated_data.type
        camera_source.sourceCredentials = updated_data.sourceCredentials
        camera_source.sourceDetails = updated_data.sourceDetails
        
        session.commit()
        session.refresh(camera_source)
        
        return JSONResponse(content={"message": "Camera source updated successfully"}, status_code=200)
    except Exception as e:
        print(e)
        session.rollback()
        return JSONResponse(content={"message": "An error occurred while updating the camera source"}, status_code=500)

def DeleteCameraSource(
    camera_id: int,
    session: SessionDep
    ) -> JSONResponse:
    try:
        camera_source = session.query(CameraSources).filter(CameraSources.id == camera_id).first()
        
        if not camera_source:
            raise HTTPException(status_code=404, detail="Camera source not found")
        
        session.delete(camera_source)
        session.commit()
        
        return JSONResponse(content={"message": "Camera source deleted successfully"}, status_code=200)
    except Exception as e:
        print(e)
        session.rollback()
        return JSONResponse(content={"message": "An error occurred while deleting the camera source"}, status_code=500)

