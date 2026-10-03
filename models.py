from datetime import datetime, timezone

from database import Base
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, DateTime, Integer, String, Text

# ==================== SQLAlchemy модели ====================

class DeviceDB(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(String, unique=True, index=True, nullable=False)
    device_type = Column(String, nullable=False)  # computer, monitor, printer
    serial_number = Column(String, nullable=False)
    inventory_number = Column(String, nullable=False)
    owner = Column(String, nullable=True)
    cabinet = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class DisputeDB(Base):
    __tablename__ = "disputes"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    comment = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# ==================== Pydantic схемы ====================

class DeviceCreate(BaseModel):
    system_id: str = Field(..., min_length=1, max_length=50, examples=["Y1000"])
    device_type: str = Field(..., pattern="^(computer|monitor|printer)$", examples=["computer"])
    serial_number: str = Field(..., min_length=1, examples=["S36284158"])
    inventory_number: str = Field(..., min_length=1, examples=["727827063"])
    owner: str | None = None
    cabinet: str | None = None


class DeviceResponse(BaseModel):
    id: int
    system_id: str
    device_type: str
    serial_number: str
    inventory_number: str
    owner: str | None = None
    cabinet: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DisputeCreate(BaseModel):
    device_id: int = Field(..., ge=1, examples=[1])
    reason: str = Field(..., min_length=10, max_length=500, examples=["Штрих-код повреждён, оборудование на месте"])
    comment: str | None = Field(None, max_length=1000)


class DisputeResponse(BaseModel):
    id: int
    device_id: int
    reason: str
    comment: str | None = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)