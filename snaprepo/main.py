#!/usr/bin/env python3
import sys
from pathlib import Path
import click
from typing import List, Dict, Iterator
import fnmatch
import chardet
from rich import print as rprint
from rich.panel import Panel
from rich.syntax import Syntax
from rich.console import Console
import tiktoken
import pyperclip
from snaprepo import config  # When imported as a package


class snaprepo:
    """Main class for creating AI-friendly snapshots of code projects."""

    def __init__(
        self,
        project_path: str = ".",
        output_file: str = None,
        skip_common: bool = False,
        skip_files: list = None,
    ):
        self.project_path = Path(project_path)
        self.output_file = Path(output_file).resolve() if output_file else None
        self.ignore_patterns = []
        self.skip_common = skip_common
        self.skip_files = skip_files or []
        self.redacted_patterns = config.REDACTED_PATTERNS
        self.sensitive_patterns = config.SENSITIVE_PATTERNS
        self.common_files = config.COMMON_FILES
        self.binary_extensions = config.BINARY_EXTENSIONS
        self.extension_map = config.EXTENSION_MAP
        self.stats = dict(config.DEFAULT_STATS)  # Make a copy to avoid sharing
        self._ignored_dirs = set()  # Add this line
        self.debug = False  # Add this line

    def initialize(self) -> None:
        """Initialize ignore patterns from .gitignore if it exists"""
        from rich import print as rprint

        # Add default patterns
        rprint("\n[yellow]Loading default ignore patterns:[/]")
        self.ignore_patterns.extend(config.DEFAULT_IGNORE_PATTERNS)
        for pattern in config.DEFAULT_IGNORE_PATTERNS:
            rprint(f"[cyan]Added default pattern:[/] {pattern}")

        # Read .gitignore if it exists
        gitignore_path = self.project_path / ".gitignore"
        if gitignore_path.exists():
            rprint(f"\n[yellow].gitignore found at:[/] {gitignore_path}")
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if line.startswith("!"):  # Handle negative patterns
                            rprint(f"[yellow]Skipping negative pattern:[/] {line}")
                            continue
                        if line.startswith("./"):  # Normalize pattern
                            line = line[2:]
                        self.ignore_patterns.append(line)
                        rprint(f"[cyan]Added .gitignore pattern:[/] {line}")
                    elif line.startswith("#"):
                        rprint(f"[dim]Skipping comment:[/] {line}")

        rprint(f"\n[green]Total patterns loaded:[/] {len(self.ignore_patterns)}")
        rprint("\n[yellow]Active ignore patterns:[/]")
        for pattern in self.ignore_patterns:
            rprint(f"  • {pattern}")

    def is_template(self, path: Path) -> tuple[bool, str]:
        """Check if a file is a template and return its content"""
        name = path.name.lower()
        if any(name.endswith(suffix) for suffix in config.TEMPLATE_SUFFIXES):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                return True, content
            except Exception as e:
                rprint(f"[yellow]Warning:[/] Could not read template {path}: {str(e)}")
                return True, f"# Error reading template file: {str(e)}"
        return False, ""

    def should_ignore(self, file_path: Path) -> bool:
        """Check if a file or directory should be ignored based on patterns."""
        from rich import print as rprint

        rel_path = str(file_path.relative_to(self.project_path))

        # First check if any parent directory is already known to be ignored
        parent = file_path.parent
        while parent != self.project_path:
            parent_path = str(parent.relative_to(self.project_path))
            if parent_path in self._ignored_dirs:
                if file_path.is_dir():
                    if self.debug:
                        rprint(f"Parent directory already ignored: {parent_path}")
                return True
            parent = parent.parent

        if self.debug:
            rprint(f"\nChecking path: {rel_path}")

        # If this is the output file, ignore it
        if self.output_file and file_path.resolve() == self.output_file:
            return True

        # Check if the file should be redacted
        is_redacted, redaction_msg = self.is_redacted(file_path)
        if is_redacted:
            return False

        # Convert path to parts for precise matching
        path_parts = rel_path.split("/")

        # Check each pattern
        for pattern in self.ignore_patterns:
            if not pattern or pattern.startswith("#"):
                continue

            # Clean up the pattern
            pattern = pattern.rstrip("/")

            if self.debug:
                rprint(f"Testing '{rel_path}' against pattern: '{pattern}'")

            # Handle glob patterns
            if pattern.startswith("*"):
                if fnmatch.fnmatch(file_path.name, pattern):
                    if self.debug:
                        rprint(f"Glob match: {file_path.name} matches {pattern}")
                    return True
            # Handle directory/file patterns
            else:
                # Split pattern into parts
                pattern_parts = pattern.split("/")

                # Match exact directory/file names
                for i in range(len(path_parts) - len(pattern_parts) + 1):
                    if path_parts[i : i + len(pattern_parts)] == pattern_parts:
                        if self.debug:
                            rprint(
                                f"Path match: {'/'.join(path_parts[i:i+len(pattern_parts)])} matches {pattern}"
                            )
                        if file_path.is_dir():
                            self._ignored_dirs.add(rel_path)
                        return True

        return False

    def is_sensitive_file(self, path: Path) -> bool:
        """Check if a file matches sensitive file patterns"""
        rel_path = str(path.relative_to(self.project_path))
        return any(
            fnmatch.fnmatch(rel_path, pattern) for pattern in self.sensitive_patterns
        )

    def is_redacted(self, path: Path) -> tuple[bool, str]:
        """Check if a path should be redacted and return the redaction message"""
        rel_path = str(path.relative_to(self.project_path))

        # Check exact matches in redacted_patterns
        if rel_path in self.redacted_patterns:
            return True, self.redacted_patterns[rel_path]

        # Check directory matches (with trailing slash)
        if not path.is_file():
            rel_path_dir = rel_path + "/"
            if rel_path_dir in self.redacted_patterns:
                return True, self.redacted_patterns[rel_path_dir]

        # Check if file matches sensitive patterns
        if self.is_sensitive_file(path):
            return True, "[REDACTED - Sensitive Data]"

        return False, ""

    def get_language(self, file_path: Path) -> str:
        """Get the language identifier for syntax highlighting"""
        return self.extension_map.get(file_path.suffix.lstrip(".").lower(), "")

    def is_text_file(self, file_path: Path, max_size: int = 1_000_000) -> bool:
        """Check if a file is a text file and within size limits"""
        try:
            # Check extension first
            if file_path.suffix.lstrip(".").lower() in self.binary_extensions:
                return False

            if file_path.stat().st_size > max_size:  # Skip files larger than max_size
                return False

            # Read first 4KB of the file
            with open(file_path, "rb") as f:
                chunk = f.read(4096)

            # Try to detect the encoding
            result = chardet.detect(chunk)
            if result["encoding"] is None:
                return False

            # Check for null bytes
            if b"\x00" in chunk:
                return False

            return True
        except Exception:
            return False

    @staticmethod
    def estimate_tokens(text: str) -> Dict[str, Dict[str, float]]:
        """
        Returns:
            {
                "GPT-4": {
                    "tokens": 1234,
                    "max_context": 8192,
                    "usage_percent": 15.07,
                    "remaining_tokens": 6958,
                    ...
                },
                ...
            }
        """
        enc = tiktoken.get_encoding("cl100k_base")
        baseline_count = len(enc.encode(text))

        results = {}
        for model_name, specs in config.MODEL_SPECS.items():
            multiplier = specs["multiplier"]
            max_ctx = specs["max_context"]

            est_tokens = int(baseline_count * multiplier)
            usage_percent = (est_tokens / max_ctx) * 100 if max_ctx > 0 else 0
            remaining_tokens = max_ctx - est_tokens

            results[model_name] = {
                "tokens": est_tokens,
                "max_context": max_ctx,
                "usage_percent": usage_percent,
                "remaining_tokens": remaining_tokens,
            }

        return results

    def generate_tree(self) -> str:
        """Generate a directory tree of the project"""
        tree_lines = ["```", "."]
        sorted_files = sorted(
            [p for p in self.project_path.rglob("*") if not self.should_ignore(p)],
            key=lambda x: str(x),
        )

        for path in sorted_files:
            rel_path = path.relative_to(self.project_path)
            level = len(rel_path.parts) - 1
            prefix = "│   " * (level - 1) + ("├── " if level > 0 else "")
            name = rel_path.parts[-1]

            # Check if file/directory should be redacted
            is_redacted, redaction_msg = self.is_redacted(path)

            if not path.is_file():  # Directory
                tree_line = f"{prefix}{name}/"
                if is_redacted:
                    tree_line += f" {redaction_msg}"
                tree_lines.append(tree_line)
            else:
                tree_line = f"{prefix}{name}"
                if is_redacted:
                    tree_line += f" {redaction_msg}"
                tree_lines.append(tree_line)

        tree_lines.append("```")
        return "\n".join(tree_lines)

    def concatenate(
        self,
        max_file_size: int = 1_000_000,
        summary: bool = True,
        token_estimate: bool = False,
    ) -> str:
        """Concatenate all project files into a markdown string"""
        self.initialize()
        output = ["# Project Source Code\n"]

        # Add directory tree
        output.extend(["## Project Structure", self.generate_tree(), ""])

        # Collect and sort all files
        files = []
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file():
                self.stats["total_files"] += 1
                if not self.should_ignore(file_path):
                    files.append(file_path)
                else:
                    self.stats["ignored_files"] += 1

        files.sort()

        # Inside concatenate(), replace the file processing part with:
        for file_path in files:
            rel_path = file_path.relative_to(self.project_path)

            # Check if file should be redacted
            is_redacted, redaction_msg = self.is_redacted(file_path)
            if is_redacted:
                output.extend([f"\n## {rel_path}\n", f"*{redaction_msg}*\n"])
                continue

            # Check if file is a template
            is_template, template_content = self.is_template(file_path)
            if is_template:
                lang = self.get_language(file_path)
                output.extend(
                    [f"\n## {rel_path}\n", f"```{lang}", template_content, "```\n"]
                )
                continue

            # Process normal files
            if self.is_text_file(file_path, max_file_size):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    lang = self.get_language(file_path)
                    self.stats["included_files"] += 1
                    self.stats["total_size"] += len(content)
                    if lang:
                        self.stats["languages"].add(lang)

                    output.extend(
                        [f"\n## {rel_path}\n", f"```{lang}", content, "```\n"]
                    )
                except Exception as e:
                    rprint(f"[yellow]Warning:[/] Skipping {rel_path}: {str(e)}")
            else:
                self.stats["binary_files"] += 1
                output.extend([f"\n## {rel_path}\n", "*[Binary file]*\n"])

        result = "\n".join(output)

        if token_estimate:
            tokens = self.estimate_tokens(result)
            if tokens:
                token_info = ["\n## Token Estimates\n"]
                for model, count in tokens.items():
                    token_info.append(f"- {model}: ~{count:,} tokens")
                result = "\n".join([result, *token_info])

        # Print statistics to console only
        if summary:
            rprint("\n[green]Project Statistics:[/]")
            rprint(f"  • Total files scanned: {self.stats['total_files']}")
            rprint(f"  • Files included: {self.stats['included_files']}")
            rprint(f"  • Binary files: {self.stats['binary_files']}")
            rprint(f"  • Ignored files: {self.stats['ignored_files']}")
            rprint(f"  • Total size: {self.stats['total_size'] / 1024:.1f}KB")
            rprint(f"  • Languages: {', '.join(sorted(self.stats['languages']))}")

        return result

    def stream_output(
        self,
        max_file_size: int = 1_000_000,
    ) -> Iterator[str]:
        """Stream the concatenated output of all project files.

        Args:
            max_file_size: Maximum size of individual files to include

        Yields:
            Chunks of the markdown output as they're generated
        """
        self.initialize()

        # Disable rich formatting when streaming
        console = Console(file=sys.stdout, force_terminal=False)

        # Header
        yield "# Project Source Code\n\n"

        # Project structure
        yield "## Project Structure\n"
        yield self.generate_tree()
        yield "\n"

        # Process files
        files = []
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file():
                self.stats["total_files"] += 1
                if not self.should_ignore(file_path):
                    files.append(file_path)
                else:
                    self.stats["ignored_files"] += 1

        files.sort()

        # Inside stream_output(), replace the file processing part with:
        for file_path in files:
            rel_path = file_path.relative_to(self.project_path)
            yield f"\n## {rel_path}\n"

            # Check if file should be redacted
            is_redacted, redaction_msg = self.is_redacted(file_path)
            if is_redacted:
                yield f"*{redaction_msg}*\n"
                continue

            # Check if file is a template
            is_template, template_content = self.is_template(file_path)
            if is_template:
                lang = self.get_language(file_path)
                yield f"```{lang}\n"
                yield template_content
                yield "```\n"
                continue

            # Process normal files
            if self.is_text_file(file_path, max_file_size):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    lang = self.get_language(file_path)
                    self.stats["included_files"] += 1
                    self.stats["total_size"] += len(content)
                    if lang:
                        self.stats["languages"].add(lang)

                    yield f"```{lang}\n"
                    yield content
                    yield "```\n"
                except Exception as e:
                    console.print(f"[yellow]Warning:[/] Skipping {rel_path}: {str(e)}")
                    yield "*[Error reading file]*\n"
            else:
                self.stats["binary_files"] += 1
                yield "*[Binary file]*\n"


