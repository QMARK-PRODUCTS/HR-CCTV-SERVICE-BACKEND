from src.database.db import get_session
from fastapi import Depends, HTTPException, Query ,UploadFile, File, Body, Form
from fastapi.responses import JSONResponse, Response
from sqlmodel import Session, select
from typing import Annotated
from src.app.v1.People.models.users_models import *
from src.app.v1.People.serializers import *
import shutil, os, json
from typing import Any

USER_STORAGE_DIR = f"{os.getenv('STORAGE_DIR', './storage')}/users/"

SessionDep = Annotated[Session, Depends(get_session)]

def AddNewUserModel(
    userModel: PeopleModel,
    session: SessionDep
    ) -> JSONResponse:
    
    try:
        session.add(userModel)
        session.commit()
        session.refresh(userModel)
        return JSONResponse(content={"message": "User model added successfully"}, status_code=201)
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "An error occurred while adding the user"}, status_code=500)
    

def GetUserModels(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    ) -> list[PeopleModel]:
    
    try:
        
        user_models = session.exec(select(PeopleModel).offset(offset).limit(limit)).all()
        
        user_models_data = [user.model_dump() for user in user_models]
        
        return JSONResponse(content={"result": user_models_data}, status_code=200)
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "An error occurred while fetching the user models"}, status_code=500)
    finally:
        session.close()
        
def DeleteUserModel(
    userModelId: int,
    session: SessionDep
    ) -> JSONResponse:
    
    try:
        user_model = session.query(PeopleModel).filter(PeopleModel.id == userModelId).first()
        
        if not user_model:
            raise HTTPException(status_code=404, detail="User model not found")
        
        session.delete(user_model)
        session.commit()
        
        return JSONResponse(content={"message": "User model deleted successfully"}, status_code=200)
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "An error occurred while deleting the user model"}, status_code=500)
    finally:
        session.close()
        

async def AddNewUser(
    session: SessionDep,
    userModelId: int = Form(...),
    name: str = Form(...),
    image: UploadFile = File(...),
    otherDetails: str = Form(...),
) -> JSONResponse:
    
    try:
        
        if not name or not userModelId:
            return JSONResponse(content={"message": "Missing required fields"}, status_code=400)

        try:
            otherDetails_dict: Dict[str, Any] = json.loads(otherDetails)
        except json.JSONDecodeError:
            return JSONResponse(content={"message": "Invalid JSON format in otherDetails"}, status_code=400)

        print("Parsed otherDetails:", otherDetails_dict)

        # 1. Check if PeopleModel exists
        user_model = session.exec(select(PeopleModel).where(PeopleModel.id == userModelId)).first()
        if not user_model:
            return JSONResponse(content={"message": "PeopleModel not found"}, status_code=404)
        
        # 2. Validate otherDetails data types
        processed_other_details = {}
        for key, value in otherDetails_dict.items():
            if key not in user_model.otherDetails:
                return JSONResponse(content={"message": f"Unexpected field '{key}' in otherDetails"}, status_code=400)

            expected_type = type(user_model.otherDetails[key])
            if not isinstance(value, expected_type):
                return JSONResponse(
                    content={"message": f"Incorrect data type for '{key}'. Expected {expected_type.__name__}, got {type(value).__name__}"},
                    status_code=400
                )
            
            processed_other_details[key] = value
        
        # 3. Create a new User entry (without the image first to get the ID)
        new_user = People(
            name=name,
            role=user_model.role,  # Assign role from PeopleModel
            otherDetails=processed_other_details,
            imageUrl="",  # Temporary empty path
            people_model_id=userModelId
        )
        
        session.add(new_user)
        session.commit()
        session.refresh(new_user)  # Get the assigned ID after insertion
        
        # 4. Create a directory for this user inside STORAGE_DIR
        user_folder = os.path.join(USER_STORAGE_DIR, str(new_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        # 5. Store image inside the user-specific folder
        file_extension = os.path.splitext(image.filename)[-1]
        file_path = os.path.join(user_folder, f"profile{file_extension}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # 6. Update imageUrl in database
        new_user.imageUrl = f"/api/v1/storage-operations/uploads/{new_user.id}/profile{file_extension}"
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        
        labels_file = os.path.join(USER_STORAGE_DIR, "labels.txt")
        with open(labels_file, "a") as f:
            f.write(f"{new_user.id},{new_user.name},{new_user.imageUrl}\n")

        return JSONResponse(content={"message": "User added successfully", "user": new_user.dict()}, status_code=201)

    except Exception as e:
        print("Error:", e)
        return JSONResponse(content={"message": "An error occurred while adding the user"}, status_code=500)
    
    
def DeleteUser(
    userId: int,
    session: SessionDep
    ) -> JSONResponse:
    
    try:
        user = session.query(People).filter(People.id == userId).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        labels_file = os.path.join(USER_STORAGE_DIR, "labels.txt")
        
        if os.path.exists(labels_file):
            with open(labels_file, "r") as file:
                lines = file.readlines()
            
            with open(labels_file, "w") as file:
                for line in lines:
                    if not line.startswith(f"{userId},"):
                        file.write(line)
    
        # Delete the user's folder and all its contents
        user_folder = os.path.join(USER_STORAGE_DIR, str(user.id))
        
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder)
        
        session.delete(user)
        session.commit()
        
        return JSONResponse(content={"message": "User deleted successfully"}, status_code=200)
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "An error occurred while deleting the user"}, status_code=500)
    finally:
        session.close()
        
        
def GetUsers(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    ) -> list[People]:
    
    try:
        
        users = session.exec(select(People).offset(offset).limit(limit)).all()
        
        users_data = [user.dict() for user in users]
        
        return JSONResponse(content={"result": users_data}, status_code=200)
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "An error occurred while fetching the users"}, status_code=500)
    finally:
        session.close()