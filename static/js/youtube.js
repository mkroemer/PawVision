// PawVision YouTube Management
// YouTube video handling, validation, and downloading

/**
 * YouTube management controller
 */
const YouTube = {
    validationTimeout: null,

    /**
     * Download YouTube video with confirmation
     * @param {string} videoPath - YouTube video path
     * @param {string} quality - Video quality (default: 720p)
     */
    downloadVideo(videoPath, quality = '720p') {
        if (typeof Modal !== 'undefined') {
            const title = typeof t !== 'undefined' ? t('youtube.downloadVideo') : '📥 Download Video';
            const message = typeof t !== 'undefined' ? t('youtube.downloadConfirmation') : 'Download this YouTube video for offline playback? This may take several minutes depending on video length and quality.';
            const confirmText = typeof t !== 'undefined' ? t('upload.download') : 'Download';
            const cancelText = typeof t !== 'undefined' ? t('modal.cancel') : 'Cancel';

            Modal.confirm({
                title: title,
                message: message,
                confirmText: confirmText,
                cancelText: cancelText,
                onConfirm: () => this.startDownload(videoPath, quality),
                onCancel: () => console.log('Download cancelled')
            });
        } else {
            // Fallback if modals not available
            const message = typeof t !== 'undefined' ? t('youtube.downloadConfirmation') : 'Download this YouTube video for offline playback? This may take several minutes depending on video length and quality.';
            if (confirm(message)) {
                this.startDownload(videoPath, quality);
            }
        }
    },

    /**
     * Start YouTube video download
     * @param {string} videoPath - YouTube video path
     * @param {string} quality - Video quality
     */
    startDownload(videoPath, quality) {
        // Show progress modal
        let progressModalId = null;
        if (typeof Modal !== 'undefined') {
            const title = typeof t !== 'undefined' ? t('youtube.downloadingVideo') : '📥 Downloading Video';
            const startingMessage = typeof t !== 'undefined' ? t('youtube.startingDownload') : 'Starting download...';
            const preparingMessage = typeof t !== 'undefined' ? t('youtube.startingDownload') : 'Preparing download...';
            const cancelText = typeof t !== 'undefined' ? t('modal.cancel') : 'Cancel';

            progressModalId = Modal.show({
                title: title,
                content: `
                    <div class="download-progress">
                        <div class="progress-message">${startingMessage}</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 0%"></div>
                        </div>
                        <div class="progress-text">${preparingMessage}</div>
                    </div>
                `,
                closable: false,
                buttons: [{
                    text: cancelText,
                    class: 'btn-secondary',
                    onclick: () => {
                        Modal.hide(progressModalId);
                    }
                }]
            });
        }
        
        fetch('/api/youtube/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                path: videoPath,
                quality: quality
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'started' && data.download_id) {
                if (progressModalId) {
                    // Update progress modal
                    const progressMessage = document.querySelector(`#${progressModalId} .progress-message`);
                    const progressText = document.querySelector(`#${progressModalId} .progress-text`);
                    const inProgressMessage = typeof t !== 'undefined' ? t('youtube.downloadInProgress') : 'Download in progress...';
                    const timeMessage = typeof t !== 'undefined' ? t('youtube.downloadMayTakeTime') : 'This may take several minutes';
                    
                    if (progressMessage) progressMessage.textContent = inProgressMessage;
                    if (progressText) progressText.textContent = timeMessage;
                    
                    // Auto-close after 3 seconds with success message
                    setTimeout(() => {
                        Modal.hide(progressModalId);
                        const successMessage = typeof t !== 'undefined' ? t('youtube.downloadStarted') : 'Download started! Check back in a few minutes.';
                        if (typeof NotificationSystem !== 'undefined') {
                            NotificationSystem.show(successMessage, 'success');
                        } else if (typeof VideoManager !== 'undefined') {
                            VideoManager.showMessage(successMessage, 'success');
                        }
                    }, 3000);
                } else {
                    const successMessage = typeof t !== 'undefined' ? t('youtube.downloadStarted') : 'Download started! Check back in a few minutes.';
                    if (typeof NotificationSystem !== 'undefined') {
                        NotificationSystem.show(successMessage, 'success');
                    } else if (typeof VideoManager !== 'undefined') {
                        VideoManager.showMessage(successMessage, 'success');
                    }
                }
            } else {
                if (progressModalId) Modal.hide(progressModalId);
                const errorMsg = data.error || (typeof t !== 'undefined' ? t('youtube.failedToStartDownload') : 'Failed to start download');
                if (typeof NotificationSystem !== 'undefined') {
                    NotificationSystem.show(errorMsg, 'error');
                } else if (typeof VideoManager !== 'undefined') {
                    VideoManager.showMessage(errorMsg, 'error');
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (progressModalId) Modal.hide(progressModalId);
            const errorMsg = typeof t !== 'undefined' ? t('youtube.errorStartingDownload') : 'Error starting download';
            if (typeof NotificationSystem !== 'undefined') {
                NotificationSystem.show(errorMsg, 'error');
            } else if (typeof VideoManager !== 'undefined') {
                VideoManager.showMessage(errorMsg, 'error');
            }
        });
    },

    /**
     * Validate YouTube URL and fetch title
     * @param {string} url - YouTube URL to validate
     */
    validateUrl(url) {
        // Clear previous timeout
        if (this.validationTimeout) {
            clearTimeout(this.validationTimeout);
        }

        // Hide validation if URL is empty
        const validationDiv = document.getElementById('url-validation');
        if (!url.trim()) {
            if (validationDiv) validationDiv.style.display = 'none';
            return;
        }

        // Show loading state
        if (validationDiv) {
            const validatingMessage = typeof t !== 'undefined' ? t('youtube.validatingUrl') : '⏳ Validating URL...';
            validationDiv.innerHTML = `<span style="color: #666;">${validatingMessage}</span>`;
            validationDiv.style.display = 'block';
        }

        // Debounce validation requests
        this.validationTimeout = setTimeout(() => {
            fetch('/api/youtube/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            })
            .then(response => response.json())
            .then(data => {
                if (data.valid) {
                    if (validationDiv) {
                        const validMessage = typeof t !== 'undefined' ? 
                            t('youtube.validYoutubeVideo', { title: data.title || 'YouTube Video' }) : 
                            `✓ Valid: ${data.title || 'YouTube Video'}`;
                        validationDiv.innerHTML = `<span style="color: #2BA8A0;">${validMessage}</span>`;
                    }
                    
                    // Auto-populate title in advanced form
                    const titleInput = document.getElementById('youtube-title');
                    if (titleInput && !titleInput.value && data.title) {
                        titleInput.value = data.title;
                    }
                    
                    // Enable the quick add button
                    const quickAddBtn = document.getElementById('add-youtube-quick');
                    if (quickAddBtn) {
                        quickAddBtn.disabled = false;
                    }
                } else {
                    if (validationDiv) {
                        const invalidMessage = typeof t !== 'undefined' ? t('youtube.invalidYoutubeUrl') : 'Invalid YouTube URL';
                        const errorMsg = data.error || invalidMessage;
                        validationDiv.innerHTML = `<span style="color: #ee5a24;">✗ ${errorMsg}</span>`;
                    }
                    
                    // Disable the quick add button
                    const quickAddBtn = document.getElementById('add-youtube-quick');
                    if (quickAddBtn) {
                        quickAddBtn.disabled = true;
                    }
                }
            })
            .catch(error => {
                console.error('Validation error:', error);
                if (validationDiv) {
                    const validationFailedMessage = typeof t !== 'undefined' ? t('youtube.validationFailed') : '✗ Validation failed';
                    validationDiv.innerHTML = `<span style="color: #ee5a24;">${validationFailedMessage}</span>`;
                }
            });
        }, 1000); // 1 second debounce
    },

    /**
     * Quick add YouTube video with default settings
     * @param {Event} event - Button click event
     */
    quickAdd(event) {
        event.preventDefault();
        
        const url = document.getElementById('youtube-url-quick').value;
        
        if (!url) {
            const message = typeof t !== 'undefined' ? t('youtube.enterYoutubeUrl') : 'Please enter a YouTube URL';
            this.showMessage(message, true);
            return;
        }

        // Create JSON data instead of FormData
        const data = {
            url: url,
            title: '',
            quality: '720p',
            start_time: 0,
            end_time: null,
            download: false
        };

        fetch('/api/youtube/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' || data.message) {
                const successMessage = data.message || (typeof t !== 'undefined' ? t('youtube.videoAddedSuccessfully') : 'Video added successfully');
                this.showMessage(successMessage, false);
                document.getElementById('youtube-url-quick').value = '';
                const validationDiv = document.getElementById('url-validation');
                if (validationDiv) {
                    validationDiv.style.display = 'none';
                }
                // Disable the quick add button
                const quickAddBtn = document.getElementById('add-youtube-quick');
                if (quickAddBtn) {
                    quickAddBtn.disabled = true;
                }
                setTimeout(() => {
                    // Refresh the page to show the new video
                    window.location.reload();
                }, 1500);
            } else {
                const errorMessage = data.error || (typeof t !== 'undefined' ? t('youtube.failedToAddVideo') : 'Failed to add video');
                this.showMessage(errorMessage, true);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            const errorMessage = typeof t !== 'undefined' ? t('youtube.errorAddingVideo') : 'Error adding video';
            this.showMessage(errorMessage, true);
        });
    },

    /**
     * Submit advanced YouTube form
     * @param {Event} event - Form submit event
     */
    submitAdvanced(event) {
        event.preventDefault();
        
        const form = event.target;
        
        // Get URL from quick input since advanced form doesn't have URL field
        const quickUrl = document.getElementById('youtube-url-quick');
        if (!quickUrl || !quickUrl.value) {
            const errorMessage = typeof t !== 'undefined' ? t('youtube.pleaseEnterUrl') : 'Please enter a YouTube URL first';
            this.showMessage(errorMessage, true);
            return;
        }
        
        // Create JSON data from form
        const formData = new FormData(form);
        const data = {
            url: quickUrl.value,
            title: formData.get('title') || '',
            quality: formData.get('quality') || '720p',
            start_time: parseFloat(formData.get('start_time')) || 0,
            end_time: formData.get('end_offset') ? parseFloat(formData.get('end_offset')) : null,
            download: formData.has('download')
        };

        fetch('/api/youtube/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' || data.message) {
                const successMessage = data.message || (typeof t !== 'undefined' ? t('youtube.videoAddedSuccessfully') : 'Video added successfully');
                this.showMessage(successMessage, false);
                form.reset();
                // Hide advanced options
                const advancedDiv = document.getElementById('advanced-options');
                if (advancedDiv) {
                    advancedDiv.style.display = 'none';
                }
                // Clear the quick URL input
                quickUrl.value = '';
                const validationDiv = document.getElementById('url-validation');
                if (validationDiv) {
                    validationDiv.style.display = 'none';
                }
                setTimeout(() => {
                    // Refresh the page to show the new video
                    window.location.reload();
                }, 1500);
            } else {
                const errorMessage = data.error || (typeof t !== 'undefined' ? t('youtube.failedToAddVideo') : 'Failed to add video');
                this.showMessage(errorMessage, true);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            const errorMessage = typeof t !== 'undefined' ? t('youtube.errorAddingVideo') : 'Error adding video';
            this.showMessage(errorMessage, true);
        });
    },

    /**
     * Clear advanced form
     */
    clearAdvancedForm() {
        const form = document.getElementById('youtube-form');
        if (form) {
            form.reset();
        }
    },

    /**
     * Show YouTube-specific message using unified notification system
     * @param {string} message - Message to show
     * @param {boolean} isError - Whether this is an error (legacy parameter)
     * @param {string} type - Message type ('success', 'error', 'warning', 'info')
     */
    showMessage(message, isError = false, type = null) {
        // Determine message type
        let msgType = type;
        if (!msgType) {
            msgType = isError ? 'error' : 'success';
        }
        
        // Use unified notification system if available
        if (typeof NotificationSystem !== 'undefined') {
            NotificationSystem.show(message, msgType, 4000);
            return;
        }
        
        // Fallback to local YouTube message area
        const messageDiv = document.getElementById('youtube-message');
        if (messageDiv) {
            messageDiv.textContent = message;
            messageDiv.className = isError ? 'error' : 'success';
            messageDiv.style.display = 'block';
            
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 4000);
        } else {
            // Final fallback to console
            console.log(`YouTube ${msgType.toUpperCase()}: ${message}`);
        }
    },

    /**
     * Initialize YouTube functionality
     */
    init() {
        // Add event listeners for YouTube download buttons
        const downloadButtons = document.querySelectorAll('.download-youtube-btn');
        downloadButtons.forEach(button => {
            button.addEventListener('click', function() {
                const videoPath = this.dataset.path;
                const quality = this.dataset.quality || '720p';
                YouTube.downloadVideo(videoPath, quality);
            });
        });

        // Add event listener for YouTube advanced form submission
        const youtubeForm = document.getElementById('youtube-form');
        if (youtubeForm) {
            youtubeForm.addEventListener('submit', (e) => YouTube.submitAdvanced(e));
        }

        // Add URL validation to the quick input
        const urlInput = document.getElementById('youtube-url-quick');
        if (urlInput) {
            urlInput.addEventListener('input', (e) => YouTube.validateUrl(e.target.value));
        }
    },

    /**
     * Toggle advanced YouTube options form
     */
    toggleAdvancedOptions() {
        const advancedForm = document.getElementById('youtube-advanced-form');
        const toggleBtn = document.getElementById('advanced-toggle-btn');
        
        if (advancedForm && toggleBtn) {
            if (advancedForm.classList.contains('hidden')) {
                advancedForm.classList.remove('hidden');
                toggleBtn.textContent = '▲ Hide Advanced';
            } else {
                advancedForm.classList.add('hidden');
                toggleBtn.textContent = '⚙️ Advanced';
            }
        }
    },
    
    /**
     * Clear the advanced YouTube form
     */
    clearAdvancedForm() {
        const fields = [
            'youtube-title',
            'youtube-start',
            'youtube-end'
        ];
        
        fields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.value = fieldId === 'youtube-start' ? '0' : '';
            }
        });
        
        const qualityField = document.getElementById('youtube-quality');
        if (qualityField) {
            qualityField.value = '720p';
        }
        
        const downloadField = document.getElementById('youtube-download');
        if (downloadField) {
            downloadField.checked = false;
        }
    }
};

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = YouTube;
}
