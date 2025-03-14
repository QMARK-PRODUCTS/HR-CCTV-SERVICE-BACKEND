from src.database.db import get_session
from fastapi import Depends, HTTPException, Query ,UploadFile, File, Body, Form
from fastapi.responses import JSONResponse, Response
from sqlmodel import Session, select
from typing import Annotated
from src.app.v1.Users.models.models import *
from passlib.context import CryptContext
from ..services.auth import *
from src.app.v1.Users.schemas import *
from src.config.variables import SECRET_KEY

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hashPassword(password: str) -> str:

    return pwd_context.hash(password + SECRET_KEY)

def verify_password(plain_password: str, hashed_password: str) -> bool:

    try:
        return pwd_context.verify(plain_password + SECRET_KEY, hashed_password)
    except Exception as e:
        print(e)
        return False

SessionDep = Annotated[Session, Depends(get_session)]

def AddNewUser(
    user: UserCreateSchema, 
    db: Session = Depends(get_session)
    ) -> JSONResponse:
    
    try:
        existing_users = db.exec(select(Users).where(Users.email == user.email)).all()
        if existing_users:
            raise HTTPException(status_code=400, detail="User already exists")
        
        total_users = db.exec(select(Users)).all()

        # Set role and password based on conditions
        if not total_users:
            role = "admin"
            is_active = True
            password = hashPassword(user.password)
        elif not user.role or user.role not in ["admin", "moderator"]:
            role = "moderator"
            is_active = False
            password = None  # Don't store an empty string as a password
        else:    
            role = user.role
            is_active = True
            password = hashPassword(user.password)

        # Convert Pydantic schema to ORM model
        new_user = Users(
            name=user.name,
            email=user.email,
            role=role,
            isActive=is_active,
            password=password
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return JSONResponse(content={"message": "User added successfully"}, status_code=201)
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "An error occurred while adding the user"}, status_code=500)
    
    
def CreateAdminUser(
    user: UserCreateSchema,
    db: Session = Depends(get_session)
    ) -> JSONResponse:
    try:
        users = db.exec(select(Users)).all()
        if users:
            raise HTTPException(status_code=400, detail="Admin user already exists")
        
        role = "admin"
        isActive = True
        password = hashPassword(user.password)
        

        new_user = Users(
            name=user.name,
            email=user.email,
            role=role,
            isActive=isActive,
            password=password
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return JSONResponse(content={"message": "Admin user added successfully"}, status_code=201)
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "An error occurred while adding the admin user"}, status_code=500)
    
       
def GetUsers(db: Session = Depends(get_session)):
    try:
        users = db.exec(select(Users)).all()
        users_data = [UsersGetSchema.model_validate(user).model_dump(mode="json") for user in users]

        return JSONResponse(content={"users": users_data}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def GetUserById(user_id: int, db: Session = Depends(get_session)):
    try:
        user = db.exec(select(Users).where(Users.id == user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = UsersGetSchema.model_validate(user).model_dump(mode="json")
        
        return JSONResponse(content=user_data, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
def UpdateUser(
    id: int,
    updatedData: UserUpdateSchema,
    db: Session = Depends(get_session)
) -> JSONResponse:
    try:
        if updatedData.role and updatedData.role not in ["admin", "moderator"]:
            raise HTTPException(status_code=400, detail="Invalid role")

        userInstance = db.get(Users, id)
        if not userInstance:
            raise HTTPException(status_code=404, detail="User not found")

        # Debugging: Check received data
        print(updatedData.dict(exclude_unset=True))

        # Update only the fields provided in the request
        for key, value in updatedData.dict(exclude_unset=True).items():
            setattr(userInstance, key, value)

        db.commit()
        db.refresh(userInstance)

        return JSONResponse(content={"message": "User updated successfully"}, status_code=200)
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(content={"message": "An error occurred while updating the user"}, status_code=500)
    
    
def DeleteUser(
    id: int,
    db: Session = Depends(get_session)
    ) -> JSONResponse:
    try:
        userInstance = db.get(Users, id)
        if not userInstance:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.delete(userInstance)
        db.commit()
        
        return JSONResponse(content={"message": "User deleted successfully"}, status_code=200)
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(content={"message": "An error occurred while deleting the user"}, status_code=500)
    
    
def AuthenticateUser(
    authData: UserAuthSchema,
    db: Session = Depends(get_session)
    ) -> JSONResponse:
    try:
        user = db.exec(select(Users).where(Users.email == authData.email)).first()
        
        if not user or not verify_password(authData.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        access_token = CreateAccessToken(user.id)
        refresh_token = CreateRefreshToken(user.id)
        
        return JSONResponse(content={
            "accessToken": access_token, 
            "refreshToken": refresh_token,
            "name": user.name,
            "email": user.email
            }, status_code=200)
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "An error occurred while authenticating the user"}, status_code=500)
    
    
def RefreshAccessToken(
    refreshData: RefreshTokenSchema,
    db: Session = Depends(get_session)
    ) -> JSONResponse:
    try:
        new_token = GenerateNewAccessToken(refreshData.refreshToken, db)
        if not new_token:
            return JSONResponse(content={"message": "Invalid refresh token"}, status_code=401)
        
        return JSONResponse(content={"accessToken": new_token}, status_code=200)
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "An error occurred while refreshing the access token"}, status_code=500)
    
    
def ValidateAccessToken(
    token: str
    ) -> JSONResponse:
    try:
        payload = ValidateToken(token)
        if payload and payload.get('userId'):
            return JSONResponse(content={"message": "Valid token"}, status_code=200)
        else:
            return JSONResponse(content={"message": "Invalid token"}, status_code=401)
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "An error occurred while validating the token"}, status_code=500)