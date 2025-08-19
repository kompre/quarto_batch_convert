from quarto_batch_convert.quarto_batch_convert import convert_files
import os

def change_dir():
    os.chdir("tests/assets")
    convert_files(["*"])

def is_recursive():
    convert_files(
        ["tests/assets"]
    )

def simple_run():
    convert_files(
        [
            r'C:\Users\s.follador\Desktop\__canc__', '-r', '-p', 'OUT/', 
        ]
    )



if __name__ == "__main__":
    # is_recursive()
    # change_dir()
    simple_run()