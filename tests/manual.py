from quarto_batch_convert.quarto_batch_convert import convert_files
import os
import glob

def change_dir():
    os.chdir("tests/assets")
    convert_files(["*"])

def is_recursive():
    convert_files(
        ["tests/assets"]
    )

def simple_run():
    # files = glob.glob("C:/Users/s.follador/Desktop/__canc__/qbc/**/*.ipynb", recursive=True)
    files = ["C:/Users/s.follador/Desktop/__canc__/qbc/**/*"]
    convert_files(
        [
            *files
        ]
    )




if __name__ == "__main__":
    # is_recursive()
    # change_dir()
    simple_run()