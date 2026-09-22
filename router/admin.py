from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated, Optional
from pydantic import BaseModel, EmailStr
from database import SessionLocal
from models import Users, Requests, Donation_Responses
from router.auth import get_current_user


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
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


user_dependency = Annotated[
    dict,
    Depends(get_current_user)
]


def admin_required(
    current_user: user_dependency
):

    if current_user["role"] != "admin":

        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user


admin_dependency = Annotated[
    dict,
    Depends(admin_required)
]


class UpdateUser(BaseModel):

    email: EmailStr
    username: str
    firstname: str
    lastname: str
    phone: str
    district: str
    blood_group: Optional[str] = None
    role: str
    is_available: bool = True


class UpdateRole(BaseModel):

    role: str


class UpdateAvailability(BaseModel):

    is_available: bool


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@router.get("/")
def admin_dashboard(
    current_user: admin_dependency,
    db: db_dependency
):

    total_users = db.query(
        Users
    ).count()

    total_donors = db.query(
        Users
    ).filter(
        Users.role == "donor"
    ).count()

    available_donors = db.query(
        Users
    ).filter(
        Users.role == "donor",
        Users.is_available == True
    ).count()

    total_requests = db.query(
        Requests
    ).count()

    open_requests = db.query(
        Requests
    ).filter(
        Requests.status == "open"
    ).count()

    fulfilled_requests = db.query(
        Requests
    ).filter(
        Requests.status == "fulfilled"
    ).count()

    total_responses = db.query(
        Donation_Responses
    ).count()

    return {
        "message": "Admin Dashboard",
        "total_users": total_users,
        "total_donors": total_donors,
        "available_donors": available_donors,
        "total_requests": total_requests,
        "open_requests": open_requests,
        "fulfilled_requests": fulfilled_requests,
        "total_donation_responses": total_responses
    }


# =========================================================
# USERS
# =========================================================

@router.get("/users")
def get_all_users(
    current_user: admin_dependency,
    db: db_dependency,
    search: Optional[str] = None,
    role: Optional[str] = None
):

    users = db.query(Users)

    if search:

        search_value = f"%{search}%"

        users = users.filter(
            (Users.firstname.ilike(search_value)) |
            (Users.lastname.ilike(search_value)) |
            (Users.username.ilike(search_value)) |
            (Users.email.ilike(search_value)) |
            (Users.phone.ilike(search_value))
        )

    if role:

        users = users.filter(
            Users.role == role
        )

    return users.order_by(
        Users.created_at.desc()
    ).all()


@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    current_user: admin_dependency,
    db: db_dependency
):

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

    return user


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    user_data: UpdateUser,
    current_user: admin_dependency,
    db: db_dependency
):

    if user_data.role not in [
        "user",
        "donor",
        "admin"
    ]:

        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )

    if (
        user_data.role == "donor"
        and not user_data.blood_group
    ):

        raise HTTPException(
            status_code=400,
            detail="Blood group is required before making user a donor"
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

    existing_email = db.query(
        Users
    ).filter(
        Users.email == user_data.email,
        Users.id != user_id
    ).first()

    if existing_email:

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    existing_username = db.query(
        Users
    ).filter(
        Users.username == user_data.username,
        Users.id != user_id
    ).first()

    if existing_username:

        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    existing_phone = db.query(
        Users
    ).filter(
        Users.phone == user_data.phone,
        Users.id != user_id
    ).first()

    if existing_phone:

        raise HTTPException(
            status_code=400,
            detail="Phone number already exists"
        )

    user.email = user_data.email
    user.username = user_data.username
    user.firstname = user_data.firstname
    user.lastname = user_data.lastname
    user.phone = user_data.phone
    user.district = user_data.district
    user.blood_group = user_data.blood_group
    user.role = user_data.role
    user.is_available = user_data.is_available

    db.commit()
    db.refresh(user)

    return {
        "message": "User information updated successfully",
        "user": user
    }


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role_data: UpdateRole,
    current_user: admin_dependency,
    db: db_dependency
):

    if role_data.role not in [
        "user",
        "donor",
        "admin"
    ]:

        raise HTTPException(
            status_code=400,
            detail="Invalid role"
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

    if (
        role_data.role == "donor"
        and not user.blood_group
    ):

        raise HTTPException(
            status_code=400,
            detail="Blood group is required before making user a donor"
        )

    if (
        user.id == current_user["id"]
        and role_data.role != "admin"
    ):

        raise HTTPException(
            status_code=400,
            detail="You cannot remove your own admin role"
        )

    user.role = role_data.role

    db.commit()
    db.refresh(user)

    return {
        "message": "User role updated successfully",
        "user_id": user.id,
        "role": user.role
    }


# =========================================================
# DONOR AVAILABILITY
# =========================================================

@router.put("/donors/{donor_id}/availability")
def update_donor_availability(
    donor_id: int,
    availability_data: UpdateAvailability,
    current_user: admin_dependency,
    db: db_dependency
):

    donor = db.query(
        Users
    ).filter(
        Users.id == donor_id,
        Users.role == "donor"
    ).first()

    if not donor:

        raise HTTPException(
            status_code=404,
            detail="Donor not found"
        )

    donor.is_available = (
        availability_data.is_available
    )

    db.commit()
    db.refresh(donor)

    return {
        "message": "Donor availability updated successfully",
        "donor_id": donor.id,
        "is_available": donor.is_available
    }


# =========================================================
# DELETE USER
# =========================================================

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: admin_dependency,
    db: db_dependency
):

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

    if user.id == current_user["id"]:

        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own admin account"
        )

    user_requests = db.query(
        Requests
    ).filter(
        Requests.requester_id == user_id
    ).all()

    user_responses = db.query(
        Donation_Responses
    ).filter(
        Donation_Responses.donor_id == user_id
    ).all()

    for response in user_responses:

        db.delete(response)

    for request in user_requests:

        request_responses = db.query(
            Donation_Responses
        ).filter(
            Donation_Responses.request_id == request.id
        ).all()

        for response in request_responses:

            db.delete(response)

        db.delete(request)

    db.delete(user)

    db.commit()

    return {
        "message": "User deleted successfully"
    }


