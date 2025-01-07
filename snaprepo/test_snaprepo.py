import unittest
from pathlib import Path
from click.testing import CliRunner
from main import cli, snaprepo


class Testsnaprepo(unittest.TestCase):
    def setUp(self):
        """Set up the test environment."""
        self.runner = CliRunner()
        self.test_project_path = Path("test_project")
        self.test_output_file = self.test_project_path / "output.md"
        self.test_project_path.mkdir(exist_ok=True)

        # Create test files
        (self.test_project_path / "test_file.py").write_text("print('Hello, world!')\n")
        (self.test_project_path / "test_file.md").write_text("# Test Markdown\n\nThis is a test.")
        (self.test_project_path / "test_binary.dat").write_bytes(b"\x00\x01\x02")

    def tearDown(self):
        """Clean up the test environment."""
        for item in self.test_project_path.iterdir():
            item.unlink()
        self.test_project_path.rmdir()

    def test_snap_command(self):
        """Test the snap command."""
        result = self.runner.invoke(cli, [
            "snap",
            "-p", str(self.test_project_path),
            "-o", str(self.test_output_file),
            "--summary"
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(self.test_output_file.exists())

        content = self.test_output_file.read_text()
        self.assertIn("# Project Source Code", content)
        self.assertIn("print('Hello, world!')", content)

    def test_should_ignore(self):
        """Test the should_ignore method."""
        snaprepo = snaprepo(project_path=self.test_project_path)
        
        # Conditionally create .gitignore for testing
        gitignore_file = self.test_project_path / ".gitignore"
        gitignore_file.write_text("test_binary.dat\n")
        
        snaprepo.initialize()
        
        # Test ignored and non-ignored files
        self.assertTrue(snaprepo.should_ignore(self.test_project_path / "test_binary.dat"))
        self.assertFalse(snaprepo.should_ignore(self.test_project_path / "test_file.py"))
    


    def test_is_text_file(self):
        """Test the is_text_file method."""
        snaprepo = snaprepo(project_path=self.test_project_path)
        text_file = self.test_project_path / "test_file.py"
        binary_file = self.test_project_path / "test_binary.dat"

        self.assertTrue(snaprepo.is_text_file(text_file))
        self.assertFalse(snaprepo.is_text_file(binary_file))

    def test_completion_command(self):
        """Test the completion command."""
        result = self.runner.invoke(cli, ["completion", "bash"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Warning:", result.output)  # Since completions are not implemented in this example


if __name__ == "__main__":
    unittest.main()

