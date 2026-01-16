"""HTML generator for benchmark viewer.

This module generates standalone HTML files for visualizing
benchmark evaluation results with interactive features.
"""

import json
from pathlib import Path
from typing import Optional

from openadapt_viewer.core.html_builder import HTMLBuilder
from openadapt_viewer.core.types import BenchmarkRun
from openadapt_viewer.viewers.benchmark.data import load_benchmark_data, create_sample_data


def generate_benchmark_html(
    data_path: Optional[Path | str] = None,
    output_path: Path | str = "benchmark_viewer.html",
    standalone: bool = False,
    run_data: Optional[BenchmarkRun] = None,
) -> str:
    """Generate a standalone HTML viewer for benchmark results.

    Args:
        data_path: Path to benchmark results directory (optional if run_data provided)
        output_path: Where to write the HTML file
        standalone: If True, embed Plotly.js for offline viewing
        run_data: Pre-loaded BenchmarkRun data (optional, will load from data_path if not provided)

    Returns:
        Path to the generated HTML file
    """
    # Load data
    if run_data is not None:
        run = run_data
    elif data_path is not None:
        run = load_benchmark_data(data_path)
    else:
        # Create sample data for demo
        run = create_sample_data()

    # Generate HTML using template
    builder = HTMLBuilder()
    html = _generate_viewer_html(builder, run, standalone)

    # Write to file
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)

    return str(output_path)


def _generate_viewer_html(builder: HTMLBuilder, run: BenchmarkRun, standalone: bool) -> str:
    """Generate the complete HTML for the benchmark viewer.

    Uses inline template since this is specific to the benchmark viewer.
    """
    # Prepare data for template
    domain_stats = run.get_domain_stats()

    # Convert run data to JSON-serializable format
    tasks_data = []
    for task in run.tasks:
        # Find corresponding execution
        execution = next((e for e in run.executions if e.task_id == task.task_id), None)
        tasks_data.append({
            "task_id": task.task_id,
            "instruction": task.instruction,
            "domain": task.domain or "unknown",
            "difficulty": task.difficulty or "unknown",
            "success": execution.success if execution else False,
            "steps": [
                {
                    "step_number": s.step_number,
                    "action_type": s.action_type,
                    "action_details": s.action_details,
                    "reasoning": s.reasoning,
                    "screenshot_path": s.screenshot_path,
                }
                for s in (execution.steps if execution else [])
            ],
            "error": execution.error if execution else None,
        })

    # Inline template for benchmark viewer
    template = _get_benchmark_template()

    return builder.render_inline(
        template,
        run=run,
        tasks_data=tasks_data,
        domain_stats=domain_stats,
        standalone=standalone,
    )


