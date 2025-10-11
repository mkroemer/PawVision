/**
 * Statistics functionality for PawVision
 */
const Statistics = {
    currentFilter: '24h',
    currentDate: null,
    
    // Initialize statistics
    init() {
        console.log('Statistics module initialized');
        this.setDefaultDate();
        // Don't load data immediately - wait for tab activation
    },
    
    // Initialize statistics when tab becomes active
    initializeTab() {
        console.log('Statistics tab activated');
        this.setDefaultDate();
        this.loadData(this.currentFilter);
        // Load chart after a short delay to ensure DOM is ready
        setTimeout(() => {
            // Make sure date input is set
            const dateInput = document.getElementById('plays-chart-date');
            if (dateInput && !dateInput.value) {
                dateInput.value = this.currentDate;
            }
            this.loadPlaysChart(this.currentDate);
        }, 100);
    },
    
    // Set default date to today
    setDefaultDate() {
        const today = new Date().toISOString().split('T')[0];
        const dateInput = document.getElementById('plays-chart-date');
        if (dateInput) {
            dateInput.value = today;
            this.currentDate = today;
        } else {
            // If element doesn't exist yet, just set the date
            this.currentDate = today;
        }
    },
    
    // Filter time periods
    filterTime(period, event = null) {
        this.currentFilter = period;
        
        // Update active button
        document.querySelectorAll('.filter button').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Set active button (either from event or find by period)
        if (event && event.target) {
            event.target.classList.add('active');
        } else {
            const targetBtn = document.querySelector(`.filter button[data-period="${period}"]`);
            if (targetBtn) {
                targetBtn.classList.add('active');
            }
        }
        
        this.loadData(period);
    },
    
    // Update plays chart for specific date
    updatePlaysChart(date) {
        this.currentDate = date;
        this.loadPlaysChart(date);
    },
    
    // Reset plays chart to today
    resetPlaysChart() {
        const today = new Date().toISOString().split('T')[0];
        const dateInput = document.getElementById('plays-chart-date');
        if (dateInput) {
            dateInput.value = today;
            this.currentDate = today;
            this.loadPlaysChart(today);
        }
    },
    
    // Load statistics data
    async loadData(period = '24h') {
        try {
            const response = await fetch(`/api/statistics?period=${period}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success' || data.success) {
                // Handle both possible response formats
                const stats = data.stats || data;
                this.updateStatsCards(stats);
            } else {
                console.error('Failed to load statistics:', data.message || data.error);
                const errorMessage = typeof t !== 'undefined' ? t('statistics.failedToLoadStats') : 'Failed to load statistics data';
                this.showStatsError(errorMessage);
            }
        } catch (error) {
            console.error('Error loading statistics:', error);
            const errorMessage = typeof t !== 'undefined' ? t('statistics.errorConnectingServer') : 'Error connecting to server';
            this.showStatsError(errorMessage);
        }
    },
    
    // Show error in stats area
    showStatsError(message) {
        const elements = ['total-plays', 'total-duration', 'avg-daily', 'avg-watch-time'];
        const errorText = typeof t !== 'undefined' ? t('common.error') : 'Error';
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = errorText;
                element.style.color = 'var(--error-color, #ee5a24)';
            }
        });
        
        if (typeof NotificationSystem !== 'undefined') {
            NotificationSystem.show(message, 'error');
        }
    },
    
    // Update stats cards
    updateStatsCards(stats) {
        const elements = {
            'total-plays': stats.total_plays || 0,
            'total-duration': stats.total_watch_time_str || stats.total_duration_str || "0m",
            'avg-daily': stats.avg_daily_plays || stats.average_daily_plays || 0,
            'avg-watch-time': stats.avg_watch_time_str || stats.average_watch_time_str || "0m"
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                element.style.color = ''; // Reset error color if any
            }
        });
    },
    
    // Load plays chart for specific date
    async loadPlaysChart(date) {
        if (!date) {
            console.log('No date provided for chart loading');
            return;
        }
        
        // Check if chart element exists
        const chartElement = document.getElementById('plays-chart');
        if (!chartElement) {
            console.log('Chart element not found, skipping chart load');
            return;
        }
        
        // Show loading state
        chartElement.innerHTML = '<div class="chart-loading">Loading chart data...</div>';
        
        try {
            const response = await fetch(`/api/statistics/hourly?date=${date}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success' || data.success) {
                const hourlyData = data.hourly_data || data.data || [];
                this.renderPlaysChart(hourlyData);
            } else {
                console.error('Failed to load hourly data:', data.message || data.error);
                const errorMessage = typeof t !== 'undefined' ? t('statistics.failedToLoadChart') : 'Failed to load chart data';
                this.showChartError(errorMessage);
            }
        } catch (error) {
            console.error('Error loading hourly data:', error);
            const errorMessage = typeof t !== 'undefined' ? t('statistics.errorLoadingChart') : 'Error loading chart data';
            this.showChartError(errorMessage);
        }
    },
    
    // Show error in chart
    showChartError(message) {
        const chartElement = document.getElementById('plays-chart');
        if (chartElement) {
            const retryText = typeof t !== 'undefined' ? t('statistics.retry') : '🔄 Retry';
            chartElement.innerHTML = `
                <div class="chart-error">
                    <div class="error-icon">⚠️</div>
                    <div class="error-message">${message}</div>
                    <button onclick="Statistics.loadPlaysChart(Statistics.currentDate)" class="btn-secondary btn-sm">
                        ${retryText}
                    </button>
                </div>
            `;
        }
    },
    
    // Render plays chart
    renderPlaysChart(hourlyData) {
        const chartElement = document.getElementById('plays-chart');
        if (!chartElement) return;
        
        // Clear the placeholder styling and content
        chartElement.className = 'chart-content';
        
        const hours = Array.from({length: 24}, (_, i) => i);
        const plays = hours.map(hour => {
            // Find data for this local hour
            // The server should be sending data with local time already,
            // so we don't need to convert - just use the hour directly
            const hourData = hourlyData.find(d => d.hour === hour);
            return hourData ? hourData.plays : 0;
        });
        
        const maxPlays = Math.max(...plays, 1);
        const totalPlays = plays.reduce((a, b) => a + b, 0);
        
        // Create enhanced chart with better styling
        let chartHtml = `
            <div class="chart-stats">
                <div class="chart-summary">
                    <span class="total-plays">${totalPlays} total plays</span>
                </div>
            </div>
            <div class="chart-container-inner">
                <div class="chart-bars">
        `;
        
        hours.forEach((hour, index) => {
            const height = maxPlays > 0 ? (plays[index] / maxPlays) * 100 : 0;
            const isActive = plays[index] > 0;
            const timeLabel = this.formatHourLabel(hour);
            
            chartHtml += `
                <div class="chart-bar ${isActive ? 'has-data' : ''}">
                    <div class="bar" 
                         style="height: ${Math.max(height, 2)}%" 
                         title="${timeLabel}: ${plays[index]} plays"
                         data-plays="${plays[index]}">
                    </div>
                </div>
            `;
        });
        
        chartHtml += `
                </div>
                <div class="chart-x-axis">
                    <div class="x-axis-labels">
        `;
        
        // Add main hour labels at the bottom
        for (let i = 0; i < 24; i += 6) {
            chartHtml += `<span class="x-axis-label">${this.formatHourLabel(i)}</span>`;
        }
        
        chartHtml += `
                    </div>
                    <div class="axis-title">
                        <span class="axis-label">Time (Local)</span>
                    </div>
                </div>
            </div>
        `;
        
        chartElement.innerHTML = chartHtml;
        
        // Add interaction effects
        this.addChartInteractions();
    },
    
    // Format hour label for display
    formatHourLabel(hour) {
        if (hour === 0) return '12AM';
        if (hour === 12) return '12PM';
        if (hour < 12) return `${hour}AM`;
        return `${hour - 12}PM`;
    },
    
    // Add chart interactions
    addChartInteractions() {
        const bars = document.querySelectorAll('#plays-chart .bar');
        bars.forEach(bar => {
            bar.addEventListener('mouseenter', function() {
                this.style.transform = 'scaleY(1.1)';
                this.style.filter = 'brightness(1.1)';
            });
            
            bar.addEventListener('mouseleave', function() {
                this.style.transform = 'scaleY(1)';
                this.style.filter = 'brightness(1)';
            });
        });
    },
    
    // Refresh activity log
    async refreshActivity() {
        try {
            const response = await fetch('/api/statistics/activity');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.updateActivityLog(data.activity || []);
            }
        } catch (error) {
            console.error('Error refreshing activity:', error);
        }
    },
    
    // Update activity log
    updateActivityLog(activities) {
        const logElement = document.getElementById('activity-log');
        if (!logElement) return;
        
        if (activities.length === 0) {
            logElement.innerHTML = `
                <div class="log-entry">
                    <span class="log-icon">📭</span>
                    <div class="log-content">
                        <div class="log-action">No recent activity</div>
                        <div class="log-details">Start playing videos to see activity here</div>
                    </div>
                    <div class="log-time">-</div>
                </div>
            `;
            return;
        }
        
        let html = '';
        activities.forEach(activity => {
            const icon = this.getActivityIcon(activity.action);
            html += `
                <div class="log-entry">
                    <span class="log-icon">${icon}</span>
                    <div class="log-content">
                        <div class="log-action">${this.getActivityLabel(activity.action)}</div>
                        <div class="log-details">
                            ${activity.video_title || activity.details || 'Unknown video'}
                            ${activity.duration ? ` • Duration: ${activity.duration_str}` : ''}
                        </div>
                    </div>
                    <div class="log-time">${activity.time_ago}</div>
                </div>
            `;
        });
        
        logElement.innerHTML = html;
    },
    
    // Get activity icon
    getActivityIcon(action) {
        const icons = {
            'play': '▶️',
            'upload': '📤',
            'delete': '🗑️',
            'download': '📥',
            'edit': '✏️'
        };
        return icons[action] || '📌';
    },
    
    // Get activity label
    getActivityLabel(action) {
        const labels = {
            'play': 'Played video',
            'upload': 'Uploaded new video',
            'delete': 'Deleted video',
            'download': 'Downloaded video from YouTube',
            'edit': 'Edited video settings'
        };
        return labels[action] || action.charAt(0).toUpperCase() + action.slice(1);
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (typeof Statistics !== 'undefined') {
        Statistics.init();
    }
});
