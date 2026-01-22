#!/usr/bin/env python3
"""Script to detect sensitive files based on regex patterns."""

import argparse
import os
import re
import sys


def load_patterns(config_file):
    """Load regex patterns from a configuration file.

    Args:
        config_file (str): Path to the configuration file containing regex
            patterns.

    Returns:
        list: A list of compiled regex objects.

    """
    patterns = []
    if not os.path.exists(config_file):
        print(f"Error: Configuration file '{config_file}' not found.")
        sys.exit(1)

    try:
        with open(config_file, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        patterns.append(re.compile(line))
                    except re.error as error:
                        print(f"Error compiling regex '{line}': {error}")
                        sys.exit(1)
    except Exception as error:  # pylint: disable=broad-except
        print(f"Error reading configuration file: {error}")
        sys.exit(1)

    return patterns


def get_files_to_check(paths):
    """Retrieve all files to check from the provided paths.

    If a path is a directory, it will be traversed recursively.

    Args:
        paths (list): List of file or directory paths.

    Returns:
        list: A list of file paths relative to the current working directory.

    """
    files_to_check = []
    for path in paths:
        if os.path.isfile(path):
            files_to_check.append(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    full_path = os.path.join(root, file)
                    # Normalize path to be relative to CWD if possible
                    rel_path = os.path.relpath(full_path, os.getcwd())
                    files_to_check.append(rel_path)
        else:
            # If path doesn't exist, we assume it's a file path that was
            # deleted or it's just a string pattern being passed (like from
            # git diff output)
            # In the context of git diff --name-only, these are paths
            # relative to root
            files_to_check.append(path)

    return files_to_check


def check_files(files, patterns):
    """Check files against a list of sensitive patterns.

    Args:
        files (list): List of file paths to check.
        patterns (list): List of compiled regex objects.

    Returns:
        list: A list of matching file paths.

    """
    matches = []
    for file_path in files:
        for pattern in patterns:
            if pattern.search(file_path):
                matches.append(file_path)
                break
    return matches


def main():
    """Execute the sensitive file check."""
    parser = argparse.ArgumentParser(
        description="Check for sensitive file changes based on regex patterns."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the configuration file containing regex patterns.",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="List of files or directories to check.",
    )

    args = parser.parse_args()

    patterns = load_patterns(args.config)
    files = get_files_to_check(args.files)
    sensitive_files = check_files(files, patterns)

    if sensitive_files:
        print("Unauthorized changes detected in sensitive files:")
        for file in sensitive_files:
            print(f"- {file}")
        sys.exit(1)
    else:
        print("No sensitive files detected.")
        sys.exit(0)


if __name__ == "__main__":
    main()