def _get_benchmark_template() -> str:
    """Return the Jinja2 template for the benchmark viewer."""
    return '''<!DOCTYPE html>
<html lang="en" x-data="benchmarkViewer()" x-init="init()" :class="{ 'dark': darkMode }">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Benchmark Viewer - {{ run.benchmark_name }}</title>

    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        primary: {
                            50: '#eff6ff', 100: '#dbeafe', 200: '#bfdbfe', 300: '#93c5fd',
                            400: '#60a5fa', 500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8',
                            800: '#1e40af', 900: '#1e3a8a',
                        }
                    }
                }
            }
        }
    </script>

    <!-- Alpine.js -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>

    <style>
        [x-cloak] { display: none !important; }
        .screenshot-container { aspect-ratio: 16/9; }
    </style>
</head>
<body class="bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 min-h-screen">

    <!-- Header -->
    <header class="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div class="container mx-auto px-4 py-3 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <svg class="w-8 h-8 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <div>
                    <h1 class="text-xl font-semibold">{{ run.benchmark_name }}</h1>
                    <p class="text-sm text-gray-500 dark:text-gray-400">Model: {{ run.model_id }}</p>
                </div>
            </div>
            <button @click="darkMode = !darkMode; localStorage.setItem('darkMode', darkMode)"
                    class="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600">
                <svg x-show="darkMode" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
                <svg x-show="!darkMode" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
            </button>
        </div>
    </header>

    <main class="container mx-auto px-4 py-6">
        <!-- Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                <div class="text-sm text-gray-500 dark:text-gray-400">Total Tasks</div>
                <div class="text-2xl font-bold">{{ run.total_tasks }}</div>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                <div class="text-sm text-gray-500 dark:text-gray-400">Passed</div>
                <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ run.passed_tasks }}</div>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                <div class="text-sm text-gray-500 dark:text-gray-400">Failed</div>
                <div class="text-2xl font-bold text-red-600 dark:text-red-400">{{ run.failed_tasks }}</div>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                <div class="text-sm text-gray-500 dark:text-gray-400">Success Rate</div>
                <div class="text-2xl font-bold text-primary-600 dark:text-primary-400">{{ "%.1f" | format(run.success_rate * 100) }}%</div>
            </div>
        </div>

        <!-- Domain Breakdown -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
            <h2 class="text-lg font-semibold mb-3">Results by Domain</h2>
            <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
                {% for domain, stats in domain_stats.items() %}
                <div class="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div class="text-sm font-medium capitalize">{{ domain }}</div>
                    <div class="flex items-center space-x-2 mt-1">
                        <span class="text-green-600 dark:text-green-400">{{ stats.passed }}</span>
                        <span class="text-gray-400">/</span>
                        <span class="text-gray-600 dark:text-gray-300">{{ stats.total }}</span>
                        <span class="text-xs text-gray-500">({{ "%.0f" | format(stats.passed / stats.total * 100 if stats.total > 0 else 0) }}%)</span>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Filters -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
            <div class="flex flex-wrap gap-4">
                <div>
                    <label class="block text-sm font-medium mb-1">Domain</label>
                    <select x-model="filterDomain" class="px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 dark:border-gray-600">
                        <option value="">All Domains</option>
                        {% for domain in domain_stats.keys() %}
                        <option value="{{ domain }}">{{ domain | capitalize }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Status</label>
                    <select x-model="filterStatus" class="px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 dark:border-gray-600">
                        <option value="">All</option>
                        <option value="passed">Passed</option>
                        <option value="failed">Failed</option>
                    </select>
                </div>
            </div>
        </div>

        <!-- Task List and Detail View -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Task List -->
            <div class="lg:col-span-1 bg-white dark:bg-gray-800 rounded-lg shadow">
                <div class="p-4 border-b border-gray-200 dark:border-gray-700">
                    <h2 class="font-semibold">Tasks</h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400" x-text="'Showing ' + filteredTasks.length + ' of ' + tasks.length"></p>
                </div>
                <div class="max-h-[600px] overflow-y-auto">
                    <template x-for="task in filteredTasks" :key="task.task_id">
                        <div @click="selectTask(task)"
                             :class="{'bg-primary-50 dark:bg-primary-900/20 border-l-4 border-primary-500': selectedTask?.task_id === task.task_id}"
                             class="p-3 border-b border-gray-100 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50">
                            <div class="flex items-start justify-between">
                                <div class="flex-1 min-w-0">
                                    <div class="font-medium truncate" x-text="task.task_id"></div>
                                    <div class="text-sm text-gray-500 dark:text-gray-400 truncate" x-text="task.instruction"></div>
                                </div>
                                <span :class="task.success ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'"
                                      class="ml-2 px-2 py-0.5 text-xs font-medium rounded-full"
                                      x-text="task.success ? 'Pass' : 'Fail'"></span>
                            </div>
                        </div>
                    </template>
                </div>
            </div>

            <!-- Detail View -->
            <div class="lg:col-span-2 bg-white dark:bg-gray-800 rounded-lg shadow">
                <template x-if="selectedTask">
                    <div>
                        <div class="p-4 border-b border-gray-200 dark:border-gray-700">
                            <div class="flex items-center justify-between">
                                <h2 class="font-semibold" x-text="selectedTask.task_id"></h2>
                                <span :class="selectedTask.success ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'"
                                      class="px-3 py-1 text-sm font-medium rounded-full"
                                      x-text="selectedTask.success ? 'Passed' : 'Failed'"></span>
                            </div>
                            <p class="mt-2 text-gray-600 dark:text-gray-300" x-text="selectedTask.instruction"></p>
                            <div class="mt-2 flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                                <span x-text="'Domain: ' + selectedTask.domain"></span>
                                <span x-text="'Difficulty: ' + selectedTask.difficulty"></span>
                                <span x-text="'Steps: ' + selectedTask.steps.length"></span>
                            </div>
                            <template x-if="selectedTask.error">
                                <div class="mt-2 p-2 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 rounded text-sm" x-text="selectedTask.error"></div>
                            </template>
                        </div>

                        <!-- Step Viewer -->
                        <div class="p-4" x-show="selectedTask.steps.length > 0">
                            <!-- Step Navigation -->
                            <div class="flex items-center justify-between mb-4">
                                <div class="flex items-center space-x-2">
                                    <button @click="prevStep()" :disabled="currentStep === 0"
                                            class="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded disabled:opacity-50">Prev</button>
                                    <span class="text-sm" x-text="'Step ' + (currentStep + 1) + ' of ' + selectedTask.steps.length"></span>
                                    <button @click="nextStep()" :disabled="currentStep >= selectedTask.steps.length - 1"
                                            class="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded disabled:opacity-50">Next</button>
                                </div>
                                <div class="flex items-center space-x-2">
                                    <button @click="togglePlayback()"
                                            class="px-3 py-1 bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 rounded">
                                        <span x-text="isPlaying ? 'Pause' : 'Play'"></span>
                                    </button>
                                    <select x-model="playbackSpeed" class="px-2 py-1 text-sm border rounded bg-white dark:bg-gray-700 dark:border-gray-600">
                                        <option value="0.5">0.5x</option>
                                        <option value="1">1x</option>
                                        <option value="2">2x</option>
                                        <option value="4">4x</option>
                                    </select>
                                </div>
                            </div>

                            <!-- Progress Bar -->
                            <div class="mb-4">
                                <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                    <div class="h-full bg-primary-500 transition-all duration-200"
                                         :style="'width: ' + ((currentStep + 1) / selectedTask.steps.length * 100) + '%'"></div>
                                </div>
                            </div>

                            <!-- Current Step -->
                            <template x-if="selectedTask.steps[currentStep]">
                                <div>
                                    <div class="screenshot-container bg-gray-100 dark:bg-gray-700 rounded-lg mb-4 flex items-center justify-center">
                                        <template x-if="selectedTask.steps[currentStep].screenshot_path">
                                            <img :src="selectedTask.steps[currentStep].screenshot_path"
                                                 class="max-w-full max-h-full object-contain rounded"
                                                 alt="Screenshot">
                                        </template>
                                        <template x-if="!selectedTask.steps[currentStep].screenshot_path">
                                            <div class="text-gray-400">No screenshot available</div>
                                        </template>
                                    </div>
                                    <div class="space-y-2">
                                        <div class="flex items-center space-x-2">
                                            <span class="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-sm font-medium"
                                                  x-text="selectedTask.steps[currentStep].action_type.toUpperCase()"></span>
                                            <span class="text-sm text-gray-500" x-text="JSON.stringify(selectedTask.steps[currentStep].action_details)"></span>
                                        </div>
                                        <template x-if="selectedTask.steps[currentStep].reasoning">
                                            <div class="p-3 bg-gray-50 dark:bg-gray-700 rounded text-sm">
                                                <div class="font-medium mb-1">Reasoning:</div>
                                                <div class="text-gray-600 dark:text-gray-300" x-text="selectedTask.steps[currentStep].reasoning"></div>
                                            </div>
                                        </template>
                                    </div>
                                </div>
                            </template>
                        </div>

                        <div class="p-4 text-center text-gray-500" x-show="selectedTask.steps.length === 0">
                            No steps recorded for this task
                        </div>
                    </div>
                </template>

                <div x-show="!selectedTask" class="p-8 text-center text-gray-500 dark:text-gray-400">
                    Select a task from the list to view details
                </div>
            </div>
        </div>
    </main>

    <footer class="container mx-auto px-4 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
        Generated by <a href="https://github.com/OpenAdaptAI/openadapt-viewer" class="text-primary-600 dark:text-primary-400 hover:underline">openadapt-viewer</a>
    </footer>

    <script>
        function benchmarkViewer() {
            return {
                darkMode: localStorage.getItem('darkMode') === 'true',
                tasks: {{ tasks_data | tojson_safe }},
                selectedTask: null,
                currentStep: 0,
                isPlaying: false,
                playbackSpeed: 1,
                playbackInterval: null,
                filterDomain: '',
                filterStatus: '',

                init() {
                    // Auto-select first task if available
                    if (this.filteredTasks.length > 0) {
                        this.selectTask(this.filteredTasks[0]);
                    }
                },

                get filteredTasks() {
                    return this.tasks.filter(task => {
                        if (this.filterDomain && task.domain !== this.filterDomain) return false;
                        if (this.filterStatus === 'passed' && !task.success) return false;
                        if (this.filterStatus === 'failed' && task.success) return false;
                        return true;
                    });
                },

                selectTask(task) {
                    this.selectedTask = task;
                    this.currentStep = 0;
                    this.stopPlayback();
                },

                prevStep() {
                    if (this.currentStep > 0) this.currentStep--;
                },

                nextStep() {
                    if (this.selectedTask && this.currentStep < this.selectedTask.steps.length - 1) {
                        this.currentStep++;
                    }
                },

                togglePlayback() {
                    if (this.isPlaying) {
                        this.stopPlayback();
                    } else {
                        this.startPlayback();
                    }
                },

                startPlayback() {
                    this.isPlaying = true;
                    const interval = 1000 / this.playbackSpeed;
                    this.playbackInterval = setInterval(() => {
                        if (this.selectedTask && this.currentStep < this.selectedTask.steps.length - 1) {
                            this.currentStep++;
                        } else {
                            this.stopPlayback();
                        }
                    }, interval);
                },

                stopPlayback() {
                    this.isPlaying = false;
                    if (this.playbackInterval) {
                        clearInterval(this.playbackInterval);
                        this.playbackInterval = null;
                    }
                }
            }
        }
    </script>
</body>
</html>'''
