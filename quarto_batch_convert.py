import os
import subprocess
import time
import click
import concurrent.futures

@click.command()
@click.option("-e", "--extension", default=".ipynb", help="File extension to filter files (default: .ipynb)", show_default=True)
@click.option("-t", "--token", default="_", help="Token to filter file names (default: _)", show_default=True)
@click.option("-i", "--input-path", default=".", help="input path for search the files (default: current input_path)", show_default=True)
@click.option("-p", "--prefix", default="", help="Prefix to add to the new file name")
@click.option("-k", "--keep-extension", is_flag=True, help="Keep the original extension as part of the filename")
@click.option("-o", "--output-path", default=None, help="Output path where to generate the .qmd files (default: same as input input_path)")
def convert_files(extension, token, input_path, prefix, keep_extension, output_path):
    """
    Convert files with specified extension and filtered by token using Quarto.
    
    Args:
        extension (str): File extension to filter files (default: .ipynb).
        token (str): Token to filter file names (default: _).
        input_path (str): input_path where to find the file (default: current directory).
        prefix (str): Prefix to add to the new file name.
        keep_extension (bool): Whether to keep the original extension as part of the filename.
        output_path (str): Output path where to generate the .qmd files (default: same as input_path).
    """
    if output_path is None:
        output_path = input_path
    else:
        # Create the input_path if it does not exist
        os.makedirs(output_path, exist_ok=True)
        
    files = [file for file in os.listdir(input_path) if file.endswith(extension)]
    filtered_files = [file for file in files if file.startswith(token)]
    
    print(f"Found {len(filtered_files)} '{extension}' file(s) to be converted:\n")
    print(f"\n\t{filtered_files}\n")
    
    files_copied = 0
    start_time = time.time()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []
        for file in filtered_files:
            filepath = os.path.join(input_path, file)
            new_file_name, old_extension = os.path.splitext(file)
            if keep_extension:
                new_file_path = os.path.join(output_path, prefix + file + '.qmd')
            else:
                new_file_path = os.path.join(output_path, prefix + new_file_name + '.qmd')
            future = executor.submit(subprocess.run, ['quarto', 'convert', filepath, '--output', new_file_path])
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
