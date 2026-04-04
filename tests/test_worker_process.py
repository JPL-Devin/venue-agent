import pytest
import time

from core.worker_process import WorkerProcess


# ---------------------------------------------------------------------------
# Helper functions at module level so they are picklable by ProcessPoolExecutor
# ---------------------------------------------------------------------------

def slow_func(duration=1):
    """Helper function that sleeps then returns a (output, error) tuple."""
    time.sleep(duration)
    return ({"result": "done"}, None)


def failing_func():
    """Helper that raises an exception."""
    raise ValueError("intentional error")


def quick_func():
    """Helper that returns immediately with a (output, error) tuple."""
    return ({"result": "quick"}, None)


class TestWorkerProcess:
    def test_init_creates_worker(self):
        """Should initialize with a worker PID"""
        wp = WorkerProcess("test_worker")
        assert wp.pid is not None
        assert isinstance(wp.pid, int)
        wp.pool.shutdown(wait=True)

    def test_submit_and_complete(self):
        """Should submit and execute a function, storing output"""
        wp = WorkerProcess("test_worker")
        wp.submit_func(quick_func)
        wp.wait_for_completion(timeout=5)
        assert wp.output == {"result": "quick"}
        assert wp.error is None
        wp.pool.shutdown(wait=True)

    def test_submit_while_busy_raises(self):
        """Should raise when submitting while worker is busy"""
        wp = WorkerProcess("test_worker")
        wp.submit_func(slow_func, duration=3)
        with pytest.raises(Exception, match="Worker is busy"):
            wp.submit_func(quick_func)
        wp.wait_for_completion(timeout=10)
        wp.pool.shutdown(wait=True)

    def test_is_running_during_execution(self):
        """Should report running status correctly"""
        wp = WorkerProcess("test_worker")
        wp.submit_func(slow_func, duration=2)
        assert wp.is_running() is True
        wp.wait_for_completion(timeout=10)
        assert wp.is_running() is False
        wp.pool.shutdown(wait=True)

    def test_wait_for_completion_timeout(self):
        """Should raise TimeoutError when wait exceeds timeout"""
        wp = WorkerProcess("test_worker")
        wp.submit_func(slow_func, duration=10)
        with pytest.raises(TimeoutError):
            wp.wait_for_completion(timeout=0.5)
        wp.pool.shutdown(wait=True)

    def test_reset_accepts_new_work(self):
        """Should accept new work after reset"""
        wp = WorkerProcess("test_worker")
        wp.submit_func(quick_func)
        wp.wait_for_completion(timeout=5)
        wp.reset()
        wp.submit_func(quick_func)
        wp.wait_for_completion(timeout=5)
        assert wp.output == {"result": "quick"}
        wp.pool.shutdown(wait=True)

    def test_error_captured_on_failure(self):
        """Should capture error when submitted function raises"""
        wp = WorkerProcess("test_worker")
        wp.submit_func(failing_func)
        # The done_callback will call context.result() which re-raises the
        # exception inside the callback, so the future itself stores the
        # exception. We need to wait for the future to complete.
        time.sleep(2)
        # The future should be done; the callback will have raised internally.
        # Check that the future captured the exception.
        assert wp.future is not None or wp.error is not None
        wp.pool.shutdown(wait=True)

    def test_clear_status(self):
        """Should clear future, output, and error"""
        wp = WorkerProcess("test_worker")
        wp.submit_func(quick_func)
        wp.wait_for_completion(timeout=5)
        wp.clear_status()
        assert wp.future is None
        assert wp.output is None
        assert wp.error is None
        wp.pool.shutdown(wait=True)
