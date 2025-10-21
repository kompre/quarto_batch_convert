import os
import shutil
import subprocess
import time
import click
import concurrent.futures
import re
from typing import List, Optional
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError

def get_package_info() -> str:
    """Get formatted package information for epilogue display."""
    from importlib.metadata import metadata
    try:
        meta = metadata("quarto-batch-convert")
        pkg_version = meta.get("Version", "unknown")
        author = meta.get("Author", "kompre")
        return f"quarto-batch-convert v{pkg_version} | by {author} | https://github.com/kompre/quarto_batch_convert"
    except PackageNotFoundError:
        return "quarto-batch-convert | https://github.com/kompre/quarto_batch_convert"
    
def get_epilog() -> str:
    """Get formatted epilog with examples and package info."""
    return f"""Examples: qbc . -r -m "^__/_"

{get_package_info()}"""

def get_version() -> str:
    """Get package version from metadata."""
    try:
        return version("quarto-batch-convert")
    except PackageNotFoundError:
        return "unknown"


def check_quarto_installation() -> None:
    """Check if Quarto CLI is installed and exit if not found.

    This function verifies that the Quarto CLI tool is available in the system PATH.
    If Quarto is not installed, it prints installation instructions and exits the program
    with code 1.

    Raises:
        SystemExit: Always exits with code 1 if Quarto is not installed.
    """
    if not shutil.which("quarto"):
        print(
            "Error: Quarto CLI is not installed. Please install it before running this command."
        )
        print("See https://quarto.org/docs/get-started/ for installation instructions")
        print(
            "or install from PYPI using `pipx install quarto-cli` or `uv tool install quarto-cli`"
        )
        exit(1)


def create_directory(output_path: str, relative_path: str) -> None:
    """Create the directory at the given path if it doesn't exist.

    This function combines the output path and relative path to create
    a directory structure, creating intermediate directories as needed.

    Args:
        output_path: The base path for the output directory.
        relative_path: The relative path of the directory to be created.
    """
    directory_path = os.path.join(output_path, relative_path)
    os.makedirs(directory_path, exist_ok=True)


def collect_files_from_directory(
    directory: str, extension: str, recursive: bool = False
) -> List[str]:
    """Collect files with the specified extension from a directory.

    This function searches for files with a specific extension either in a single
    directory or recursively through all subdirectories.

    Args:
        directory: The directory path to search.
        extension: The file extension to filter (e.g., '.ipynb').
        recursive: Whether to search recursively in subdirectories. Defaults to False.

    Returns:
        A list of file paths matching the extension.
    """
    files = []
    if recursive:
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                if filename.endswith(extension):
                    files.append(os.path.join(root, filename))
    else:
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path) and item.endswith(extension):
                files.append(item_path)
    return files


def convert_file(
    input_path: str,
    output_path: str,
    prefix: str,
    keep_extension: bool,
    file: str,
    match_pattern: Optional[str],
    replace_pattern: Optional[str],
    output_extension: str,
) -> None:
    """Convert a file using Quarto CLI.

    This function converts a single file (e.g., .ipynb to .qmd or vice versa) using
    the Quarto CLI tool. It handles directory structure preservation, filename
    transformations via regex patterns, and prefix additions.

    Args:
        input_path: The base path of the input files.
        output_path: The base path of the output files.
        prefix: The prefix to add to the new file name.
        keep_extension: Whether to keep the original extension as part of the filename.
        file: The full path of the file to be converted.
        match_pattern: The regex pattern to match filenames for replacement.
        replace_pattern: The replacement pattern for the match. Can be None.
        output_extension: The extension for the output file (e.g., '.qmd', '.ipynb').
    """
    dirname = os.path.dirname(file)
    relative_path = os.path.relpath(dirname, input_path) if dirname else input_path
    if relative_path != ".":
        create_directory(output_path, relative_path)

    new_file_name, _ = os.path.splitext(os.path.basename(file))

    # Apply regex replacement if both patterns are provided
    if match_pattern and replace_pattern is not None:
        new_file_name = re.sub(match_pattern, replace_pattern, new_file_name)

    if keep_extension:
        new_file_path = os.path.join(
            output_path,
            relative_path,
            prefix + os.path.basename(file) + output_extension,
        )
    else:
        new_file_path = os.path.join(
            output_path, relative_path, prefix + new_file_name + output_extension
        )

    # Create the directory if it doesn't exist
    new_file_dirname = os.path.dirname(new_file_path)
    os.makedirs(new_file_dirname, exist_ok=True)

    subprocess.run(["quarto", "convert", file, "--output", new_file_path])


