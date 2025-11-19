from flask import Flask, render_template, request, jsonify, send_file, url_for
import os
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from werkzeug.utils import secure_filename
from datetime import datetime

from config import Config, allowed_file, generate_result_filename
from utils.video_processor import VideoAnalyzer

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Initialize analyzer
analyzer = VideoAnalyzer()

@app.route('/')
def index():
    """Home page with upload form"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    """Handle video file upload and analysis"""
    try:
        # Check if file was uploaded
        if 'video_file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['video_file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if file and allowed_file(file.filename):
            # Secure filename and save
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Get analysis options
            create_output_video = request.form.get('create_output', 'false') == 'true'
            detailed_analysis = request.form.get('detailed_analysis', 'false') == 'true'
            
            # Analyze video
            results = analyzer.analyze_video(
                filepath, 
                create_output=create_output_video,
                detailed_analysis=detailed_analysis
            )
            
            # Generate result filename and save
            result_filename = generate_result_filename()
            result_path = os.path.join(app.config['RESULT_FOLDER'], result_filename)
            
            with open(result_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Generate visualization charts
            charts = generate_charts(results)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return render_template('results.html', 
                                results=results, 
                                charts=charts,
                                filename=filename)
        
        else:
            return jsonify({'error': 'Invalid file type. Allowed types: mp4, avi, mov, mkv, webm'}), 400
            
    except Exception as e:
        app.logger.error(f"Error processing video: {str(e)}")
        return render_template('error.html', error_message=str(e)), 500

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for video analysis"""
    try:
        if 'video_file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['video_file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Analyze video
            results = analyzer.analyze_video(filepath)
            
            # Clean up
            os.remove(filepath)
            
            return jsonify(results)
        
        else:
            return jsonify({'error': 'Invalid file type'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/results/<filename>')
def get_result(filename):
    """Serve analysis results"""
    result_path = os.path.join(app.config['RESULT_FOLDER'], filename)
    
    if os.path.exists(result_path):
        with open(result_path, 'r') as f:
            results = json.load(f)
        return jsonify(results)
    else:
        return jsonify({'error': 'Result not found'}), 404

def generate_charts(results):
    """Generate Plotly charts for visualization"""
    charts = {}
    
    # Confidence Gauge Chart
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = results['overall_confidence'],
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Overall Confidence Score"},
        delta = {'reference': 50},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 40], 'color': "lightcoral"},
                {'range': [40, 70], 'color': "lightyellow"},
                {'range': [70, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig_gauge.update_layout(height=300)
    charts['confidence_gauge'] = json.dumps(fig_gauge, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Emotion Distribution Pie Chart
    emotion_data = results['breakdown']['emotion_breakdown']
    fig_pie = px.pie(
        values=list(emotion_data.values()),
        names=list(emotion_data.keys()),
        title="Emotion Distribution",
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    fig_pie.update_layout(height=400)
    charts['emotion_pie'] = json.dumps(fig_pie, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Confidence Breakdown Bar Chart
    breakdown_data = {
        'Liveness': results['breakdown']['liveness_confidence'],
        'Reaction': results['breakdown']['reaction_confidence']
    }
    
    fig_bar = px.bar(
        x=list(breakdown_data.keys()),
        y=list(breakdown_data.values()),
        title="Confidence Score Breakdown",
        labels={'x': 'Metric', 'y': 'Confidence Score (%)'},
        color=list(breakdown_data.keys()),
        color_discrete_sequence=['#1f77b4', '#ff7f0e']
    )
    fig_bar.update_layout(height=400, showlegend=False)
    charts['breakdown_bar'] = json.dumps(fig_bar, cls=plotly.utils.PlotlyJSONEncoder)
    
    return charts

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 100MB.'}), 413

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                         error_message="Internal server error. Please try again."), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
