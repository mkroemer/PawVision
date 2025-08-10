/*!
 * PawVision Theme JavaScript
 * Enhanced for better accessibility and modern practices
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
});

/**
 * Initialize theme functionality
 */
function initializeTheme() {
    setupSmoothScrolling();
    setupTabNavigation();
    setupAccessibilityFeatures();
    setupFormValidation();
    console.log('🐾 PawVision theme initialized successfully!');
}

/**
 * Setup smooth scrolling for anchor links
 */
function setupSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                // Update focus for accessibility
                targetElement.focus();
            }
        });
    });
}

/**
 * Setup tab navigation if tabs exist
 */
function setupTabNavigation() {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    if (tabs.length === 0) return;
    
    tabs.forEach((tab, index) => {
        // Add keyboard support
        tab.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
            
            // Arrow key navigation
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                e.preventDefault();
                const currentIndex = Array.from(tabs).indexOf(this);
                let nextIndex;
                
                if (e.key === 'ArrowLeft') {
                    nextIndex = currentIndex === 0 ? tabs.length - 1 : currentIndex - 1;
                } else {
                    nextIndex = currentIndex === tabs.length - 1 ? 0 : currentIndex + 1;
                }
                
                tabs[nextIndex].focus();
                tabs[nextIndex].click();
            }
        });
        
        // Click handler
        tab.addEventListener('click', function() {
            activateTab(index);
        });
        
        // Add proper ARIA attributes
        tab.setAttribute('role', 'tab');
        tab.setAttribute('tabindex', index === 0 ? '0' : '-1');
        tab.setAttribute('aria-selected', index === 0 ? 'true' : 'false');
        tab.setAttribute('aria-controls', `tab-content-${index}`);
        tab.id = `tab-${index}`;
    });
    
    // Setup tab content ARIA attributes
    tabContents.forEach((content, index) => {
        content.setAttribute('role', 'tabpanel');
        content.setAttribute('aria-labelledby', `tab-${index}`);
        content.id = `tab-content-${index}`;
        content.setAttribute('tabindex', '0');
    });
    
    // Add tab container role
    const tabContainer = document.querySelector('.tabs');
    if (tabContainer) {
        tabContainer.setAttribute('role', 'tablist');
    }
}

/**
 * Activate a specific tab
 */
function activateTab(activeIndex) {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach((tab, index) => {
        const isActive = index === activeIndex;
        tab.classList.toggle('active', isActive);
        tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
        tab.setAttribute('tabindex', isActive ? '0' : '-1');
    });
    
    tabContents.forEach((content, index) => {
        content.classList.toggle('active', index === activeIndex);
    });
}

/**
 * Setup accessibility features
 */
function setupAccessibilityFeatures() {
    // Add skip link if not present
    addSkipLink();
    
    // Enhance form labels
    enhanceFormLabels();
    
    // Add ARIA landmarks
    addAriaLandmarks();
    
    // Setup focus management
    setupFocusManagement();
}

/**
 * Add skip link for keyboard navigation
 */
function addSkipLink() {
    if (document.querySelector('.skip-link')) return;
    
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.className = 'skip-link';
    skipLink.textContent = 'Skip to main content';
    skipLink.style.cssText = `
        position: absolute;
        top: -40px;
        left: 6px;
        background: var(--primary-color);
        color: white;
        padding: 8px;
        text-decoration: none;
        border-radius: 4px;
        z-index: 1000;
        transition: top 0.3s;
    `;
    
    skipLink.addEventListener('focus', function() {
        this.style.top = '6px';
    });
    
    skipLink.addEventListener('blur', function() {
        this.style.top = '-40px';
    });
    
    document.body.insertBefore(skipLink, document.body.firstChild);
}

/**
 * Enhance form labels for better accessibility
 */
function enhanceFormLabels() {
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        if (!input.id && input.name) {
            input.id = input.name + '-' + Math.random().toString(36).substr(2, 9);
        }
        
        // Associate labels with inputs
        const label = document.querySelector(`label[for="${input.id}"]`);
        if (!label) {
            const nearbyLabel = input.previousElementSibling;
            if (nearbyLabel && nearbyLabel.tagName === 'LABEL') {
                nearbyLabel.setAttribute('for', input.id);
            }
        }
    });
}

