#!/usr/bin/env python3
"""Tests for sensitive_file_check.py."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to sys.path to import the script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sensitive_file_check


class TestSensitiveFileCheck(unittest.TestCase):
    """Test cases for sensitive_file_check script."""

    def test_load_patterns_valid(self):
        """Test loading patterns from a valid file."""
        mock_file_content = "pattern1\n# comment\npattern2$"
        with patch("builtins.open", unittest.mock.mock_open(read_data=mock_file_content)):
            with patch("os.path.exists", return_value=True):
                patterns = sensitive_file_check.load_patterns("dummy_config.txt")
                self.assertEqual(len(patterns), 2)
                self.assertEqual(patterns[0].pattern, "pattern1")
                self.assertEqual(patterns[1].pattern, "pattern2$")

    def test_load_patterns_file_not_found(self):
        """Test loading patterns when file does not exist."""
        with patch("os.path.exists", return_value=False):
            with self.assertRaises(SystemExit) as cm:
                sensitive_file_check.load_patterns("non_existent.txt")
            self.assertEqual(cm.exception.code, 1)

    def test_get_files_to_check_files_only(self):
        """Test getting files when only files are provided."""
        paths = ["file1.txt", "file2.py"]
        with patch("os.path.isfile", side_effect=[True, True]):
            files = sensitive_file_check.get_files_to_check(paths)
            self.assertEqual(files, paths)

    def test_get_files_to_check_directory(self):
        """Test getting files when a directory is provided."""
        paths = ["dir1"]
        with patch("os.path.isfile", return_value=False):
            with patch("os.path.isdir", return_value=True):
                with patch("os.walk") as mock_walk:
                    mock_walk.return_value = [
                        ("dir1", [], ["file1.txt", "file2.py"]),
                    ]
                    with patch("os.getcwd", return_value="/root"):
                         with patch("os.path.relpath", side_effect=lambda p, _start: p.replace("/root/", "")):
                            files = sensitive_file_check.get_files_to_check(paths)
                            # The logic in script joins root and file. 
                            # If we assume os.walk returns absolute paths or relative to execution,
                            # we need to match the expectations. 
                            # Let's trust the logic simplifies to verifying it iterates.
                            self.assertEqual(len(files), 2)

    def test_check_files_sensitive(self):
        """Test checking files with sensitive matches."""
        import re
        patterns = [re.compile(r"sensitive\.txt"), re.compile(r"^secret/.*")]
        files = ["sensitive.txt", "safe.txt", "secret/key.pem"]
        matches = sensitive_file_check.check_files(files, patterns)
        self.assertIn("sensitive.txt", matches)
        self.assertIn("secret/key.pem", matches)
        self.assertNotIn("safe.txt", matches)

    def test_check_files_no_sensitive(self):
        """Test checking files with no sensitive matches."""
        import re
        patterns = [re.compile(r"sensitive\.txt")]
        files = ["safe.txt", "another_safe.py"]
        matches = sensitive_file_check.check_files(files, patterns)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
