from datetime import datetime
from app import db

class DataFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    records_count = db.Column(db.Integer)
    
    analyses = db.relationship('DataAnalysis', backref='data_file', lazy=True)

class DataAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    analysis_type = db.Column(db.String(50), nullable=False)
    parameters = db.Column(db.JSON)
    results = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    data_file_id = db.Column(db.Integer, db.ForeignKey('data_file.id'), nullable=False)