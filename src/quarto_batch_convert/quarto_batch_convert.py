import os
import subprocess
import time
import click
import concurrent.futures
import glob
import re

def create_directory(output_path, relative_path):
    """Create the directory at the given path if it doesn't exist.
    
    Parameters:
    output_path (str): The base path for the output directory.
    relative_path (str): The relative path of the directory to be created.
    """
    directory_path = os.path.join(output_path, relative_path)
    os.makedirs(directory_path, exist_ok=True)

def convert_file(input_path, output_path, prefix, keep_extension, file, match_pattern, replace_pattern, output_extension):
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
    relative_path = os.path.relpath(os.path.dirname(file), input_path)
    if relative_path != '.':
        create_directory(output_path, relative_path)

    new_file_name, _ = os.path.splitext(os.path.basename(file))

    # Apply regex replacement if both patterns are provided
    if match_pattern and replace_pattern is not None:
        new_file_name = re.sub(match_pattern, replace_pattern, new_file_name)

    if keep_extension:
        new_file_path = os.path.join(output_path, relative_path, prefix + os.path.basename(file) + output_extension)
    else:
        new_file_path = os.path.join(output_path, relative_path, prefix + new_file_name + output_extension)

    subprocess.run(['quarto', 'convert', file, '--output', new_file_path])

@click.command()
@click.argument("input_paths", nargs=-1, required=True)
@click.option("-q", "--qmd-to-ipynb", is_flag=True, help="Convert .qmd files to .ipynb files (default: .ipynb to .qmd)")
@click.option(
    "-m",
    "--match-replace-pattern",
    metavar="MATCH/REPLACE",
    help="Match pattern and optional replace pattern, separated by a forward slash. "
         "If no slash is present, only matching is performed."
)
@click.option("-p", "--prefix", default="", help="Prefix to add to the new file name")
@click.option("-k", "--keep-extension", is_flag=True, help="Keep the original extension as part of the filename")
@click.option("-o", "--output-path", default=None, help="Output path where to generate the .qmd files (default: current directory)")
@click.option("-r", "--recursive", is_flag=True, help="Search files recursively when input is a directory")
@click.pass_context
def convert_files(ctx, input_paths, qmd_to_ipynb, match_replace_pattern, prefix, keep_extension, output_path, recursive):
    """
    Convert files with specified extension and filtered by regex pattern using Quarto.
    
    INPUT_PATHS: One or more directory paths, file paths, or glob patterns to search for files to convert.
                 Examples: 
                 - qbc .
                 - qbc file1.ipynb file2.ipynb
                 - qbc "*.ipynb" 
                 - qbc notebooks/ specific_file.ipynb
                 - qbc "notebooks/**/*.ipynb"
    
    Options:
        qmd_to_ipynb (bool): Convert .qmd files to .ipynb files (default: .ipynb to .qmd)
        match_replace_pattern: Match pattern (and optional replace). Use once for match only, twice for match+replace.
        prefix (str): Prefix to add to the new file name.
        keep_extension (bool): Whether to keep the original extension as part of the filename.
        output_path (str): Output path where to generate the .qmd files (default: current directory).
        recursive (bool): Search files recursively when input is a directory.
    """
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
    files = []
    base_input_path = "."
    
    for input_path in input_paths:
        # Expand glob patterns first
        expanded_paths = glob.glob(input_path, recursive=True) if ('*' in input_path or '?' in input_path) else [input_path]
        
        if not expanded_paths:
            click.echo(f"Warning: No files or directories found matching '{input_path}'")
            continue
        
        for path in expanded_paths:
            if not os.path.exists(path):
                click.echo(f"Warning: Path '{path}' does not exist")
                continue
                
            if os.path.isfile(path):
                files.append(path)
                # Set base_input_path to the directory of the first file if not set to a specific directory
                if base_input_path == "." and len(input_paths) == 1 and len(expanded_paths) == 1:
                    base_input_path = os.path.dirname(path) or "."
            elif os.path.isdir(path):
                # For directories, use the first directory as base_input_path
                if base_input_path == ".":
                    base_input_path = path
                
                # Directory handling - use existing logic
                if recursive:
                    for root, _, filenames in os.walk(path):
                        files.extend([os.path.join(root, filename) for filename in filenames if filename.endswith(input_extension)])
                else:
                    files.extend([os.path.join(path, file) for file in os.listdir(path) if file.endswith(input_extension)])
                    
    # Check if any files were found    
    if not files:
        click.echo("Error: No files found to process")
        ctx.exit(1)
    
    if output_path is None:
        output_path = base_input_path
    else:
        # Create the output path if it does not exist
        os.makedirs(output_path, exist_ok=True)
    
    # Remove duplicates and ensure all files exist
    files = list(set([f for f in files if os.path.isfile(f) and f.endswith(input_extension)]))
    
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
            future = executor.submit(convert_file, base_input_path, output_path, prefix, keep_extension, file, match_regex, replace_pattern, output_extension)
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
    convert_files(["src/tests", r"--match-replace-pattern", "^_", "-q", "-r"])