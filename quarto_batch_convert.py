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

def convert_file(input_path, output_path, prefix, keep_extension, file, match_pattern, replace_pattern):
    """Convert a file from ipynb to qmd using Quarto.

    Parameters:
    input_path (str): The base path of the input files.
    output_path (str): The base path of the output files.
    prefix (str): The prefix to add to the new file name.
    keep_extension (bool): Whether to keep the original extension as part of the filename.
    file (str): The full path of the file to be converted.
    match_pattern (str): The regex pattern to match filenames. If replace pattern is provided, the match will be replaced.
    replace_pattern (str): The replacement pattern for the match. If None, the match will not be replaced.
    """
    relative_path = os.path.relpath(os.path.dirname(file), input_path)
    if relative_path != '.':
        create_directory(output_path, relative_path)

    new_file_name, _ = os.path.splitext(os.path.basename(file))

    # Apply regex replacement if both patterns are provided
    if match_pattern and replace_pattern:
        new_file_name = re.sub(match_pattern, replace_pattern, new_file_name)

    if keep_extension:
        new_file_path = os.path.join(output_path, relative_path, prefix + os.path.basename(file) + '.qmd')
    else:
        new_file_path = os.path.join(output_path, relative_path, prefix + new_file_name + '.qmd')

    subprocess.run(['quarto', 'convert', file, '--output', new_file_path])

@click.command()
@click.argument("input_paths", nargs=-1, required=True)
@click.option("-e", "--extension", default=".ipynb", help="File extension to filter files when input is a directory (default: .ipynb)", show_default=True)
@click.option("-mrp", "--match-replace-pattern", nargs=2, help="Match pattern (and optional replace pattern). Usage: -mrp MATCH or -mrp MATCH REPLACE")
@click.option("-p", "--prefix", default="", help="Prefix to add to the new file name")
@click.option("-k", "--keep-extension", is_flag=True, help="Keep the original extension as part of the filename")
@click.option("-o", "--output-path", default=None, help="Output path where to generate the .qmd files (default: current directory)")
@click.option("-r", "--recursive", is_flag=True, help="Search files recursively when input is a directory")
@click.pass_context
def convert_files(ctx, input_paths, extension, match_replace_pattern, prefix, keep_extension, output_path, recursive):
    """
    Convert files with specified extension and filtered by regex pattern using Quarto.
    
    INPUT_PATHS: One or more directory paths, file paths, or glob patterns to search for files to convert.
                 Examples: 
                 - qbc .
                 - qbc file1.ipynb file2.ipynb
                 - qbc "*.ipynb" 
                 - qbc notebooks/ "*.py" specific_file.ipynb
                 - qbc "notebooks/**/*.ipynb"
    
    Options:
        extension (str): File extension to filter files when input is a directory (default: .ipynb).
        match_replace_pattern: Match pattern (and optional replace). Use once for match only, twice for match+replace.
        prefix (str): Prefix to add to the new file name.
        keep_extension (bool): Whether to keep the original extension as part of the filename.
        output_path (str): Output path where to generate the .qmd files (default: current directory).
        recursive (bool): Search files recursively when input is a directory.
    """
    # Parse match-replace-pattern arguments
    match_regex = replace_pattern = None
    
    if match_replace_pattern:
        if len(match_replace_pattern) == 1:
            match_regex = match_replace_pattern[0]
            replace_pattern = None  # Only filtering, no replacement
        elif len(match_replace_pattern) == 2:
            match_regex, replace_pattern = match_replace_pattern
        else:
            click.echo("Error: --match-replace-pattern accepts 1 argument (match only) or 2 arguments (match and replace)")
            ctx.exit(1)
        
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
                        files.extend([os.path.join(root, filename) for filename in filenames if filename.endswith(extension)])
                else:
                    files.extend([os.path.join(path, file) for file in os.listdir(path) if file.endswith(extension)])
                    
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
    files = list(set([f for f in files if os.path.isfile(f) and f.endswith(extension)]))
    
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
            future = executor.submit(convert_file, base_input_path, output_path, prefix, keep_extension, file, match_regex, replace_pattern)
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
    convert_files()