"""
Repository layer for database operations.

Provides clean interface for storing and retrieving mappings, trips,
and upload history. Abstracts away SQL details from business logic.
"""

from typing import List, Optional, Dict
from datetime import datetime, date
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from .schemas import Base, ClinicMappingDB, TripDB, UploadHistoryDB
from ..core.models import ColumnMapping, Trip, ParseResult


class MappingRepository:
    """
    Repository for clinic column mappings.

    Handles CRUD operations for saving and retrieving how each clinic's
    Excel columns map to our standardized schema.
    """

    def __init__(self, database_url: str = "sqlite:///nemt_trips.db"):
        """
        Initialize repository with database connection.

        Args:
            database_url: SQLAlchemy database URL
                Examples:
                - "sqlite:///nemt_trips.db" (local SQLite)
                - "postgresql://user:pass@localhost/nemt"
                - "mysql://user:pass@localhost/nemt"
        """
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def _mapping_to_db(self, mapping: ColumnMapping) -> ClinicMappingDB:
        """Convert ColumnMapping model to database model"""
        return ClinicMappingDB(
            clinic_id=mapping.clinic_id,
            clinic_name=mapping.clinic_name,
            patient_name=mapping.patient_name,
            patient_phone=mapping.patient_phone,
            medicaid_id=mapping.medicaid_id,
            date_of_birth=mapping.date_of_birth,
            pickup_address=mapping.pickup_address,
            pickup_city=mapping.pickup_city,
            pickup_state=mapping.pickup_state,
            pickup_zip=mapping.pickup_zip,
            dropoff_address=mapping.dropoff_address,
            dropoff_city=mapping.dropoff_city,
            dropoff_state=mapping.dropoff_state,
            dropoff_zip=mapping.dropoff_zip,
            appointment_date=mapping.appointment_date,
            appointment_time=mapping.appointment_time,
            trip_type=mapping.trip_type,
            wheelchair=mapping.wheelchair,
            stretcher=mapping.stretcher,
            ambulatory=mapping.ambulatory,
            notes=mapping.notes,
            appointment_type=mapping.appointment_type,
            clinic_name_col=mapping.clinic_name,
            created_at=mapping.created_at or datetime.now(),
            updated_at=mapping.updated_at or datetime.now(),
        )

    def _db_to_mapping(self, db_mapping: ClinicMappingDB) -> ColumnMapping:
        """Convert database model to ColumnMapping model"""
        return ColumnMapping(
            clinic_id=db_mapping.clinic_id,
            clinic_name=db_mapping.clinic_name,
            patient_name=db_mapping.patient_name,
            patient_phone=db_mapping.patient_phone,
            medicaid_id=db_mapping.medicaid_id,
            date_of_birth=db_mapping.date_of_birth,
            pickup_address=db_mapping.pickup_address,
            pickup_city=db_mapping.pickup_city,
            pickup_state=db_mapping.pickup_state,
            pickup_zip=db_mapping.pickup_zip,
            dropoff_address=db_mapping.dropoff_address,
            dropoff_city=db_mapping.dropoff_city,
            dropoff_state=db_mapping.dropoff_state,
            dropoff_zip=db_mapping.dropoff_zip,
            appointment_date=db_mapping.appointment_date,
            appointment_time=db_mapping.appointment_time,
            trip_type=db_mapping.trip_type,
            wheelchair=db_mapping.wheelchair,
            stretcher=db_mapping.stretcher,
            ambulatory=db_mapping.ambulatory,
            notes=db_mapping.notes,
            appointment_type=db_mapping.appointment_type,
            created_at=db_mapping.created_at,
            updated_at=db_mapping.updated_at,
        )

    def save_mapping(self, mapping: ColumnMapping) -> bool:
        """
        Save or update a clinic mapping.

        Args:
            mapping: ColumnMapping to save

        Returns:
            True if successful, False otherwise
        """
        with self.SessionLocal() as session:
            try:
                db_mapping = self._mapping_to_db(mapping)

                # Check if exists
                existing = session.query(ClinicMappingDB).filter_by(
                    clinic_id=mapping.clinic_id
                ).first()

                if existing:
                    # Update existing
                    for key, value in db_mapping.__dict__.items():
                        if not key.startswith('_'):
                            setattr(existing, key, value)
                    existing.updated_at = datetime.now()
                else:
                    # Insert new
                    session.add(db_mapping)

                session.commit()
                return True

            except Exception as e:
                session.rollback()
                print(f"Error saving mapping: {e}")
                return False

    def get_mapping(self, clinic_id: str) -> Optional[ColumnMapping]:
        """
        Retrieve mapping for a clinic.

        Args:
            clinic_id: Unique clinic identifier

        Returns:
            ColumnMapping if found, None otherwise
        """
        with self.SessionLocal() as session:
            db_mapping = session.query(ClinicMappingDB).filter_by(
                clinic_id=clinic_id
            ).first()

            if db_mapping:
                return self._db_to_mapping(db_mapping)
            return None

    def list_clinics(self) -> List[Dict[str, str]]:
        """
        List all clinics with saved mappings.

        Returns:
            List of dicts with clinic_id and clinic_name
        """
        with self.SessionLocal() as session:
            mappings = session.query(ClinicMappingDB).all()
            return [
                {
                    "clinic_id": m.clinic_id,
                    "clinic_name": m.clinic_name or m.clinic_id,
                    "updated_at": m.updated_at.isoformat() if m.updated_at else None,
                }
                for m in mappings
            ]

    def delete_mapping(self, clinic_id: str) -> bool:
        """Delete a clinic mapping"""
        with self.SessionLocal() as session:
            try:
                mapping = session.query(ClinicMappingDB).filter_by(
                    clinic_id=clinic_id
                ).first()

                if mapping:
                    session.delete(mapping)
                    session.commit()
                    return True
                return False

            except Exception as e:
                session.rollback()
                print(f"Error deleting mapping: {e}")
                return False


