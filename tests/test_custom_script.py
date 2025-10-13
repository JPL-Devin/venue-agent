"""
Test that the VenueServer `/api/v3/custom_script/start` endpoint can launch the
example script `tests/custom_script_for_tests/test_cs.py`.

The test:
1. Computes the SHA‑256 hash of the script file (required by the API).
2. Posts a JSON payload that follows the `ScriptStartBodyModel` schema.
3. Asserts a 200 response and the presence of a `scriptRunId` in the reply.
"""

import hashlib
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app


def _sha256(file_path: Path) -> str:
    """Return the SHA‑256 hash of *file_path* as a hex string."""
    hasher = hashlib.sha256()
    hasher.update(file_path.read_bytes())
    return hasher.hexdigest()

# ----------------------------------------------------------------------
# Test: start a custom script with a valid JWT (authenticated request).
# ----------------------------------------------------------------------
def test_start_custom_script_success(auth_client: TestClient):
    """
    Verify that the `/api/v3/custom_script/start` endpoint works when a
    correctly‑signed JWT is supplied (the `client` fixture adds the header).
    """
    script_path = Path(__file__).parent / "custom_script_for_tests" / "test_cs.py"
    assert script_path.is_file(), f"Script not found: {script_path}"

    inputs = {'inputs': {'duration': 30,
                         'script_result': 'PASS'}}

    payload = {
        "scriptName": "test_cs",
        "scriptPath": "custom_script_for_tests/test_cs.py",
        "scriptHash": _sha256(script_path),
        "inputs": inputs,    # No inputs needed for this script.
        "outputs": {"custom_script_status": "PENDING"}
    }

    response = auth_client.post("/api/v3/custom_script/start", json=payload)

    assert response.status_code == 200, (
        f"Unexpected status {response.status_code}: {response.text}"
    )
    data = response.json()
    assert "scriptRunId" in data, "Response JSON missing 'scriptRunId'"

@pytest.mark.timeout(35)
def test_status_custom_script_pass_30(auth_client: TestClient):
    """
    Verify that the `/api/v3/custom_script/` endpoint works when a
    correctly‑signed JWT is supplied (the `client` fixture adds the header).
    """
    script_path = Path(__file__).parent / "custom_script_for_tests" / "test_cs.py"
    assert script_path.is_file(), f"Script not found: {script_path}"

    inputs = {'inputs': {'duration': 30,
                         'script_result': 'PASS'}}

    payload = {
        "scriptName": "test_cs",
        "scriptPath": "custom_script_for_tests/test_cs.py",
        "scriptHash": _sha256(script_path),
        "inputs": inputs,    # No inputs needed for this script.
        "outputs": {"custom_script_status": "PENDING"}
    }

    response = auth_client.post("/api/v3/custom_script/start", json=payload)

    assert response.status_code == 200, (
        f"Unexpected status {response.status_code}: {response.text}"
    )
    data = response.json()
    assert "scriptRunId" in data, "Response JSON missing 'scriptRunId'"

    script_run_id = data["scriptRunId"]

    script_status = ""

    while script_status != "PASS":
        response = auth_client.get(f"/api/v3/custom_script/{script_run_id}")

        assert response.status_code == 200, (
            f"Unexpected status {response.status_code}: {response.text}"
        )
        data = response.json()

        script_status = data["custom_script_status"]
        time.sleep(1)

    assert script_status == "PASS", (f"Unexpected script completion status {script_status}")


@pytest.mark.timeout(60)
def test_status_custom_script_halt_30(auth_client: TestClient):
    """
    Verify that the `/api/v3/custom_script/` endpoint works when a
    correctly‑signed JWT is supplied (the `client` fixture adds the header).
    """
    script_path = Path(__file__).parent / "custom_script_for_tests" / "test_cs.py"
    assert script_path.is_file(), f"Script not found: {script_path}"

    inputs = {'inputs': {'duration': 60,
                         'script_result': 'PASS'}}

    payload = {
        "scriptName": "test_cs",
        "scriptPath": "custom_script_for_tests/test_cs.py",
        "scriptHash": _sha256(script_path),
        "inputs": inputs,    # No inputs needed for this script.
        "outputs": {"custom_script_status": "PENDING"}
    }

    response = auth_client.post("/api/v3/custom_script/start", json=payload)

    assert response.status_code == 200, (
        f"Unexpected status {response.status_code}: {response.text}"
    )
    data = response.json()
    assert "scriptRunId" in data, "Response JSON missing 'scriptRunId'"

    time.sleep(10)

    script_run_id = data["scriptRunId"]

    script_status = ""

    while script_status != "PENDING":
        response = auth_client.get(f"/api/v3/custom_script/{script_run_id}")

        assert response.status_code == 200, (
            f"Unexpected status {response.status_code}: {response.text}"
        )
        data = response.json()

        script_status = data["custom_script_status"]
        time.sleep(1)

    assert script_status == "PENDING", (f"Unexpected script completion status {script_status}")

    response = auth_client.post(f"/api/v3/custom_script/{script_run_id}/halt")

    assert response.status_code == 204, (
        f"Unexpected status {response.status_code}: {response.text}"
    )


