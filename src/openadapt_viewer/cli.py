"""Command-line interface for openadapt-viewer.

Usage:
    openadapt-viewer benchmark --data DIR [--output FILE] [--standalone]
    openadapt-viewer demo [--output FILE]
"""

import argparse
import sys
import webbrowser
from pathlib import Path

from openadapt_viewer.viewers.benchmark import generate_benchmark_html


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Generate standalone HTML viewers for OpenAdapt ML results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate benchmark viewer from results directory
    openadapt-viewer benchmark --data benchmark_results/run_001/

    # Generate with embedded resources (standalone)
    openadapt-viewer benchmark --data results/ --standalone

    # Generate demo viewer with sample data
    openadapt-viewer demo --output demo.html --open
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Benchmark command
    benchmark_parser = subparsers.add_parser(
        "benchmark", help="Generate a benchmark viewer"
    )
    benchmark_parser.add_argument(
        "--data",
        "-d",
        type=Path,
        help="Path to benchmark results directory",
    )
    benchmark_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("benchmark_viewer.html"),
        help="Output HTML file path (default: benchmark_viewer.html)",
    )
    benchmark_parser.add_argument(
        "--standalone",
        "-s",
        action="store_true",
        help="Embed all resources for offline viewing",
    )
    benchmark_parser.add_argument(
        "--open",
        action="store_true",
        help="Open the generated file in browser",
    )

    # Demo command
    demo_parser = subparsers.add_parser(
        "demo", help="Generate a demo viewer with sample data"
    )
    demo_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("demo_viewer.html"),
        help="Output HTML file path (default: demo_viewer.html)",
    )
    demo_parser.add_argument(
        "--tasks",
        "-n",
        type=int,
        default=10,
        help="Number of sample tasks (default: 10)",
    )
    demo_parser.add_argument(
        "--open",
        action="store_true",
        help="Open the generated file in browser",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "benchmark":
        run_benchmark_command(args)
    elif args.command == "demo":
        run_demo_command(args)


def run_benchmark_command(args):
    """Handle the benchmark command."""
    if args.data and not args.data.exists():
        print(f"Error: Data directory not found: {args.data}", file=sys.stderr)
        sys.exit(1)

    print(f"Generating benchmark viewer...")
    output_path = generate_benchmark_html(
        data_path=args.data,
        output_path=args.output,
        standalone=args.standalone,
    )
    print(f"Generated: {output_path}")

    if args.open:
        webbrowser.open(f"file://{Path(output_path).absolute()}")


def run_demo_command(args):
    """Handle the demo command."""
    from openadapt_viewer.viewers.benchmark.data import create_sample_data

    print(f"Generating demo viewer with {args.tasks} sample tasks...")
    run_data = create_sample_data(num_tasks=args.tasks)

    output_path = generate_benchmark_html(
        output_path=args.output,
        standalone=False,
        run_data=run_data,
    )
    print(f"Generated: {output_path}")

    if args.open:
        webbrowser.open(f"file://{Path(output_path).absolute()}")


if __name__ == "__main__":
    main()
