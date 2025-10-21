from quarto_batch_convert.quarto_batch_convert import quarto_batch_convert
import os
import glob

def change_dir():
    os.chdir("tests/assets")
    quarto_batch_convert(["*"])

def is_recursive():
    quarto_batch_convert(
        ["tests/assets"]
    )

def simple_run():
    # files = glob.glob("C:/Users/s.follador/Desktop/__canc__/qbc/**/*.ipynb", recursive=True)
    files = ["C:/Users/s.follador/Desktop/__canc__/qbc/**/*"]
    quarto_batch_convert(
        [
            *files
        ]
    )




if __name__ == "__main__":
    # is_recursive()
    # change_dir()
    simple_run()