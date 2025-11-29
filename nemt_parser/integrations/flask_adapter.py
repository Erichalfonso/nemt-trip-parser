"""
Flask integration adapter for NEMT Trip Parser.

Drop this into your existing Flask application!
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from pathlib import Path
import os

from ..core.parser import TripParser
from ..core.models import ColumnMapping
from ..core.output_schema import convert_to_output_format
from ..database.repositories import MappingRepository, TripRepository, UploadHistoryRepository


# Create blueprint
nemt_bp = Blueprint('nemt', __name__, url_prefix='/api/nemt')


def init_parser():
    """Initialize parser with database from Flask config"""
    db_url = current_app.config.get('NEMT_DATABASE_URL', 'sqlite:///nemt_trips.db')
    mapping_repo = MappingRepository(db_url)
    trip_repo = TripRepository(db_url)
    upload_repo = UploadHistoryRepository(db_url)

    parser = TripParser(mapping_repository=mapping_repo)

    return parser, mapping_repo, trip_repo, upload_repo


@nemt_bp.route('/upload', methods=['POST'])
def upload_trip_data():
    """
    Upload Excel file with trip data.

    Expected form data:
        - file: Excel file
        - clinic_id: Clinic identifier

    Returns:
        JSON response with parsed trips or mapping request
    """
    # Validate request
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    if 'clinic_id' not in request.form:
        return jsonify({'success': False, 'error': 'clinic_id required'}), 400

    file = request.files['file']
    clinic_id = request.form['clinic_id']
    clinic_name = request.form.get('clinic_name')

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    # Save uploaded file temporarily
    filename = secure_filename(file.filename)
    upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
    upload_dir.mkdir(exist_ok=True)

    file_path = upload_dir / filename
    file.save(str(file_path))
    file_size = os.path.getsize(file_path)

    try:
        # Initialize parser
        parser, _, trip_repo, upload_repo = init_parser()

        # Validate Excel file
        is_valid, error_msg = parser.validate_excel_file(file_path)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400

        # Parse file
        result = parser.parse_excel(
            file_path=file_path,
            clinic_id=clinic_id,
            clinic_name=clinic_name
        )

        # Log upload
        user_id = request.form.get('user_id') or request.headers.get('X-User-ID')
        upload_repo.log_upload(
            clinic_id=clinic_id,
            filename=filename,
            result=result,
            uploaded_by=user_id,
            file_size=file_size
        )

        # First-time clinic - needs mapping confirmation
        if result.needs_mapping:
            return jsonify({
                'success': False,
                'needs_mapping': True,
                'detected_columns': result.detected_columns,
                'suggested_mapping': result.suggested_mapping.model_dump(),
                'message': 'Please review and confirm the column mapping'
            }), 200

        # Parse successful
        if result.success:
            # Convert trips to your exact output format
            output_trips = [convert_to_output_format(trip).model_dump() for trip in result.trips]

            # Save trips to database (optional)
            saved_count = trip_repo.save_trips(result.trips)

            return jsonify({
                'success': True,
                'trips_parsed': result.successful_rows,
                'trips_saved': saved_count,
                'trips_failed': result.failed_rows,
                'warnings': result.warnings if result.warnings else [],
                'trips': output_trips  # All trips in YOUR exact format
            }), 200
        else:
            return jsonify({
                'success': False,
                'errors': result.errors,
                'warnings': result.warnings
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500

    finally:
        # Optionally delete temp file
        if current_app.config.get('DELETE_AFTER_PROCESSING', False):
            if file_path.exists():
                file_path.unlink()


@nemt_bp.route('/mapping/save', methods=['POST'])
def save_mapping():
    """
    Save or update clinic mapping.

    Expected JSON body: ColumnMapping object
    """
    try:
        data = request.get_json()
        mapping = ColumnMapping(**data)

        parser, _, _, _ = init_parser()

        if parser.save_mapping(mapping):
            return jsonify({
                'success': True,
                'message': 'Mapping saved successfully',
                'clinic_id': mapping.clinic_id
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save mapping'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@nemt_bp.route('/mapping/<clinic_id>', methods=['GET'])
def get_mapping(clinic_id):
    """Get saved mapping for a clinic"""
    try:
        parser, _, _, _ = init_parser()
        mapping = parser.get_mapping(clinic_id)

        if mapping:
            return jsonify({
                'success': True,
                'mapping': mapping.model_dump()
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Mapping not found'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@nemt_bp.route('/clinics', methods=['GET'])
def list_clinics():
    """List all clinics with saved mappings"""
    try:
        parser, _, _, _ = init_parser()
        clinics = parser.list_clinics()

        return jsonify({
            'success': True,
            'clinics': clinics,
            'count': len(clinics)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@nemt_bp.route('/history', methods=['GET'])
def upload_history():
    """Get upload history"""
    try:
        clinic_id = request.args.get('clinic_id')
        limit = int(request.args.get('limit', 50))

        _, _, _, upload_repo = init_parser()
        history = upload_repo.get_upload_history(clinic_id=clinic_id, limit=limit)

        return jsonify({
            'success': True,
            'uploads': [
                {
                    'id': h.id,
                    'clinic_id': h.clinic_id,
                    'filename': h.filename,
                    'total_rows': h.total_rows,
                    'successful_rows': h.successful_rows,
                    'failed_rows': h.failed_rows,
                    'uploaded_at': h.uploaded_at.isoformat(),
                    'errors': h.errors,
                    'warnings': h.warnings
                }
                for h in history
            ]
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Example Flask app setup
def create_app_example():
    """
    Example of how to integrate into your Flask app.

    Add this to your main Flask application file.
    """
    from flask import Flask

    app = Flask(__name__)

    # Configuration
    app.config['NEMT_DATABASE_URL'] = 'sqlite:///nemt_trips.db'
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['DELETE_AFTER_PROCESSING'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    # Register blueprint
    app.register_blueprint(nemt_bp)

    return app


if __name__ == '__main__':
    # Test the Flask app
    app = create_app_example()
    app.run(debug=True, port=5000)
    print("Flask API running at http://localhost:5000")
    print("Endpoints:")
    print("  POST /api/nemt/upload - Upload Excel file")
    print("  POST /api/nemt/mapping/save - Save mapping")
    print("  GET  /api/nemt/mapping/<clinic_id> - Get mapping")
    print("  GET  /api/nemt/clinics - List clinics")
    print("  GET  /api/nemt/history - Upload history")
