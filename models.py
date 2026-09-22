from database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship


class Users(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    firstname = Column(String)
    lastname = Column(String)
    phone = Column(String, unique=True)
    district = Column(String)
    hash_password = Column(String)
    blood_group = Column(String)
    last_donation_date = Column(DateTime)
    is_available = Column(Boolean, default=True)
    role = Column(String, default="user")    # (donor, requester, admin)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    blood_requests = relationship("Requests", back_populates="requester")
    donation_responses = relationship("Donation_Responses", back_populates="donor")
    
    
    
    
    
class Requests(Base):
    
    __tablename__ = 'requests'
    
    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey('users.id'))
    blood_group_needed = Column(String)
    units_needed  = Column(Integer)
    district = Column(String)
    hospital_name = Column(String)
    urgency = Column(String, default="normal")   # (normal, urgent, critical)
    status = Column(String, default="open")    #   (open, fulfilled, expired)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    requester = relationship("Users", back_populates="blood_requests")
    donation_responses = relationship("Donation_Responses", back_populates="request")
    
    


class Donation_Responses(Base):
    
    __tablename__ = 'donation_responses'
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey('requests.id'))
    donor_id = Column(Integer, ForeignKey('users.id'))
    status = Column(String, default="offered")  # offered, confirmed, completed, cancelled)
    responded_at = Column(DateTime, default=datetime.utcnow)
    request = relationship("Requests", back_populates="donation_responses")
    donor = relationship("Users", back_populates="donation_responses")
    