@click.group(invoke_without_command=True)
@click.pass_context
@click.option(
    "-p",
    "--path",
    "project_path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path to the project directory",
)
@click.option(
    "--max-file-size",
    default=1_000_000,
    type=int,
    help="Maximum file size in bytes",
)
@click.option(
    "--skip-common",
    is_flag=True,
    help="Skip commonly referenced files (LICENSE, README, etc.)",
)
@click.option(
    "--skip-files",
    multiple=True,
    help="Additional files or patterns to skip",
)
def cli(ctx, project_path, max_file_size, skip_common, skip_files):
    """snaprepo - Format your code for AI tools like ChatGPT and Claude."""
    if ctx.invoked_subcommand is None:
        # Default behavior: Stream to clipboard
        # Stream logic here

        # Capture stream output to clipboard
        output = []
        try:
            paster = snaprepo(
                project_path=project_path,
                output_file=None,
                skip_common=skip_common,
                skip_files=skip_files,
            )

            # Collect all chunks
            for chunk in paster.stream_output():
                output.append(chunk)

            # Join and copy to clipboard
            full_output = "".join(output)
            import pyperclip

            pyperclip.copy(full_output)

            console = Console(stderr=True)
            console.print("[green]✓[/] Project snapshot copied to clipboard!")

        except Exception as e:
            console = Console(stderr=True)
            console.print(f"[red]Error:[/] {str(e)}")
            raise click.Abort()


