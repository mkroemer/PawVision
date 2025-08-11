// PawVision Configuration Management
// Form handling, validation, and real-time updates

/**
 * Configuration management
 */
const ConfigManager = {
    /**
     * Initialize configuration form functionality
     */
    init() {
        this.setupSliderUpdates();
        this.setupFormValidation();
        this.setupResetFunctionality();
        this.updateEmptyScheduleMessage();
        console.log('Configuration Manager initialized');
    },

    /**
     * Setup real-time slider value updates
     */
    setupSliderUpdates() {
        // Volume slider
        const volumeSlider = document.getElementById('volume');
        const volumeValue = document.getElementById('volume-value');
        if (volumeSlider && volumeValue) {
            volumeSlider.addEventListener('input', function() {
                volumeValue.textContent = this.value + '%';
            });
        }

        // Night volume slider
        const nightVolumeSlider = document.getElementById('night_volume');
        const nightVolumeValue = document.getElementById('night-volume-value');
        if (nightVolumeSlider && nightVolumeValue) {
            nightVolumeSlider.addEventListener('input', function() {
                nightVolumeValue.textContent = this.value + '%';
            });
        }

        // Motion sensitivity slider
        const motionSlider = document.getElementById('motion_sensitivity');
        const motionValue = document.getElementById('motion-sensitivity-value');
        if (motionSlider && motionValue) {
            motionSlider.addEventListener('input', function() {
                motionValue.textContent = this.value;
            });
        }
    },

    /**
     * Setup form validation
     */
    setupFormValidation() {
        const form = document.querySelector('form');
        if (!form) return;

        form.addEventListener('submit', function(e) {
            // Validate scheduled playback if enabled
            const scheduledEnabled = document.querySelector('input[name="scheduled_playback_enabled"]')?.checked;
            
            if (scheduledEnabled) {
                const scheduleInputs = document.querySelectorAll('input[name="schedule_times[]"]');
                
                if (scheduleInputs.length === 0) {
                    e.preventDefault();
                    alert('Please add at least one scheduled time');
                    return false;
                }
                
                // Check for duplicate times
                const times = Array.from(scheduleInputs).map(input => input.value).filter(Boolean);
                const uniqueTimes = [...new Set(times)];
                
                if (times.length !== uniqueTimes.length) {
                    e.preventDefault();
                    alert('Please remove duplicate scheduled times');
                    return false;
                }
                
                // Check for empty times
                if (times.some(time => !time)) {
                    e.preventDefault();
                    alert('Please set all scheduled times');
                    return false;
                }
            }
            
            // Validate night mode times if enabled
            const nightModeEnabled = document.querySelector('input[name="night_mode_enabled"]')?.checked;
            
            if (nightModeEnabled) {
                const startTime = document.getElementById('night_mode_start')?.value;
                const endTime = document.getElementById('night_mode_end')?.value;
                
                if (!startTime || !endTime) {
                    e.preventDefault();
                    alert('Please set both night mode start and end times');
                    return false;
                }
            }
            
            // Show loading state
            const submitBtn = document.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.textContent = '💾 Saving...';
                submitBtn.disabled = true;
            }
        });
    },

    /**
     * Setup reset functionality
     */
    setupResetFunctionality() {
        // The resetForm function is called from the template button
        window.resetForm = this.resetForm.bind(this);
    },

    /**
     * Reset form to default values
     */
    resetForm() {
        if (!confirm('Reset all settings to default values? This cannot be undone.')) {
            return;
        }

        // Set default values
        const defaults = {
            'playback_duration': '15',
            'post_playback_cooldown': '2',
            'volume': '75',
            'night_volume': '25',
            'button_cooldown': '30',
            'motion_sensitivity': '5',
            'motion_stop_timeout': '300',
            'schedule_time': '08:00',
            'night_mode_start': '22:00',
            'night_mode_end': '07:00'
        };

        // Apply default values
        for (const [id, value] of Object.entries(defaults)) {
            const element = document.getElementById(id);
            if (element) {
                element.value = value;
                
                // Trigger input event for sliders to update display values
                if (element.type === 'range') {
                    element.dispatchEvent(new Event('input'));
                }
            }
        }

        // Update volume display
        const volumeValue = document.getElementById('volume-value');
        if (volumeValue) {
            volumeValue.textContent = '75%';
        }

        // Update night volume display
        const nightVolumeValue = document.getElementById('night-volume-value');
        if (nightVolumeValue) {
            nightVolumeValue.textContent = '25%';
        }

        // Update motion sensitivity display
        const motionValue = document.getElementById('motion-sensitivity-value');
        if (motionValue) {
            motionValue.textContent = '5';
        }
        
        // Reset checkboxes
        document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = checkbox.name === 'button_enabled';
        });
        
        // Reset schedule times to single default entry
        this.resetScheduleTimes();
    },

    /**
     * Add a new schedule time input
     */
    addScheduleTime() {
        const scheduleList = document.getElementById('schedule-times-list');
        if (!scheduleList) return;

        const scheduleItem = document.createElement('div');
        scheduleItem.className = 'schedule-time-item';
        scheduleItem.innerHTML = `
            <input type="time" name="schedule_times[]" value="08:00" class="schedule-time-input">
            <button type="button" class="btn-danger btn-sm" onclick="ConfigManager.removeScheduleTime(this)">
                🗑️ Remove
            </button>
        `;

        scheduleList.appendChild(scheduleItem);
        this.updateEmptyScheduleMessage();
        
        // Focus on the new time input
        const newInput = scheduleItem.querySelector('.schedule-time-input');
        if (newInput) {
            newInput.focus();
        }
    },

    /**
     * Remove a schedule time item
     * @param {HTMLElement} button - The remove button that was clicked
     */
    removeScheduleTime(button) {
        const scheduleItem = button.closest('.schedule-time-item');
        const scheduleList = document.getElementById('schedule-times-list');
        
        if (!scheduleItem || !scheduleList) return;
        
        // Don't allow removing the last item
        const remainingItems = scheduleList.querySelectorAll('.schedule-time-item').length;
        if (remainingItems <= 1) {
            alert('You must have at least one scheduled time.');
            return;
        }
        
        scheduleItem.remove();
        this.updateEmptyScheduleMessage();
    },

    /**
     * Update the visibility of the empty schedule message
     */
    updateEmptyScheduleMessage() {
        const scheduleList = document.getElementById('schedule-times-list');
        const emptyMessage = document.getElementById('empty-schedule-message');
        
        if (!scheduleList || !emptyMessage) return;
        
        const scheduleItems = scheduleList.querySelectorAll('.schedule-time-item');
        if (scheduleItems.length === 0) {
            emptyMessage.style.display = 'block';
        } else {
            emptyMessage.style.display = 'none';
        }
    },

    /**
     * Reset schedule times to default
     */
    resetScheduleTimes() {
        const scheduleList = document.getElementById('schedule-times-list');
        if (!scheduleList) return;
        
        // Clear existing items
        scheduleList.innerHTML = '';
        
        // Add default schedule item
        const defaultItem = document.createElement('div');
        defaultItem.className = 'schedule-time-item';
        defaultItem.innerHTML = `
            <input type="time" name="schedule_times[]" value="08:00" class="schedule-time-input">
            <button type="button" class="btn-danger btn-sm" onclick="ConfigManager.removeScheduleTime(this)">
                🗑️ Remove
            </button>
        `;
        
        scheduleList.appendChild(defaultItem);
        this.updateEmptyScheduleMessage();
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    ConfigManager.init();
});