@click.command(
    no_args_is_help=True,
    epilog=get_epilog(),
    help="Batch quarto convert multiple .ipynb to .qmd files or vice versa",
)
@click.argument(
    "input_paths",
    nargs=-1,
    type=click.Path(exists=True),
)
@click.option(
    "-q",
    "--qmd-to-ipynb",
    is_flag=True,
    help="Convert .qmd files to .ipynb files (default: .ipynb to .qmd)",
)
@click.option(
    "-m",
    "--match-replace-pattern",
    metavar="MATCH/REPLACE",
    help="Match pattern and optional replace pattern, separated by a forward slash. "
    "If no slash is present, only matching is performed.",
)
@click.option("-p", "--prefix", default="", help="Prefix to add to the new file name")
@click.option(
    "-k",
    "--keep-extension",
    is_flag=True,
    help="Keep the original extension as part of the filename",
)
@click.option(
    "-o",
    "--output-path",
    default=None,
    help="Output path where to generate the .qmd files (default: current directory)",
)
@click.option(
    "-r",
    "--recursive",
    is_flag=True,
    help="Search files recursively when input is a directory",
)
@click.version_option(version=get_version(), prog_name="Quarto Batch Converter")
@click.pass_context
def quarto_batch_convert(
    ctx: click.Context,
    input_paths: tuple,
    qmd_to_ipynb: bool,
    match_replace_pattern: Optional[str],
    prefix: str,
    keep_extension: bool,
    output_path: Optional[str],
    recursive: bool,
) -> None:
    """ CLI wrapper for convert_files - see help parameters @click.command decorator"""
    return convert_files(
        ctx,
        input_paths,
        qmd_to_ipynb,
        match_replace_pattern,
        prefix,
        keep_extension,
        output_path,
        recursive,
    )

def convert_files(
    ctx: click.Context,
    input_paths: tuple,
    qmd_to_ipynb: bool,
    match_replace_pattern: Optional[str],
    prefix: str,
    keep_extension: bool,
    output_path: Optional[str],
    recursive: bool,
) -> None:
    """Convert files with specified extension using Quarto CLI.

    This is the main CLI command that processes one or more input files or directories,
    optionally filtering by regex patterns, and converts them using Quarto. The function
    supports both .ipynb to .qmd conversion (default) and .qmd to .ipynb conversion.

    Args:
        ctx: Click context object for command execution.
        input_paths: One or more files, directories, or glob patterns to search for files to convert.
        qmd_to_ipynb: If True, convert .qmd to .ipynb. Otherwise, convert .ipynb to .qmd.
        match_replace_pattern: Optional regex pattern for matching/replacing filenames.
            Format: "MATCH/REPLACE" or just "MATCH" for filtering only.
        prefix: String prefix to add to the new file names.
        keep_extension: If True, keep the original extension as part of the filename.
        output_path: Directory path where converted files will be saved. Defaults to current directory.
        recursive: If True, search directories recursively for files to convert.

    Examples:
        Basic conversion of current directory:
            $ qbc .

        Convert specific files:
            $ qbc file1.ipynb file2.ipynb

        Use glob patterns:
            $ qbc "*.ipynb"
            $ qbc notebooks/* specific_file.ipynb
            $ qbc "notebooks/**/*.ipynb"
    """
    # check that `quarto` is installed
    check_quarto_installation()

    # determinate output extension (ipynb->qmd, qmd->ipynb)
    input_extension = ".ipynb" if not qmd_to_ipynb else ".qmd"
    output_extension = ".qmd" if not qmd_to_ipynb else ".ipynb"

    # Parse match-replace-pattern arguments
    match_regex = replace_pattern = None

    if match_replace_pattern:
        if "/" in match_replace_pattern:
            match_regex, replace_pattern = match_replace_pattern.split("/", 1)
        else:
            match_regex = match_replace_pattern

        # Validate the regex pattern
        try:
            re.compile(match_regex)
        except re.error as e:
            click.echo(f"Error: Invalid regex pattern: {e}")
            ctx.exit(1)

    # Handle multiple input paths: directories, files, or glob patterns
    base_input_path = "."

    # Collect files from input paths (files, directories, or already-expanded globs)
    files = []
    for path in input_paths:
        if os.path.isfile(path) and path.endswith(input_extension):
            # Direct file path
            files.append(path)
        elif os.path.isdir(path):
            # Directory path - collect files based on recursive flag
            dir_files = collect_files_from_directory(path, input_extension, recursive)
            files.extend(dir_files)
        # else: path might be from shell glob expansion that doesn't exist anymore, skip it

    # Check if any files were found
    if not files:
        click.echo("Error: No files found to process")
        ctx.exit(1)

    if output_path is None:
        output_path = base_input_path
    else:
        # Create the output path if it does not exist
        os.makedirs(output_path, exist_ok=True)

    # Filter files by regex pattern if provided
    if match_regex:
        filtered_files = []
        pattern = re.compile(match_regex)
        for file in files:
            filename = os.path.basename(file)
            if pattern.search(filename):
                filtered_files.append(file)
        files = filtered_files

    if not files:
        if match_regex:
            click.echo(f"No files found matching the regex pattern: {match_regex}")
        else:
            click.echo("No files found to process")
        ctx.exit(1)

    print(f"Found {len(files)} file(s) to be converted:\n")
    print(f"\n\t{files}\n")

    files_copied = 0
    start_time = time.time()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []
        for file in files:
            future = executor.submit(
                convert_file,
                base_input_path,
                output_path,
                prefix,
                keep_extension,
                file,
                match_regex,
                replace_pattern,
                output_extension,
            )
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            future.result()
            files_copied += 1

    elapsed_time = time.time() - start_time
    text = f"Converted {len(files)} files in {elapsed_time:.3f} seconds"
    print("-" * len(text))
    print(text)
    print("-" * len(text))





if __name__ == "__main__":
    pass
