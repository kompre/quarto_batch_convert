from setuptools import setup

setup(
    name='quarto_batch_convert',
    version='2024.04.0',
    py_modules=['quarto_batch_convert'],
    install_requires=[
        'Click',
    ],
    entry_points={
        'console_scripts': [
            'quarto_batch_convert = quarto_batch_convert:convert_files',
            'qbc = quarto_batch_convert:convert_files',
        ],
    },
)