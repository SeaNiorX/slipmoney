// static/js/dashboard-charts.js - Chart.js setup for Dashboard

document.addEventListener('DOMContentLoaded', () => {
    // 1. Monthly Trend Chart (Income vs Expense)
    const monthlyCanvas = document.getElementById('monthlyTrendChart');
    if (monthlyCanvas && window.chartMonthlyData) {
        const labels = window.chartMonthlyData.map(d => d.month);
        const incomeData = window.chartMonthlyData.map(d => d.income);
        const expenseData = window.chartMonthlyData.map(d => d.expense);

        // If no data, supply current month dummy so chart looks great
        const displayLabels = labels.length > 0 ? labels : ['Current'];
        const displayIncome = labels.length > 0 ? incomeData : [0];
        const displayExpense = labels.length > 0 ? expenseData : [0];

        new Chart(monthlyCanvas, {
            type: 'bar',
            data: {
                labels: displayLabels,
                datasets: [
                    {
                        label: window.langIncomeText || 'Income',
                        data: displayIncome,
                        backgroundColor: '#10b981',
                        borderRadius: 6,
                        maxBarThickness: 32
                    },
                    {
                        label: window.langExpenseText || 'Expense',
                        data: displayExpense,
                        backgroundColor: '#ef4444',
                        borderRadius: 6,
                        maxBarThickness: 32
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            font: { family: "'Plus Jakarta Sans', 'Prompt', sans-serif", weight: '600' },
                            usePointStyle: true,
                            boxWidth: 8
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) label += ': ';
                                if (context.parsed.y !== null) {
                                    label += (window.currencySymbol || '฿') + Number(context.parsed.y).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: "'Plus Jakarta Sans', 'Prompt', sans-serif" } }
                    },
                    y: {
                        border: { dash: [4, 4] },
                        grid: { color: '#f1f5f9' },
                        ticks: {
                            font: { family: "'Plus Jakarta Sans', 'Prompt', sans-serif" },
                            callback: function(value) {
                                return (window.currencySymbol || '฿') + Number(value).toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    // 2. Expense by Category Doughnut Chart
    const categoryCanvas = document.getElementById('categoryPieChart');
    if (categoryCanvas && window.chartCategoryLabels && window.chartCategoryLabels.length > 0) {
        const colors = [
            '#4f46e5', '#06b6d4', '#f59e0b', '#ec4899', 
            '#8b5cf6', '#10b981', '#64748b'
        ];

        new Chart(categoryCanvas, {
            type: 'doughnut',
            data: {
                labels: window.chartCategoryLabels,
                datasets: [{
                    data: window.chartCategoryValues,
                    backgroundColor: colors.slice(0, window.chartCategoryLabels.length),
                    borderWidth: 2,
                    borderColor: '#ffffff',
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '68%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            font: { family: "'Plus Jakarta Sans', 'Prompt', sans-serif", weight: '500' },
                            usePointStyle: true,
                            boxWidth: 8,
                            padding: 12
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.label || '';
                                if (label) label += ': ';
                                if (context.raw !== null) {
                                    label += (window.currencySymbol || '฿') + Number(context.raw).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                                }
                                return label;
                            }
                        }
                    }
                }
            }
        });
    }
});
