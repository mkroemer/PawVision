// PawVision Video Management
// Video playback, editing, and deletion

/**
 * Video management controller
 */
const VideoManager = {
    /**
     * Play current video
     */
    async playVideo() {
        try {
            const response = await fetch('/api/play', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            });
            const result = await response.json();
            
            if (result.success) {
                this.showMessage('Video playback started!', 'success');
                this.updateStatus();
            } else {
                this.showMessage(result.message || 'Failed to start video', 'error');
            }
        } catch (error) {
            console.error('Error starting video:', error);
            this.showMessage('Failed to start video', 'error');
        }
    },

    /**
     * Stop current video
     */
    async stopVideo() {
        try {
            const response = await fetch('/api/stop', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            });
            const result = await response.json();
            
            if (result.success) {
                this.showMessage('Video playback stopped', 'success');
                this.updateStatus();
            } else {
                this.showMessage(result.message || 'Failed to stop video', 'error');
            }
        } catch (error) {
            console.error('Error stopping video:', error);
            this.showMessage('Failed to stop video', 'error');
        }
    },

    /**
     * Play a specific video
     * @param {string} path - Path to the video file
     */
    async playSpecificVideo(path) {
        try {
            const response = await fetch('/api/play', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({video_path: path})
            });
            const result = await response.json();
            
            if (result.success) {
                this.showMessage('Video started!', 'success');
                this.updateStatus();
            } else {
                this.showMessage(result.message || 'Failed to start video', 'error');
            }
        } catch (error) {
            console.error('Error starting specific video:', error);
            this.showMessage('Failed to start video', 'error');
        }
    },

    /**
     * Update video status display
     */
    async updateStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            
            // Update status display
            const playingStatus = document.getElementById('playing-status');
            if (playingStatus) {
                playingStatus.textContent = status.is_playing ? 'Yes' : 'No';
                playingStatus.style.color = status.is_playing ? 'var(--success-color)' : 'var(--text-muted)';
            }
            
            // Update button states
            const playButton = document.getElementById('play-button');
            const stopButton = document.getElementById('stop-button');
            
            if (playButton && stopButton) {
                if (status.is_playing) {
                    playButton.disabled = true;
                    stopButton.disabled = false;
                } else {
                    playButton.disabled = false;
                    stopButton.disabled = true;
                }
            }
            
            // Update current video display
            const currentVideo = document.getElementById('current-video');
            if (currentVideo) {
                currentVideo.textContent = status.current_video || 'None';
            }
            
            return status;
        } catch (error) {
            console.error('Error updating status:', error);
            return null;
        }
    },

    /**
     * Show status message
     * @param {string} message - Message to display
     * @param {string} type - Message type ('success', 'error', 'warning', 'info')
     */
    showMessage(message, type = 'info') {
        // Try to find the specific control status message first
        let messageElement = document.getElementById('control-status-message');
        
        // Fallback to global status message
        if (!messageElement) {
            messageElement = document.getElementById('status-message');
        }
        
        if (messageElement) {
            messageElement.textContent = message;
            messageElement.className = `status-message ${type}`;
            messageElement.style.display = 'block';
            
            // Apply styles based on type
            switch(type) {
                case 'success':
                    messageElement.style.backgroundColor = 'var(--success-color)';
                    messageElement.style.color = 'white';
                    break;
                case 'error':
                    messageElement.style.backgroundColor = 'var(--error-color)';
                    messageElement.style.color = 'white';
                    break;
                case 'warning':
                    messageElement.style.backgroundColor = 'var(--warning-color)';
                    messageElement.style.color = 'white';
                    break;
                default:
                    messageElement.style.backgroundColor = 'var(--primary-color)';
                    messageElement.style.color = 'white';
            }
            
            // Hide after 3 seconds
            setTimeout(() => {
                messageElement.style.display = 'none';
            }, 3000);
        } else {
            // Fallback to console if no status element found
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    },

    /**
     * Toggle schedule functionality
     */
    toggleSchedule() {
        console.log('Toggle schedule functionality');
        this.showMessage('Schedule toggle feature coming soon', 'info');
    },

    /**
     * Emergency stop all video playback
     */
    emergencyStop() {
        if (confirm('Emergency stop all video playback?')) {
            this.stopVideo();
        }
    },

    /**
     * Delete a video
     * @param {string} videoPath - Path of video to delete
     */
    async deleteVideo(videoPath) {
        try {
            const response = await fetch('/api/video/delete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({path: videoPath})
            });
            
            const result = await response.json();
            if (result.success) {
                // Refresh the library if we're on the playlist tab
                if (typeof SPA !== 'undefined' && SPA.currentTab === 'playlist' && typeof Library !== 'undefined') {
                    Library.refreshLibrary();
                }
                this.showMessage('Video deleted successfully', 'success');
            } else {
                this.showMessage(result.message || 'Failed to delete video', 'error');
            }
        } catch (error) {
            console.error('Error deleting video:', error);
            this.showMessage('Failed to delete video', 'error');
        }
    },

    /**
     * Open video edit modal
     * @param {string} path - Video path
     * @param {string} title - Video title
     * @param {number} startTime - Start time in seconds
     * @param {number} endTime - End time in seconds
     * @param {number} duration - Total duration in seconds
     */
    openEditModal(path, title, startTime, endTime, duration) {
        if (typeof Modal !== 'undefined') {
            // Calculate end offset from duration
            let endOffset = '';
            if (endTime && endTime > 0 && duration && duration > 0) {
                endOffset = duration - endTime;
            }

            Modal.form({
                title: 'Edit Video Settings',
                fields: [
                    { name: 'path', type: 'hidden', value: path },
                    { name: 'title', type: 'text', label: 'Video Title', value: title || '', placeholder: 'Enter video title' },
                    { name: 'start_time', type: 'number', label: 'Start Time (seconds)', value: startTime || 0, placeholder: '0' },
                    { name: 'end_time_offset', type: 'number', label: 'End Time Offset (seconds from end)', value: endOffset, placeholder: '0' }
                ],
                submitText: 'Save Changes',
                cancelText: 'Cancel',
                onSubmit: async (data) => {
                    try {
                        const response = await fetch('/api/video/update', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(data)
                        });
                        
                        const result = await response.json();
                        if (result.success) {
                            VideoManager.showMessage('Video settings updated successfully!', 'success');
                            // Refresh the library if we're on the playlist tab
                            if (typeof SPA !== 'undefined' && SPA.currentTab === 'playlist' && typeof Library !== 'undefined') {
                                Library.refreshLibrary();
                            }
                            return true; // Close modal
                        } else {
                            VideoManager.showMessage(result.error || 'Failed to update video settings', 'error');
                            return false; // Keep modal open
                        }
                    } catch (error) {
                        console.error('Error updating video:', error);
                        VideoManager.showMessage('Error updating video settings', 'error');
                        return false; // Keep modal open
                    }
                },
                onCancel: () => {
                    console.log('Video edit cancelled');
                }
            });
        } else {
            console.log('Modal system not available');
            this.showMessage('Edit functionality not available', 'error');
        }
    },

    /**
     * Show delete confirmation modal
     * @param {string} path - Video path
     * @param {string} title - Video title
     */
    showDeleteModal(path, title) {
        if (typeof Modal !== 'undefined') {
            Modal.confirm({
                title: 'Delete Video',
                message: `Are you sure you want to delete "${title}"? This action cannot be undone.`,
                confirmText: 'Delete',
                cancelText: 'Cancel',
                type: 'danger',
                onConfirm: () => {
                    this.deleteVideo(path);
                },
                onCancel: () => {
                    console.log('Delete cancelled');
                }
            });
        } else {
            console.log('Modal system not available');
            if (confirm(`Are you sure you want to delete "${title}"?`)) {
                this.deleteVideo(path);
            }
        }
    },

    /**
     * Initialize video management
     */
    init() {
        // Set up event delegation for dynamically added buttons
        document.addEventListener('click', (e) => {
            // Handle edit button clicks
            if (e.target.closest('.edit-btn')) {
                const button = e.target.closest('.edit-btn');
                const path = button.dataset.path;
                const title = button.dataset.title;
                const startTime = parseFloat(button.dataset.start) || 0;
                const endTime = parseFloat(button.dataset.end) || 0;
                const duration = parseFloat(button.dataset.duration) || 0;
                
                e.preventDefault();
                e.stopPropagation();
                
                try {
                    this.openEditModal(path, title, startTime, endTime, duration);
                } catch (error) {
                    console.error('Error opening edit modal:', error);
                    document.body.classList.remove('modal-open'); // Safety cleanup
                    this.showMessage('Error opening edit dialog', 'error');
                }
            }
            
            // Handle delete button clicks
            if (e.target.closest('.delete-btn')) {
                const button = e.target.closest('.delete-btn');
                const path = button.dataset.path;
                const title = button.dataset.title;
                
                e.preventDefault();
                e.stopPropagation();
                
                try {
                    this.showDeleteModal(path, title);
                } catch (error) {
                    console.error('Error opening delete modal:', error);
                    document.body.classList.remove('modal-open'); // Safety cleanup
                    this.showMessage('Error opening delete dialog', 'error');
                }
            }
        });
        
        // Add a global error handler to clean up modal state
        window.addEventListener('error', () => {
            document.body.classList.remove('modal-open');
        });
        
        console.log('VideoManager initialized with event delegation');
    }
};

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VideoManager;
}
