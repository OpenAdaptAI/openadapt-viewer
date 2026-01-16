"""Data loading and models for benchmark viewer.

This module handles loading benchmark results from directories
and provides sample data for testing the viewer.
"""

from datetime import datetime, timedelta
from pathlib import Path
import random

from openadapt_viewer.core.types import (
    BenchmarkRun,
    BenchmarkTask,
    TaskExecution,
    ExecutionStep,
)
from openadapt_viewer.core.data_loader import DataLoader


def load_benchmark_data(data_path: Path | str) -> BenchmarkRun:
    """Load benchmark data from a directory.

    Args:
        data_path: Path to the benchmark results directory

    Returns:
        BenchmarkRun with all tasks and executions loaded
    """
    return DataLoader.load_benchmark_run(data_path)


def create_sample_data(num_tasks: int = 10) -> BenchmarkRun:
    """Create sample benchmark data for testing/demo purposes.

    Args:
        num_tasks: Number of sample tasks to generate

    Returns:
        BenchmarkRun with synthetic data
    """
    domains = ["office", "browser", "system", "file_management", "communication"]
    difficulties = ["easy", "medium", "hard"]

    instructions = [
        "Open Notepad and type 'Hello World'",
        "Navigate to google.com in Chrome",
        "Create a new folder named 'Test' on the Desktop",
        "Open the Windows Settings app",
        "Compose a new email in Outlook",
        "Calculate 2+2 in Calculator",
        "Open File Explorer and navigate to Documents",
        "Change the desktop wallpaper",
        "Open Task Manager and check CPU usage",
        "Create a new text document and save it",
        "Open PowerPoint and create a blank presentation",
        "Navigate to a URL and bookmark it",
        "Open the Control Panel",
        "Take a screenshot and save it",
        "Open Word and create a bullet list",
    ]

    tasks = []
    executions = []
    start_time = datetime.now() - timedelta(hours=2)

    for i in range(num_tasks):
        task_id = f"task_{i+1:03d}"
        domain = random.choice(domains)
        instruction = random.choice(instructions)

        task = BenchmarkTask(
            task_id=task_id,
            instruction=instruction,
            domain=domain,
            difficulty=random.choice(difficulties),
            time_limit=300,
            metadata={"source": "synthetic"},
        )
        tasks.append(task)

        # Create execution with random success/failure
        success = random.random() > 0.3  # 70% success rate
        num_steps = random.randint(3, 8)
        task_start = start_time + timedelta(minutes=i * 5)

        steps = []
        for j in range(num_steps):
            action_type = random.choice(["click", "type", "scroll", "wait"])
            step = ExecutionStep(
                step_number=j,
                timestamp=task_start + timedelta(seconds=j * 2),
                screenshot_path=f"tasks/{task_id}/screenshots/step_{j:03d}.png",
                action_type=action_type,
                action_details={
                    "click": {"x": random.randint(100, 1800), "y": random.randint(100, 900)},
                    "type": {"text": "sample text"},
                    "scroll": {"direction": "down", "amount": 100},
                    "wait": {"duration": 1.0},
                }.get(action_type, {}),
                reasoning=f"Step {j+1}: Performing {action_type} to complete the task",
                raw_output=f"Action: {action_type.upper()}(...)",
            )
            steps.append(step)

        execution = TaskExecution(
            task_id=task_id,
            start_time=task_start,
            end_time=task_start + timedelta(seconds=num_steps * 2 + random.randint(5, 30)),
            steps=steps,
            success=success,
            error=None if success else "Task failed: Could not locate target element",
        )
        executions.append(execution)

    return BenchmarkRun(
        run_id="sample_run_001",
        benchmark_name="Sample Benchmark",
        model_id="sample-agent-v1",
        start_time=start_time,
        end_time=datetime.now(),
        tasks=tasks,
        executions=executions,
        config={
            "max_steps": 10,
            "timeout": 300,
            "source": "synthetic_sample",
        },
    )
