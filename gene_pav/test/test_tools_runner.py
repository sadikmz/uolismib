#!/usr/bin/env python3
"""
Tests for tools_runner.py module.

Tests the ToolsRunner class and ExternalTool interface.
Note: Tests that require external tools (DIAMOND, InterProScan, etc.)
are marked as integration tests and skipped by default.
"""

import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from tools_runner import ToolsRunner, ExternalTool


class TestToolsRunner(unittest.TestCase):
    """Tests for ToolsRunner class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.test_dir, "output")
        self.temp_dir = os.path.join(self.test_dir, "tmp")

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_init_creates_directories(self):
        """Test that ToolsRunner creates output and temp directories."""
        runner = ToolsRunner(
            output_dir=self.output_dir,
            temp_dir=self.temp_dir
        )
        self.assertTrue(os.path.exists(self.output_dir))
        self.assertTrue(os.path.exists(self.temp_dir))

    def test_init_dry_run_mode(self):
        """Test dry_run mode initialization."""
        runner = ToolsRunner(
            output_dir=self.output_dir,
            dry_run=True
        )
        self.assertTrue(runner.dry_run)

    def test_output_dir_path_object(self):
        """Test that output_dir is converted to Path object."""
        runner = ToolsRunner(output_dir=self.output_dir)
        self.assertIsInstance(runner.output_dir, Path)

    def test_temp_dir_path_object(self):
        """Test that temp_dir is converted to Path object."""
        runner = ToolsRunner(
            output_dir=self.output_dir,
            temp_dir=self.temp_dir
        )
        self.assertIsInstance(runner.temp_dir, Path)


class TestExternalToolInterface(unittest.TestCase):
    """Tests for ExternalTool abstract base class."""

    def test_external_tool_is_abstract(self):
        """Test that ExternalTool cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            ExternalTool()

    def test_concrete_tool_must_implement_name(self):
        """Test that concrete tools must implement name property."""
        class IncompleteTool(ExternalTool):
            @property
            def executable(self):
                return "test"

            def run(self, *args, **kwargs):
                pass

            def parse_output(self, output_path):
                pass

        with self.assertRaises(TypeError):
            IncompleteTool()

    def test_concrete_tool_must_implement_executable(self):
        """Test that concrete tools must implement executable property."""
        class IncompleteTool(ExternalTool):
            @property
            def name(self):
                return "test"

            def run(self, *args, **kwargs):
                pass

            def parse_output(self, output_path):
                pass

        with self.assertRaises(TypeError):
            IncompleteTool()

    def test_concrete_tool_implementation(self):
        """Test that a properly implemented tool can be instantiated."""
        class CompleteTool(ExternalTool):
            @property
            def name(self):
                return "test_tool"

            @property
            def executable(self):
                return "echo"  # echo is available on most systems

            def run(self, *args, **kwargs):
                return "output"

            def parse_output(self, output_path):
                return {}

        tool = CompleteTool()
        self.assertEqual(tool.name, "test_tool")
        self.assertEqual(tool.executable, "echo")

    def test_check_installed_with_existing_command(self):
        """Test check_installed returns True for existing commands."""
        class EchoTool(ExternalTool):
            @property
            def name(self):
                return "echo"

            @property
            def executable(self):
                return "echo"

            def run(self, *args, **kwargs):
                pass

            def parse_output(self, output_path):
                pass

        tool = EchoTool()
        # echo should be available on all systems
        self.assertTrue(tool.check_installed())

    def test_check_installed_with_nonexistent_command(self):
        """Test check_installed returns False for nonexistent commands."""
        class FakeTool(ExternalTool):
            @property
            def name(self):
                return "fake"

            @property
            def executable(self):
                return "this_command_definitely_does_not_exist_12345"

            def run(self, *args, **kwargs):
                pass

            def parse_output(self, output_path):
                pass

        tool = FakeTool()
        self.assertFalse(tool.check_installed())


if __name__ == '__main__':
    unittest.main()