# =========================================================
# DONORS
# =========================================================

@router.get("/donors")
def get_all_donors(
    current_user: admin_dependency,
    db: db_dependency,
    blood_group: Optional[str] = None,
    district: Optional[str] = None,
    is_available: Optional[bool] = None,
    search: Optional[str] = None
):

    donors = db.query(
        Users
    ).filter(
        Users.role == "donor"
    )

    if blood_group:

        donors = donors.filter(
            Users.blood_group == blood_group
        )

    if district:

        donors = donors.filter(
            Users.district.ilike(
                f"%{district}%"
            )
        )

    if is_available is not None:

        donors = donors.filter(
            Users.is_available == is_available
        )

    if search:

        search_value = f"%{search}%"

        donors = donors.filter(
            (Users.firstname.ilike(search_value)) |
            (Users.lastname.ilike(search_value)) |
            (Users.username.ilike(search_value)) |
            (Users.email.ilike(search_value)) |
            (Users.phone.ilike(search_value)) |
            (Users.blood_group.ilike(search_value)) |
            (Users.district.ilike(search_value))
        )

    return donors.order_by(
        Users.created_at.desc()
    ).all()


@router.get("/donors/{donor_id}")
def get_donor(
    donor_id: int,
    current_user: admin_dependency,
    db: db_dependency
):

    donor = db.query(
        Users
    ).filter(
        Users.id == donor_id,
        Users.role == "donor"
    ).first()

    if not donor:

        raise HTTPException(
            status_code=404,
            detail="Donor not found"
        )

    return donor


@router.put("/donors/{donor_id}")
def update_donor(
    donor_id: int,
    donor_data: UpdateUser,
    current_user: admin_dependency,
    db: db_dependency
):

    donor = db.query(
        Users
    ).filter(
        Users.id == donor_id,
        Users.role == "donor"
    ).first()

    if not donor:

        raise HTTPException(
            status_code=404,
            detail="Donor not found"
        )

    if not donor_data.blood_group:

        raise HTTPException(
            status_code=400,
            detail="Blood group is required for donor"
        )

    existing_email = db.query(
        Users
    ).filter(
        Users.email == donor_data.email,
        Users.id != donor_id
    ).first()

    if existing_email:

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    existing_username = db.query(
        Users
    ).filter(
        Users.username == donor_data.username,
        Users.id != donor_id
    ).first()

    if existing_username:

        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    existing_phone = db.query(
        Users
    ).filter(
        Users.phone == donor_data.phone,
        Users.id != donor_id
    ).first()

    if existing_phone:

        raise HTTPException(
            status_code=400,
            detail="Phone number already exists"
        )

    donor.email = donor_data.email
    donor.username = donor_data.username
    donor.firstname = donor_data.firstname
    donor.lastname = donor_data.lastname
    donor.phone = donor_data.phone
    donor.district = donor_data.district
    donor.blood_group = donor_data.blood_group
    donor.is_available = donor_data.is_available

    db.commit()
    db.refresh(donor)

    return {
        "message": "Donor information updated successfully",
        "donor": donor
    }


