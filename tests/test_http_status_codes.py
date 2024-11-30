import pytest
from pydantic import ValidationError, BaseModel
from validators.http_status_codes import HTTPStatusCode

class ValidationModel(BaseModel):
    status_code: HTTPStatusCode

def test_valid_status_code():
    # Test with a valid status code
    status_code = ValidationModel(status_code=200)
    assert status_code.status_code == 200

def test_invalid_status_code():
    # Test with an invalid status code
    with pytest.raises(ValidationError):
        ValidationModel(status_code=99)  # Below the valid range

    with pytest.raises(ValidationError):
        ValidationModel(status_code=600)  # Above the valid range

def test_unassigned_status_code():
    # Test with an unassigned status code
    with pytest.warns(UserWarning, match="Status code 106 is unassigned or invalid."):
        ValidationModel(status_code=106)

if __name__ == "__main__":
    pytest.main()