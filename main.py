from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Annotated, Optional
import models
from models import Users, Donation_Responses, Requests
from database import engine, SessionLocal
from datetime import datetime, date

from router import admin, auth
from router.auth import get_current_user

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()


origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://blood-aid-assistance.netlify.app",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




models.Base.metadata.create_all(
    bind=engine
)


app.include_router(auth.router)
app.include_router(admin.router)


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


@app.get("/")
def home():

    return {
        "message": "Blood Donation & Emergency Assistance"
    }


@app.get("/about")
def about():

    return {
        "message": "API for managing blood donors, blood requests and emergency assistance"
    }


@app.get("/users")
def get_users(
    db: db_dependency,
    search: Optional[str] = None,
    blood_group: Optional[str] = None,
    district: Optional[str] = None,
    is_available: Optional[bool] = None,
    role: Optional[str] = None,
    sort_by: str = "newest",
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):

    user = db.query(Users)

    if search:

        if search.isdigit():

            user = user.filter(
                Users.id == int(search)
            )

        else:

            search_value = f"%{search}%"

            user = user.filter(
                (Users.firstname.ilike(search_value)) |
                (Users.lastname.ilike(search_value)) |
                (Users.username.ilike(search_value))
            )

    if blood_group:

        user = user.filter(
            Users.blood_group == blood_group
        )

    if district:

        user = user.filter(
            Users.district.ilike(
                f"%{district}%"
            )
        )

    if is_available is not None:

        user = user.filter(
            Users.is_available == is_available
        )

    if role:

        user = user.filter(
            Users.role == role
        )

    if sort_by == "alphabetical":

        user = user.order_by(
            Users.firstname.asc()
        )

    elif sort_by == "oldest":

        user = user.order_by(
            Users.created_at.asc()
        )

    else:

        user = user.order_by(
            Users.created_at.desc()
        )

    total = user.count()

    users = user.offset(
        (page - 1) * page_size
    ).limit(
        page_size
    ).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (
            total + page_size - 1
        ) // page_size,
        "users": users
    }


@app.get("/users/{user_id}")
def get_user_by_id(
    user_id: int,
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


@app.get("/donors")
def get_donors(
    db: db_dependency,
    search: Optional[str] = None,
    blood_group: Optional[str] = None,
    district: Optional[str] = None,
    sort_by: str = "newest",
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):

    user = db.query(
        Users
    ).filter(
        Users.role == "donor",
        Users.is_available == True
    )

    if search:

        if search.isdigit():

            user = user.filter(
                Users.id == int(search)
            )

        else:

            search_value = f"%{search}%"

            user = user.filter(
                (Users.firstname.ilike(search_value)) |
                (Users.lastname.ilike(search_value)) |
                (Users.username.ilike(search_value))
            )

    if blood_group:

        user = user.filter(
            Users.blood_group == blood_group
        )

    if district:

        user = user.filter(
            Users.district.ilike(
                f"%{district}%"
            )
        )

    if sort_by == "alphabetical":

        user = user.order_by(
            Users.firstname.asc()
        )

    elif sort_by == "last_donation":

        user = user.order_by(
            Users.last_donation_date.asc()
        )

    elif sort_by == "oldest":

        user = user.order_by(
            Users.created_at.asc()
        )

    else:

        user = user.order_by(
            Users.created_at.desc()
        )

    total = user.count()

    donors = user.offset(
        (page - 1) * page_size
    ).limit(
        page_size
    ).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (
            total + page_size - 1
        ) // page_size,
        "users": donors
    }


