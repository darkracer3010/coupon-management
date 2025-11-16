from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import pytz

Base = declarative_base()

# IST timezone
IST = pytz.timezone('Asia/Kolkata')


def get_ist_time():
    """Get current time in IST"""
    return datetime.now(IST)


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # Unique alphanumeric code
    type = Column(String, nullable=False)  # cart-wise, product-wise, bxgy
    details = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=get_ist_time)
    updated_at = Column(DateTime, default=get_ist_time, onupdate=get_ist_time)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    repetition_limit = Column(Integer, nullable=True)  # Extracted from details and stored separately
    times_used = Column(Integer, default=0)
