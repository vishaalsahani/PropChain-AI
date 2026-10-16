import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    buyer = "buyer"
    owner = "owner"
    reviewer = "reviewer"
    admin = "admin"


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class FindingSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.buyer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    properties: Mapped[list["Property"]] = relationship(back_populates="owner")


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(100), default="Maharashtra")
    district: Mapped[str] = mapped_column(String(100), default="")
    taluka: Mapped[str] = mapped_column(String(100), default="")
    village: Mapped[str] = mapped_column(String(100), default="")
    survey_number: Mapped[str] = mapped_column(String(100), default="")
    gat_number: Mapped[str] = mapped_column(String(100), default="")
    cts_number: Mapped[str] = mapped_column(String(100), default="")
    area_sqft: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner: Mapped["User"] = relationship(back_populates="properties")
    documents: Mapped[list["Document"]] = relationship(back_populates="property", cascade="all, delete-orphan")
    findings: Mapped[list["Finding"]] = relationship(back_populates="property", cascade="all, delete-orphan")
    ownership_nodes: Mapped[list["OwnershipNode"]] = relationship(back_populates="property", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_hash: Mapped[str] = mapped_column(String(64))
    doc_type: Mapped[str] = mapped_column(String(100), default="unknown")
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.pending)
    extracted_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    blockchain_tx: Mapped[str | None] = mapped_column(String(100), nullable=True)
    blockchain_verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    property: Mapped["Property"] = relationship(back_populates="documents")


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    category: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[FindingSeverity] = mapped_column(Enum(FindingSeverity))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    property: Mapped["Property"] = relationship(back_populates="findings")


class OwnershipNode(Base):
    __tablename__ = "ownership_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    person_name: Mapped[str] = mapped_column(String(255))
    transaction_type: Mapped[str] = mapped_column(String(100))
    transaction_date: Mapped[str] = mapped_column(String(50))
    document_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, default=0)

    property: Mapped["Property"] = relationship(back_populates="ownership_nodes")
