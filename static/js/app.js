// Auto-Viz AngularJS Application
var app = angular.module('autoVizApp', []);

// Main Controller
app.controller('MainController', ['$scope', '$http', '$timeout', function($scope, $http, $timeout) {
    // State
    $scope.currentView = 'dashboard';
    $scope.dashboards = [];
    $scope.groups = [];
    $scope.selectedDashboard = null;
    $scope.uploading = false;
    $scope.uploadProgress = '';
    $scope.isDragging = false;
    $scope.showCreateGroup = false;
    $scope.newGroupName = '';
    $scope.toast = { show: false, message: '', type: 'success' };

    // Initialize
    $scope.init = function() {
        $scope.loadDashboards();
        $scope.loadGroups();
    };

    // View Management
    $scope.setView = function(view) {
        $scope.currentView = view;
        if (view === 'dashboard') {
            $scope.loadDashboards();
        } else if (view === 'groups') {
            $scope.loadGroups();
        }
    };

    // Toast Notifications
    $scope.showToast = function(message, type) {
        $scope.toast = { show: true, message: message, type: type || 'success' };
        $timeout(function() {
            $scope.toast.show = false;
        }, 3000);
    };

    // Date Formatting
    $scope.formatDate = function(dateStr) {
        if (!dateStr) return '';
        var date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    // Dashboard Functions
    $scope.loadDashboards = function() {
        $http.get('/api/dashboards').then(function(response) {
            $scope.dashboards = response.data.sort(function(a, b) {
                return new Date(b.created_at) - new Date(a.created_at);
            });
        });
    };

    $scope.openDashboard = function(dashboard) {
        $scope.selectedDashboard = dashboard;
        $scope.currentView = 'single-dashboard';

        // Render charts after view updates
        $timeout(function() {
            $scope.renderAllCharts();
        }, 100);
    };

    $scope.deleteDashboard = function(id, event) {
        event.stopPropagation();
        if (confirm('Are you sure you want to delete this dashboard?')) {
            $http.delete('/api/dashboards/' + id).then(function() {
                $scope.loadDashboards();
                $scope.showToast('Dashboard deleted', 'success');
            });
        }
    };

    // File Upload
    $scope.handleFileSelect = function(files) {
        if (files && files.length > 0) {
            $scope.uploadFile(files[0]);
        }
    };

    $scope.uploadFile = function(file) {
        if (!file) return;

        var validExtensions = ['.csv', '.xlsx', '.xls'];
        var fileName = file.name.toLowerCase();
        var isValid = validExtensions.some(function(ext) {
            return fileName.endsWith(ext);
        });

        if (!isValid) {
            $scope.showToast('Please upload a CSV or Excel file', 'error');
            return;
        }

        $scope.uploading = true;
        $scope.uploadProgress = 'Uploading file...';

        var formData = new FormData();
        formData.append('file', file);

        $timeout(function() {
            $scope.uploadProgress = 'Analyzing data structure...';
        }, 500);

        $timeout(function() {
            $scope.uploadProgress = 'Generating visualizations...';
        }, 1500);

        $http.post('/api/upload', formData, {
            headers: { 'Content-Type': undefined },
            transformRequest: angular.identity
        }).then(function(response) {
            $scope.uploading = false;
            $scope.uploadProgress = '';
            $scope.showToast('Visualizations generated successfully!', 'success');

            // Open the new dashboard
            $scope.selectedDashboard = response.data;
            $scope.currentView = 'single-dashboard';

            $timeout(function() {
                $scope.renderAllCharts();
            }, 100);
        }).catch(function(error) {
            $scope.uploading = false;
            $scope.uploadProgress = '';
            var msg = error.data && error.data.error ? error.data.error : 'Upload failed';
            $scope.showToast(msg, 'error');
        });
    };

    // Chart Rendering
    $scope.renderAllCharts = function() {
        if (!$scope.selectedDashboard || !$scope.selectedDashboard.charts) return;

        $scope.selectedDashboard.charts.forEach(function(chart) {
            $scope.renderChart(chart);
        });
    };

    $scope.renderChart = function(chart) {
        var canvas = document.getElementById('chart-' + chart.id);
        if (!canvas) return;

        var ctx = canvas.getContext('2d');

        // Destroy existing chart if any
        if (canvas.chartInstance) {
            canvas.chartInstance.destroy();
        }

        var chartType = chart.type;
        if (chartType === 'histogram' || chartType === 'grouped_bar') {
            chartType = 'bar';
        }

        var options = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: chartType !== 'bar',
                    position: 'bottom',
                    labels: {
                        color: '#a0a0b0',
                        padding: 15,
                        font: { family: 'Inter' }
                    }
                },
                tooltip: {
                    backgroundColor: '#1a1a2e',
                    titleColor: '#ffffff',
                    bodyColor: '#a0a0b0',
                    borderColor: '#00ff88',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8
                }
            },
            scales: {}
        };

        if (chartType !== 'pie' && chartType !== 'doughnut') {
            options.scales = {
                x: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: {
                        color: '#606070',
                        maxRotation: 45,
                        minRotation: 0
                    }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#606070' },
                    beginAtZero: true
                }
            };
        }

        if (chartType === 'scatter') {
            options.scales.x.type = 'linear';
            options.scales.x.position = 'bottom';
        }

        canvas.chartInstance = new Chart(ctx, {
            type: chartType,
            data: chart.data,
            options: options
        });
    };

    // Groups Functions
    $scope.loadGroups = function() {
        $http.get('/api/groups').then(function(response) {
            $scope.groups = response.data;
        });
    };

    $scope.createGroup = function() {
        var selectedIds = $scope.dashboards
            .filter(function(d) { return d.selected; })
            .map(function(d) { return d.id; });

        $http.post('/api/groups', {
            name: $scope.newGroupName || 'Untitled Group',
            dashboard_ids: selectedIds
        }).then(function() {
            $scope.showCreateGroup = false;
            $scope.newGroupName = '';
            $scope.dashboards.forEach(function(d) { d.selected = false; });
            $scope.loadGroups();
            $scope.showToast('Group created successfully!', 'success');
        });
    };

    $scope.deleteGroup = function(id) {
        if (confirm('Are you sure you want to delete this group?')) {
            $http.delete('/api/groups/' + id).then(function() {
                $scope.loadGroups();
                $scope.showToast('Group deleted', 'success');
            });
        }
    };

    $scope.getDashboardName = function(id) {
        var dashboard = $scope.dashboards.find(function(d) { return d.id === id; });
        return dashboard ? dashboard.name : 'Unknown';
    };

    // Initialize app
    $scope.init();

    // Handle drag and drop
    document.addEventListener('dragover', function(e) {
        e.preventDefault();
    });

    document.addEventListener('drop', function(e) {
        e.preventDefault();
        if ($scope.currentView === 'upload' && e.dataTransfer.files.length > 0) {
            $scope.$apply(function() {
                $scope.uploadFile(e.dataTransfer.files[0]);
            });
        }
    });
}]);

// Directive for rendering charts
app.directive('chartRender', function() {
    return {
        restrict: 'A',
        scope: {
            chartData: '='
        },
        link: function(scope, element, attrs) {
            // Chart rendering is handled by the controller
        }
    };
});
