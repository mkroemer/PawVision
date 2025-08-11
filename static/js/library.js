// PawVision Library Management
// Video library loading and management

/**
 * Library management controller for video collections
 */
const Library = {
    /**
     * Load and refresh the video library from the server
     */
    async refreshLibrary() {
        // Debug: prevent infinite loops
        if (this._refreshing) {
            console.warn('refreshLibrary already running, skipping duplicate call');
            return;
        }
        
        this._refreshing = true;
        
        try {
            console.log('refreshLibrary: Starting refresh');
            const response = await fetch('/api/video/library');
            const data = await response.json();
            
            if (data.success) {
                // Update video count
                const countElement = document.getElementById('video-count');
                if (countElement) {
                    countElement.textContent = data.videos ? data.videos.length : 0;
                }
                
                console.log('Library refreshed successfully');
            }
        } catch (error) {
            console.error('Failed to refresh library:', error);
            if (typeof VideoManager !== 'undefined') {
                VideoManager.showMessage('Failed to refresh library', 'error');
            }
        } finally {
            this._refreshing = false;
        }
    },

    /**
     * Initialize library functionality when the page loads
     */
    init() {
        // Any initialization logic can go here
        console.log('Library management initialized');
        
        // Initialize upload functionality
        this.initUpload();
    },

    /**
     * Initialize video upload with progress modal
     */
    initUpload() {
        const uploadForm = document.getElementById('video-upload-form');
        if (uploadForm) {
            uploadForm.addEventListener('submit', (e) => this.handleUpload(e));
        }

        // Initialize cancel button
        const cancelBtn = document.getElementById('cancel-upload-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.cancelUpload());
        }
    },

    /**
     * Handle video upload with progress modal
     */
    async handleUpload(event) {
        event.preventDefault();
        
        const form = event.target;
        const fileInput = document.getElementById('playlist-file-input');
        const file = fileInput.files[0];
        
        if (!file) {
            this.showMessage('Please select a file to upload', 'error');
            return;
        }

        // Show upload modal
        this.showUploadModal(file.name);
        
        // Create FormData
        const formData = new FormData(form);
        
        // Create XMLHttpRequest for progress tracking
        this.currentUploadXHR = new XMLHttpRequest();
        
        // Set up progress tracking
        this.currentUploadXHR.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                this.updateUploadProgress(percentComplete, 'Uploading...');
            }
        });
        
        // Set up completion handler
        this.currentUploadXHR.addEventListener('load', () => {
            if (this.currentUploadXHR.status === 200) {
                try {
                    const response = JSON.parse(this.currentUploadXHR.responseText);
                    this.updateUploadProgress(100, 'Upload complete!');
                    setTimeout(() => {
                        this.hideUploadModal();
                        this.showMessage('Video uploaded successfully!', 'success');
                        this.refreshLibrary();
                        form.reset();
                    }, 1000);
                } catch (error) {
                    this.hideUploadModal();
                    this.showMessage('Upload completed but response was invalid', 'error');
                }
            } else {
                this.hideUploadModal();
                this.showMessage('Upload failed', 'error');
            }
        });
        
        // Set up error handler
        this.currentUploadXHR.addEventListener('error', () => {
            this.hideUploadModal();
            this.showMessage('Upload failed due to network error', 'error');
        });
        
        // Set up abort handler
        this.currentUploadXHR.addEventListener('abort', () => {
            this.hideUploadModal();
            this.showMessage('Upload cancelled', 'info');
        });
        
        // Start upload
        this.currentUploadXHR.open('POST', form.action);
        this.currentUploadXHR.send(formData);
    },

    /**
     * Show upload modal
     */
    showUploadModal(filename) {
        const modal = document.getElementById('upload-modal');
        const filenameElement = document.getElementById('upload-filename');
        
        if (modal) {
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        }
        
        if (filenameElement) {
            filenameElement.textContent = filename;
        }
        
        this.updateUploadProgress(0, 'Preparing upload...');
    },

    /**
     * Hide upload modal
     */
    hideUploadModal() {
        const modal = document.getElementById('upload-modal');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = ''; // Restore scrolling
        }
    },

    /**
     * Update upload progress
     */
    updateUploadProgress(percent, status) {
        const progressFill = document.getElementById('upload-progress-fill');
        const statusElement = document.getElementById('upload-status');
        
        if (progressFill) {
            progressFill.style.width = `${percent}%`;
        }
        
        if (statusElement) {
            statusElement.textContent = status;
        }
    },

    /**
     * Cancel current upload
     */
    cancelUpload() {
        if (this.currentUploadXHR) {
            this.currentUploadXHR.abort();
            this.currentUploadXHR = null;
        }
    },

    /**
     * Show message to user
     */
    showMessage(message, type = 'info') {
        // Use existing message system if available
        if (typeof VideoManager !== 'undefined' && VideoManager.showMessage) {
            VideoManager.showMessage(message, type === 'error');
        } else {
            // Fallback to alert
            alert(message);
        }
    }
};

/**
 * Download video function for library items
 * @param {string} path - Path to the video file
 */
async function downloadVideo(path) {
    try {
        const response = await fetch('/api/download-video', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({path: path})
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = path.split('/').pop();
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            if (typeof VideoManager !== 'undefined') {
                VideoManager.showMessage('Video download started', 'success');
            }
        } else {
            throw new Error('Download failed');
        }
    } catch (error) {
        console.error('Error downloading video:', error);
        if (typeof VideoManager !== 'undefined') {
            VideoManager.showMessage('Error downloading video', 'error');
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    Library.init();
});
