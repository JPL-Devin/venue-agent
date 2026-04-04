import pytest
from pydantic import ValidationError

from core.schema import (
    ErrorResponse,
    HealthStatus,
    HealthStatusEnum,
    ScriptRunInfo,
    ScriptStartBodyModel,
    ScriptStatusResp,
)


class TestScriptStartBodyModel:
    def test_valid_relative_path(self):
        """Should accept a valid relative scriptPath"""
        model = ScriptStartBodyModel(
            scriptName="test_script",
            scriptPath="scripts/my_script.py",
            scriptHash="abc123",
            inputs={},
            outputs={},
        )
        assert model.scriptPath == "scripts/my_script.py"

    def test_reject_absolute_path(self):
        """Should reject absolute paths starting with /"""
        with pytest.raises(ValidationError):
            ScriptStartBodyModel(
                scriptName="test",
                scriptPath="/etc/passwd",
                scriptHash="abc",
                inputs={},
                outputs={},
            )

    def test_reject_path_traversal(self):
        """Should reject paths containing .."""
        with pytest.raises(ValidationError):
            ScriptStartBodyModel(
                scriptName="test",
                scriptPath="../../../etc/passwd",
                scriptHash="abc",
                inputs={},
                outputs={},
            )

    def test_reject_home_directory(self):
        """Should reject paths containing ~"""
        with pytest.raises(ValidationError):
            ScriptStartBodyModel(
                scriptName="test",
                scriptPath="~/malicious.py",
                scriptHash="abc",
                inputs={},
                outputs={},
            )

    def test_require_script_name(self):
        """Should require scriptName field"""
        with pytest.raises(ValidationError):
            ScriptStartBodyModel(
                scriptPath="scripts/test.py",
                scriptHash="abc",
                inputs={},
                outputs={},
            )

    def test_require_script_path(self):
        """Should require scriptPath field"""
        with pytest.raises(ValidationError):
            ScriptStartBodyModel(
                scriptName="test",
                scriptHash="abc",
                inputs={},
                outputs={},
            )

    def test_require_script_hash(self):
        """Should require scriptHash field"""
        with pytest.raises(ValidationError):
            ScriptStartBodyModel(
                scriptName="test",
                scriptPath="scripts/test.py",
                inputs={},
                outputs={},
            )

    def test_optional_inputs_outputs(self):
        """Should accept model without inputs and outputs (they have defaults)"""
        model = ScriptStartBodyModel(
            scriptName="test",
            scriptPath="scripts/test.py",
            scriptHash="abc123",
        )
        assert model.inputs == {}
        assert model.outputs == {}


class TestHealthStatus:
    def test_health_ok_status(self):
        """Should create HealthStatus with OK"""
        status = HealthStatus(status=HealthStatusEnum.OK, message="")
        assert status.status == HealthStatusEnum.OK

    def test_health_error_status(self):
        """Should create HealthStatus with ERROR"""
        status = HealthStatus(status=HealthStatusEnum.ERROR, message="something broke")
        assert status.status == HealthStatusEnum.ERROR
        assert status.message == "something broke"


class TestErrorResponse:
    def test_error_response(self):
        """Should create ErrorResponse with message"""
        resp = ErrorResponse(message="something went wrong")
        assert resp.message == "something went wrong"

    def test_error_response_default_message(self):
        """Should create ErrorResponse with default empty message"""
        resp = ErrorResponse()
        assert resp.message == ""


class TestScriptRunInfo:
    def test_script_run_info(self):
        """Should create ScriptRunInfo with scriptRunId"""
        info = ScriptRunInfo(scriptRunId="abc-123")
        assert info.scriptRunId == "abc-123"

    def test_script_run_info_requires_id(self):
        """Should require scriptRunId field"""
        with pytest.raises(ValidationError):
            ScriptRunInfo()


class TestScriptStatusResp:
    def test_script_status_resp_defaults(self):
        """Should create ScriptStatusResp with default values"""
        resp = ScriptStatusResp()
        assert resp.logfile_url == ""
        assert resp.logfile_path == ""
        assert resp.custom_script_status.value == "PENDING"
        assert resp.logfile_lines == []
