#!/usr/bin/env python3
"""
Failure Log Processing Script
===============================
Processes GitHub Actions failure contexts by grouping them by repository
and selecting the top 3 contexts per repository with the largest log files.
Organizes them in a hierarchical structure for benchmarking and analysis.

Author: Senior Python Engineer
"""

import json
import shutil
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Tuple

# ==================== CONFIGURATION ====================
TOP_N_PER_REPO = 3  # Number of largest logs to process per repository
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FAILURE_CONTEXTS_DIR = DATA_DIR / "failure_contexts"
OUTPUT_DIR = DATA_DIR / "test"
# =======================================================


def get_log_file_size(log_path: Path) -> int:
    """
    Get the size of a log file in bytes.

    Args:
        log_path: Path to the log file

    Returns:
        Size in bytes, or 0 if file doesn't exist
    """
    try:
        return log_path.stat().st_size
    except (FileNotFoundError, OSError):
        return 0


def load_failure_context(json_path: Path) -> Dict:
    """
    Load and parse a failure context JSON file.

    Args:
        json_path: Path to the JSON file

    Returns:
        Parsed JSON data as a dictionary
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_metadata(context_data: Dict) -> Dict[str, any]:
    """
    Extract key metadata from a failure context.

    Args:
        context_data: The parsed failure context JSON

    Returns:
        Dictionary with owner, repo, run_id, job_id, and full_log_path
    """
    repository = context_data.get("repository", {})
    run = context_data.get("run", {})
    job = context_data.get("job", {})

    return {
        "owner": repository.get("owner", {}).get("login", "unknown"),
        "repo": repository.get("name", "unknown"),
        "full_name": repository.get("full_name", "unknown/unknown"),
        "run_id": run.get("id"),
        "job_id": job.get("id"),
        "full_log_path": context_data.get("full_log_path", "")
    }


def construct_github_url(owner: str, repo: str, run_id: int, job_id: int) -> str:
    """
    Construct a GitHub Actions job URL.

    Args:
        owner: Repository owner
        repo: Repository name
        run_id: GitHub Actions run ID
        job_id: GitHub Actions job ID

    Returns:
        Complete GitHub URL string
    """
    return f"https://github.com/{owner}/{repo}/actions/runs/{run_id}/job/{job_id}"


def sanitize_repo_name(full_name: str) -> str:
    """
    Sanitize repository name for use as a directory name.
    Replaces forward slash with underscore.

    Args:
        full_name: Repository full name (e.g., "facebook/react")

    Returns:
        Sanitized name (e.g., "facebook_react")
    """
    return full_name.replace("/", "_")


def create_markdown_file(output_path: Path, github_url: str) -> None:
    """
    Create the gh_exp.md markdown file with the required template.

    Args:
        output_path: Path where the markdown file should be created
        github_url: The GitHub Actions URL to include
    """
    markdown_content = f"""# GitHub Actions Failure Analysis

## GitHub URL
{github_url}

## Log Analysis
<!-- TODO: Add manual analysis here -->

## Generation Time
<!-- TODO: Add generation time here -->
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)


def scan_and_group_contexts() -> Dict[str, List[Tuple[Path, Dict, int]]]:
    """
    Scan all failure contexts and group them by repository.
    Within each repository, sort by log file size (descending).

    Returns:
        Dictionary mapping repository full_name to a list of tuples
        (json_path, metadata, log_size) sorted by log_size descending
    """
    if not FAILURE_CONTEXTS_DIR.exists():
        raise FileNotFoundError(f"Failure contexts directory not found: {FAILURE_CONTEXTS_DIR}")

    # Group contexts by repository
    repo_groups = defaultdict(list)

    json_files = list(FAILURE_CONTEXTS_DIR.glob("*.json"))
    print(f"Found {len(json_files)} JSON files in {FAILURE_CONTEXTS_DIR}")

    for json_path in json_files:
        try:
            # Load the failure context
            context_data = load_failure_context(json_path)
            metadata = extract_metadata(context_data)

            # Get the log file size
            log_relative_path = metadata["full_log_path"]
            if log_relative_path:
                log_full_path = DATA_DIR / log_relative_path
                log_size = get_log_file_size(log_full_path)
            else:
                log_size = 0

            # Group by repository
            repo_key = metadata["full_name"]
            repo_groups[repo_key].append((json_path, metadata, log_size))

        except Exception as e:
            print(f"Warning: Error processing {json_path.name}: {e}")
            continue

    # Sort each repository's contexts by log size (descending)
    for repo_key in repo_groups:
        repo_groups[repo_key].sort(key=lambda x: x[2], reverse=True)

    return dict(repo_groups)


