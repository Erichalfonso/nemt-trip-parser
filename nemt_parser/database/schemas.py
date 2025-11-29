"""
Database schemas for storing clinic mappings and trip data.

Uses SQLAlchemy for ORM - compatible with PostgreSQL, MySQL, SQLite, etc.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean, Date, Time, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class ClinicMappingDB(Base):
    """
    Stores column mappings for each clinic.

    Each clinic gets one row that defines how their Excel columns
    map to our standardized fields.
    """

    __tablename__ = "clinic_mappings"

    clinic_id = Column(String(100), primary_key=True, index=True)
    clinic_name = Column(String(255), nullable=True)

    # Required field mappings
    patient_name = Column(String(100), nullable=False)
    medicaid_id = Column(String(100), nullable=False)

    pickup_address = Column(String(100), nullable=False)
    pickup_city = Column(String(100), nullable=False)
    pickup_zip = Column(String(100), nullable=False)

    dropoff_address = Column(String(100), nullable=False)
    dropoff_city = Column(String(100), nullable=False)
    dropoff_zip = Column(String(100), nullable=False)

    appointment_date = Column(String(100), nullable=False)

    # Optional field mappings
    patient_phone = Column(String(100), nullable=True)
    date_of_birth = Column(String(100), nullable=True)

    pickup_state = Column(String(100), nullable=True)
    dropoff_state = Column(String(100), nullable=True)

    appointment_time = Column(String(100), nullable=True)

    trip_type = Column(String(100), nullable=True)
    wheelchair = Column(String(100), nullable=True)
    stretcher = Column(String(100), nullable=True)
    ambulatory = Column(String(100), nullable=True)

    notes = Column(String(100), nullable=True)
    appointment_type = Column(String(100), nullable=True)
    clinic_name_col = Column(String(100), nullable=True)  # Column that contains clinic name

    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<ClinicMapping(clinic_id='{self.clinic_id}', clinic_name='{self.clinic_name}')>"


class TripDB(Base):
    """
    Stores parsed trip data in standardized format.

    After parsing, trips are stored here for billing, scheduling, etc.
    """

    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Patient Information
    patient_name = Column(String(255), nullable=False, index=True)
    patient_phone = Column(String(20), nullable=True)
    medicaid_id = Column(String(50), nullable=False, index=True)
    date_of_birth = Column(Date, nullable=True)

    # Pickup Location
    pickup_address = Column(String(500), nullable=False)
    pickup_city = Column(String(100), nullable=False)
    pickup_state = Column(String(2), default="FL")
    pickup_zip = Column(String(10), nullable=False)

    # Dropoff Location
    dropoff_address = Column(String(500), nullable=False)
    dropoff_city = Column(String(100), nullable=False)
    dropoff_state = Column(String(2), default="FL")
    dropoff_zip = Column(String(10), nullable=False)

    # Appointment Details
    appointment_date = Column(Date, nullable=False, index=True)
    appointment_time = Column(Time, nullable=True)

    # Trip Characteristics
    trip_type = Column(String(20), default="round_trip")
    wheelchair = Column(Boolean, default=False)
    stretcher = Column(Boolean, default=False)
    ambulatory = Column(Boolean, default=True)

    # Additional Information
    notes = Column(Text, nullable=True)
    appointment_type = Column(String(100), nullable=True)
    clinic_name = Column(String(255), nullable=True)

    # Metadata
    source_clinic_id = Column(String(100), nullable=True, index=True)
    uploaded_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return (
            f"<Trip(id={self.id}, patient='{self.patient_name}', "
            f"date={self.appointment_date}, clinic='{self.source_clinic_id}')>"
        )


class UploadHistoryDB(Base):
    """
    Tracks file uploads for auditing and debugging.

    Stores metadata about each Excel file processed.
    """

    __tablename__ = "upload_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    clinic_id = Column(String(100), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)  # bytes

    # Parse results
    total_rows = Column(Integer, nullable=False, default=0)
    successful_rows = Column(Integer, nullable=False, default=0)
    failed_rows = Column(Integer, nullable=False, default=0)

    # Metadata
    uploaded_at = Column(DateTime, default=func.now())
    uploaded_by = Column(String(100), nullable=True)  # User ID if applicable

    # Store any errors/warnings as JSON
    errors = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)

    def __repr__(self):
        return (
            f"<UploadHistory(id={self.id}, clinic='{self.clinic_id}', "
            f"file='{self.filename}', success={self.successful_rows}/{self.total_rows})>"
        )