@pytest.mark.timeout(30)
def test_status_custom_script_halt_completed_script(auth_client: TestClient):
    """
    Verify that the `/api/v3/custom_script/` endpoint works when a
    correctly‑signed JWT is supplied (the `client` fixture adds the header).
    """
    script_path = Path(__file__).parent / "custom_script_for_tests" / "test_cs.py"
    assert script_path.is_file(), f"Script not found: {script_path}"

    inputs = {'inputs': {'duration': 10,
                         'script_result': 'PASS'}}

    payload = {
        "scriptName": "test_cs",
        "scriptPath": "custom_script_for_tests/test_cs.py",
        "scriptHash": _sha256(script_path),
        "inputs": inputs,    # No inputs needed for this script.
        "outputs": {"custom_script_status": "PENDING"}
    }

    response = auth_client.post("/api/v3/custom_script/start", json=payload)

    assert response.status_code == 200, (
        f"Unexpected status {response.status_code}: {response.text}"
    )
    data = response.json()
    assert "scriptRunId" in data, "Response JSON missing 'scriptRunId'"

    script_run_id = data["scriptRunId"]

    script_status = ""

    while script_status != "PASS":
        response = auth_client.get(f"/api/v3/custom_script/{script_run_id}")

        assert response.status_code == 200, (
            f"Unexpected status {response.status_code}: {response.text}"
        )
        data = response.json()

        script_status = data["custom_script_status"]
        time.sleep(1)

    assert script_status == "PASS", (f"Unexpected script completion status {script_status}")

    response = auth_client.post(f"/api/v3/custom_script/{script_run_id}/halt")

    assert response.status_code == 204, (
        f"Unexpected status {response.status_code}: {response.text}"
    )

@pytest.mark.timeout(30)
def test_halt_custom_script_invalid_id(auth_client: TestClient):
    """
    Verify that the `/api/v3/custom_script/` endpoint works when a
    correctly‑signed JWT is supplied (the `client` fixture adds the header).
    """

    script_run_id = "InvalidID"

    response = auth_client.post(f"/api/v3/custom_script/{script_run_id}/halt")

    assert response.status_code == 400, (
        f"Unexpected status {response.status_code}: {response.text}"
    )


@pytest.mark.timeout(35)
def test_custom_script_large_response(auth_client: TestClient):
    """
    Verify that the `/api/v3/custom_script/` endpoint works when a
    correctly‑signed JWT is supplied (the `client` fixture adds the header).
    """
    script_path = Path(__file__).parent / "custom_script_for_tests" / "test_cs.py"
    assert script_path.is_file(), f"Script not found: {script_path}"

    inputs = {'inputs': {'duration': 30,
                         'script_result': 'PASS',
                         "output_random_data": 1000000}}

    payload = {
        "scriptName": "test_cs",
        "scriptPath": "custom_script_for_tests/test_cs.py",
        "scriptHash": _sha256(script_path),
        "inputs": inputs,    # No inputs needed for this script.
        "outputs": {"custom_script_status": "PENDING"}
    }

    response = auth_client.post("/api/v3/custom_script/start", json=payload)

    assert response.status_code == 200, (
        f"Unexpected status {response.status_code}: {response.text}"
    )
    data = response.json()
    assert "scriptRunId" in data, "Response JSON missing 'scriptRunId'"

    time.sleep(20)

    script_run_id = data["scriptRunId"]

    script_status = ""

    while script_status != "PASS":
        response = auth_client.get(f"/api/v3/custom_script/{script_run_id}")

        assert response.status_code == 200, (
            f"Unexpected status {response.status_code}: {response.text}"
        )
        data = response.json()

        script_status = data["custom_script_status"]
        time.sleep(1)

    assert script_status == "PASS", f"Unexpected script completion status {script_status}"


