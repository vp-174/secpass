import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def test_password():
    return "test_password_123"


@pytest.fixture
def keyfile(temp_dir):
    path = temp_dir / "keyfile.key"
    path.write_bytes(b"additional_key_material_16bytes")
    return path