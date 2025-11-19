class VideoAnalyzerApp {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // File upload handling
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('videoFile');
        const uploadForm = document.getElementById('uploadForm');

        if (uploadArea && fileInput) {
            uploadArea.addEventListener('click', () => fileInput.click());
            
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFileSelection(files[0]);
                }
            });

            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFileSelection(e.target.files[0]);
                }
            });
        }

        // Form submission
        if (uploadForm) {
            uploadForm.addEventListener('submit', (e) => {
                this.handleFormSubmission(e);
            });
        }
    }

    handleFileSelection(file) {
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const uploadArea = document.getElementById('uploadArea');
        const submitBtn = document.getElementById('submitBtn');

        if (file) {
            // Validate file type
            const allowedTypes = ['mp4', 'avi', 'mov', 'mkv', 'webm'];
            const fileExtension = file.name.split('.').pop().toLowerCase();
            
            if (!allowedTypes.includes(fileExtension)) {
                this.showError('Invalid file type. Please upload a video file (MP4, AVI, MOV, MKV, WEBM).');
                return;
            }

            // Validate file size (100MB)
            const maxSize = 100 * 1024 * 1024;
            if (file.size > maxSize) {
                this.showError('File too large. Maximum size is 100MB.');
                return;
            }

            // Update UI
            fileName.textContent = file.name;
            fileSize.textContent = this.formatFileSize(file.size);
            uploadArea.style.borderColor = '#27ae60';
            uploadArea.style.background = '#e8f6f3';
            submitBtn.disabled = false;

            this.hideError();
        }
    }

    async handleFormSubmission(e) {
        e.preventDefault();
        
        const form = e.target;
        const formData = new FormData(form);
        const submitBtn = document.getElementById('submitBtn');
        const loading = document.getElementById('loading');

        // Show loading state
        submitBtn.disabled = true;
        loading.style.display = 'block';

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const html = await response.text();
                document.open();
                document.write(html);
                document.close();
            } else {
                const error = await response.json();
                this.showError(error.error || 'An error occurred during analysis.');
            }
        } catch (error) {
            this.showError('Network error. Please check your connection and try again.');
        } finally {
            submitBtn.disabled = false;
            loading.style.display = 'none';
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showError(message) {
        let errorDiv = document.getElementById('errorMessage');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'errorMessage';
            errorDiv.className = 'alert alert-error';
            document.querySelector('.card').prepend(errorDiv);
        }
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }

    hideError() {
        const errorDiv = document.getElementById('errorMessage');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }

    // Method to update progress bar (if implementing real-time progress)
    updateProgress(percent) {
        const progressFill = document.getElementById('progressFill');
        if (progressFill) {
            progressFill.style.width = percent + '%';
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new VideoAnalyzerApp();
});

// Utility function for API calls
async function analyzeVideoApi(formData) {
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });
        return await response.json();
    } catch (error) {
        throw new Error('API request failed');
    }
}