@cli.command()
@click.option(
    "-p",
    "--path",
    "project_path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path to the project directory",
)
@click.option(
    "--max-file-size",
    default=1_000_000,
    type=int,
    help="Maximum file size in bytes",
)
@click.option(
    "--skip-common",
    is_flag=True,
    help="Skip commonly referenced files (LICENSE, README, etc.)",
)
@click.option(
    "--skip-files",
    multiple=True,
    help="Additional files or patterns to skip",
)
def stream(project_path, max_file_size, skip_common, skip_files):
    """Stream project snapshot to stdout for piping."""
    # Stream command logic here

    try:
        paster = snaprepo(
            project_path=project_path,
            output_file=None,  # We don't need an output file for streaming
            skip_common=skip_common,
            skip_files=skip_files,
        )

        for chunk in paster.stream_output(max_file_size=max_file_size):
            sys.stdout.write(chunk)
            sys.stdout.flush()  # Ensure immediate output

    except Exception as e:
        console = Console(stderr=True)
        console.print(f"[red]Error:[/] {str(e)}")
        raise click.Abort()


@cli.command()
@click.option(
    "-p",
    "--path",
    "project_path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path to the project directory",
)
@click.option(
    "-o",
    "--output",
    "output_file",
    default=None,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output markdown file (default: {project_dir}_source.md)",
)
@click.option(
    "--summary/--no-summary",
    default=True,
    help="Show project stats in terminal output",
)
@click.option(
    "--max-file-size",
    default=1_000_000,
    type=int,
    help="Maximum file size in bytes",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Force overwrite existing output file",
)
@click.option(
    "--skip-common",
    is_flag=True,
    help="Skip commonly referenced files (LICENSE, README, etc.)",
)
@click.option(
    "--skip-files",
    multiple=True,
    help="Additional files or patterns to skip",
)
def snap(
    project_path, output_file, summary, max_file_size, force, skip_common, skip_files
):
    """Create a markdown snapshot of your project for AI models."""
    # Snap command logic here

    """Create a markdown snapshot of your project for AI models."""
    try:
        # Generate default output filename based on project directory
        if output_file is None:
            project_name = Path(project_path).resolve().name
            output_file = Path(f"{project_name}_source.md")

        if output_file.exists() and not force:
            if not click.confirm(f"\nFile {output_file} already exists. Overwrite?"):
                rprint("[yellow]Operation cancelled.[/]")
                return

        rprint(Panel.fit("📸 Creating project snapshot...", border_style="blue"))

        paster = snaprepo(
            project_path=project_path,
            output_file=output_file,
            skip_common=skip_common,
            skip_files=skip_files,
        )
        markdown = paster.concatenate(
            max_file_size=max_file_size, summary=summary, token_estimate=False
        )

        output_file.write_text(markdown, encoding="utf-8")
        rprint(
            Panel.fit(
                f"✨ Snapshot created at [blue]{output_file}[/]", border_style="green"
            )
        )

    except Exception as e:
        rprint(Panel.fit(f"❌ Error: {str(e)}", border_style="red"))
        raise click.Abort()


