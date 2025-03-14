import jwt
from datetime import datetime, timedelta, timezone
from ..models.models import *
from jose import JWTError
from src.config.variables import SECRET_KEY
from src.app.v1.Users.api.controller import get_session
from fastapi import HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from ..schemas import UsersGetSchema


def GetUserById(user_id: int, db: Session):
    try:
        user = db.exec(select(Users).where(Users.id == user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = UsersGetSchema.model_validate(user).model_dump(mode="json")
        
        return JSONResponse(content=user_data, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def CreateAccessToken(user_id: int):
    try:
    
        payload = {
            'userId': user_id,
            'exp': datetime.now(timezone.utc) + timedelta(days=1)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    except Exception as e:
        print(e)
        return None
    
    
def CreateRefreshToken(user_id: int):
    try:
    
        payload = {
            'userId': user_id,
            'exp': datetime.now(timezone.utc) + timedelta(days=90)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    except Exception as e:
        print(e)
        return None
    
    
def ValidateToken(token):
    try:
        # Decode the token and validate signature & expiration automatically
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        print(payload)
        return payload  # Return the decoded payload if valid
    except JWTError as e:
        print(e)
        # Check for specific errors: Expired signature or invalid signature
        if "expired" in str(e).lower():
            print("Token has expired.")
        elif "signature" in str(e).lower():
            print("Invalid signature.")
        else:
            print(f"JWT Error: {e}")
        return None
    
def ValidateAccessToken(token):
    try:
        payload = ValidateToken(token)
        if payload and payload.get('userId'):
            userExist = GetUserById(payload.get('userId'))
            if userExist:
                return userExist
    except Exception as e:
        print(f"Error in ValidateAccessToken: {e}")
    return None



def GenerateNewAccessToken(refresh_token: str, db: Session):
    
    try:
        payload = ValidateToken(refresh_token)
        print(payload)
        if payload and payload.get('userId'):
            userExist = GetUserById(user_id=payload.get('userId'), db=db)
            if userExist:
                print(userExist)
                return CreateAccessToken(payload.get('userId'))
    except Exception as e:
        print(f"Error in GenerateNewAccessToken: {e}")
    return None

def GenerateTokens(user_id: int):
    try:
        access_token = CreateAccessToken(user_id)
        refresh_token = CreateRefreshToken(user_id)
        return access_token, refresh_token
    except Exception as e:
        print(f"Error in GenerateTokens: {e}")
    return None, None

