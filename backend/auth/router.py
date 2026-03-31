from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from backend.database import get_db
from backend.auth.schemas import UserCreate, UserLogin, UserOut, Token
from backend.auth import service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    return service.register_user(db, data)


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = service.authenticate_user(db, data.email, data.password)
    token = service.create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def me(current_user=Depends(service.get_current_user)):
    return current_user


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


@router.patch("/me", response_model=UserOut)
def update_me(data: UserUpdate, current_user=Depends(service.get_current_user), db: Session = Depends(get_db)):
    if data.full_name:
        current_user.full_name = data.full_name
    if data.phone is not None:
        current_user.phone = data.phone
    if data.new_password:
        if not data.current_password:
            raise HTTPException(status_code=400, detail="Aktuálne heslo je povinné")
        if not service.verify_password(data.current_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Nesprávne aktuálne heslo")
        if len(data.new_password) < 8:
            raise HTTPException(status_code=400, detail="Nové heslo musí mať aspoň 8 znakov")
        current_user.hashed_password = service.hash_password(data.new_password)
    db.commit()
    db.refresh(current_user)
    return current_user
