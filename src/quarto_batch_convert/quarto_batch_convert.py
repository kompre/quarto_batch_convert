import os
import shutil
import subprocess
import time
import click
import concurrent.futures
import re

from .version import __version__


def check_quarto_installation():
    """
    Check if Quarto CLI is installed.
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


def create_directory(output_path, relative_path):
    """Create the directory at the given path if it doesn't exist.

    Parameters:
    output_path (str): The base path for the output directory.
    relative_path (str): The relative path of the directory to be created.
    """
    directory_path = os.path.join(output_path, relative_path)
    os.makedirs(directory_path, exist_ok=True)


def convert_file(
    input_path,
    output_path,
    prefix,
    keep_extension,
    file,
    match_pattern,
    replace_pattern,
    output_extension,
):
    """Convert a file from ipynb to qmd using Quarto.

    Parameters:
    input_path (str): The base path of the input files.
    output_path (str): The base path of the output files.
    prefix (str): The prefix to add to the new file name.
    keep_extension (bool): Whether to keep the original extension as part of the filename.
    file (str): The full path of the file to be converted.
    match_pattern (str): The regex pattern to match filenames.
    replace_pattern (str, optional): The replacement pattern for the match. Defaults to None.
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


@click.command(no_args_is_help=True)
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
@click.version_option(version=__version__, prog_name="Quarto Batch Converter")
@click.pass_context
def convert_files(
    ctx,
    input_paths,
    qmd_to_ipynb,
    match_replace_pattern,
    prefix,
    keep_extension,
    output_path,
):
    """
    Convert files with specified extension and filtered by regex pattern using Quarto.

    INPUT_PATHS: One or more files or glob patterns to search for files to convert.
    
        Examples:   \n
        - qbc . \n
        - qbc file1.ipynb file2.ipynb   \n
        - qbc "*.ipynb" \n
        - qbc notebooks/* specific_file.ipynb   \n
        - qbc "notebooks/**/*.ipynb"    \n

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

    # filter the files with the correct extension
    files = [
        path
        for path in input_paths
        if os.path.isfile(path) and path.endswith(input_extension)
    ]

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