@app.get("/donors/{donor_id}")
def get_donor_by_id(
    donor_id: int,
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


# =========================================================
# CREATE BLOOD REQUEST
# =========================================================

@app.post("/requests")
def create_request(
    request_data: dict,
    current_user: user_dependency,
    db: db_dependency
):

    requester_id = current_user["id"]

    blood_group_needed = request_data.get(
        "blood_group_needed"
    )

    units_needed = request_data.get(
        "units_needed"
    )

    district = request_data.get(
        "district"
    )

    hospital_name = request_data.get(
        "hospital_name"
    )

    urgency = request_data.get(
        "urgency",
        "normal"
    )

    description = request_data.get(
        "description"
    )

    user = db.query(
        Users
    ).filter(
        Users.id == requester_id
    ).first()

    if not user:

        raise HTTPException(
            status_code=404,
            detail="Requester not found"
        )

    if not blood_group_needed:

        raise HTTPException(
            status_code=400,
            detail="Blood group is required"
        )

    if not units_needed or units_needed <= 0:

        raise HTTPException(
            status_code=400,
            detail="Units needed must be greater than 0"
        )

    if not district:

        raise HTTPException(
            status_code=400,
            detail="District is required"
        )

    if not hospital_name:

        raise HTTPException(
            status_code=400,
            detail="Hospital name is required"
        )

    if urgency not in [
        "normal",
        "urgent",
        "critical"
    ]:

        raise HTTPException(
            status_code=400,
            detail="Invalid urgency"
        )

    new_request = Requests(
        requester_id=requester_id,
        blood_group_needed=blood_group_needed,
        units_needed=units_needed,
        district=district,
        hospital_name=hospital_name,
        urgency=urgency,
        status="open",
        description=description
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return new_request


# =========================================================
# ALL OPEN BLOOD REQUESTS
# DONORS USE THIS ENDPOINT
# =========================================================

@app.get("/requests")
def get_all_blood_requests(
    db: db_dependency,
    search: Optional[str] = None,
    blood_group: Optional[str] = None,
    district: Optional[str] = None,
    urgency: Optional[str] = None
):

    requests = db.query(
        Requests
    ).filter(
        Requests.status == "open"
    )

    if search:

        search_value = f"%{search}%"

        requests = requests.filter(
            (Requests.hospital_name.ilike(search_value)) |
            (Requests.district.ilike(search_value)) |
            (Requests.description.ilike(search_value)) |
            (Requests.blood_group_needed.ilike(search_value))
        )

    if blood_group:

        requests = requests.filter(
            Requests.blood_group_needed == blood_group
        )

    if district:

        requests = requests.filter(
            Requests.district.ilike(
                f"%{district}%"
            )
        )

    if urgency:

        requests = requests.filter(
            Requests.urgency == urgency
        )

    return requests.order_by(
        Requests.created_at.desc()
    ).all()


# =========================================================
# MY REQUESTS
# LOGGED-IN USER USES THIS
# =========================================================

@app.get("/requests/my")
def get_my_requests(
    current_user: user_dependency,
    db: db_dependency,
    search: Optional[str] = None,
    blood_group: Optional[str] = None,
    district: Optional[str] = None,
    sort_by: str = "newest",
    urgency: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):

    user = db.query(
        Requests
    ).filter(
        Requests.requester_id == current_user["id"]
    )

    if search:

        if search.isdigit():

            user = user.filter(
                Requests.id == int(search)
            )

        else:

            search_value = f"%{search}%"

            user = user.filter(
                (Requests.hospital_name.ilike(search_value)) |
                (Requests.district.ilike(search_value)) |
                (Requests.description.ilike(search_value)) |
                (Requests.blood_group_needed.ilike(search_value))
            )

    if blood_group:

        user = user.filter(
            Requests.blood_group_needed == blood_group
        )

    if district:

        user = user.filter(
            Requests.district.ilike(
                f"%{district}%"
            )
        )

    if urgency:

        user = user.filter(
            Requests.urgency == urgency
        )

    if status:

        user = user.filter(
            Requests.status == status
        )

    if start_date:

        user = user.filter(
            Requests.created_at >= datetime.combine(
                start_date,
                datetime.min.time()
            )
        )

    if end_date:

        user = user.filter(
            Requests.created_at <= datetime.combine(
                end_date,
                datetime.max.time()
            )
        )

    if sort_by == "oldest":

        user = user.order_by(
            Requests.created_at.asc()
        )

    elif sort_by == "hospital":

        user = user.order_by(
            Requests.hospital_name.asc()
        )

    else:

        user = user.order_by(
            Requests.created_at.desc()
        )

    total = user.count()

    requests = user.offset(
        (page - 1) * page_size
    ).limit(
        page_size
    ).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (
            total + page_size - 1
        ) // page_size,
        "requests": requests
    }


# =========================================================
# GET REQUEST
# =========================================================

@app.get("/requests/{request_id}")
def get_request_by_id(
    request_id: int,
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


# =========================================================
# UPDATE REQUEST
# =========================================================

@app.put("/requests/{request_id}")
def update_request(
    request_id: int,
    request_data: dict,
    current_user: user_dependency,
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

    if (
        request.requester_id != current_user["id"]
        and current_user["role"] != "admin"
    ):

        raise HTTPException(
            status_code=403,
            detail="You do not have permission to update this request"
        )

    if "blood_group_needed" in request_data:

        request.blood_group_needed = request_data[
            "blood_group_needed"
        ]

    if "units_needed" in request_data:

        if request_data["units_needed"] <= 0:

            raise HTTPException(
                status_code=400,
                detail="Units needed must be greater than 0"
            )

        request.units_needed = request_data[
            "units_needed"
        ]

    if "district" in request_data:

        request.district = request_data[
            "district"
        ]

    if "hospital_name" in request_data:

        request.hospital_name = request_data[
            "hospital_name"
        ]

    if "urgency" in request_data:

        if request_data["urgency"] not in [
            "normal",
            "urgent",
            "critical"
        ]:

            raise HTTPException(
                status_code=400,
                detail="Invalid urgency"
            )

        request.urgency = request_data[
            "urgency"
        ]

    if "status" in request_data:

        if request_data["status"] not in [
            "open",
            "fulfilled",
            "expired"
        ]:

            raise HTTPException(
                status_code=400,
                detail="Invalid status"
            )

        if (
            current_user["role"] != "admin"
            and request_data["status"] != request.status
        ):

            raise HTTPException(
                status_code=403,
                detail="Only admin can change request status"
            )

        request.status = request_data[
            "status"
        ]

    if "description" in request_data:

        request.description = request_data[
            "description"
        ]

    db.commit()
    db.refresh(request)

    return request


# =========================================================
# DELETE REQUEST
# =========================================================

@app.delete("/requests/{request_id}")
def delete_request(
    request_id: int,
    current_user: user_dependency,
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

    if (
        request.requester_id != current_user["id"]
        and current_user["role"] != "admin"
    ):

        raise HTTPException(
            status_code=403,
            detail="You do not have permission to delete this request"
        )

    existing_responses = db.query(
        Donation_Responses
    ).filter(
        Donation_Responses.request_id == request_id
    ).first()

    if existing_responses:

        raise HTTPException(
            status_code=400,
            detail="Cannot delete a request that has donation responses"
        )

    db.delete(request)
    db.commit()

    return {
        "message": "Blood request deleted successfully"
    }


# =========================================================
# DONOR RESPOND
# =========================================================

@app.post("/requests/{request_id}/respond")
def respond_to_request(
    request_id: int,
    current_user: user_dependency,
    db: db_dependency
):

    if current_user["role"] != "donor":

        raise HTTPException(
            status_code=403,
            detail="Only donors can respond to blood requests"
        )

    donor_id = current_user["id"]

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

    donor = db.query(
        Users
    ).filter(
        Users.id == donor_id
    ).first()

    if not donor:

        raise HTTPException(
            status_code=404,
            detail="Donor not found"
        )

    if donor.role != "donor":

        raise HTTPException(
            status_code=400,
            detail="Only donors can respond to blood requests"
        )

    if donor.is_available is not True:

        raise HTTPException(
            status_code=400,
            detail="Donor is currently unavailable"
        )

    if request.status != "open":

        raise HTTPException(
            status_code=400,
            detail="This blood request is no longer open"
        )

    existing_response = db.query(
        Donation_Responses
    ).filter(
        Donation_Responses.request_id == request_id,
        Donation_Responses.donor_id == donor_id
    ).first()

    if existing_response:

        raise HTTPException(
            status_code=400,
            detail="You have already responded to this request"
        )

    response = Donation_Responses(
        request_id=request_id,
        donor_id=donor_id,
        status="offered"
    )

    db.add(response)
    db.commit()
    db.refresh(response)

    return response


# =========================================================
# REQUEST RESPONSES
# =========================================================

@app.get("/requests/{request_id}/responses")
def get_request_responses(
    request_id: int,
    current_user: user_dependency,
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

    if (
        request.requester_id != current_user["id"]
        and current_user["role"] != "admin"
    ):

        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view these responses"
        )

    responses = db.query(
        Donation_Responses
    ).filter(
        Donation_Responses.request_id == request_id
    ).order_by(
        Donation_Responses.responded_at.desc()
    ).all()

    return responses


# =========================================================
# DONOR RESPONSES
# =========================================================

@app.get("/donors/{donor_id}/responses")
def get_donor_responses(
    donor_id: int,
    current_user: user_dependency,
    db: db_dependency
):

    if (
        donor_id != current_user["id"]
        and current_user["role"] != "admin"
    ):

        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view these responses"
        )

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

    responses = db.query(
        Donation_Responses
    ).filter(
        Donation_Responses.donor_id == donor_id
    ).order_by(
        Donation_Responses.responded_at.desc()
    ).all()

    return responses