@router.delete("/donors/{donor_id}")
def delete_donor(
    donor_id: int,
    current_user: admin_dependency,
    db: db_dependency
):

    donor = db.query(
        Users
    ).filter(
        Users.id == donor_id,
        Users.role == "donor"
    ).first()

    if not donor:

        raise HTTPException(
            status_code=404,
            detail="Donor not found"
        )

    if donor.id == current_user["id"]:

        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own admin account"
        )

    donor_responses = db.query(
        Donation_Responses
    ).filter(
        Donation_Responses.donor_id == donor_id
    ).all()

    for response in donor_responses:

        db.delete(response)

    db.delete(donor)

    db.commit()

    return {
        "message": "Donor deleted successfully"
    }


# =========================================================
# REQUESTS
# =========================================================

@router.get("/requests")
def get_all_requests(
    current_user: admin_dependency,
    db: db_dependency,
    status: Optional[str] = None,
    urgency: Optional[str] = None
):

    requests = db.query(
        Requests
    )

    if status:

        requests = requests.filter(
            Requests.status == status
        )

    if urgency:

        requests = requests.filter(
            Requests.urgency == urgency
        )

    return requests.order_by(
        Requests.created_at.desc()
    ).all()


@router.get("/requests/{request_id}")
def get_request(
    request_id: int,
    current_user: admin_dependency,
    db: db_dependency
):

    request = db.query(
        Requests
    ).filter(
        Requests.id == request_id
    ).first()

    if not request:

        raise HTTPException(
            status_code=404,
            detail="Blood request not found"
        )

    return request


@router.put("/requests/{request_id}/status")
def update_request_status(
    request_id: int,
    status: str,
    current_user: admin_dependency,
    db: db_dependency
):

    if status not in [
        "open",
        "fulfilled",
        "expired"
    ]:

        raise HTTPException(
            status_code=400,
            detail="Invalid request status"
        )

    request = db.query(
        Requests
    ).filter(
        Requests.id == request_id
    ).first()

    if not request:

        raise HTTPException(
            status_code=404,
            detail="Blood request not found"
        )

    request.status = status

    db.commit()
    db.refresh(request)

    return {
        "message": "Request status updated successfully",
        "request_id": request.id,
        "status": request.status
    }


@router.delete("/requests/{request_id}")
def delete_request(
    request_id: int,
    current_user: admin_dependency,
    db: db_dependency
):

    request = db.query(
        Requests
    ).filter(
        Requests.id == request_id
    ).first()

    if not request:

        raise HTTPException(
            status_code=404,
            detail="Blood request not found"
        )

    responses = db.query(
        Donation_Responses
    ).filter(
        Donation_Responses.request_id == request_id
    ).all()

    for response in responses:

        db.delete(response)

    db.delete(request)

    db.commit()

    return {
        "message": "Blood request deleted successfully"
    }


# =========================================================
# RESPONSES
# =========================================================

@router.get("/responses")
def get_all_responses(
    current_user: admin_dependency,
    db: db_dependency,
    status: Optional[str] = None
):

    responses = db.query(
        Donation_Responses
    )

    if status:

        responses = responses.filter(
            Donation_Responses.status == status
        )

    return responses.order_by(
        Donation_Responses.responded_at.desc()
    ).all()


@router.get("/responses/{response_id}")
def get_response(
    response_id: int,
    current_user: admin_dependency,
    db: db_dependency
):

    response = db.query(
        Donation_Responses
    ).filter(
        Donation_Responses.id == response_id
    ).first()

    if not response:

        raise HTTPException(
            status_code=404,
            detail="Donation response not found"
        )

    return response


@router.put("/responses/{response_id}/status")
def update_response_status(
    response_id: int,
    status: str,
    current_user: admin_dependency,
    db: db_dependency
):

    if status not in [
        "offered",
        "confirmed",
        "completed",
        "cancelled"
    ]:

        raise HTTPException(
            status_code=400,
            detail="Invalid donation response status"
        )

    response = db.query(
        Donation_Responses
    ).filter(
        Donation_Responses.id == response_id
    ).first()

    if not response:

        raise HTTPException(
            status_code=404,
            detail="Donation response not found"
        )

    response.status = status

    db.commit()
    db.refresh(response)

    return {
        "message": "Donation response status updated successfully",
        "response_id": response.id,
        "status": response.status
    }


@router.delete("/responses/{response_id}")
def delete_response(
    response_id: int,
    current_user: admin_dependency,
    db: db_dependency
):

    response = db.query(
        Donation_Responses
    ).filter(
        Donation_Responses.id == response_id
    ).first()

    if not response:

        raise HTTPException(
            status_code=404,
            detail="Donation response not found"
        )

    db.delete(response)
    db.commit()

    return {
        "message": "Donation response deleted successfully"
    }