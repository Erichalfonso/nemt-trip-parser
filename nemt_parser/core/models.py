"""
Core data models for NEMT trip data.

These models define the standardized schema that all clinic data
gets transformed into, regardless of their original format.
"""

from datetime import date, time, datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class TripType(str, Enum):
    """Types of NEMT trips"""
    PICKUP = "pickup"
    RETURN = "return"
    ROUND_TRIP = "round_trip"


class Trip(BaseModel):
    """
    Standardized trip data model.

    All clinic data, regardless of original format, gets transformed into this schema.
    This ensures consistency across your billing, scheduling, and operations.
    """

    # Patient Information
    patient_name: str = Field(..., description="Full patient name")
    patient_phone: Optional[str] = Field(None, description="Patient contact number")
    medicaid_id: str = Field(..., description="Medicaid/insurance ID")
    date_of_birth: Optional[date] = Field(None, description="Patient date of birth")

    # Pickup Location
    pickup_address: str = Field(..., description="Street address for pickup")
    pickup_city: str = Field(..., description="Pickup city")
    pickup_state: Optional[str] = Field("FL", description="Pickup state")
    pickup_zip: str = Field(..., description="Pickup ZIP code")

    # Dropoff Location
    dropoff_address: str = Field(..., description="Street address for dropoff")
    dropoff_city: str = Field(..., description="Dropoff city")
    dropoff_state: Optional[str] = Field("FL", description="Dropoff state")
    dropoff_zip: str = Field(..., description="Dropoff ZIP code")

    # Appointment Details
    appointment_date: date = Field(..., description="Date of appointment")
    appointment_time: Optional[time] = Field(None, description="Time of appointment")

    # Trip Characteristics
    trip_type: TripType = Field(default=TripType.ROUND_TRIP, description="Type of trip")
    wheelchair: bool = Field(default=False, description="Wheelchair required")
    stretcher: bool = Field(default=False, description="Stretcher required")
    ambulatory: bool = Field(default=True, description="Patient is ambulatory")

    # Additional Information
    notes: Optional[str] = Field(None, description="Special instructions or notes")
    appointment_type: Optional[str] = Field(None, description="Type of medical appointment")
    clinic_name: Optional[str] = Field(None, description="Name of medical facility")

    # Metadata
    source_clinic_id: Optional[str] = Field(None, description="ID of clinic that submitted")
    uploaded_at: Optional[datetime] = Field(None, description="When this was uploaded")

    @field_validator('patient_phone', 'pickup_zip', 'dropoff_zip')
    @classmethod
    def clean_strings(cls, v: Optional[str]) -> Optional[str]:
        """Remove extra whitespace from string fields"""
        if v:
            return v.strip()
        return v

    @field_validator('medicaid_id')
    @classmethod
    def validate_medicaid_id(cls, v: str) -> str:
        """Ensure Medicaid ID is not empty"""
        if not v or not v.strip():
            raise ValueError("Medicaid ID is required")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "patient_name": "John Doe",
                "patient_phone": "555-123-4567",
                "medicaid_id": "MCD123456789",
                "date_of_birth": "1950-01-15",
                "pickup_address": "123 Main St",
                "pickup_city": "Miami",
                "pickup_state": "FL",
                "pickup_zip": "33101",
                "dropoff_address": "456 Hospital Ave",
                "dropoff_city": "Miami",
                "dropoff_state": "FL",
                "dropoff_zip": "33102",
                "appointment_date": "2025-01-15",
                "appointment_time": "10:30:00",
                "trip_type": "round_trip",
                "wheelchair": False,
                "notes": "Patient needs assistance walking",
                "clinic_name": "Miami Medical Center"
            }
        }


class ColumnMapping(BaseModel):
    """
    Defines how a clinic's Excel columns map to our standardized fields.

    Each clinic has their own column names - this mapping tells us
    how to transform their format into our Trip model.
    """

    clinic_id: str = Field(..., description="Unique identifier for the clinic")
    clinic_name: Optional[str] = Field(None, description="Human-readable clinic name")

    # Field mappings: our_field -> their_column_name
    patient_name: str = Field(..., description="Their column for patient name")
    patient_phone: Optional[str] = None
    medicaid_id: str = Field(..., description="Their column for Medicaid ID")
    date_of_birth: Optional[str] = None

    pickup_address: str
    pickup_city: str
    pickup_state: Optional[str] = None
    pickup_zip: str

    dropoff_address: str
    dropoff_city: str
    dropoff_state: Optional[str] = None
    dropoff_zip: str

    appointment_date: str
    appointment_time: Optional[str] = None

    trip_type: Optional[str] = None
    wheelchair: Optional[str] = None
    stretcher: Optional[str] = None
    ambulatory: Optional[str] = None

    notes: Optional[str] = None
    appointment_type: Optional[str] = None
    clinic_name: Optional[str] = None

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "clinic_id": "miami_medical_center",
                "clinic_name": "Miami Medical Center",
                "patient_name": "Patient Name",
                "medicaid_id": "Medicaid #",
                "pickup_address": "Pick-up Address",
                "pickup_city": "Pick-up City",
                "pickup_zip": "Pick-up ZIP",
                "dropoff_address": "Drop-off Address",
                "dropoff_city": "Drop-off City",
                "dropoff_zip": "Drop-off ZIP",
                "appointment_date": "Appt Date",
                "appointment_time": "Appt Time",
                "wheelchair": "Wheelchair?"
            }
        }


class ParseResult(BaseModel):
    """Result of parsing an Excel file"""

    success: bool = Field(..., description="Whether parsing succeeded")
    needs_mapping: bool = Field(default=False, description="Whether clinic needs initial mapping")
    clinic_id: Optional[str] = None

    # Parsed trips (if successful)
    trips: list[Trip] = Field(default_factory=list)

    # Column detection (for new clinics)
    detected_columns: list[str] = Field(default_factory=list)
    suggested_mapping: Optional[ColumnMapping] = None

    # Errors and warnings
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # Statistics
    total_rows: int = 0
    successful_rows: int = 0
    failed_rows: int = 0


class MappingSuggestion(BaseModel):
    """LLM-generated suggestion for column mapping"""

    confidence: Literal["high", "medium", "low"]
    suggested_mapping: dict[str, str]
    reasoning: Optional[str] = None
