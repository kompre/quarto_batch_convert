import os
import subprocess
import time
import click
import concurrent.futures

@click.command()
@click.option("-e", "--extension", default=".ipynb", help="File extension to filter files (default: .ipynb)", show_default=True)
@click.option("-t", "--token", default="_", help="Token to filter file names (default: _)", show_default=True)
@click.option("-d", "--directory", default=".", help="Working directory (default: current directory)", show_default=True)
@click.option("-p", "--prefix", default="", help="Prefix to add to the new file name")
@click.option("-k", "--keep-extension", is_flag=True, help="Keep the original extension as part of the filename")
def convert_files(extension, token, directory, prefix, keep_extension):
    """
    Convert files with specified extension and filtered by token using Quarto.
    
    Args:
        extension (str): File extension to filter files (default: .ipynb).
        token (str): Token to filter file names (default: _).
        directory (str): Working directory (default: current directory).
        prefix (str): Prefix to add to the new file name.
    """
    os.chdir(directory)
    files = [file for file in os.listdir() if file.endswith(extension)]
    filtered_files = [file for file in files if file.startswith(token)]
    
    print(f"Found {len(filtered_files)} '{extension}' file to be converted:\n")
    print(f"\n\t{filtered_files}\n")
    
    files_copied = 0
    start_time = time.time()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []
        for file in filtered_files:
            new_file_name, old_extension = os.path.splitext(file)
            if keep_extension:
                new_file_path = prefix + file + '.qmd'
            else:
                new_file_path = prefix + new_file_name + '.qmd'
            future = executor.submit(subprocess.run, ['quarto', 'convert', file, '--output', new_file_path])
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
