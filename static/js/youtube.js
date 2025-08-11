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
            Modal.confirm({
                title: '📥 Download Video',
                message: 'Download this YouTube video for offline playback? This may take several minutes depending on video length and quality.',
                confirmText: 'Download',
                cancelText: 'Cancel',
                onConfirm: () => this.startDownload(videoPath, quality),
                onCancel: () => console.log('Download cancelled')
            });
        } else {
            // Fallback if modals not available
            if (confirm('Download this YouTube video for offline playback? This may take several minutes depending on video length and quality.')) {
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
            progressModalId = Modal.show({
                title: '📥 Downloading Video',
                content: `
                    <div class="download-progress">
                        <div class="progress-message">Starting download...</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 0%"></div>
                        </div>
                        <div class="progress-text">Preparing download...</div>
                    </div>
                `,
                closable: false,
                buttons: [{
                    text: 'Cancel',
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
                    if (progressMessage) progressMessage.textContent = 'Download in progress...';
                    if (progressText) progressText.textContent = 'This may take several minutes';
                    
                    // Auto-close after 3 seconds with success message
                    setTimeout(() => {
                        Modal.hide(progressModalId);
                        if (typeof VideoManager !== 'undefined') {
                            VideoManager.showMessage('Download started! Check back in a few minutes.', 'success');
                        }
                    }, 3000);
                } else {
                    if (typeof VideoManager !== 'undefined') {
                        VideoManager.showMessage('Download started! Check back in a few minutes.', 'success');
                    }
                }
            } else {
                if (progressModalId) Modal.hide(progressModalId);
                if (typeof VideoManager !== 'undefined') {
                    VideoManager.showMessage(data.error || 'Failed to start download', 'error');
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (progressModalId) Modal.hide(progressModalId);
            if (typeof VideoManager !== 'undefined') {
                VideoManager.showMessage('Error starting download', 'error');
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
            validationDiv.innerHTML = '<span style="color: #666;">⏳ Validating URL...</span>';
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
                        validationDiv.innerHTML = `<span style="color: #2BA8A0;">✓ Valid: ${data.title || 'YouTube Video'}</span>`;
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
                        validationDiv.innerHTML = `<span style="color: #ee5a24;">✗ ${data.error || 'Invalid YouTube URL'}</span>`;
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
                    validationDiv.innerHTML = '<span style="color: #ee5a24;">✗ Validation failed</span>';
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
            this.showMessage('Please enter a YouTube URL', true);
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
                this.showMessage(data.message || 'Video added successfully', false);
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
                this.showMessage(data.error || 'Failed to add video', true);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showMessage('Error adding video', true);
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
            this.showMessage('Please enter a YouTube URL first', true);
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
                this.showMessage(data.message || 'Video added successfully', false);
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
                this.showMessage(data.error || 'Failed to add video', true);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showMessage('Error adding video', true);
        });
    },

    /**
     * Toggle advanced options
     * @param {Event} event - Click event
     */
    toggleAdvancedOptions(event) {
        const advancedDiv = document.getElementById('advanced-options');
        const toggleButton = event.target; // Use the actual button that was clicked
        
        if (advancedDiv.style.display === 'none' || advancedDiv.style.display === '') {
            advancedDiv.style.display = 'block';
            toggleButton.textContent = '⚙️ Hide Advanced';
            
            // Copy URL from quick input to advanced form if needed
            const quickUrl = document.getElementById('youtube-url-quick');
            if (quickUrl && quickUrl.value) {
                // URL is already validated via the quick input
                const titleInput = document.getElementById('youtube-title');
                if (titleInput && !titleInput.value) {
                    // Title may already be populated from validation
                }
            }
        } else {
            advancedDiv.style.display = 'none';
            toggleButton.textContent = '⚙️ Advanced';
        }
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
     * Show YouTube-specific message
     * @param {string} message - Message to show
     * @param {boolean} isError - Whether this is an error
     */
    showMessage(message, isError) {
        const messageDiv = document.getElementById('youtube-message');
        if (messageDiv) {
            messageDiv.textContent = message;
            messageDiv.className = isError ? 'error' : 'success';
            messageDiv.style.display = 'block';
            
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 3000);
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
            if (advancedForm.style.display === 'none' || !advancedForm.style.display) {
                advancedForm.style.display = 'block';
                toggleBtn.textContent = '▼ Hide Advanced Options';
            } else {
                advancedForm.style.display = 'none';
                toggleBtn.textContent = '⚙️ Advanced Options';
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
