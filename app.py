from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
import os
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static')
CORS(app)

UPLOAD_FOLDER = 'uploads'
DATA_FOLDER = 'data'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# In-memory storage for dashboards and groups
dashboards_db = {}
groups_db = {}

def load_db():
    global dashboards_db, groups_db
    try:
        if os.path.exists(f'{DATA_FOLDER}/dashboards.json'):
            with open(f'{DATA_FOLDER}/dashboards.json', 'r') as f:
                dashboards_db = json.load(f)
        if os.path.exists(f'{DATA_FOLDER}/groups.json'):
            with open(f'{DATA_FOLDER}/groups.json', 'r') as f:
                groups_db = json.load(f)
    except:
        pass

def save_db():
    with open(f'{DATA_FOLDER}/dashboards.json', 'w') as f:
        json.dump(dashboards_db, f)
    with open(f'{DATA_FOLDER}/groups.json', 'w') as f:
        json.dump(groups_db, f)

load_db()

def analyze_column(series):
    """Analyze a single column and return its characteristics"""
    dtype = str(series.dtype)
    unique_count = series.nunique()
    total_count = len(series)
    null_count = series.isnull().sum()

    col_type = 'unknown'
    if pd.api.types.is_numeric_dtype(series):
        if unique_count <= 10:
            col_type = 'categorical_numeric'
        else:
            col_type = 'continuous'
    elif pd.api.types.is_datetime64_any_dtype(series):
        col_type = 'datetime'
    else:
        # Try to parse as datetime
        try:
            pd.to_datetime(series.dropna().head(100))
            col_type = 'datetime'
        except:
            if unique_count / total_count < 0.05 or unique_count <= 20:
                col_type = 'categorical'
            else:
                col_type = 'text'

    return {
        'dtype': dtype,
        'type': col_type,
        'unique_count': int(unique_count),
        'null_count': int(null_count),
        'total_count': int(total_count)
    }

def recommend_visualizations(df):
    """Recommend visualizations based on data analysis"""
    recommendations = []
    columns_info = {}

    for col in df.columns:
        columns_info[col] = analyze_column(df[col])

    numeric_cols = [c for c, info in columns_info.items() if info['type'] in ['continuous', 'categorical_numeric']]
    categorical_cols = [c for c, info in columns_info.items() if info['type'] == 'categorical']
    datetime_cols = [c for c, info in columns_info.items() if info['type'] == 'datetime']

    # Single numeric distribution
    for col in numeric_cols[:3]:
        recommendations.append({
            'type': 'histogram',
            'title': f'Distribution of {col}',
            'config': {'column': col},
            'priority': 1
        })

    # Categorical value counts
    for col in categorical_cols[:3]:
        if columns_info[col]['unique_count'] <= 15:
            recommendations.append({
                'type': 'bar',
                'title': f'{col} Distribution',
                'config': {'column': col},
                'priority': 2
            })
            recommendations.append({
                'type': 'pie',
                'title': f'{col} Breakdown',
                'config': {'column': col},
                'priority': 3
            })

    # Time series
    for dt_col in datetime_cols[:1]:
        for num_col in numeric_cols[:2]:
            recommendations.append({
                'type': 'line',
                'title': f'{num_col} over Time',
                'config': {'x': dt_col, 'y': num_col},
                'priority': 1
            })

    # Scatter plots for numeric pairs
    if len(numeric_cols) >= 2:
        for i, col1 in enumerate(numeric_cols[:3]):
            for col2 in numeric_cols[i+1:4]:
                recommendations.append({
                    'type': 'scatter',
                    'title': f'{col1} vs {col2}',
                    'config': {'x': col1, 'y': col2},
                    'priority': 2
                })

    # Grouped bar charts
    if categorical_cols and numeric_cols:
        for cat_col in categorical_cols[:2]:
            if columns_info[cat_col]['unique_count'] <= 10:
                for num_col in numeric_cols[:2]:
                    recommendations.append({
                        'type': 'grouped_bar',
                        'title': f'Average {num_col} by {cat_col}',
                        'config': {'category': cat_col, 'value': num_col},
                        'priority': 2
                    })

    # Sort by priority
    recommendations.sort(key=lambda x: x['priority'])

    return recommendations[:12], columns_info

