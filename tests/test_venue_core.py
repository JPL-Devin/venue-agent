import pytest
import os
import json
from unittest.mock import patch, MagicMock, call

import redis


# ---------------------------------------------------------------------------
# Test _get_redis
# ---------------------------------------------------------------------------

class TestGetRedis:

    @patch.dict(os.environ, {}, clear=True)
    def test_get_redis_default_config(self):
        """Should use localhost:6379 when env vars not set."""
        # Re-import to pick up cleared env vars
        import importlib
        import core.venue_core as vc
        # We can't easily re-trigger module-level code, so test _get_redis
        # by patching redis.StrictRedis and checking the call
        with patch("core.venue_core.redis.StrictRedis") as mock_redis:
            # Temporarily override the module-level vars
            orig_host = vc._redis_host
            orig_port = vc._redis_port
            orig_pw = vc._redis_password
            try:
                vc._redis_host = "localhost"
                vc._redis_port = 6379
                vc._redis_password = None
                vc._get_redis()
                mock_redis.assert_called_once_with(
                    host="localhost", port=6379, db=0, password=None
                )
            finally:
                vc._redis_host = orig_host
                vc._redis_port = orig_port
                vc._redis_password = orig_pw

    def test_get_redis_custom_host(self):
        """Should read REDIS_HOST from environment."""
        import core.venue_core as vc
        with patch("core.venue_core.redis.StrictRedis") as mock_redis:
            orig = vc._redis_host
            try:
                vc._redis_host = "redis.example.com"
                vc._get_redis()
                assert mock_redis.call_args[1]["host"] == "redis.example.com"
            finally:
                vc._redis_host = orig

    def test_get_redis_custom_port(self):
        """Should read REDIS_PORT from environment."""
        import core.venue_core as vc
        with patch("core.venue_core.redis.StrictRedis") as mock_redis:
            orig = vc._redis_port
            try:
                vc._redis_port = 6380
                vc._get_redis()
                assert mock_redis.call_args[1]["port"] == 6380
            finally:
                vc._redis_port = orig

    def test_get_redis_with_password(self):
        """Should pass REDIS_PASSWORD when set."""
        import core.venue_core as vc
        with patch("core.venue_core.redis.StrictRedis") as mock_redis:
            orig = vc._redis_password
            try:
                vc._redis_password = "s3cret"
                vc._get_redis()
                assert mock_redis.call_args[1]["password"] == "s3cret"
            finally:
                vc._redis_password = orig

    def test_get_redis_no_password(self):
        """Should pass None password when REDIS_PASSWORD not set."""
        import core.venue_core as vc
        with patch("core.venue_core.redis.StrictRedis") as mock_redis:
            orig = vc._redis_password
            try:
                vc._redis_password = None
                vc._get_redis()
                assert mock_redis.call_args[1]["password"] is None
            finally:
                vc._redis_password = orig


# ---------------------------------------------------------------------------
# Test start_custom_script
# ---------------------------------------------------------------------------

class TestStartCustomScript:

    def test_start_custom_script_hash_mismatch(self, tmp_path):
        """Should raise error when script hash doesn't match."""
        import core.venue_core as vc

        # Create a real script file so isfile passes
        script_file = tmp_path / "my_script.py"
        script_file.write_text("print('hello')")

        with patch.object(vc, "_custom_script_base_dir", str(tmp_path)):
            with pytest.raises(Exception, match="did not match"):
                vc.start_custom_script(
                    script_hash="0000000000000000000000000000000000000000000000000000000000000000",
                    script_path="my_script.py",
                    inputs={},
                    outputs={},
                )

    def test_start_custom_script_stores_in_redis(self, tmp_path):
        """Should store run metadata in Redis with correct key."""
        import core.venue_core as vc
        import hashlib

        # Create a real script file
        script_file = tmp_path / "my_script.py"
        script_file.write_text("print('hello')")
        script_file.chmod(0o755)

        # Compute real hash
        real_hash = hashlib.sha256(script_file.read_bytes()).hexdigest()

        # Mock launch_script to avoid subprocess/Redis/file-system side effects
        # while still exercising hash validation and the return value.
        with patch.object(vc, "_custom_script_base_dir", str(tmp_path)), \
             patch.object(vc, "launch_script", return_value="test-run-id") as mock_launch:

            result = vc.start_custom_script(
                script_hash=real_hash,
                script_path="my_script.py",
                inputs={"key": "value"},
                outputs={},
            )

        assert result == {"scriptRunId": "test-run-id"}
        # Verify launch_script was called with the correct joined path and args
        mock_launch.assert_called_once()
        call_args = mock_launch.call_args[0]
        assert call_args[0].endswith("my_script.py")
        assert call_args[1] == {"key": "value"}
        assert call_args[2] == {}


# ---------------------------------------------------------------------------
# Test halt_custom_script
# ---------------------------------------------------------------------------

class TestHaltCustomScript:

    def test_halt_custom_script_cleans_redis(self):
        """Should delete Redis entry after halting."""
        import core.venue_core as vc

        redis_data = json.dumps({
            "process_id": "99999",
            "output_path": "/tmp/out.json",
            "logfile_path": "/tmp/script.log",
            "logfile_url": "custom_script/abc/files",
            "custom_script_temp_dir": "/tmp/cs/abc",
        })

        mock_redis_instance = MagicMock()
        mock_redis_instance.get.return_value = redis_data

        with patch("core.venue_core._get_redis", return_value=mock_redis_instance), \
             patch("os.kill", side_effect=OSError):
            # OSError on os.kill means process already dead; killpg will also
            # be attempted but may fail – that's fine.
            with patch("os.killpg", side_effect=Exception("no such process")):
                result = vc.halt_custom_script("abc-run-id")

        assert result == ""
        mock_redis_instance.delete.assert_called_once_with("abc-run-id")

    def test_halt_custom_script_invalid_id(self):
        """Should handle missing script_run_id."""
        import core.venue_core as vc

        mock_redis_instance = MagicMock()
        mock_redis_instance.get.return_value = None  # key not found

        with patch("core.venue_core._get_redis", return_value=mock_redis_instance):
            with pytest.raises(Exception, match="was not found"):
                vc.halt_custom_script("nonexistent-id")


# ---------------------------------------------------------------------------
# Test get_custom_script_status
# ---------------------------------------------------------------------------

class TestGetCustomScriptStatus:

    def test_get_status_missing_run_id(self):
        """Should handle missing script_run_id in Redis."""
        import core.venue_core as vc

        mock_redis_instance = MagicMock()
        mock_redis_instance.get.return_value = None  # key not found

        with patch("core.venue_core._get_redis", return_value=mock_redis_instance):
            with pytest.raises(Exception, match="was not found"):
                vc.get_custom_script_status("nonexistent-id")
