from fastapi import APIRouter, Request, Depends, HTTPException, status, Form, Response
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from database import get_db
from models import User
import json
import uuid

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your_secret_key"  # Replace with a secure secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def generate_uuid():
    return str(uuid.uuid4())

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post('/signup')
def signup(
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if the email is already registered
    user = db.query(User).filter_by(Email=email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    # Hash the password
    hashed_password = get_password_hash(password)
    # Create a new user instance
    new_user = User(
        UserID = generate_uuid(),
        Email=email,
        Password=hashed_password,
        Name=name,
        Role=True  # Default role is user; change as needed
    )
    # Add the user to the database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # Create an access token for the new user
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(new_user.UserID)}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": new_user.Role
    }

@router.post('/login')
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(Email=email).first()
    if user and verify_password(password, user.Password):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.UserID)}, expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": user.Role
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post('/logout')
def logout(response: Response):
    # Implement on client side: Remove the token from storage

    return {"message": "Logged out successfully"}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter_by(UserID=user_id).first()
    if user is None:
        raise credentials_exception
    return user