def generate_chart_data(df, viz_config):
    """Generate chart data based on visualization config"""
    viz_type = viz_config['type']
    config = viz_config['config']

    try:
        if viz_type == 'histogram':
            col = config['column']
            data = df[col].dropna()
            hist, bin_edges = np.histogram(data, bins=20)
            return {
                'labels': [f'{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}' for i in range(len(hist))],
                'datasets': [{
                    'label': col,
                    'data': hist.tolist(),
                    'backgroundColor': 'rgba(0, 255, 136, 0.6)',
                    'borderColor': 'rgba(0, 255, 136, 1)',
                    'borderWidth': 1
                }]
            }

        elif viz_type == 'bar':
            col = config['column']
            value_counts = df[col].value_counts().head(15)
            return {
                'labels': value_counts.index.tolist(),
                'datasets': [{
                    'label': 'Count',
                    'data': value_counts.values.tolist(),
                    'backgroundColor': 'rgba(0, 255, 136, 0.6)',
                    'borderColor': 'rgba(0, 255, 136, 1)',
                    'borderWidth': 1
                }]
            }

        elif viz_type == 'pie':
            col = config['column']
            value_counts = df[col].value_counts().head(10)
            colors = [
                'rgba(0, 255, 136, 0.8)',
                'rgba(0, 200, 100, 0.8)',
                'rgba(0, 150, 75, 0.8)',
                'rgba(50, 255, 150, 0.8)',
                'rgba(100, 255, 180, 0.8)',
                'rgba(0, 255, 200, 0.8)',
                'rgba(0, 200, 150, 0.8)',
                'rgba(50, 200, 100, 0.8)',
                'rgba(100, 200, 130, 0.8)',
                'rgba(0, 150, 100, 0.8)',
            ]
            return {
                'labels': value_counts.index.tolist(),
                'datasets': [{
                    'data': value_counts.values.tolist(),
                    'backgroundColor': colors[:len(value_counts)],
                    'borderColor': '#1a1a2e',
                    'borderWidth': 2
                }]
            }

        elif viz_type == 'line':
            x_col = config['x']
            y_col = config['y']
            temp_df = df[[x_col, y_col]].dropna().copy()
            temp_df[x_col] = pd.to_datetime(temp_df[x_col])
            temp_df = temp_df.sort_values(x_col)
            # Sample if too many points
            if len(temp_df) > 100:
                temp_df = temp_df.iloc[::len(temp_df)//100]
            return {
                'labels': temp_df[x_col].dt.strftime('%Y-%m-%d').tolist(),
                'datasets': [{
                    'label': y_col,
                    'data': temp_df[y_col].tolist(),
                    'borderColor': 'rgba(0, 255, 136, 1)',
                    'backgroundColor': 'rgba(0, 255, 136, 0.1)',
                    'fill': True,
                    'tension': 0.4
                }]
            }

        elif viz_type == 'scatter':
            x_col = config['x']
            y_col = config['y']
            temp_df = df[[x_col, y_col]].dropna()
            # Sample if too many points
            if len(temp_df) > 500:
                temp_df = temp_df.sample(500)
            return {
                'datasets': [{
                    'label': f'{x_col} vs {y_col}',
                    'data': [{'x': row[x_col], 'y': row[y_col]} for _, row in temp_df.iterrows()],
                    'backgroundColor': 'rgba(0, 255, 136, 0.6)',
                    'borderColor': 'rgba(0, 255, 136, 1)',
                    'pointRadius': 4
                }]
            }

        elif viz_type == 'grouped_bar':
            cat_col = config['category']
            val_col = config['value']
            grouped = df.groupby(cat_col)[val_col].mean().head(10)
            return {
                'labels': grouped.index.tolist(),
                'datasets': [{
                    'label': f'Avg {val_col}',
                    'data': grouped.values.tolist(),
                    'backgroundColor': 'rgba(0, 255, 136, 0.6)',
                    'borderColor': 'rgba(0, 255, 136, 1)',
                    'borderWidth': 1
                }]
            }
    except Exception as e:
        return {'error': str(e)}

    return {}

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
        else:
            return jsonify({'error': 'Unsupported file format'}), 400

        recommendations, columns_info = recommend_visualizations(df)

        # Generate chart data for each recommendation
        charts = []
        for rec in recommendations:
            chart_data = generate_chart_data(df, rec)
            if 'error' not in chart_data:
                charts.append({
                    'id': str(uuid.uuid4()),
                    'type': rec['type'],
                    'title': rec['title'],
                    'data': chart_data,
                    'config': rec['config']
                })

        # Create dashboard
        dashboard_id = str(uuid.uuid4())
        dashboard = {
            'id': dashboard_id,
            'name': filename.rsplit('.', 1)[0],
            'filename': filename,
            'created_at': datetime.now().isoformat(),
            'charts': charts,
            'columns_info': columns_info,
            'row_count': len(df),
            'col_count': len(df.columns)
        }

        dashboards_db[dashboard_id] = dashboard
        save_db()

        return jsonify(dashboard)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboards', methods=['GET'])
def get_dashboards():
    return jsonify(list(dashboards_db.values()))

@app.route('/api/dashboards/<dashboard_id>', methods=['GET'])
def get_dashboard(dashboard_id):
    if dashboard_id in dashboards_db:
        return jsonify(dashboards_db[dashboard_id])
    return jsonify({'error': 'Dashboard not found'}), 404

@app.route('/api/dashboards/<dashboard_id>', methods=['DELETE'])
def delete_dashboard(dashboard_id):
    if dashboard_id in dashboards_db:
        del dashboards_db[dashboard_id]
        save_db()
        return jsonify({'success': True})
    return jsonify({'error': 'Dashboard not found'}), 404

@app.route('/api/groups', methods=['GET'])
def get_groups():
    return jsonify(list(groups_db.values()))

@app.route('/api/groups', methods=['POST'])
def create_group():
    data = request.json
    group_id = str(uuid.uuid4())
    group = {
        'id': group_id,
        'name': data.get('name', 'Untitled Group'),
        'dashboard_ids': data.get('dashboard_ids', []),
        'created_at': datetime.now().isoformat()
    }
    groups_db[group_id] = group
    save_db()
    return jsonify(group)

@app.route('/api/groups/<group_id>', methods=['PUT'])
def update_group(group_id):
    if group_id not in groups_db:
        return jsonify({'error': 'Group not found'}), 404

    data = request.json
    groups_db[group_id].update({
        'name': data.get('name', groups_db[group_id]['name']),
        'dashboard_ids': data.get('dashboard_ids', groups_db[group_id]['dashboard_ids'])
    })
    save_db()
    return jsonify(groups_db[group_id])

@app.route('/api/groups/<group_id>', methods=['DELETE'])
def delete_group(group_id):
    if group_id in groups_db:
        del groups_db[group_id]
        save_db()
        return jsonify({'success': True})
    return jsonify({'error': 'Group not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
