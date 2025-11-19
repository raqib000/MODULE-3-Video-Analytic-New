import os
from datetime import datetime

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    
    # File Upload Configuration
    UPLOAD_FOLDER = 'uploads'
    RESULT_FOLDER = 'results'
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    
    # Analysis Configuration
    FRAME_SKIP = 5
    TARGET_FPS = 10
    EAR_THRESHOLD = 0.21
    EXPECTED_BLINKS_PER_MINUTE = 15
    
    # Output Configuration
    CHART_THEME = 'plotly_white'
    
    @staticmethod
    def init_app(app):
        # Create necessary directories
        for folder in [Config.UPLOAD_FOLDER, Config.RESULT_FOLDER]:
            if not os.path.exists(folder):
                os.makedirs(folder)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def generate_result_filename():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"analysis_{timestamp}.json"