/**
 * Add ARIA landmarks where missing
 */
function addAriaLandmarks() {
    // Ensure main content has proper landmark
    const main = document.querySelector('main');
    if (main && !main.hasAttribute('role')) {
        main.setAttribute('role', 'main');
    }
    
    // Add navigation landmarks
    const nav = document.querySelector('nav');
    if (nav && !nav.hasAttribute('role')) {
        nav.setAttribute('role', 'navigation');
    }
}

/**
 * Setup focus management
 */
function setupFocusManagement() {
    // Trap focus in modals if any exist
    const modals = document.querySelectorAll('.modal, .dialog');
    modals.forEach(modal => {
        modal.addEventListener('keydown', trapFocus);
    });
    
    // Ensure visible focus indicators
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            document.body.classList.add('keyboard-navigation');
        }
    });
    
    document.addEventListener('mousedown', function() {
        document.body.classList.remove('keyboard-navigation');
    });
}

/**
 * Trap focus within an element
 */
function trapFocus(e) {
    if (e.key !== 'Tab') return;
    
    const focusableElements = this.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    
    if (e.shiftKey) {
        if (document.activeElement === firstElement) {
            lastElement.focus();
            e.preventDefault();
        }
    } else {
        if (document.activeElement === lastElement) {
            firstElement.focus();
            e.preventDefault();
        }
    }
}

/**
 * Setup form validation
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Validate a form
 */
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    return isValid;
}

/**
 * Show field error
 */
function showFieldError(field, message) {
    clearFieldError(field);
    
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error';
    errorElement.textContent = message;
    errorElement.style.cssText = `
        color: var(--error-color);
        font-size: var(--font-size-sm);
        margin-top: var(--spacing-xs);
    `;
    
    field.parentNode.appendChild(errorElement);
    field.setAttribute('aria-invalid', 'true');
    field.setAttribute('aria-describedby', errorElement.id = 'error-' + field.id);
}

/**
 * Clear field error
 */
function clearFieldError(field) {
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    field.removeAttribute('aria-invalid');
    field.removeAttribute('aria-describedby');
}

// Legacy functions for backwards compatibility
function addScheduleItem() {
    const scheduleList = document.getElementById('schedule-list');
    if (!scheduleList) return;
    
    const newItem = document.createElement('div');
    newItem.className = 'schedule-item';
    newItem.innerHTML = `
        <input type="time" name="schedule_times" value="" aria-label="Schedule time">
        <button type="button" class="btn btn-danger" onclick="removeScheduleItem(this)" aria-label="Remove schedule item">Remove</button>
    `;
    scheduleList.appendChild(newItem);
}

function removeScheduleItem(button) {
    button.parentElement.remove();
}

