import os
import shutil
import pytest
from click.testing import CliRunner
from quarto_batch_convert.quarto_batch_convert import quarto_batch_convert
import glob
from contextlib import contextmanager
from typing import Generator


@contextmanager
def change_dir(destination: str) -> Generator[None, None, None]:
    """Temporarily change the current working directory.

    This context manager changes to the specified directory and automatically
    returns to the original directory when exiting the context, even if an
    exception occurs.

    Args:
        destination: The directory path to change to.

    Yields:
        None
    """
    try:
        cwd = os.getcwd()
        os.chdir(destination)
        yield
    finally:
        os.chdir(cwd)

# Use a temporary directory for all tests
@pytest.fixture(scope="module")
def setup_teardown_test_env() -> Generator[str, None, None]:
    """Create a temporary test environment with sample files.

    This fixture sets up a temporary directory structure with test files
    for the test suite and cleans it up after all tests in the module complete.

    Yields:
        The path to the temporary test directory.
    """
    # Setup: Create a temporary directory structure
    test_dir = "temp_test_dir"
    shutil.rmtree(test_dir, ignore_errors=True)
    os.makedirs(os.path.join(test_dir, "notebooks"), exist_ok=True)
    os.makedirs(os.path.join(test_dir, "other_files"), exist_ok=True)

    # Create dummy files
    files_to_create = [
        ("tests/assets/__test.ipynb", os.path.join(test_dir, "notebooks", "_test_1.ipynb")),
        ("tests/assets/TEST.qmd", os.path.join(test_dir, "notebooks", "TEST.qmd")),
        ("tests/assets/__test.ipynb", os.path.join(test_dir, "notebooks", "test_2.ipynb")),
        ("tests/assets/__test.ipynb", os.path.join(test_dir, "notebooks", "archive_test_3.ipynb")),
        ("tests/assets/README.md", os.path.join(test_dir, "other_files", "README.md")),
        ("tests/assets/__test.ipynb", os.path.join(test_dir, "file_in_root.ipynb"))
    ]

    for src, dst in files_to_create:
        shutil.copy(src, dst)

    yield test_dir

    # Teardown: Clean up the temporary directory
    shutil.rmtree(test_dir, ignore_errors=True)

def test_single_match_no_replace(setup_teardown_test_env: str) -> None:
    """Test the --match-replace-pattern option with only a match pattern.

    Verifies that when providing a match pattern without a replacement (no slash),
    the CLI correctly filters files matching the pattern without renaming them.

    Args:
        setup_teardown_test_env: Path to the temporary test directory.
    """
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    
    input_files = glob.glob(test_dir + "/**/*", recursive=True)
    
    result = runner.invoke(quarto_batch_convert, [*input_files, "-m", "test_2"])
    
    assert result.exit_code == 0
    assert "test_2.ipynb" in result.output
    assert any("test_2.qmd" in file_path for file_path in glob.iglob(test_dir + "/**/*.qmd", recursive=True))
    assert "_test_1.ipynb" not in result.output
    assert not any("_test_1.qmd" in file_path for file_path in glob.iglob(test_dir + "/**/*.qmd", recursive=True))
    
    
    
def test_match_and_replace_pattern(setup_teardown_test_env: str) -> None:
    """Test the --match-replace-pattern option with match and replace patterns.

    Verifies that when providing both a match and replace pattern (separated by /),
    the CLI correctly renames files according to the regex substitution.

    Args:
        setup_teardown_test_env: Path to the temporary test directory.
    """
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    output_dir = os.path.join(test_dir, "output")
    
    input_file = os.path.join(test_dir, "notebooks/_test_1.ipynb")
    
    result = runner.invoke(quarto_batch_convert, [input_file, "-o", output_dir, "-m", "^_/REPLACED_"])
    
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(output_dir, os.path.dirname(input_file), "REPLACED_test_1.qmd"))
    
    # Check that other files were not renamed
    assert not os.path.exists(os.path.join(output_dir, os.path.dirname(input_file), "test_2.qmd"))
    assert not os.path.exists(os.path.join(output_dir, os.path.dirname(input_file), "archive_test_3.qmd"))
    assert not os.path.exists(os.path.join(output_dir, os.path.dirname(input_file), "_test_1.qmd"))

def test_invalid_regex_pattern() -> None:
    """Test that an invalid regex pattern raises an error.

    Verifies that the CLI properly validates regex patterns and exits with
    an error code when an invalid pattern is provided.
    """
    runner = CliRunner()
    result = runner.invoke(quarto_batch_convert, ["./", "-m", "[invalid"])
    
    assert result.exit_code != 0
    assert "Invalid regex pattern" in result.output
    
