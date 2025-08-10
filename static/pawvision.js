// PawVision JavaScript Functions

function addScheduleItem() {
    const scheduleList = document.getElementById('schedule-list');
    const newItem = document.createElement('div');
    newItem.className = 'schedule-item';
    newItem.innerHTML = `
        <input type="time" name="schedule_times" value="" style="width: auto; display: inline-block; margin-right: 10px;">
        <button type="button" class="danger" onclick="removeScheduleItem(this)" style="padding: 6px 12px;">Remove</button>
    `;
    scheduleList.appendChild(newItem);
}

function removeScheduleItem(button) {
    button.parentElement.remove();
}

function showStatus(message, isError = false) {
    const statusDiv = document.getElementById('status-message');
    statusDiv.textContent = message;
    statusDiv.style.display = 'block';
    statusDiv.style.backgroundColor = isError ? 'rgba(255, 107, 107, 0.2)' : 'rgba(62, 193, 185, 0.2)';
    statusDiv.style.color = isError ? '#ee5a24' : '#2BA8A0';
    statusDiv.style.border = `1px solid ${isError ? 'rgba(255, 107, 107, 0.4)' : 'rgba(62, 193, 185, 0.4)'}`;
    
    // Hide the message after 3 seconds
    setTimeout(() => {
        statusDiv.style.display = 'none';
    }, 3000);
}

function toggleButtonSettings() {
    const buttonSettings = document.getElementById('button_settings');
    const buttonEnabled = document.querySelector('input[name="button_enabled"]').checked;
    const inputs = buttonSettings.querySelectorAll('input, button');
    const labels = buttonSettings.querySelectorAll('label');
    
    inputs.forEach(input => {
        input.disabled = !buttonEnabled;
    });
    
    labels.forEach(label => {
        if (!buttonEnabled) {
            label.classList.add('disabled');
        } else {
            label.classList.remove('disabled');
        }
    });
}

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
