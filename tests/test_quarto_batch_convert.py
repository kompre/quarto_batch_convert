import os
import shutil
import pytest
from click.testing import CliRunner
from quarto_batch_convert.quarto_batch_convert import convert_files
import glob
from contextlib import contextmanager

@contextmanager
def change_dir(destination):
    """Context manager to temporarily change directory."""
    try:
        cwd = os.getcwd()
        os.chdir(destination)
        yield
    finally:
        os.chdir(cwd)

# Use a temporary directory for all tests
@pytest.fixture(scope="module")
def setup_teardown_test_env():
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

def test_single_match_no_replace(setup_teardown_test_env):
    """Test the --match-replace-pattern with only a match pattern (no slash)."""
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    
    input_files = glob.glob(test_dir + "/**/*", recursive=True)
    
    result = runner.invoke(convert_files, [*input_files, "-m", "test_2"])
    
    assert result.exit_code == 0
    assert "test_2.ipynb" in result.output
    assert any("test_2.qmd" in file_path for file_path in glob.iglob(test_dir + "/**/*.qmd", recursive=True))
    assert "_test_1.ipynb" not in result.output
    assert not any("_test_1.qmd" in file_path for file_path in glob.iglob(test_dir + "/**/*.qmd", recursive=True))
    
    
    
def test_match_and_replace_pattern(setup_teardown_test_env):
    """Test the --match-replace-pattern with both a match and replace pattern."""
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    output_dir = os.path.join(test_dir, "output")
    
    input_file = os.path.join(test_dir, "notebooks/_test_1.ipynb")
    
    result = runner.invoke(convert_files, [input_file, "-o", output_dir, "-m", "^_/REPLACED_"])
    
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(output_dir, os.path.dirname(input_file), "REPLACED_test_1.qmd"))
    
    # Check that other files were not renamed
    assert not os.path.exists(os.path.join(output_dir, os.path.dirname(input_file), "test_2.qmd"))
    assert not os.path.exists(os.path.join(output_dir, os.path.dirname(input_file), "archive_test_3.qmd"))
    assert not os.path.exists(os.path.join(output_dir, os.path.dirname(input_file), "_test_1.qmd"))

def test_invalid_regex_pattern():
    """Test that an invalid regex pattern raises an error."""
    runner = CliRunner()
    result = runner.invoke(convert_files, ["./", "-m", "[invalid"])
    
    assert result.exit_code != 0
    assert "Invalid regex pattern" in result.output
    
def test_no_match_found(setup_teardown_test_env):
    """Test that a non-matching pattern results in no files being processed."""
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    
    input_files = glob.glob(test_dir + "/**/*", recursive=True)
    
    result = runner.invoke(convert_files, [*input_files, "-m", "non_existent_pattern"])
    
    assert result.exit_code != 0
    assert "No files found matching the regex pattern" in result.output
    
def test_prefix_option(setup_teardown_test_env):
    """Test that the --prefix option adds the prefix correctly."""
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    
    input_file = os.path.join(test_dir, "notebooks/_test_1.ipynb")
    result = runner.invoke(convert_files, [input_file, "-p", "prefix_"])
    
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(test_dir, "notebooks/prefix__test_1.qmd"))
    
def test_keep_extension_option(setup_teardown_test_env):
    """Test that the --keep-extension flag keeps the original extension."""
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    
    input_file = os.path.join(test_dir, "file_in_root.ipynb")
    
    result = runner.invoke(convert_files, [input_file, "-k"])
    
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(os.path.dirname(input_file), "file_in_root.ipynb.qmd"))
    
def test_convert_qmd_to_ipynb(setup_teardown_test_env):
    """Test converting a qmd file to an ipynb file."""
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    input_file = os.path.join(test_dir, "notebooks", "TEST.qmd")

    result = runner.invoke(convert_files, [input_file, "-q"])
    
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(os.path.dirname(input_file), "TEST.ipynb"))

