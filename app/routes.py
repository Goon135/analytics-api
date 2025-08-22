from flask import Blueprint, request, jsonify, current_app
import os
import pandas as pd
from app import db
from app.models import DataFile, DataAnalysis
from app.utils import (
    allowed_file, read_data_file, calculate_statistics,
    clean_data, save_uploaded_file
)
from sqlalchemy.exc import SQLAlchemyError
import traceback

bp = Blueprint('main', __name__)

@bp.route('/upload', methods=['POST'])
def upload_file():
    """Upload CSV or Excel file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
            return jsonify({'error': 'Unsupported file type'}), 415
        
        # Save file to uploads directory
        filename, filepath = save_uploaded_file(file, current_app.config.get('UPLOAD_FOLDER', 'uploads'))
        
        # Read and analyze file
        df = read_data_file(filepath, filename)
        records_count = len(df)
        
        # Save file info to database
        data_file = DataFile(
            filename=filename,
            original_filename=file.filename,
            file_size=os.path.getsize(filepath),
            records_count=records_count
        )
        
        db.session.add(data_file)
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file_id': data_file.id,
            'filename': data_file.original_filename,
            'records_count': records_count
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'Failed to process file'}), 500

@bp.route('/data/stats', methods=['GET'])
def get_data_stats():
    """Get statistics for uploaded data"""
    try:
        file_id = request.args.get('file_id')
        if not file_id:
            return jsonify({'error': 'file_id parameter is required'}), 400
        
        data_file = DataFile.query.get_or_404(file_id)
        filepath = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), data_file.filename)
        
        # Read file and calculate statistics
        df = read_data_file(filepath, data_file.filename)
        stats = calculate_statistics(df)
        
        # Save analysis to database
        analysis = DataAnalysis(
            analysis_type='statistics',
            results=stats,
            data_file_id=data_file.id
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        return jsonify({
            'file_id': data_file.id,
            'filename': data_file.original_filename,
            'statistics': stats
        }), 200
        
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Stats error: {str(e)}")
        return jsonify({'error': 'Failed to calculate statistics'}), 500

@bp.route('/data/clean', methods=['GET'])
def clean_data_endpoint():
    """Clean data by removing duplicates and filling missing values"""
    try:
        file_id = request.args.get('file_id')
        remove_duplicates = request.args.get('remove_duplicates', 'true').lower() == 'true'
        fill_missing = request.args.get('fill_missing', 'true').lower() == 'true'
        fill_strategy = request.args.get('fill_strategy', 'mean')
        
        if not file_id:
            return jsonify({'error': 'file_id parameter is required'}), 400
        
        data_file = DataFile.query.get_or_404(file_id)
        filepath = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), data_file.filename)
        
        # Read file and clean data
        df = read_data_file(filepath, data_file.filename)
        df_cleaned = clean_data(df, remove_duplicates, fill_missing, fill_strategy)
        
        # Calculate cleaning results
        cleaning_stats = {
            'original_records': len(df),
            'cleaned_records': len(df_cleaned),
            'duplicates_removed': len(df) - len(df_cleaned) if remove_duplicates else 0,
            'missing_values_filled': fill_missing
        }
        
        # Save cleaned file
        cleaned_filename = f"cleaned_{data_file.filename}"
        cleaned_filepath = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), cleaned_filename)
        
        if data_file.filename.endswith('.csv'):
            df_cleaned.to_csv(cleaned_filepath, index=False)
        else:
            df_cleaned.to_excel(cleaned_filepath, index=False)
        
        # Save analysis to database
        analysis = DataAnalysis(
            analysis_type='cleaning',
            parameters={
                'remove_duplicates': remove_duplicates,
                'fill_missing': fill_missing,
                'fill_strategy': fill_strategy
            },
            results=cleaning_stats,
            data_file_id=data_file.id
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        return jsonify({
            'file_id': data_file.id,
            'cleaning_stats': cleaning_stats,
            'cleaned_file': cleaned_filename
        }), 200
        
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Cleaning error: {str(e)}")
        return jsonify({'error': 'Failed to clean data'}), 500

@bp.route('/files', methods=['GET'])
def list_files():
    """Get list of uploaded files"""
    try:
        files = DataFile.query.all()
        result = []
        
        for file in files:
            result.append({
                'id': file.id,
                'filename': file.original_filename,
                'upload_date': file.upload_date.isoformat(),
                'records_count': file.records_count,
                'file_size': file.file_size
            })
        
        return jsonify({'files': result}), 200
        
    except Exception as e:
        current_app.logger.error(f"List files error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve files'}), 500

@bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500