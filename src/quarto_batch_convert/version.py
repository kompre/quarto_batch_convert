# import tomllib
# from pathlib import Path

# # def get_version():
# #     """Read version from pyproject.toml."""
# #     pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    
# #     if not pyproject_path.exists():
# #         return "unknown"
    
# #     try:
# #         with open(pyproject_path, "rb") as f:
# #             pyproject = tomllib.load(f)
# #         return pyproject["project"]["version"]
# #     except (KeyError, FileNotFoundError, tomllib.TOMLDecodeError):
# #         return "unknown"

# # __version__ = get_version()


import importlib.metadata

__version__ = importlib.metadata.version("quarto-batch-convert")

# print(__version__)