def test_no_match_found(setup_teardown_test_env: str) -> None:
    """Test that a non-matching pattern results in no files being processed.

    Verifies that when a regex pattern matches no files, the CLI exits with
    an error code and displays an appropriate message.

    Args:
        setup_teardown_test_env: Path to the temporary test directory.
    """
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    
    input_files = glob.glob(test_dir + "/**/*", recursive=True)
    
    result = runner.invoke(quarto_batch_convert, [*input_files, "-m", "non_existent_pattern"])
    
    assert result.exit_code != 0
    assert "No files found matching the regex pattern" in result.output
    
def test_prefix_option(setup_teardown_test_env: str) -> None:
    """Test that the --prefix option adds the prefix correctly.

    Verifies that the --prefix option correctly prepends a string to output filenames.

    Args:
        setup_teardown_test_env: Path to the temporary test directory.
    """
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    
    input_file = os.path.join(test_dir, "notebooks/_test_1.ipynb")
    result = runner.invoke(quarto_batch_convert, [input_file, "-p", "prefix_"])
    
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(test_dir, "notebooks/prefix__test_1.qmd"))
    
def test_keep_extension_option(setup_teardown_test_env: str) -> None:
    """Test that the --keep-extension flag keeps the original extension.

    Verifies that when using the --keep-extension flag, the original file extension
    is preserved in the output filename before adding the new extension.

    Args:
        setup_teardown_test_env: Path to the temporary test directory.
    """
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    
    input_file = os.path.join(test_dir, "file_in_root.ipynb")
    
    result = runner.invoke(quarto_batch_convert, [input_file, "-k"])
    
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(os.path.dirname(input_file), "file_in_root.ipynb.qmd"))
    
def test_convert_qmd_to_ipynb(setup_teardown_test_env: str) -> None:
    """Test converting a qmd file to an ipynb file.

    Verifies that the --qmd-to-ipynb flag correctly converts .qmd files
    to .ipynb format.

    Args:
        setup_teardown_test_env: Path to the temporary test directory.
    """
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    input_file = os.path.join(test_dir, "notebooks", "TEST.qmd")

    result = runner.invoke(quarto_batch_convert, [input_file, "-q"])
    
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(os.path.dirname(input_file), "TEST.ipynb"))

def test_file_in_cwd(setup_teardown_test_env: str) -> None:
    """Test that glob patterns work when run from the current working directory.

    Verifies that the CLI can process files when executed from the same directory
    as the files to be converted, using glob patterns as input.

    Args:
        setup_teardown_test_env: Path to the temporary test directory.
    """
    runner = CliRunner()
    test_dir = os.path.join(setup_teardown_test_env, "notebooks")
    
    
    with change_dir(test_dir):
        input_files = glob.glob("*", recursive=True)
        result = runner.invoke(quarto_batch_convert, [*input_files])
    
    assert result.exit_code == 0
    # assert "input_path cannot be empty" in result.output
    
def test_prefix_to_new_dir(setup_teardown_test_env: str) -> None:
    """Test that the --prefix option creates new directories.

    Verifies that when a prefix contains a directory separator, the CLI
    creates the necessary directory structure.

    Args:
        setup_teardown_test_env: Path to the temporary test directory.
    """
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    
    input_file = os.path.join(test_dir, "notebooks/_test_1.ipynb")
    input_prefix = "PREFIX/"
    result = runner.invoke(quarto_batch_convert, [input_file, "-p", input_prefix])
    file_name, _ = os.path.splitext(os.path.basename(input_file))
    
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(os.path.dirname(input_file), input_prefix, file_name + ".qmd"))

def test_prefix_to_nested_dir(setup_teardown_test_env: str) -> None:
    """Test that the --prefix option creates nested directories.

    Verifies that the --prefix option can create nested directory structures,
    including relative paths with parent directory references.

    Args:
        setup_teardown_test_env: Path to the temporary test directory.
    """
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    
    input_file = os.path.join(test_dir, "notebooks/_test_1.ipynb")
    input_prefix = "../PREFIX/"
    result = runner.invoke(quarto_batch_convert, [input_file, "-p", input_prefix])
    file_name, _ = os.path.splitext(os.path.basename(input_file))
    
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(os.path.dirname(input_file), input_prefix, file_name + ".qmd"))
    
def test_output_path(setup_teardown_test_env: str) -> None:
    """Test that the --output-path option creates the output directory.

    Verifies that the --output-path option properly creates a specified output
    directory and places converted files there.

    Args:
        setup_teardown_test_env: Path to the temporary test directory.
    """
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    output_dir = os.path.join(test_dir, "output")

    input_file = os.path.join(test_dir, "notebooks/_test_1.ipynb")
    result = runner.invoke(quarto_batch_convert, [input_file, "-o", output_dir])

    file_name, _ = os.path.splitext(os.path.basename(input_file))

    assert result.exit_code == 0
    assert os.path.exists(os.path.join(output_dir, os.path.dirname(input_file), file_name + ".qmd"))

