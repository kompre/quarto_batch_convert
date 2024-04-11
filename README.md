# Quarto Batch Converter

## Description

This utility will convert any `ipynb` files found in a given directory to qmd files using quarto command line:

- `ipynb` are filtered based filenmae starting with the given token (default: `_`)
- converted `qmd` files are generated in the same folder of the ipynb
- you can specify a prefix for the `qmd` file
- can be used recursively, and it will keep the same directory structure of the input files.

## Installation

```
pip install --editable .
```
