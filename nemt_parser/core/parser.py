"""
Excel parsing engine for NEMT trip data.

This is the main entry point for processing Excel files from clinics.
Handles file reading, column detection, mapping application, and data validation.
"""

import pandas as pd
from pathlib import Path
from typing import Union, Optional, List
from datetime import datetime

from .models import ParseResult, Trip, ColumnMapping
from .mapper import ColumnMapper
from .validator import DataValidator


class TripParser:
    """
    Main parser for NEMT trip Excel files.

    Usage:
        parser = TripParser()
        result = parser.parse_excel("clinic_data.xlsx", clinic_id="clinic_a")

        if result.needs_mapping:
            # First time - review and save mapping
            mapping = result.suggested_mapping
            # ... user reviews/adjusts ...
            parser.save_mapping(mapping)

        # Get parsed trips
        trips = result.trips
    """

    def __init__(self, mapping_repository=None):
        """
        Initialize parser.

        Args:
            mapping_repository: Optional repository for storing/retrieving mappings.
                               If None, mappings must be provided explicitly.
        """
        self.mapping_repository = mapping_repository
        self.mapper = ColumnMapper()
        self.validator = DataValidator()

    def parse_excel(
        self,
        file_path: Union[str, Path],
        clinic_id: str,
        clinic_name: Optional[str] = None,
        mapping: Optional[ColumnMapping] = None,
        sheet_name: Union[str, int] = 0,
        skip_rows: int = 0,
    ) -> ParseResult:
        """
        Parse an Excel file containing trip data.

        Args:
            file_path: Path to Excel file (.xlsx or .xls)
            clinic_id: Unique identifier for the clinic
            clinic_name: Optional human-readable clinic name
            mapping: Optional explicit mapping (if not using repository)
            sheet_name: Excel sheet to read (name or index)
            skip_rows: Number of rows to skip at top of file

        Returns:
            ParseResult with trips or mapping suggestions
        """
        result = ParseResult(success=False, clinic_id=clinic_id)

        try:
            # Read Excel file
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                skiprows=skip_rows,
                dtype=str,  # Read everything as string initially
                na_filter=False,  # Don't convert empty to NaN
            )

            # Clean column names
            df.columns = [str(col).strip() for col in df.columns]

            # Remove completely empty rows
            df = df.dropna(how='all')

            result.total_rows = len(df)
            result.detected_columns = df.columns.tolist()

            # Get or suggest mapping
            if mapping is None:
                mapping = self._get_or_suggest_mapping(
                    clinic_id=clinic_id,
                    clinic_name=clinic_name,
                    columns=result.detected_columns,
                    result=result,
                )

            if mapping is None:
                # No mapping available and couldn't suggest one
                result.errors.append(
                    "No mapping available for this clinic. "
                    "Please review suggested mapping and save it."
                )
                return result

            # Validate mapping against detected columns
            validation_errors = self.mapper.validate_mapping(mapping, result.detected_columns)
            if validation_errors:
                result.errors.extend(validation_errors)
                result.warnings.append(
                    "Mapping validation failed. Please review the mapping configuration."
                )
                return result

            # Parse rows
            trips = []
            for idx, row in df.iterrows():
                row_dict = row.to_dict()

                trip, errors = self.validator.row_to_trip(
                    row_data=row_dict,
                    mapping=mapping,
                    source_clinic_id=clinic_id,
                )

                if trip:
                    trips.append(trip)
                    result.successful_rows += 1
                else:
                    result.failed_rows += 1
                    # Add row number to error messages
                    for error in errors:
                        result.warnings.append(f"Row {idx + 2}: {error}")

            result.trips = trips
            result.success = len(trips) > 0

            # Add summary warnings
            if result.failed_rows > 0:
                result.warnings.insert(
                    0,
                    f"Failed to parse {result.failed_rows} of {result.total_rows} rows. "
                    f"See detailed warnings below."
                )

            # Check for unmapped columns
            unmapped = self.mapper.get_unmapped_columns(result.detected_columns, mapping)
            if unmapped:
                result.warnings.append(
                    f"Unmapped columns (data will be ignored): {', '.join(unmapped)}"
                )

        except FileNotFoundError:
            result.errors.append(f"File not found: {file_path}")
        except Exception as e:
            result.errors.append(f"Error reading Excel file: {str(e)}")

        return result

    def _get_or_suggest_mapping(
        self,
        clinic_id: str,
        clinic_name: Optional[str],
        columns: List[str],
        result: ParseResult,
    ) -> Optional[ColumnMapping]:
        """
        Get existing mapping from repository or suggest a new one.

        Updates the result object with mapping suggestions if this is
        a new clinic.
        """
        # Try to get existing mapping from repository
        if self.mapping_repository:
            existing_mapping = self.mapping_repository.get_mapping(clinic_id)
            if existing_mapping:
                return existing_mapping

        # No existing mapping - suggest one
        suggested_mapping, confidence_scores = self.mapper.suggest_mapping(
            columns=columns,
            clinic_id=clinic_id,
            clinic_name=clinic_name,
        )

        result.needs_mapping = True
        result.suggested_mapping = suggested_mapping

        # Add confidence info to warnings
        low_confidence_fields = [
            field for field, score in confidence_scores.items()
            if score < 0.7
        ]
        if low_confidence_fields:
            result.warnings.append(
                f"Low confidence mappings for: {', '.join(low_confidence_fields)}. "
                f"Please review carefully."
            )

        return suggested_mapping

    def save_mapping(self, mapping: ColumnMapping) -> bool:
        """
        Save a column mapping for future use.

        Args:
            mapping: ColumnMapping to save

        Returns:
            True if saved successfully, False otherwise
        """
        if not self.mapping_repository:
            raise ValueError(
                "No mapping repository configured. "
                "Provide one during TripParser initialization."
            )

        mapping.updated_at = datetime.now()
        if not mapping.created_at:
            mapping.created_at = datetime.now()

        return self.mapping_repository.save_mapping(mapping)

    def get_mapping(self, clinic_id: str) -> Optional[ColumnMapping]:
        """Retrieve saved mapping for a clinic"""
        if not self.mapping_repository:
            return None
        return self.mapping_repository.get_mapping(clinic_id)

    def list_clinics(self) -> List[dict]:
        """List all clinics with saved mappings"""
        if not self.mapping_repository:
            return []
        return self.mapping_repository.list_clinics()

    def delete_mapping(self, clinic_id: str) -> bool:
        """Delete a clinic's mapping"""
        if not self.mapping_repository:
            return False
        return self.mapping_repository.delete_mapping(clinic_id)

    @staticmethod
    def validate_excel_file(file_path: Union[str, Path]) -> tuple[bool, Optional[str]]:
        """
        Quick validation that file exists and is readable Excel.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(file_path)

            if not path.exists():
                return False, "File does not exist"

            if not path.is_file():
                return False, "Path is not a file"

            if path.suffix.lower() not in ('.xlsx', '.xls', '.xlsm'):
                return False, f"Invalid file type: {path.suffix}. Expected .xlsx or .xls"

            # Try to open it
            pd.read_excel(path, nrows=0)

            return True, None

        except Exception as e:
            return False, f"Error validating file: {str(e)}"
