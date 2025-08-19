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
    
    result = runner.invoke(convert_files, [test_dir, "-m", "test_2", "-r"])
    
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
    
    result = runner.invoke(convert_files, [test_dir, "-m", "non_existent_pattern"])
    
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
        result = runner.invoke(convert_files, ["*"])
    
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