class TripRepository:
    """
    Repository for parsed trip data.

    Handles storing and querying standardized trip records.
    """

    def __init__(self, database_url: str = "sqlite:///nemt_trips.db"):
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def _trip_to_db(self, trip: Trip) -> TripDB:
        """Convert Trip model to database model"""
        return TripDB(
            patient_name=trip.patient_name,
            patient_phone=trip.patient_phone,
            medicaid_id=trip.medicaid_id,
            date_of_birth=trip.date_of_birth,
            pickup_address=trip.pickup_address,
            pickup_city=trip.pickup_city,
            pickup_state=trip.pickup_state,
            pickup_zip=trip.pickup_zip,
            dropoff_address=trip.dropoff_address,
            dropoff_city=trip.dropoff_city,
            dropoff_state=trip.dropoff_state,
            dropoff_zip=trip.dropoff_zip,
            appointment_date=trip.appointment_date,
            appointment_time=trip.appointment_time,
            trip_type=trip.trip_type.value,
            wheelchair=trip.wheelchair,
            stretcher=trip.stretcher,
            ambulatory=trip.ambulatory,
            notes=trip.notes,
            appointment_type=trip.appointment_type,
            clinic_name=trip.clinic_name,
            source_clinic_id=trip.source_clinic_id,
            uploaded_at=trip.uploaded_at or datetime.now(),
        )

    def save_trips(self, trips: List[Trip]) -> int:
        """
        Bulk save trips to database.

        Args:
            trips: List of Trip objects to save

        Returns:
            Number of trips successfully saved
        """
        with self.SessionLocal() as session:
            try:
                db_trips = [self._trip_to_db(trip) for trip in trips]
                session.bulk_save_objects(db_trips)
                session.commit()
                return len(db_trips)

            except Exception as e:
                session.rollback()
                print(f"Error saving trips: {e}")
                return 0

    def get_trips_by_date_range(
        self,
        start_date: date,
        end_date: date,
        clinic_id: Optional[str] = None
    ) -> List[TripDB]:
        """Query trips by appointment date range"""
        with self.SessionLocal() as session:
            query = session.query(TripDB).filter(
                and_(
                    TripDB.appointment_date >= start_date,
                    TripDB.appointment_date <= end_date
                )
            )

            if clinic_id:
                query = query.filter(TripDB.source_clinic_id == clinic_id)

            return query.all()

    def get_trips_by_clinic(self, clinic_id: str, limit: int = 100) -> List[TripDB]:
        """Get recent trips from a specific clinic"""
        with self.SessionLocal() as session:
            return session.query(TripDB).filter(
                TripDB.source_clinic_id == clinic_id
            ).order_by(TripDB.appointment_date.desc()).limit(limit).all()


class UploadHistoryRepository:
    """
    Repository for tracking upload history.

    Useful for auditing, debugging, and showing users their upload history.
    """

    def __init__(self, database_url: str = "sqlite:///nemt_trips.db"):
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def log_upload(
        self,
        clinic_id: str,
        filename: str,
        result: ParseResult,
        uploaded_by: Optional[str] = None,
        file_size: Optional[int] = None,
    ) -> int:
        """
        Log an upload event.

        Args:
            clinic_id: Clinic identifier
            filename: Name of uploaded file
            result: ParseResult from parsing
            uploaded_by: Optional user ID
            file_size: Optional file size in bytes

        Returns:
            Upload history ID
        """
        with self.SessionLocal() as session:
            try:
                history = UploadHistoryDB(
                    clinic_id=clinic_id,
                    filename=filename,
                    file_size=file_size,
                    total_rows=result.total_rows,
                    successful_rows=result.successful_rows,
                    failed_rows=result.failed_rows,
                    uploaded_by=uploaded_by,
                    errors=result.errors if result.errors else None,
                    warnings=result.warnings if result.warnings else None,
                )

                session.add(history)
                session.commit()
                return history.id

            except Exception as e:
                session.rollback()
                print(f"Error logging upload: {e}")
                return 0

    def get_upload_history(
        self,
        clinic_id: Optional[str] = None,
        limit: int = 50
    ) -> List[UploadHistoryDB]:
        """Get recent upload history"""
        with self.SessionLocal() as session:
            query = session.query(UploadHistoryDB)

            if clinic_id:
                query = query.filter(UploadHistoryDB.clinic_id == clinic_id)

            return query.order_by(UploadHistoryDB.uploaded_at.desc()).limit(limit).all()
