#!/usr/bin/env python3
"""
Script to generate Failure Context entities from GitHub Actions run data.

This script:
1. Reads run data from data/filtered_output/
2. Reads repository structures from data/repo_structures/
3. Identifies failed jobs and steps
4. Creates GHFailureContext entities
5. Serializes them to data/failure_contexts/ as JSON

Usage:
    python scripts/generate_failure_contexts.py
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict

# Add parent directory to path to import domain modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from domain import (
    GHRun,
    GHRunAttempt,
    GHJob,
    GHStep,
    GHRepository,
    GHFailureContext,
)


def load_json_file(file_path: Path) -> Optional[Dict]:
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def load_log_file(log_path: Path, base_path: Path) -> Optional[str]:
    """Load a log file content."""
    try:
        full_path = base_path / log_path
        if full_path.exists():
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    except Exception as e:
        print(f"Warning: Could not load log {log_path}: {e}")
    return None


def find_repository_structure(repo_full_name: str, repo_structures_dir: Path) -> Optional[Dict]:
    """Find and load the repository structure file for a given repository."""
    # Convert repo name like "django/django" to "django_django"
    repo_slug = repo_full_name.replace("/", "_")

    # Find matching structure file
    for file_path in repo_structures_dir.glob(f"{repo_slug}_structure_*.json"):
        data = load_json_file(file_path)
        if data:
            return data

    print(f"Warning: Repository structure not found for {repo_full_name}")
    return None


def find_failed_step(job: GHJob) -> Optional[GHStep]:
    """Find the first failed step in a job."""
    for step in job.steps:
        if step.conclusion == "failure":
            return step
    return None


def create_failure_contexts_from_run(
    run_data: Dict,
    repo_structure_data: Optional[Dict],
    data_base_path: Path
) -> List[GHFailureContext]:
    """Create FailureContext entities from a run data file."""
    failure_contexts = []

    try:
        # Parse the run
        run = GHRun.from_dict(run_data)

        # Parse repository if available
        repository = None
        if repo_structure_data:
            repository = GHRepository.from_dict(repo_structure_data)
        elif "repository" in run_data:
            # Try to create a basic repository from the run data
            try:
                repository = GHRepository.from_dict(run_data)
            except Exception as e:
                print(f"Warning: Could not parse repository from run data: {e}")

        # Process each attempt
        for attempt in run.attempts:
            # Process each job in the attempt
            for job in attempt.jobs:
                # Only process failed jobs
                if job.conclusion != "failure":
                    continue

                # Find the failed step
                failed_step = find_failed_step(job)

                # Get log path (not content)
                full_log_path = None
                if failed_step and failed_step.log_file_path:
                    full_log_path = failed_step.log_file_path
                elif job.full_log_path:
                    full_log_path = job.full_log_path

                # Create the failure context
                failure_context = GHFailureContext(
                    run=run,
                    attempt=attempt,
                    job=job,
                    failed_step=failed_step,
                    commit=run.commit,
                    repository=repository,
                    workflow=run.workflow,
                    actor=run.actor,
                    full_log_path=full_log_path,
                )

                failure_contexts.append(failure_context)
                print(f"  Created failure context for job: {job.name}")

    except Exception as e:
        print(f"Error creating failure contexts: {e}")
        import traceback
        traceback.print_exc()

    return failure_contexts


def main():
    """Main function to generate failure contexts."""
    # Set up paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    filtered_output_dir = data_dir / "filtered_output"
    repo_structures_dir = data_dir / "repo_structures"
    output_dir = data_dir / "failure_contexts"

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    print("=" * 80)
    print("Generating Failure Contexts")
    print("=" * 80)
    print()

    # Track statistics
    total_runs = 0
    total_failures = 0
    all_failure_contexts = []

    # Process each repository directory
    for repo_dir in sorted(filtered_output_dir.iterdir()):
        if not repo_dir.is_dir():
            continue

        repo_name = repo_dir.name.replace("_", "/")
        print(f"\nProcessing repository: {repo_name}")
        print("-" * 80)

        # Load repository structure
        repo_structure = find_repository_structure(repo_name, repo_structures_dir)

        # Process each run file
        for run_file in sorted(repo_dir.glob("*.json")):
            total_runs += 1
            print(f"\nProcessing: {run_file.name}")

            # Load run data
            run_data = load_json_file(run_file)
            if not run_data:
                continue

            # Create failure contexts
            failure_contexts = create_failure_contexts_from_run(
                run_data,
                repo_structure,
                data_dir
            )

            total_failures += len(failure_contexts)
            all_failure_contexts.extend(failure_contexts)

    print()
    print("=" * 80)
    print("Serializing Failure Contexts")
    print("=" * 80)
    print()

    # Serialize each failure context
    for i, fc in enumerate(all_failure_contexts):
        # Create filename based on the failure context
        filename = f"{fc.run_identifier}.json"
        output_path = output_dir / filename

        try:
            # Serialize to JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(fc.to_dict(), f, indent=2, ensure_ascii=False)

            print(f"[{i+1}/{len(all_failure_contexts)}] Saved: {filename}")

        except Exception as e:
            print(f"Error serializing {filename}: {e}")
            import traceback
            traceback.print_exc()

    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Total runs processed: {total_runs}")
    print(f"Total failure contexts created: {total_failures}")
    print(f"Output directory: {output_dir}")
    print()

    # Test deserialization with first context
    if all_failure_contexts:
        print("Testing deserialization with first context...")
        try:
            first_fc = all_failure_contexts[0]
            serialized = first_fc.to_dict()
            deserialized = GHFailureContext.from_dict(serialized)
            print("✓ Deserialization successful!")
            print()
            print("Sample Failure Summary:")
            print("-" * 80)
            print(deserialized.get_failure_summary())
        except Exception as e:
            print(f"✗ Deserialization failed: {e}")
            import traceback
            traceback.print_exc()

    print()
    print("Done!")


if __name__ == "__main__":
    main()
