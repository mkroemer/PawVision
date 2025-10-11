// PawVision Forms Management
// Form handling, validation, and settings management
/**
 * Validate form data
 * @param {HTMLFormElement} form - Form to validate
 * @returns {Object} Validation result with valid boolean and errors array
 */
function validateForm(form) {
    const errors = [];
    const formData = new FormData(form);

    // Determine form type and appropriate validation rules
    const formAction = form.action || '';
    const formId = form.id || '';

    let rules = { required: [], numeric: [], positive: [] };

    // Different validation rules based on form type
    if (formAction.includes('/settings') || formId.includes('config') || form.method === 'POST' && formAction.includes('/settings')) {
        // Config/Settings form validation
        rules = {
            required: ['playback_duration', 'post_playback_cooldown', 'volume'],
            numeric: ['playback_duration', 'post_playback_cooldown', 'volume', 'night_volume', 'button_cooldown', 'motion_sensitivity', 'motion_stop_timeout'],
            positive: ['playback_duration', 'post_playback_cooldown', 'volume', 'night_volume', 'button_cooldown', 'motion_sensitivity', 'motion_stop_timeout']
        };
    } else if (formAction.includes('/upload') || formId.includes('upload')) {
        // Upload form validation
        rules = {
            required: ['file'],
            numeric: [],
            positive: []
        };
    } else if (formAction.includes('/youtube') || formId.includes('youtube')) {
        // YouTube form validation  
        rules = {
            required: ['url'],
            numeric: [],
            positive: []
        };
    } else {
        // Default/generic form validation (keep original rules for backwards compatibility)
        rules = {
            required: ['video_duration', 'play_frequency'],
            numeric: ['video_duration', 'play_frequency', 'start_time', 'end_time'],
            positive: ['video_duration', 'play_frequency']
        };
    }

    const Forms = {
        /**
         * Add schedule item to schedule list
         */
        addScheduleItem() {
            const scheduleList = document.getElementById('schedule-list');
            const newItem = document.createElement('div');
            newItem.className = 'schedule-item';
            newItem.innerHTML = `
            <input type="time" name="schedule_times" value="" style="width: auto; display: inline-block; margin-right: 10px;">
            <button type="button" class="danger" onclick="Forms.removeScheduleItem(this)" style="padding: 6px 12px;">Remove</button>
        `;
            scheduleList.appendChild(newItem);
        },

        /**
         * Remove schedule item from schedule list
         * @param {HTMLElement} button - Remove button element
         */
        removeScheduleItem(button) {
            button.parentElement.remove();
        },

        /**
         * Toggle button settings enable/disable
         */
        toggleButtonSettings() {
            const buttonSettings = document.getElementById('button_settings');
            const buttonEnabled = document.querySelector('input[name="button_enabled"]');

            if (!buttonSettings || !buttonEnabled) return;

            const inputs = buttonSettings.querySelectorAll('input, button');
            const labels = buttonSettings.querySelectorAll('label');

            inputs.forEach(input => {
                input.disabled = !buttonEnabled.checked;
            });

            labels.forEach(label => {
                if (!buttonEnabled.checked) {
                    label.classList.add('disabled');
                } else {
                    label.classList.remove('disabled');
                }
            });
        },

        /**
         * Toggle motion sensor settings enable/disable
         */
        toggleMotionSettings() {
            const motionSettings = document.getElementById('motion_settings');
            const motionEnabled = document.querySelector('input[name="motion_sensor_enabled"]');

            if (!motionSettings || !motionEnabled) return;

            const inputs = motionSettings.querySelectorAll('input, button');
            const labels = motionSettings.querySelectorAll('label');

            inputs.forEach(input => {
                input.disabled = !motionEnabled.checked;
            });

            labels.forEach(label => {
                if (!motionEnabled.checked) {
                    label.classList.add('disabled');
                } else {
                    label.classList.remove('disabled');
                }
            });
        },

        /**
         * Validate form inputs
         * @param {HTMLFormElement} form - Form to validate
         * @returns {Object} Validation result
         */
        validateForm(form) {
            const errors = [];
            const formData = new FormData(form);

            // Determine form type and appropriate validation rules
            const formAction = form.action || '';
            const formId = form.id || '';

            let rules = { required: [], numeric: [], positive: [] };

            // Different validation rules based on form type
            if (formAction.includes('/settings') || formId.includes('config') || form.method === 'POST' && formAction.includes('/settings')) {
                // Config/Settings form validation - only validate fields that actually exist
                rules = {
                    required: [], // No required fields for config form - all fields have defaults
                    numeric: ['playback_duration', 'post_playback_cooldown', 'volume', 'night_volume', 'button_cooldown', 'motion_sensitivity', 'motion_stop_timeout'],
                    positive: ['playback_duration', 'post_playback_cooldown', 'volume', 'night_volume', 'button_cooldown', 'motion_sensitivity', 'motion_stop_timeout']
                };
            } else if (formAction.includes('/upload') || formId.includes('upload')) {
                // Upload form validation
                rules = {
                    required: [], // File input validation is handled elsewhere
                    numeric: [],
                    positive: []
                };
            } else if (formAction.includes('/youtube') || formId.includes('youtube')) {
                // YouTube form validation  
                rules = {
                    required: [], // URL validation is handled elsewhere
                    numeric: [],
                    positive: []
                };
            } else {
                // Default/generic form validation (keep original rules for backwards compatibility)
                rules = {
                    required: ['video_duration', 'play_frequency'],
                    numeric: ['video_duration', 'play_frequency', 'start_time', 'end_time'],
                    positive: ['video_duration', 'play_frequency']
                };
            }

            // Check required fields
            rules.required.forEach(field => {
                const value = formData.get(field);
                if (!value || value.trim() === '') {
                    const fieldName = field.replace('_', ' ');
                    const errorMsg = typeof t !== 'undefined' ? t('forms.required', { field: fieldName }) : `${fieldName} is required`;
                    errors.push(errorMsg);
                }
            });

            // Check numeric fields
            rules.numeric.forEach(field => {
                const value = formData.get(field);
                if (value && isNaN(parseFloat(value))) {
                    const fieldName = field.replace('_', ' ');
                    const errorMsg = typeof t !== 'undefined' ? t('forms.mustBeNumber', { field: fieldName }) : `${fieldName} must be a number`;
                    errors.push(errorMsg);
                }
            });

            // Check positive numbers
            rules.positive.forEach(field => {
                const value = parseFloat(formData.get(field));
                if (value && value <= 0) {
                    const fieldName = field.replace('_', ' ');
                    const errorMsg = typeof t !== 'undefined' ? t('forms.mustBePositive', { field: fieldName }) : `${fieldName} must be positive`;
                    errors.push(errorMsg);
                }
            });

            return {
                valid: errors.length === 0,
                errors: errors
            };
        },

        /**
         * Handle form submission with validation
         * @param {HTMLFormElement} form - Form to submit
         * @param {string} endpoint - API endpoint
         * @param {Function} onSuccess - Success callback
         * @param {Function} onError - Error callback
         */
        submitForm(form, endpoint, onSuccess, onError) {
            const validation = this.validateForm(form);

            if (!validation.valid) {
                const errorMessage = validation.errors.join('\n');
                if (onError) {
                    onError(errorMessage);
                } else {
                    // Use unified notification system
                    if (typeof NotificationSystem !== 'undefined') {
                        validation.errors.forEach(error => {
                            NotificationSystem.show(error, 'error', 4000);
                        });
                    } else {
                        showStatus(errorMessage, true);
                    }
                }
                return;
            }

            const formData = new FormData(form);

            fetch(endpoint, {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        if (onSuccess) {
                            onSuccess(data);
                        } else {
                            // Use unified notification system
                            if (typeof NotificationSystem !== 'undefined') {
                                NotificationSystem.show(data.success, 'success');
                            } else {
                                showStatus(data.success, false);
                            }
                        }
                    } else {
                        const errorMsg = data.error || (typeof t !== 'undefined' ? t('forms.formSubmissionFailed') : 'Form submission failed');
                        if (onError) {
                            onError(errorMsg);
                        } else {
                            // Use unified notification system
                            if (typeof NotificationSystem !== 'undefined') {
                                NotificationSystem.show(errorMsg, 'error');
                            } else {
                                showStatus(errorMsg, true);
                            }
                        }
                    }
                })
                .catch(error => {
                    console.error('Form submission error:', error);
                    const errorMsg = typeof t !== 'undefined' ? t('forms.networkError') : 'Network error occurred';
                    if (onError) {
                        onError(errorMsg);
                    } else {
                        // Use unified notification system
                        if (typeof NotificationSystem !== 'undefined') {
                            NotificationSystem.show(errorMsg, 'error');
                        } else {
                            showStatus(errorMsg, true);
                        }
                    }
                });
        },

        /**
         * Reset form to default values
         * @param {HTMLFormElement} form - Form to reset
         */
        resetForm(form) {
            form.reset();

            // Trigger any change events for dependent fields
            const changeEvent = new Event('change', { bubbles: true });
            const inputs = form.querySelectorAll('input, select');
            inputs.forEach(input => {
                input.dispatchEvent(changeEvent);
            });
        },

        /**
         * Auto-save form data to localStorage
         * @param {HTMLFormElement} form - Form to auto-save
         * @param {string} key - Storage key
         */
        enableAutoSave(form, key) {
            const saveData = () => {
                const formData = new FormData(form);
                const data = {};
                for (let [name, value] of formData.entries()) {
                    data[name] = value;
                }
                localStorage.setItem(key, JSON.stringify(data));
            };

            const loadData = () => {
                const saved = localStorage.getItem(key);
                if (saved) {
                    try {
                        const data = JSON.parse(saved);
                        Object.entries(data).forEach(([name, value]) => {
                            const input = form.querySelector(`[name="${name}"]`);
                            if (input) {
                                input.value = value;
                                if (input.type === 'checkbox') {
                                    input.checked = value === 'on';
                                }
                            }
                        });
                    } catch (error) {
                        console.error('Error loading auto-saved data:', error);
                    }
                }
            };

            // Load saved data on page load
            loadData();

            // Save data on input changes
            form.addEventListener('input', debounce(saveData, 1000));
            form.addEventListener('change', saveData);
        },

        /**
         * Initialize forms functionality
         */
        init() {
            // Add event listeners for setting toggles
            const buttonEnabledInput = document.querySelector('input[name="button_enabled"]');
            if (buttonEnabledInput) {
                buttonEnabledInput.addEventListener('change', () => this.toggleButtonSettings());
                this.toggleButtonSettings(); // Initial state
            }

            const motionEnabledInput = document.querySelector('input[name="motion_sensor_enabled"]');
            if (motionEnabledInput) {
                motionEnabledInput.addEventListener('change', () => this.toggleMotionSettings());
                this.toggleMotionSettings(); // Initial state
            }

            // Add form validation to all forms
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                form.addEventListener('submit', (e) => {
                    const validation = this.validateForm(form);
                    if (!validation.valid) {
                        e.preventDefault();
                        // Use unified notification system
                        if (typeof NotificationSystem !== 'undefined') {
                            validation.errors.forEach(error => {
                                NotificationSystem.show(error, 'error', 4000);
                            });
                        } else {
                            showStatus(validation.errors.join('\n'), true);
                        }
                    }
                });
            });

            // Enable auto-save for settings forms
            const settingsForm = document.getElementById('settingsForm');
            if (settingsForm) {
                this.enableAutoSave(settingsForm, 'pawvision_settings_draft');
            }
        }
    };

    // Export for module usage
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = Forms;
    }
