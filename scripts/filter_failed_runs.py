#!/usr/bin/env python3
"""
Script to filter GitHub Actions run JSON files.
Keeps only runs with:
1. conclusion == "failure"
2. At least one job with a non-null full_log_path
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


def has_full_log_path(run_data: Dict[str, Any]) -> bool:
    """
    Check if the run has at least one job with a non-null full_log_path.

    Args:
        run_data: The parsed JSON data of a run

    Returns:
        True if at least one job has full_log_path, False otherwise
    """
    run_attempts = run_data.get("run_attempts", [])

    for attempt in run_attempts:
        jobs = attempt.get("jobs", [])
        for job in jobs:
            full_log_path = job.get("full_log_path")
            if full_log_path is not None:
                return True

    return False


def should_keep_run(run_data: Dict[str, Any]) -> bool:
    """
    Determine if a run should be kept based on the filtering criteria.

    Args:
        run_data: The parsed JSON data of a run

    Returns:
        True if the run should be kept, False otherwise
    """
    # Check if conclusion is "failure"
    if run_data.get("conclusion") != "failure":
        return False

    # Check if at least one job has full_log_path
    if not has_full_log_path(run_data):
        return False

    return True


def filter_runs(input_dir: str, output_dir: str = None, dry_run: bool = False):
    """
    Filter run JSON files in the input directory and copy matching ones to output directory.

    Args:
        input_dir: Directory containing the run JSON files
        output_dir: Directory where filtered runs will be copied (optional)
        dry_run: If True, only print what would be done without actually copying files
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist")
        return

    # Prepare output directory if specified
    if output_dir and not dry_run:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

    total_files = 0
    matching_files = 0
    skipped_files = 0
    error_files = 0

    # Walk through all subdirectories
    for json_file in input_path.rglob("*.json"):
        # Skip summary files
        if json_file.name.endswith("_summary.json"):
            continue

        total_files += 1

        try:
            # Read and parse JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                run_data = json.load(f)

            # Check if run matches criteria
            if should_keep_run(run_data):
                matching_files += 1

                if dry_run:
                    print(f"[MATCH] {json_file.relative_to(input_path)}")
                else:
                    if output_dir:
                        # Preserve directory structure
                        relative_path = json_file.relative_to(input_path)
                        output_file = Path(output_dir) / relative_path
                        output_file.parent.mkdir(parents=True, exist_ok=True)

                        # Copy file
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(run_data, f, indent=2)

                        print(f"[COPIED] {relative_path}")
                    else:
                        print(f"[MATCH] {json_file.relative_to(input_path)}")
            else:
                skipped_files += 1

        except json.JSONDecodeError as e:
            error_files += 1
            print(f"[ERROR] Failed to parse {json_file.relative_to(input_path)}: {e}")
        except Exception as e:
            error_files += 1
            print(f"[ERROR] Failed to process {json_file.relative_to(input_path)}: {e}")

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total files processed: {total_files}")
    print(f"Matching files: {matching_files}")
    print(f"Skipped files: {skipped_files}")
    print(f"Error files: {error_files}")

    if dry_run:
        print("\nThis was a dry run. No files were copied.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Filter GitHub Actions run JSON files based on failure status and log availability"
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
        default="scripts/multi_repo_output",
        help="Input directory containing run JSON files (default: scripts/multi_repo_output)"
    )
    parser.add_argument(
        "-o", "--output",
        dest="output_dir",
        help="Output directory for filtered runs (if not specified, only lists matches)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually copying files"
    )

    args = parser.parse_args()

    filter_runs(args.input_dir, args.output_dir, args.dry_run)
