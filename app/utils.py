import pandas as pd
import numpy as np
import os
from werkzeug.utils import secure_filename

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def read_data_file(filepath, filename):
    """Read CSV or Excel file into DataFrame"""
    if filename.endswith('.csv'):
        df = pd.read_csv(filepath)
    elif filename.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(filepath)
    else:
        raise ValueError("Unsupported file format")
    return df

def calculate_statistics(df):
    """Calculate basic statistics for numeric columns"""
    stats = {}
    
    for column in df.select_dtypes(include=[np.number]).columns:
        stats[column] = {
            'mean': float(df[column].mean()),
            'median': float(df[column].median()),
            'std': float(df[column].std()),
            'min': float(df[column].min()),
            'max': float(df[column].max()),
            'count': int(df[column].count())
        }
    
    # Calculate correlation matrix for numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty:
        correlation_matrix = numeric_df.corr()
        stats['correlation'] = correlation_matrix.where(
            np.triu(np.ones(correlation_matrix.shape), k=1).astype(bool)
        ).stack().to_dict()
    
    return stats

def clean_data(df, remove_duplicates=True, fill_missing=True, fill_strategy='mean'):
    """Clean data by removing duplicates and filling missing values"""
    df_cleaned = df.copy()
    
    if remove_duplicates:
        df_cleaned = df_cleaned.drop_duplicates()
    
    if fill_missing:
        for column in df_cleaned.columns:
            if df_cleaned[column].dtype in [np.int64, np.float64]:
                if fill_strategy == 'mean':
                    df_cleaned[column].fillna(df_cleaned[column].mean(), inplace=True)
                elif fill_strategy == 'median':
                    df_cleaned[column].fillna(df_cleaned[column].median(), inplace=True)
                elif fill_strategy == 'zero':
                    df_cleaned[column].fillna(0, inplace=True)
            else:
                df_cleaned[column].fillna('Unknown', inplace=True)
    
    return df_cleaned

def save_uploaded_file(file, upload_folder):
    """Save uploaded file to disk"""
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    return filename, filepath