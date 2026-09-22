from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Users
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from typing import Annotated, cast


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


SECRET_KEY = "69b61bd65567f659772872628c1bea2f916d2b74087637cebba7e782af928d32"
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 300
REFRESH_TOKEN_EXPIRE_DAYS = 7
RESET_TOKEN_EXPIRE_MINUTES = 15


bcrypt_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


oauth2_bearer = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[
    Session,
    Depends(get_db)
]


class CreateUser(BaseModel):

    email: EmailStr
    username: str
    firstname: str
    lastname: str
    phone: str
    district: str
    blood_group: str | None = None
    role: str = "user"
    password: str


class Token(BaseModel):

    access_token: str
    refresh_token: str
    token_type: str


class ForgotPassword(BaseModel):

    email: EmailStr


class ResetPassword(BaseModel):

    token: str
    new_password: str


def authenticate_user(
    username: str,
    password: str,
    db: Session
):

    user = db.query(
        Users
    ).filter(
        Users.username == username
    ).first()

    if not user:

        return False

    if not bcrypt_context.verify(
        password,
        user.hash_password
    ):

        return False

    return user


def create_access_token(
    username: str,
    user_id: int,
    role: str,
    expires_delta: timedelta
):

    encode = {
        "sub": username,
        "id": user_id,
        "role": role,
        "type": "access"
    }

    expires = (
        datetime.now(timezone.utc)
        + expires_delta
    )

    encode.update({
        "exp": expires
    })

    return jwt.encode(
        encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def create_refresh_token(
    username: str,
    user_id: int,
    role: str
):

    encode = {
        "sub": username,
        "id": user_id,
        "role": role,
        "type": "refresh"
    }

    expires = (
        datetime.now(timezone.utc)
        + timedelta(
            days=REFRESH_TOKEN_EXPIRE_DAYS
        )
    )

    encode.update({
        "exp": expires
    })

    return jwt.encode(
        encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def create_reset_token(
    user_id: int
):

    encode = {
        "id": user_id,
        "type": "reset"
    }

    expires = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=RESET_TOKEN_EXPIRE_MINUTES
        )
    )

    encode.update({
        "exp": expires
    })

    return jwt.encode(
        encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


async def get_current_user(
    token: Annotated[
        str,
        Depends(oauth2_bearer)
    ]
):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")
        user_id = payload.get("id")
        token_type = payload.get("type")

        if (
            username is None
            or user_id is None
            or token_type != "access"
        ):

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

        db = SessionLocal()

        try:

            user = db.query(
                Users
            ).filter(
                Users.id == int(user_id)
            ).first()

            if not user:

                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )

            return {
                "username": user.username,
                "id": user.id,
                "role": user.role
            }

        finally:

            db.close()

    except JWTError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


user_dependency = Annotated[
    dict,
    Depends(get_current_user)
]


def require_role(
    current_user,
    allowed_roles
):

    if current_user["role"] not in allowed_roles:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource"
        )

    return current_user


@router.post("/register")
def register_user(
    user_data: CreateUser,
    db: db_dependency
):

    existing_email = db.query(
        Users
    ).filter(
        Users.email == user_data.email
    ).first()

    if existing_email:

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    existing_username = db.query(
        Users
    ).filter(
        Users.username == user_data.username
    ).first()

    if existing_username:

        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )

    existing_phone = db.query(
        Users
    ).filter(
        Users.phone == user_data.phone
    ).first()

    if existing_phone:

        raise HTTPException(
            status_code=400,
            detail="Phone number already registered"
        )

    if user_data.role not in [
        "user",
        "donor"
    ]:

        raise HTTPException(
            status_code=400,
            detail="Role must be either user or donor"
        )

    if (
        user_data.role == "donor"
        and not user_data.blood_group
    ):

        raise HTTPException(
            status_code=400,
            detail="Blood group is required for donors"
        )

    hashed_password = bcrypt_context.hash(
        user_data.password
    )

    new_user = Users(
        email=user_data.email,
        username=user_data.username,
        firstname=user_data.firstname,
        lastname=user_data.lastname,
        phone=user_data.phone,
        district=user_data.district,
        hash_password=hashed_password,
        blood_group=user_data.blood_group,
        role=user_data.role,
        is_available=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "id": new_user.id,
        "email": new_user.email,
        "username": new_user.username,
        "firstname": new_user.firstname,
        "lastname": new_user.lastname,
        "phone": new_user.phone,
        "district": new_user.district,
        "blood_group": new_user.blood_group,
        "role": new_user.role
    }


@router.post(
    "/login",
    response_model=Token
)
def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends()
    ],
    db: db_dependency
):

    user = authenticate_user(
        form_data.username,
        form_data.password,
        db
    )

    if not user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    username_value = str(
        user.username
    )

    user_id = int(
        user.id
    )

    role_value = str(
        user.role
    )

    access_token = create_access_token(
        username_value,
        user_id,
        role_value,
        timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    refresh_token = create_refresh_token(
        username_value,
        user_id,
        role_value
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh")
def refresh_access_token(
    refresh_token: str
):

    try:

        payload = jwt.decode(
            refresh_token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")
        user_id = payload.get("id")
        role = payload.get("role")
        token_type = payload.get("type")

        if (
            username is None
            or user_id is None
            or role is None
            or token_type != "refresh"
        ):

            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )

        access_token = create_access_token(
            username,
            user_id,
            role,
            timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )


@router.get("/me")
def get_me(
    current_user: user_dependency,
    db: db_dependency
):

    user = db.query(
        Users
    ).filter(
        Users.id == current_user["id"]
    ).first()

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "phone": user.phone,
        "district": user.district,
        "blood_group": user.blood_group,
        "last_donation_date": user.last_donation_date,
        "is_available": user.is_available,
        "role": user.role
    }


@router.post("/forgot-password")
def forgot_password(
    forgot_data: ForgotPassword,
    db: db_dependency
):

    user = db.query(
        Users
    ).filter(
        Users.email == forgot_data.email
    ).first()

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User with this email was not found"
        )

    user_id = cast(
        int,
        user.id
    )

    reset_token = create_reset_token(
        user_id
    )

    return {
        "message": "Password reset token generated",
        "reset_token": reset_token
    }


@router.post("/reset-password")
def reset_password(
    reset_data: ResetPassword,
    db: db_dependency
):

    try:

        payload = jwt.decode(
            reset_data.token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("id")
        token_type = payload.get("type")

        if (
            user_id is None
            or token_type != "reset"
        ):

            raise HTTPException(
                status_code=401,
                detail="Invalid reset token"
            )

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired reset token"
        )

    user = db.query(
        Users
    ).filter(
        Users.id == user_id
    ).first()

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.hash_password = bcrypt_context.hash(
        reset_data.new_password
    )

    db.commit()

    return {
        "message": "Password reset successfully"
    }