import pytest
from unittest.mock import patch
from quarto_batch_convert.quarto_batch_convert import check_quarto_installation

@pytest.fixture
def mock_which():
    with patch('shutil.which') as mock:
        yield mock

def test_quarto_installed(mock_which):
    """
    Test that check_quarto_installation() does not raise an exception 
    when 'quarto' command is found.
    """
    mock_which.return_value = '/path/to/quarto'
    check_quarto_installation()

def test_quarto_not_installed(mock_which):
    """
    Test that check_quarto_installation() raises SystemExit with code 1 
    when 'quarto' command is not found.
    """
    mock_which.return_value = None
    with pytest.raises(SystemExit) as excinfo:
        check_quarto_installation()
    assert excinfo.value.code == 1