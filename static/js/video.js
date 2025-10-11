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
                const message = typeof t !== 'undefined' ? t('video.playbackStarted') : 'Video playback started!';
                this.showMessage(message, 'success');
                this.updateStatus();
            } else {
                const message = typeof t !== 'undefined' ? t('video.failedToStart') : 'Failed to start video';
                this.showMessage(result.message || message, 'error');
            }
        } catch (error) {
            console.error('Error starting video:', error);
            const message = typeof t !== 'undefined' ? t('video.failedToStart') : 'Failed to start video';
            this.showMessage(message, 'error');
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
                const message = typeof t !== 'undefined' ? t('video.playbackStopped') : 'Video playback stopped';
                this.showMessage(message, 'success');
                this.updateStatus();
            } else {
                const message = typeof t !== 'undefined' ? t('video.failedToStop') : 'Failed to stop video';
                this.showMessage(result.message || message, 'error');
            }
        } catch (error) {
            console.error('Error stopping video:', error);
            const message = typeof t !== 'undefined' ? t('video.failedToStop') : 'Failed to stop video';
            this.showMessage(message, 'error');
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
                const message = typeof t !== 'undefined' ? t('video.videoStarted') : 'Video started!';
                this.showMessage(message, 'success');
                this.updateStatus();
            } else {
                const message = typeof t !== 'undefined' ? t('video.failedToStart') : 'Failed to start video';
                this.showMessage(result.message || message, 'error');
            }
        } catch (error) {
            console.error('Error starting specific video:', error);
            const message = typeof t !== 'undefined' ? t('video.failedToStart') : 'Failed to start video';
            this.showMessage(message, 'error');
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
     * Show status message using unified notification system
     * @param {string} message - Message to display
     * @param {string} type - Message type ('success', 'error', 'warning', 'info')
     */
    showMessage(message, type = 'info') {
        // Use unified notification system if available
        if (typeof NotificationSystem !== 'undefined') {
            return NotificationSystem.show(message, type, 4000, 'control-status-message');
        }
        
        // Fallback to legacy method if NotificationSystem not available
        console.log(`${type.toUpperCase()}: ${message}`);
        
        // Try to find a status element anyway
        const messageElement = document.getElementById('control-status-message') || 
                              document.getElementById('status-message');
        
        if (messageElement) {
            messageElement.textContent = message;
            messageElement.className = `status-message ${type}`;
            messageElement.style.display = 'block';
            
            setTimeout(() => {
                messageElement.style.display = 'none';
            }, 4000);
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
                const message = typeof t !== 'undefined' ? t('video.deletedSuccessfully') : 'Video deleted successfully';
                this.showMessage(message, 'success');
            } else {
                const message = typeof t !== 'undefined' ? t('video.failedToDelete') : 'Failed to delete video';
                this.showMessage(result.message || message, 'error');
            }
        } catch (error) {
            console.error('Error deleting video:', error);
            const message = typeof t !== 'undefined' ? t('video.failedToDelete') : 'Failed to delete video';
            this.showMessage(message, 'error');
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

            const titleText = typeof t !== 'undefined' ? t('video.editVideoSettings') : 'Edit Video Settings';
            const videoTitleText = typeof t !== 'undefined' ? t('video.videoTitle') : 'Video Title';
            const videoTitlePlaceholder = typeof t !== 'undefined' ? t('video.enterVideoTitle') : 'Enter video title';
            const startTimeText = typeof t !== 'undefined' ? t('video.startTimeSeconds') : 'Start Time (seconds)';
            const endTimeOffsetText = typeof t !== 'undefined' ? t('video.endTimeOffset') : 'End Time Offset (seconds from end)';
            const saveChangesText = typeof t !== 'undefined' ? t('video.saveChanges') : 'Save Changes';
            const cancelText = typeof t !== 'undefined' ? t('modal.cancel') : 'Cancel';

            Modal.form({
                title: titleText,
                fields: [
                    { name: 'path', type: 'hidden', value: path },
                    { name: 'title', type: 'text', label: videoTitleText, value: title || '', placeholder: videoTitlePlaceholder },
                    { name: 'start_time', type: 'number', label: startTimeText, value: startTime || 0, placeholder: '0' },
                    { name: 'end_time_offset', type: 'number', label: endTimeOffsetText, value: endOffset, placeholder: '0' }
                ],
                submitText: saveChangesText,
                cancelText: cancelText,
                onSubmit: async (data) => {
                    try {
                        const response = await fetch('/api/video/update', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(data)
                        });
                        
                        const result = await response.json();
                        if (result.success) {
                            const successMessage = typeof t !== 'undefined' ? t('video.settingsUpdated') : 'Video settings updated successfully!';
                            VideoManager.showMessage(successMessage, 'success');
                            // Refresh the library if we're on the playlist tab
                            if (typeof SPA !== 'undefined' && SPA.currentTab === 'playlist' && typeof Library !== 'undefined') {
                                Library.refreshLibrary();
                            }
                            return true; // Close modal
                        } else {
                            const errorMessage = typeof t !== 'undefined' ? t('video.failedToUpdateSettings') : 'Failed to update video settings';
                            VideoManager.showMessage(result.error || errorMessage, 'error');
                            return false; // Keep modal open
                        }
                    } catch (error) {
                        console.error('Error updating video:', error);
                        const errorMessage = typeof t !== 'undefined' ? t('video.errorUpdatingSettings') : 'Error updating video settings';
                        VideoManager.showMessage(errorMessage, 'error');
                        return false; // Keep modal open
                    }
                },
                onCancel: () => {
                    console.log('Video edit cancelled');
                }
            });
        } else {
            console.log('Modal system not available');
            const message = typeof t !== 'undefined' ? t('video.editNotAvailable') : 'Edit functionality not available';
            this.showMessage(message, 'error');
        }
    },

    /**
     * Show delete confirmation modal
     * @param {string} path - Video path
     * @param {string} title - Video title
     */
    showDeleteModal(path, title) {
        console.log('showDeleteModal called for:', path, title);
        console.log('Modal available?', typeof Modal !== 'undefined');
        
        if (typeof Modal !== 'undefined') {
            console.log('Using Modal system for delete confirmation');
            const deleteTitle = typeof t !== 'undefined' ? t('video.deleteVideo') : 'Delete Video';
            const deleteMessage = typeof t !== 'undefined' ? 
                t('video.deleteConfirmation', { title: title }) : 
                `Are you sure you want to delete "${title}"? This action cannot be undone.`;
            const deleteText = typeof t !== 'undefined' ? t('modal.delete') : 'Delete';
            const cancelText = typeof t !== 'undefined' ? t('modal.cancel') : 'Cancel';

            Modal.confirm({
                title: deleteTitle,
                message: deleteMessage,
                confirmText: deleteText,
                cancelText: cancelText,
                type: 'danger',
                onConfirm: () => {
                    console.log('Delete confirmed via modal');
                    this.deleteVideo(path);
                },
                onCancel: () => {
                    console.log('Delete cancelled via modal');
                }
            });
        } else {
            console.log('Modal system not available, using fallback confirm()');
            const confirmMessage = typeof t !== 'undefined' ? 
                t('video.deleteConfirmation', { title: title }) : 
                `Are you sure you want to delete "${title}"?`;
            if (confirm(confirmMessage)) {
                console.log('Delete confirmed via fallback');
                this.deleteVideo(path);
            } else {
                console.log('Delete cancelled via fallback');
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