@cli.command()
@click.argument("file", required=False, type=click.Path(dir_okay=False))
def tokens(file):
    """
    Print a detailed token analysis of a project snapshot or user-specified file.

    This refactors 'estimate' and 'analyze' into one command that:
      - Auto-detects the snapshot if none is provided
      - Prints file stats
      - Prints per-model token usage and context stats
    """
    try:
        # 1) Determine which file to process
        if not file:
            project_name = Path.cwd().name
            file = f"{project_name}_source.md"

        file_path = Path(file)
        if not file_path.exists():
            rprint(
                Panel.fit(
                    f"❌ No project snapshot found at '{file}'.\n"
                    f"Please run [yellow]`snaprepo snap`[/] or provide a file name.\n",
                    border_style="red",
                )
            )
            raise click.Abort()

        # 2) Read the file
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        # 3) Gather basic file stats
        total_chars = len(content)
        total_lines = len(lines)
        # Count code blocks by lines that start with triple backticks
        code_blocks = sum(1 for line in lines if line.strip().startswith("```")) // 2

        # 4) Estimate tokens for each model
        model_data = snaprepo.estimate_tokens(content)

        # 5) Print a detailed report
        rprint("\n[blue]Project File Statistics[/]")
        rprint(f"  • File Name: {file_path.name}")
        rprint(f"  • Characters: {total_chars:,}")
        rprint(f"  • Lines: {total_lines:,}")
        rprint(f"  • Code Blocks: {code_blocks}")

        rprint("\n[yellow]Model-Specific Token Estimates:[/]")
        for model, info in model_data.items():
            tokens = info["tokens"]
            max_ctx = info["max_context"]
            usage = info["usage_percent"]
            remaining = info["remaining_tokens"]
            rprint(f"  • {model}: [green]{tokens:,}[/] tokens")
            rprint(
                f"     ↳ Max Context: {max_ctx:,}  |  Usage: {usage:.1f}%  |  Remaining: {remaining:,}"
            )

        rprint(
            "\n[dim]Note: All values are approximate and may vary by actual model version or usage.[/]\n"
        )

    except Exception as e:
        rprint(Panel.fit(f"❌ Error: {str(e)}", border_style="red"))
        raise click.Abort()


@cli.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completion(shell):
    """Generate shell completion script."""
    # (1) Detect if we are in a PyInstaller bundle
    if hasattr(sys, "_MEIPASS"):
        # If so, completions were placed into <_MEIPASS>/completions
        bundle_dir = Path(sys._MEIPASS)
    else:
        # (2) Otherwise, assume we're running from the repo root
        # Adjust as needed if your dev environment is different
        bundle_dir = Path(__file__).parent.parent
    # (3) Construct the path to the correct file
    completions_dir = bundle_dir / "completions"
    completion_file = completions_dir / f"snaprepo.{shell}"
    # (4) Check existence & print
    if not completion_file.exists():
        rprint(f"[yellow]Warning:[/] Completion script for {shell} not available.")
        return
    click.echo(completion_file.read_text())


def main():
    cli()


if __name__ == "__main__":
    main()
