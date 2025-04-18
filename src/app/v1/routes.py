from fastapi import APIRouter
from src.app.v1.CameraSources.routes import router as CameraSourcesRouter
from src.app.v1.DetectFaces.routes import router as DetectFacesRouter
from src.app.v1.StorageOperations.routes import router as StorageOperationsRouter
from src.app.v1.People.routes import router as PeopleRouter
from src.app.v1.Users.routes import router as UsersRouter
from src.app.v1.Functions.routes import router as FunctionsRouter

router = APIRouter()

router.include_router(CameraSourcesRouter, prefix="/camera-sources", tags=["Camera Sources"])
router.include_router(DetectFacesRouter, prefix="/detect-faces", tags=["Detect Faces"])
router.include_router(StorageOperationsRouter, prefix="/storage-operations", tags=["Storage Operations"])
router.include_router(PeopleRouter, prefix="/people", tags=["People"])
router.include_router(UsersRouter, prefix="/users", tags=["Users"])
router.include_router(FunctionsRouter, prefix="/functions", tags=["Functions"])