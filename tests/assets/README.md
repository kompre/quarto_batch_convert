# Quarto Batch Converter

## Description

Quarto Batch Converter is a utility that converts `ipynb` files to `qmd` files using the [Quarto command line](https://quarto.org/). This tool is designed to simplify the process of converting multiple `ipynb` files at once, making it ideal for large projects or batch conversions.

This cli is equivalent to perform the following statement on multiple times:

```sh
quarto convert file.ipynb
```

## Features

* Converts files to files using `quarto convert` (`ipynb` to `qmd`, `qmd` to `ipynb`) 
* Filters file based on extension (default: `ipynb`)
* Filters file based on a match pattern that could be replaced for the output file (e.g. `_test.ipynb` -> `test.qmd`)
* Preserves the original directory structure of the input files
* Allows specifying a prefix for the converted files
* Supports glob style paths as well as recursion in the subdirectory

## Installation

To install Quarto Batch Converter, run the following command:
```bash
pipx install quarto_batch_convert
```
This will install the package and make the `quarto_batch_convert` and its alias `qbc` command line available.

## Usage

To use Quarto Batch Converter, navigate to the directory containing the `ipynb` files you want to convert and run the following command:
```bash
quarto_batch_convert <input_paths> [options]
```
Replace `<input_paths>` with one or more directory paths, file paths, or glob patterns to search for `ipynb` files.

### Options

* `-q`, `--qmd-to-ipynb`: Convert `.qmd` files to `.ipynb` files (default: `.ipynb` to `.qmd`)
* `-m`, `--match-replace-pattern`: Match pattern and optional replace pattern, separated by a forward slash. If no slash is present, only matching is performed.
* `-p`, `--prefix`: Prefix to add to the new file name
* `-k`, `--keep-extension`: Keep the original extension as part of the filename
* `-o`, `--output-path`: Output path where to generate the `.qmd` files (default: current directory)
* `-r`, `--recursive`: Search files recursively when input is a directory

### Examples

* Convert all `ipynb` files in the current directory (no subdirectory):
```bash
quarto_batch_convert .
```
* Convert all `ipynb` files in the `notebooks` directory and its subdirectories:
```bash
quarto_batch_convert notebooks -r
```
* Convert all `ipynb` files in the `notebooks` directory and add a prefix `converted_` to the output files:
```bash
quarto_batch_convert notebooks -p converted_
```
* Convert all `ipynb` files in the `notebooks` directory and replace the string `old_` with `new_` in the file names:
```bash
quarto_batch_convert notebooks -m old_/new_
```
## Contributing

Contributions to Quarto Batch Converter are welcome. If you have any issues or feature requests, please submit a pull request or open an issue on the GitHub repository.

## License

Quarto Batch Converter is licensed under the [MIT License](https://opensource.org/licenses/MIT).