def process_context(json_path: Path, metadata: Dict, log_size: int) -> None:
    """
    Process a single failure context: create hierarchical output directory and files.

    Structure: /data/test/{owner_repo}/{run_id}_{job_id}/
                ├── failure_context.json
                └── gh_exp.md

    Args:
        json_path: Path to the source JSON file
        metadata: Extracted metadata dictionary
        log_size: Size of the log file in bytes
    """
    # Create hierarchical output directory structure
    repo_dir_name = sanitize_repo_name(metadata["full_name"])
    run_folder_name = f"{metadata['run_id']}_{metadata['job_id']}"
    output_run_dir = OUTPUT_DIR / repo_dir_name / run_folder_name
    output_run_dir.mkdir(parents=True, exist_ok=True)

    # Copy the JSON file with standardized name
    json_dest = output_run_dir / "failure_context.json"
    shutil.copy2(json_path, json_dest)
    print(f"  ✓ Copied JSON: {json_dest}")

    # Create the markdown file
    github_url = construct_github_url(
        metadata["owner"],
        metadata["repo"],
        metadata["run_id"],
        metadata["job_id"]
    )
    markdown_path = output_run_dir / "gh_exp.md"
    create_markdown_file(markdown_path, github_url)
    print(f"  ✓ Created markdown: {markdown_path}")
    print(f"  ✓ GitHub URL: {github_url}")
    print(f"  ✓ Log size: {log_size:,} bytes")


def main():
    """
    Main execution function.
    Groups contexts by repository and processes top N per repository.
    """
    print("=" * 70)
    print("Failure Log Processing Script (Repository-Grouped)")
    print("=" * 70)
    print(f"Configuration:")
    print(f"  - TOP_N_PER_REPO: {TOP_N_PER_REPO}")
    print(f"  - Project Root: {PROJECT_ROOT}")
    print(f"  - Failure Contexts: {FAILURE_CONTEXTS_DIR}")
    print(f"  - Output Directory: {OUTPUT_DIR}")
    print("=" * 70)
    print()

    # Scan and group all failure contexts by repository
    print("Scanning and grouping failure contexts by repository...")
    repo_groups = scan_and_group_contexts()

    if not repo_groups:
        print("No failure contexts found!")
        return

    print(f"\nFound {len(repo_groups)} unique repositories")
    print("-" * 70)

    # Process each repository
    total_processed = 0
    for repo_idx, (repo_name, contexts) in enumerate(sorted(repo_groups.items()), 1):
        print(f"\n[Repository {repo_idx}/{len(repo_groups)}] {repo_name}")
        print(f"  Total contexts available: {len(contexts)}")

        # Select top N contexts for this repository
        top_contexts = contexts[:TOP_N_PER_REPO]
        print(f"  Processing top {len(top_contexts)} (by log size):")
        print()

        # Process each selected context
        for ctx_idx, (json_path, metadata, log_size) in enumerate(top_contexts, 1):
            print(f"  [{ctx_idx}/{len(top_contexts)}] {json_path.name}")
            process_context(json_path, metadata, log_size)
            print()
            total_processed += 1

    print("=" * 70)
    print(f"✓ Successfully processed {total_processed} failure contexts")
    print(f"✓ Across {len(repo_groups)} repositories")
    print(f"✓ Output directory: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
