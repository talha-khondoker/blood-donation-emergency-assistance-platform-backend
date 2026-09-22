from database import SessionLocal
from models import Users
from passlib.context import CryptContext

db = SessionLocal()
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

admin = db.query(Users).filter(Users.username == "admin").first()

if admin is None:
    admin = Users(
        email="admin@gmail.com",
        username="admin",
        firstname="System",
        lastname="Admin",
        phone="01867051845",
        district="Jashore",
        hash_password=bcrypt_context.hash("admin"),
        blood_group="O+",
        role="admin",
        is_available=True
    )
    db.add(admin)
else:
    admin.email = "admin@gmail.com"
    admin.firstname = "System"
    admin.lastname = "Admin"
    admin.phone = "01867051845"
    admin.district = "Jashore"
    admin.hash_password = bcrypt_context.hash("admin")
    admin.role = "admin"

db.commit()
print("Admin account ready")
print("Username: admin")
print("Password: admin")