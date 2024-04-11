import os
import subprocess
import time
import click
import concurrent.futures

def create_directory(output_path, relative_path):
    directory_path = os.path.join(output_path, relative_path)
    os.makedirs(directory_path, exist_ok=True)

def convert_file(input_path, output_path, prefix, keep_extension, file, token):
    relative_path = os.path.relpath(os.path.dirname(file), input_path)
    if relative_path != '.':
        create_directory(output_path, relative_path)
    new_file_name, old_extension = os.path.splitext(os.path.basename(file))
    new_file_name = new_file_name.replace(token, "")  # Replace the token with an empty string
    if keep_extension:
        new_file_path = os.path.join(output_path, relative_path, prefix + os.path.basename(file) + '.qmd')
    else:
        new_file_path = os.path.join(output_path, relative_path, prefix + new_file_name + '.qmd')
    subprocess.run(['quarto', 'convert', file, '--output', new_file_path])

@click.command()
@click.option("-e", "--extension", default=".ipynb", help="File extension to filter files (default: .ipynb)", show_default=True)
@click.option("-t", "--token", default="_", help="Token to filter file names (default: _)", show_default=True)
@click.option("-i", "--input-path", default=".", help="Input path for searching the files (default: current directory)", show_default=True)
@click.option("-p", "--prefix", default="", help="Prefix to add to the new file name")
@click.option("-k", "--keep-extension", is_flag=True, help="Keep the original extension as part of the filename")
@click.option("-o", "--output-path", default=None, help="Output path where to generate the .qmd files (default: same as input input_path)")
@click.option("-r", "--recursive", is_flag=True, help="Search files recursively within the input path")
def convert_files(extension, token, input_path, prefix, keep_extension, output_path, recursive):
    """
    Convert files with specified extension and filtered by token using Quarto.
    
    Args:
        extension (str): File extension to filter files (default: .ipynb).
        token (str): Token to filter file names (default: _).
        input_path (str): Input path for searching the files (default: current directory).
        prefix (str): Prefix to add to the new file name.
        keep_extension (bool): Whether to keep the original extension as part of the filename.
        output_path (str): Output path where to generate the .qmd files (default: same as input_path).
        recursive (bool): Search files recursively within the input path.
    """
    if output_path is None:
        output_path = input_path
    else:
        # Create the output path if it does not exist
        os.makedirs(output_path, exist_ok=True)
    
    # Retrieve files
    if recursive:
        files = []
        for root, _, filenames in os.walk(input_path):
            files.extend([os.path.join(root, filename) for filename in filenames if filename.endswith(extension)])
    else:
        files = [os.path.join(input_path, file) for file in os.listdir(input_path) if file.endswith(extension)]
    
    filtered_files = [file for file in files if os.path.basename(file).startswith(token)]
    
    print(f"Found {len(filtered_files)} '{extension}' file(s) to be converted:\n")
    print(f"\n\t{filtered_files}\n")
    
    files_copied = 0
    start_time = time.time()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []
        for file in filtered_files:
            future = executor.submit(convert_file, input_path, output_path, prefix, keep_extension, file)
            futures.append(future)
            
        for future in concurrent.futures.as_completed(futures):
            future.result()
            files_copied += 1
        
    elapsed_time = time.time() - start_time
    text = f"Converted {len(filtered_files)} files in {elapsed_time:.3f} seconds"
    print("-" * len(text))
    print(text)
    print("-" * len(text))

if __name__ == "__main__":
    convert_files()