function showStatus(message, isError = false) {
    let statusDiv = document.getElementById('status-message');
    
    if (!statusDiv) {
        statusDiv = document.createElement('div');
        statusDiv.id = 'status-message';
        statusDiv.className = 'status-message';
        document.body.appendChild(statusDiv);
    }
    
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${isError ? 'status-error' : 'status-success'}`;
    statusDiv.style.display = 'block';
    statusDiv.setAttribute('role', 'alert');
    statusDiv.setAttribute('aria-live', 'polite');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        statusDiv.style.display = 'none';
    }, 5000);
}

function toggleButtonSettings() {
    const buttonSettings = document.getElementById('button_settings');
    const buttonEnabled = document.querySelector('input[name="button_enabled"]');
    
    if (!buttonSettings || !buttonEnabled) return;
    
    const isEnabled = buttonEnabled.checked;
    const inputs = buttonSettings.querySelectorAll('input, button, select');
    const labels = buttonSettings.querySelectorAll('label');
    
    inputs.forEach(input => {
        input.disabled = !isEnabled;
        input.setAttribute('aria-disabled', !isEnabled);
    });
    
    labels.forEach(label => {
        label.classList.toggle('disabled', !isEnabled);
    });
}

// Export functions for external use
window.PawVisionTheme = {
    addScheduleItem,
    removeScheduleItem,
    showStatus,
    toggleButtonSettings,
    activateTab
};

function toggleMotionSettings() {
	const motionSettings = document.getElementById('motion_settings');
	const motionEnabled = document.querySelector('input[name="motion_sensor_enabled"]').checked;
	const inputs = motionSettings.querySelectorAll('input, button');
	const labels = motionSettings.querySelectorAll('label');
    
	inputs.forEach(input => {
		input.disabled = !motionEnabled;
	});
    
	labels.forEach(label => {
		if (!motionEnabled) {
			label.classList.add('disabled');
		} else {
			label.classList.remove('disabled');
		}
	});
}

function playVideo() {
	fetch('/api/play', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		}
	})
	.then(response => response.json())
	.then(data => {
		if (data.status === 'success') {
			showStatus('Video playback started!', false);
		} else {
			showStatus(data.message || 'Failed to start playback', true);
		}
	})
	.catch(error => {
		console.error('Error:', error);
		showStatus('Error starting playback', true);
	});
}

function stopVideo() {
	fetch('/api/stop', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		}
	})
	.then(response => response.json())
	.then(data => {
		if (data.status === 'success') {
			showStatus('Video playback stopped!', false);
		} else {
			showStatus(data.message || 'Failed to stop playback', true);
		}
	})
	.catch(error => {
		console.error('Error:', error);
		showStatus('Error stopping playback', true);
	});
}

// Statistics functions
function loadStatistics() {
	fetch('/api/statistics')
	.then(response => response.json())
	.then(data => {
		if (data.status === 'success') {
			updateStatisticsDisplay(data.statistics);
		} else {
			console.error('Failed to load statistics:', data.message);
		}
	})
	.catch(error => {
		console.error('Error loading statistics:', error);
	});
}

function updateStatisticsDisplay(stats) {
	document.getElementById('total-presses').textContent = stats.total_button_presses || 0;
	document.getElementById('today-presses').textContent = stats.today_button_presses || 0;
	document.getElementById('avg-daily').textContent = (stats.daily_average || 0).toFixed(1);
	document.getElementById('peak-hour').textContent = stats.peak_hour || 'N/A';
    
	// Update video viewing statistics
	document.getElementById('total-viewing').textContent = stats.total_viewing_minutes || 0;
	document.getElementById('yesterday-viewing').textContent = stats.yesterday_viewing_minutes || 0;

	// Load today's hourly chart by default
	updateHourlyChart();
}

let hourlyChart = null;

function updateHourlyChart() {
	const dateInput = document.getElementById('chart-date');
	const selectedDate = dateInput.value || new Date().toISOString().split('T')[0];
    
	fetch(`/api/statistics/hourly?date=${selectedDate}`)
	.then(response => response.json())
	.then(data => {
		if (data.status === 'success') {
			renderHourlyChart(data.hourly_data || {});
		} else {
			console.error('Failed to load hourly data:', data.message);
		}
	})
	.catch(error => {
		console.error('Error loading hourly data:', error);
	});
}

function renderHourlyChart(hourlyData) {
	const ctx = document.getElementById('hourlyChart').getContext('2d');
    
	// Destroy existing chart if it exists
	if (hourlyChart) {
		hourlyChart.destroy();
	}

	// Prepare data for all 24 hours
	const hours = [];
	const values = [];
	const regularPresses = [];
	const interruptions = [];
    
	for (let i = 0; i < 24; i++) {
		const hour = i.toString().padStart(2, '0');
		hours.push(hour + ':00');
		const hourData = hourlyData[hour] || { button_presses: 0, interruptions: 0 };
		values.push(hourData.button_presses || 0);
		regularPresses.push((hourData.button_presses || 0) - (hourData.interruptions || 0));
		interruptions.push(hourData.interruptions || 0);
	}

	hourlyChart = new Chart(ctx, {
		type: 'bar',
		data: {
			labels: hours,
			datasets: [
				{
					label: 'Button Presses',
					data: values,
					backgroundColor: 'rgba(54, 162, 235, 0.8)',
					borderColor: 'rgba(54, 162, 235, 1)',
					borderWidth: 1
				}
			]
		},
		options: {
			responsive: true,
			maintainAspectRatio: false,
			scales: {
				x: {
					title: {
						display: true,
						text: 'Hour of Day'
					}
				},
				y: {
					beginAtZero: true,
					title: {
						display: true,
						text: 'Number of Presses'
					},
					ticks: {
						stepSize: 1
					}
				}
			},
			plugins: {
				title: {
					display: true,
					text: 'Button Press Activity by Hour'
				},
				legend: {
					display: true,
					position: 'top'
				}
			}
		}
	});
}

function refreshStats() {
	loadStatistics();
	showStatus('Statistics refreshed!', false);
}

function clearStats() {
	if (confirm('Are you sure you want to clear all statistics? This action cannot be undone.')) {
		fetch('/api/statistics/clear', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			}
		})
		.then(response => response.json())
		.then(data => {
			if (data.status === 'success') {
				loadStatistics();
				showStatus('Statistics cleared!', false);
			} else {
				showStatus('Failed to clear statistics', true);
			}
		})
		.catch(error => {
			console.error('Error:', error);
			showStatus('Error clearing statistics', true);
		});
	}
}

// Load statistics when statistics tab is opened
function openTab(evt, tabName) {
	var i, tabcontent, tabs;
    
	// Hide all tab content
	tabcontent = document.getElementsByClassName("tab-content");
	for (i = 0; i < tabcontent.length; i++) {
		tabcontent[i].classList.remove("active");
	}
    
	// Remove active class from all tabs
	tabs = document.getElementsByClassName("tab");
	for (i = 0; i < tabs.length; i++) {
		tabs[i].classList.remove("active");
	}
    
	// Show the selected tab content and mark the button as active
	document.getElementById(tabName).classList.add("active");
	evt.currentTarget.classList.add("active");
    
	// Load statistics when statistics tab is opened
	if (tabName === 'statistics') {
		loadStatistics();
	}
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
	// Set today's date as default for the chart date picker
	const today = new Date().toISOString().split('T')[0];
	document.getElementById('chart-date').value = today;
    
	// Add event listeners for video edit buttons
	const editButtons = document.querySelectorAll('.edit-video-btn');
	editButtons.forEach(button => {
		button.addEventListener('click', function() {
			const path = this.dataset.path;
			const title = this.dataset.title;
			const start = parseFloat(this.dataset.start) || 0;
			const end = this.dataset.end ? parseFloat(this.dataset.end) : null;
			const duration = parseFloat(this.dataset.duration) || 0;
            
			openEditModal(path, title, start, end, duration);
		});
	});
});

// Video editing functions
function openEditModal(path, title, startTime, endTime, duration) {
	document.getElementById('edit-path').value = path;
	document.getElementById('edit-title').value = title || '';
	document.getElementById('edit-start').value = startTime || 0;
	document.getElementById('edit-start').max = duration;
	document.getElementById('edit-end').value = endTime || '';
	document.getElementById('edit-end').max = duration;
	document.getElementById('edit-modal').style.display = 'block';
}

function closeEditModal() {
	document.getElementById('edit-modal').style.display = 'none';
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
	const modal = document.getElementById('edit-modal');
	if (event.target === modal) {
		closeEditModal();
	}
});

// Handle escape key to close modal
document.addEventListener('keydown', function(event) {
	if (event.key === 'Escape') {
		closeEditModal();
	}
});

// Format time helper function
function formatTime(seconds) {
	if (seconds < 60) {
		return `${Math.round(seconds)}s`;
	} else if (seconds < 3600) {
		const minutes = Math.floor(seconds / 60);
		const secs = Math.round(seconds % 60);
		return `${minutes}m ${secs}s`;
	} else {
		const hours = Math.floor(seconds / 3600);
		const minutes = Math.floor((seconds % 3600) / 60);
		return `${hours}h ${minutes}m`;
	}
}
