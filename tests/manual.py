from quarto_batch_convert.quarto_batch_convert import convert_files
import os

if __name__ == "__main__":
    os.chdir("tests/assets")
    convert_files(["*"])