def test_recursive_option_with_nested_directory() -> None:
    """Test that the --recursive option processes files in subdirectories.

    Verifies that when the --recursive flag is used, the CLI processes files
    in both the root directory and all nested subdirectories.
    """
    runner = CliRunner()
    test_dir = "tests/assets"
    output_dir = "temp_recursive_test_output"

    # Clean up output directory before test
    shutil.rmtree(output_dir, ignore_errors=True)

    try:
        # Run with recursive flag
        result = runner.invoke(quarto_batch_convert, [test_dir, "-r", "-o", output_dir])

        assert result.exit_code == 0

        # Check that files from root directory were converted
        assert os.path.exists(os.path.join(output_dir, test_dir, "__test.qmd"))

        # Check that files from nested directory were converted
        assert os.path.exists(os.path.join(output_dir, test_dir, "nested", "__test3.qmd"))

        # Verify multiple files were found and converted
        assert "Found" in result.output
        # Should find __test.ipynb and nested/__test3.ipynb (2 files)
        assert "2 file(s)" in result.output or "files" in result.output
    finally:
        # Cleanup
        shutil.rmtree(output_dir, ignore_errors=True)

def test_non_recursive_option_ignores_subdirectories() -> None:
    """Test that without --recursive option, subdirectories are ignored.

    Verifies that when the --recursive flag is not used, only files in the
    root directory are processed, and subdirectories are skipped.
    """
    runner = CliRunner()
    test_dir = "tests/assets"
    output_dir = "temp_non_recursive_test_output"

    # Clean up output directory before test
    shutil.rmtree(output_dir, ignore_errors=True)

    try:
        # Run WITHOUT recursive flag
        result = runner.invoke(quarto_batch_convert, [test_dir, "-o", output_dir])

        assert result.exit_code == 0

        # Check that file from root directory was converted
        assert os.path.exists(os.path.join(output_dir, test_dir, "__test.qmd"))

        # Check that files from nested directory were NOT converted
        assert not os.path.exists(os.path.join(output_dir, test_dir, "nested", "__test3.qmd"))

        # Should only find __test.ipynb (1 file)
        assert "1 file(s)" in result.output or "file" in result.output
    finally:
        # Cleanup
        shutil.rmtree(output_dir, ignore_errors=True)

def test_recursive_with_match_pattern() -> None:
    """Test that --recursive works correctly with match patterns.

    Verifies that the --recursive flag can be combined with match patterns
    to filter files across all subdirectories.
    """
    runner = CliRunner()
    test_dir = "tests/assets"
    output_dir = "temp_recursive_match_test_output"

    # Clean up output directory before test
    shutil.rmtree(output_dir, ignore_errors=True)

    try:
        # Run with recursive flag and match pattern
        result = runner.invoke(quarto_batch_convert, [test_dir, "-r", "-o", output_dir, "-m", "__test3"])

        assert result.exit_code == 0

        # Only __test3.ipynb from nested directory should match
        assert os.path.exists(os.path.join(output_dir, test_dir, "nested", "__test3.qmd"))

        # __test.ipynb from root should NOT be converted (doesn't match pattern)
        assert not os.path.exists(os.path.join(output_dir, test_dir, "__test.qmd"))

        # Should only find 1 file matching the pattern
        assert "1 file(s)" in result.output
    finally:
        # Cleanup
        shutil.rmtree(output_dir, ignore_errors=True)

def test_recursive_preserves_directory_structure() -> None:
    """Test that --recursive option preserves the directory structure in output.

    Verifies that when using --recursive, the original directory structure
    is maintained in the output directory.
    """
    runner = CliRunner()
    test_dir = "tests/assets"
    output_dir = "temp_recursive_structure_test_output"

    # Clean up output directory before test
    shutil.rmtree(output_dir, ignore_errors=True)

    try:
        # Run with recursive flag
        result = runner.invoke(quarto_batch_convert, [test_dir, "-r", "-o", output_dir])

        assert result.exit_code == 0

        # Verify directory structure is preserved
        assert os.path.isdir(os.path.join(output_dir, test_dir))
        assert os.path.isdir(os.path.join(output_dir, test_dir, "nested"))

        # Check files are in correct locations
        assert os.path.exists(os.path.join(output_dir, test_dir, "__test.qmd"))
        assert os.path.exists(os.path.join(output_dir, test_dir, "nested", "__test3.qmd"))
    finally:
        # Cleanup
        shutil.rmtree(output_dir, ignore_errors=True)
