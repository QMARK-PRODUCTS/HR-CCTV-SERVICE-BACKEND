from src.database.db import get_session
from fastapi import Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from sqlmodel import Session, select
from typing import Annotated
from src.app.v1.CameraSources.models.camera_sources import *
from sqlalchemy.sql.expression import cast
from sqlalchemy.types import String

SessionDep = Annotated[Session, Depends(get_session)]


def AddNewConnection(camera_source: CameraSources, session: SessionDep) -> CameraSources:
    try:
        if camera_source.type != "RTSP":
            raise HTTPException(status_code=400, detail="Only RTSP cameras are supported at the moment.")
        
        if not camera_source.sourceCredentials:
            raise HTTPException(status_code=400, detail="Source credentials are required")
        
        if not camera_source.sourceDetails:
            raise HTTPException(status_code=400, detail="Source details are required")
        
        username = camera_source.sourceCredentials.get("username")
        password = camera_source.sourceCredentials.get("password")
        ip_address = camera_source.sourceDetails.get("ipAddress")
        no_of_cameras = camera_source.sourceDetails.get("NoOfCameras")
        
        if not username or not password or not ip_address:
            raise HTTPException(status_code=400, detail="Username, password and IP address are required")
        
        if not no_of_cameras or not isinstance(no_of_cameras, int) or no_of_cameras <= 0:
            raise HTTPException(status_code=400, detail="Valid number of cameras is required")
        
        # Fetch all camera sources and check manually for existing IP
        all_camera_sources = session.query(CameraSources).all()
        existing_camera_source = None
        
        for cam in all_camera_sources:
            if cam.sourceDetails.get("ipAddress") == ip_address:
                existing_camera_source = cam
                break
        
        # Generate the full new camera list
        cameras = [
            {
                "name": f"Camera {i}",
                "url": f"rtsp://{username}:{password}@{ip_address}:554/{i}"
            }
            for i in range(1, no_of_cameras + 1)
        ]
        
        if existing_camera_source:
            # Replace cameras array completely
            existing_camera_source.sourceDetails = {
                "ipAddress": ip_address,
                "NoOfCameras": no_of_cameras,
                "cameras": cameras
            }
            print(existing_camera_source.sourceCredentials)
            existing_camera_source.sourceCredentials = camera_source.sourceCredentials

            
            session.commit()
            session.refresh(existing_camera_source)
            return JSONResponse(content={"message": "Camera source updated successfully"}, status_code=200)
        
        # If no existing source, add a new one
        camera_source.sourceDetails["cameras"] = cameras  # Add cameras to sourceDetails
        session.add(camera_source)
        session.commit()
        session.refresh(camera_source)
        
        return JSONResponse(content={"message": "Camera source added successfully"}, status_code=201)
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "An error occurred while adding/updating the camera source"}, status_code=500)

    
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
        
        # Extract required details
        username = updated_data.sourceCredentials.get("username")
        password = updated_data.sourceCredentials.get("password")
        ip_address = updated_data.sourceDetails.get("ipAddress")
        no_of_cameras = updated_data.sourceDetails.get("NoOfCameras")

        if not username or not password or not ip_address:
            raise HTTPException(status_code=400, detail="Username, password, and IP address are required")

        if not no_of_cameras or not isinstance(no_of_cameras, int) or no_of_cameras <= 0:
            raise HTTPException(status_code=400, detail="Valid number of cameras is required")

        # Generate updated cameras list
        updated_cameras = [
            {
                "name": f"Camera {i}",
                "url": f"rtsp://{username}:{password}@{ip_address}:554/{i}"
            }
            for i in range(1, no_of_cameras + 1)
        ]

        # Update only the necessary fields
        camera_source.sourceCredentials = updated_data.sourceCredentials
        camera_source.sourceDetails = {
            "ipAddress": ip_address,
            "NoOfCameras": no_of_cameras,
            "cameras": updated_cameras  # Completely replacing the cameras array
        }

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