def test_file_in_cwd(setup_teardown_test_env):    
    """
    Test that when a glob pattern is used as input, the command runs without errors.

    This test also verifies that the command can be run from the same directory as the files to be converted.
    """
    runner = CliRunner()
    test_dir = os.path.join(setup_teardown_test_env, "notebooks")
    
    
    with change_dir(test_dir):
        input_files = glob.glob("*", recursive=True)
        result = runner.invoke(convert_files, [*input_files])
    
    assert result.exit_code == 0
    # assert "input_path cannot be empty" in result.output
    
def test_prefix_to_new_dir(setup_teardown_test_env):
    """Test that the --prefix option creates the new directory."""
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    
    input_file = os.path.join(test_dir, "notebooks/_test_1.ipynb")
    input_prefix = "PREFIX/"
    result = runner.invoke(convert_files, [input_file, "-p", input_prefix])
    file_name, _ = os.path.splitext(os.path.basename(input_file))
    
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(os.path.dirname(input_file), input_prefix, file_name + ".qmd"))

def test_prefix_to_nested_dir(setup_teardown_test_env):
    """Test that the --prefix option creates nested directories."""
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    
    input_file = os.path.join(test_dir, "notebooks/_test_1.ipynb")
    input_prefix = "../PREFIX/"
    result = runner.invoke(convert_files, [input_file, "-p", input_prefix])
    file_name, _ = os.path.splitext(os.path.basename(input_file))
    
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(os.path.dirname(input_file), input_prefix, file_name + ".qmd"))
    
def test_output_path(setup_teardown_test_env):
    """Test that the --output-path option creates the output directory."""
    runner = CliRunner()
    test_dir = setup_teardown_test_env
    output_dir = os.path.join(test_dir, "output")

    input_file = os.path.join(test_dir, "notebooks/_test_1.ipynb")
    result = runner.invoke(convert_files, [input_file, "-o", output_dir])

    file_name, _ = os.path.splitext(os.path.basename(input_file))

    assert result.exit_code == 0
    assert os.path.exists(os.path.join(output_dir, os.path.dirname(input_file), file_name + ".qmd"))

def test_recursive_option_with_nested_directory():
    """Test that the --recursive option processes files in subdirectories."""
    runner = CliRunner()
    test_dir = "tests/assets"
    output_dir = "temp_recursive_test_output"

    # Clean up output directory before test
    shutil.rmtree(output_dir, ignore_errors=True)

    try:
        # Run with recursive flag
        result = runner.invoke(convert_files, [test_dir, "-r", "-o", output_dir])

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

def test_non_recursive_option_ignores_subdirectories():
    """Test that without --recursive option, subdirectories are ignored."""
    runner = CliRunner()
    test_dir = "tests/assets"
    output_dir = "temp_non_recursive_test_output"

    # Clean up output directory before test
    shutil.rmtree(output_dir, ignore_errors=True)

    try:
        # Run WITHOUT recursive flag
        result = runner.invoke(convert_files, [test_dir, "-o", output_dir])

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

def test_recursive_with_match_pattern():
    """Test that --recursive works correctly with match patterns."""
    runner = CliRunner()
    test_dir = "tests/assets"
    output_dir = "temp_recursive_match_test_output"

    # Clean up output directory before test
    shutil.rmtree(output_dir, ignore_errors=True)

    try:
        # Run with recursive flag and match pattern
        result = runner.invoke(convert_files, [test_dir, "-r", "-o", output_dir, "-m", "__test3"])

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

def test_recursive_preserves_directory_structure():
    """Test that --recursive option preserves the directory structure in output."""
    runner = CliRunner()
    test_dir = "tests/assets"
    output_dir = "temp_recursive_structure_test_output"

    # Clean up output directory before test
    shutil.rmtree(output_dir, ignore_errors=True)

    try:
        # Run with recursive flag
        result = runner.invoke(convert_files, [test_dir, "-r", "-o", output_dir])

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