@pytest.mark.timeout(45)
def test_custom_script_files(auth_client: TestClient):
    """
    Verify that the `/api/v3/custom_script/` endpoint works when a
    correctly‑signed JWT is supplied (the `client` fixture adds the header).
    """
    script_path = Path(__file__).parent / "custom_script_for_tests" / "test_cs.py"
    assert script_path.is_file(), f"Script not found: {script_path}"

    inputs = {'inputs': {'duration': 30,
                         'script_result': 'PASS',
                         "output_random_data": 1000000}}

    payload = {
        "scriptName": "test_cs",
        "scriptPath": "custom_script_for_tests/test_cs.py",
        "scriptHash": _sha256(script_path),
        "inputs": inputs,    # No inputs needed for this script.
        "outputs": {"custom_script_status": "PENDING"}
    }

    response = auth_client.post("/api/v3/custom_script/start", json=payload)

    assert response.status_code == 200, (
        f"Unexpected status {response.status_code}: {response.text}"
    )
    data = response.json()
    assert "scriptRunId" in data, "Response JSON missing 'scriptRunId'"

    script_run_id = data["scriptRunId"]

    script_status = ""

    while script_status != "PASS":
        response = auth_client.get(f"/api/v3/custom_script/{script_run_id}")

        assert response.status_code == 200, (
            f"Unexpected status {response.status_code}: {response.text}"
        )
        data = response.json()

        script_status = data["custom_script_status"]
        time.sleep(1)

    assert script_status == "PASS", (f"Unexpected script completion status {script_status}")

    files = auth_client.get(f"/api/v3/custom_script/{script_run_id}/files")

    assert files.status_code == 200, f"Unexpected status {files.status_code}: {files.text}"

@pytest.mark.timeout(100)
def test_custom_script_heavy_writes_no_wait(auth_client: TestClient):
    """
    Verify that the `/api/v3/custom_script/` endpoint works when a
    correctly‑signed JWT is supplied (the `client` fixture adds the header).
    """
    script_path = Path(__file__).parent / "custom_script_for_tests" / "test_cs.py"
    assert script_path.is_file(), f"Script not found: {script_path}"

    inputs = {'inputs': {'duration': 90,
                         'script_result': 'PASS',
                         'heavy_writes' : 'true',
                         "output_random_data": 1000000}}

    payload = {
        "scriptName": "test_cs",
        "scriptPath": "custom_script_for_tests/test_cs.py",
        "scriptHash": _sha256(script_path),
        "inputs": inputs,    # No inputs needed for this script.
        "outputs": {"custom_script_status": "PENDING"}    # No predefined outputs.
    }


    response = auth_client.post("/api/v3/custom_script/start", json=payload)

    assert response.status_code == 200, (
        f"Unexpected status {response.status_code}: {response.text}"
    )
    data = response.json()
    assert "scriptRunId" in data, "Response JSON missing 'scriptRunId'"

    script_run_id = data["scriptRunId"]

    script_status = ""

    while script_status != "PASS":
        response = auth_client.get(f"/api/v3/custom_script/{script_run_id}")

        assert response.status_code == 200, (
            f"Unexpected status {response.status_code}: {response.text}"
        )
        data = response.json()

        script_status = data["custom_script_status"]

        time.sleep(0.5)

    assert script_status == "PASS", (f"Unexpected script completion status {script_status}")

# ----------------------------------------------------------------------
# Test: start a custom script without any JWT (should be rejected).
# ----------------------------------------------------------------------
def test_start_custom_script_unauthenticated():
    """
    Ensure the API returns **401 Unauthorized** when the request lacks a JWT.
    This uses a fresh `TestClient` without the auth header that the `client`
    fixture injects.
    """
    # Fresh client – no Authorization header.
    client_no_auth = TestClient(app)

    script_path = Path(__file__).parent / "custom_script_for_tests" / "test_cs.py"
    assert script_path.is_file(), f"Script not found: {script_path}"

    payload = {
        "scriptName": "test_cs",
        "scriptPath": "custom_script_for_tests/test_cs.py",
        "scriptHash": _sha256(script_path),
        "inputs": {},
        "outputs": {}
    }

    response = client_no_auth.post("/api/v3/custom_script/start", json=payload)

    assert response.status_code == 401, (
        f"Expected 401 Unauthorized, got {response.status_code}"
    )
  