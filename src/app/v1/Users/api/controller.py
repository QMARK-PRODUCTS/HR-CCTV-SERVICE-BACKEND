from src.database.db import get_session
from fastapi import Depends, HTTPException, Query ,UploadFile, File
from fastapi.responses import JSONResponse, Response
from sqlmodel import Session, select
from typing import Annotated
from src.app.v1.Users.models.users_models import *
from src.app.v1.Users.serializers import *
import shutil, os, json

USER_STORAGE_DIR = f"{os.getenv('STORAGE_DIR', './storage')}/users/"

SessionDep = Annotated[Session, Depends(get_session)]

def AddNewUserModel(
    userModel: UserModel,
    session: SessionDep
    ) -> JSONResponse:
    
    try:
        session.add(userModel)
        session.commit()
        session.refresh(userModel)
        return JSONResponse(content={"message": "User added successfully"}, status_code=201)
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "An error occurred while adding the user"}, status_code=500)
    

def GetUserModels(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    ) -> list[UserModel]:
    
    try:
        
        user_models = session.exec(select(UserModel).offset(offset).limit(limit)).all()
        
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
        user_model = session.query(UserModel).filter(UserModel.id == userModelId).first()
        
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
        
        
        
def AddNewUser(
    name: str,
    otherDetails: str,
    userModelId: int,
    session: SessionDep,
    image: UploadFile = File(...),
) -> JSONResponse:
    
    try:
        # Convert otherDetails from JSON string to dictionary
        try:
            otherDetails_dict = json.loads(otherDetails) if isinstance(otherDetails, str) else otherDetails
        except json.JSONDecodeError:
            return JSONResponse(content={"message": "Invalid JSON format in otherDetails"}, status_code=400)

        print("Parsed otherDetails:", otherDetails_dict)
        print("Type of otherDetails:", type(otherDetails_dict))

        # 1. Check if UserModel exists
        user_model = session.exec(select(UserModel).where(UserModel.id == userModelId)).first()
        if not user_model:
            return JSONResponse(content={"message": "UserModel not found"}, status_code=404)
        
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
            
            processed_other_details[key] = value  # If type matches, add to processed details
        
        # 3. Create a new User entry (without the image first to get the ID)
        new_user = User(
            name=name,
            role=user_model.role,  # Assign role from UserModel
            otherDetails=processed_other_details,
            imageUrl="",  # Temporary empty path
            user_model_id=userModelId
        )
        
        session.add(new_user)
        session.commit()
        session.refresh(new_user)  # Get the assigned ID after insertion
        
        # 4. Create a directory for this user inside STORAGE_DIR
        user_folder = os.path.join(USER_STORAGE_DIR, str(new_user.id))
        os.makedirs(user_folder, exist_ok=True)  # Ensure the user folder exists
        
        # 5. Store image inside the user-specific folder
        file_extension = os.path.splitext(image.filename)[-1]  # Get file extension
        file_path = os.path.join(user_folder, f"profile{file_extension}")  # Rename to "profile"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # 6. Update imageUrl in database
        new_user.imageUrl = f"/api/v1/storage-operations/uploads/{new_user.id}/profile{file_extension}"
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return JSONResponse(content={"message": "User added successfully", "user": new_user.dict()}, status_code=201)

    except Exception as e:
        print("Error:", e)
        return JSONResponse(content={"message": "An error occurred while adding the user"}, status_code=500)
    
    
def DeleteUser(
    userId: int,
    session: SessionDep
    ) -> JSONResponse:
    
    try:
        user = session.query(User).filter(User.id == userId).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
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
    ) -> list[User]:
    
    try:
        
        users = session.exec(select(User).offset(offset).limit(limit)).all()
        
        users_data = [user.dict() for user in users]
        
        return JSONResponse(content={"result": users_data}, status_code=200)
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "An error occurred while fetching the users"}, status_code=500)
    finally:
        session.close()