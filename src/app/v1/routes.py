from fastapi import APIRouter
from src.app.v1.CameraSources.routes import router as CameraSourcesRouter
from src.app.v1.DetectFaces.routes import router as DetectFacesRouter
from src.app.v1.StorageOperations.routes import router as StorageOperationsRouter
from src.app.v1.Users.routes import router as UsersRouter

router = APIRouter()

router.include_router(CameraSourcesRouter, prefix="/camera-sources", tags=["Camera Sources"])
router.include_router(DetectFacesRouter, prefix="/detect-faces", tags=["Detect Faces"])
router.include_router(StorageOperationsRouter, prefix="/storage-operations", tags=["Storage Operations"])
router.include_router(UsersRouter, prefix="/users", tags=["Users"])