import os
import time
import logging
import psutil
import signal
import traceback
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import current_process
from concurrent.futures.process import BrokenProcessPool

logger = logging.getLogger(__name__)

def init_worker_proc():
    # To prevent FASTAPI from shutting down when worker process is killed.
    # See https://github.com/tiangolo/fastapi/issues/1487
    signal.set_wakeup_fd(-1)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    pid = current_process().pid
    return pid

class WorkerProcess(object):
    def __init__(self, name):
        self.name = name
        
        # future of the result
        self.future = None
        self.output = None
        self.error = None

        self._init_pool()

    def _init_pool(self):    
        self.pool = ProcessPoolExecutor(max_workers=1)
        fut = self.pool.submit(init_worker_proc)
        self.pid = fut.result()
        logger.info(f'worker _init_pool pid: {self.pid} name: {self.name}')        

    def done_callback(self, context):
        # Note context is the same as self.future when the task was submitted.
        if context is self.future:
            self.output, self.error = context.result()

            logger.info(f'worker done_callback clear states. pid: {self.pid} name: {self.name} output: {self.output}')
            if self.future is not None:
                self.future = None
        else:
            logger.info(f'worker done_callback do not clear states. pid: {self.pid} name: {self.name} future: {self.future} context: {context}')

    def clear_status(self):
        self.future = None
        self.output = None
        self.error = None
                
    def shutdown(self):
        logger.info(f'worker shutdown pid: {self.pid} name: {self.name}')

        worker_process = None
        # kill child processes such as MTAK
        try:
            if self.pid:
                worker_process = psutil.Process(self.pid)
            else:
                logger.warning(f'worker pid is not valid. just return. pid: {self.pid}')
                return                
        except psutil.NoSuchProcess:
            logger.warning(f'worker process not found. just return. pid: {self.pid}')
            return
        
        pids = [self.pid]
        child_processes = worker_process.children(recursive=True)
        for child_process in child_processes:
            pids.append(child_process.pid)
            try:
                logger.info(f'Killing child process. pid: {child_process.pid}')
                os.kill(child_process.pid, signal.SIGKILL)
            except:
                logger.warning(f'Error when killing child process. child_process.pid: {child_process.pid} error: {traceback.format_exc()}')

        # Wait until the process is killed
        time_start = time.time()

        try:
            logger.info(f'Killing worker process. pid: {self.pid}')
            os.kill(self.pid, signal.SIGKILL)
        except:
            logger.warning(f'Error when force killing worker process. pid: {self.pid} error: {traceback.format_exc()}')
        
        time_start = time.time()
        while True:
            remaining_pids = list(set(pids) & set(psutil.pids()))
            if len(remaining_pids):
                logger.info(f'remaining_pids: {remaining_pids}')
                if (time.time() - time_start) > 5.0:
                    logger.warning(f'Failed to kill processes. remaining_pids: {remaining_pids}')
                    break
            else:
                logger.info(f'worker process and child processes killed. pid: {self.pid} name: {self.name}')
                break
            time.sleep(1)

    def reset(self):
        logger.info(f'worker reset pid: {self.pid} name: {self.name}')

        self.shutdown()

        self.clear_status()

        self._init_pool()

        # Re-set state after recreating the pool so that this pool is not used until the pool is re-created.
        # This is a guard to ensure the states are re-set only once by reset or by done_callback
        logger.info(f'worker reset checking pid: {self.pid} name: {self.name}')
        if self.future is not None:
            self.clear_status()

    def submit_func(self, func, **kwargs):
        if self.is_running():
            raise Exception('Worker is busy.')

        try:
            logger.info(f'worker submit_func pid: {self.pid} name: {self.name}')
            self.output = None
            self.future = self.pool.submit(func, **kwargs)
            logger.info(f'worker submit_func future: {self.future} name: {self.name}')
            self.future.add_done_callback(self.done_callback)

            return self.future
        except BrokenProcessPool as ex:
            logger.warning('pool is broken. restart worker process')
            raise Exception('Error when running step') from ex
        except Exception as ex:
            logger.warning(f'submit error: {traceback.format_exc()}')
            raise Exception('Error when running step') from ex

    def is_running(self):
        if self.future is None:
            logger.info(f'is_running future is None')
            return False
        else:
            try:
                # set to a local variable to avoid a race condition that may set future to None
                is_future_done = self.future.done()
                logger.info(f'is_running is_future_done: {is_future_done}')
                return not is_future_done
            except:
                logger.warning(f'Failed to determine task status. error: {traceback.format_exc()}')
                # This should not happen. 
                # But if this happens, the future status was not determined. 
                # Treat as running.
                return True

    def wait_for_completion(self, timeout=None):
        start_time = time.time()
        while self.is_running():
            time.sleep(0.5)

            if timeout is not None:
                if (time.time() - start_time) > timeout:
                    raise TimeoutError(f'request timed out. timeout: {timeout} seconds')
        return (self.output, self.error)


def test_func(sleep_count, sleep_interval):
    start_time = time.time()
    for i in range(sleep_count):
        time.sleep(sleep_interval)
        logger.info(f'sleep # {i}')
    
    elapsed_time = time.time() - start_time
    return (elapsed_time, None)

if __name__ == '__main__':

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    CONSOLE_LOG_FORMAT = '[%(asctime)s] [%(funcName)s] %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'
    formatter = logging.Formatter(CONSOLE_LOG_FORMAT, LOG_DATE_FORMAT)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    wp = WorkerProcess('test-wp')

    wp.submit_func(test_func, sleep_count=5, sleep_interval=1)
    try:
        # submitting another job while one is running will fail
        wp.submit_func(test_func, sleep_count=5, sleep_interval=0.5)
    except Exception as ex:
        logger.error(ex)

    output, error = wp.wait_for_completion(10)
    logger.info(f'output: {output} error: {error}')

    # this job will be timed out
    wp.submit_func(test_func, sleep_count=5, sleep_interval=0.5)
    try:
        output, error = wp.wait_for_completion(2)
        logger.info(f'output: {output} error: {error}')
    except Exception as ex:
        logger.info(f'ex: {ex}')
        assert(True)
    else:
        assert(False)

    # Submit a job right after, while the previous job is running. this should throw an exception
    try:
        wp.submit_func(test_func, sleep_count=5, sleep_interval=0.5)
    except Exception as ex:
        logger.info(f'ex: {ex}')
        assert(str(ex) == 'Worker is busy.')
    else:
        assert(False)

    # submit a job right after the previous job is completed. this should work
    time.sleep(5)
    wp.submit_func(test_func, sleep_count=5, sleep_interval=0.5)
    try:
        output, error = wp.wait_for_completion(10)
        logger.info(f'output: {output} error: {error}')
    except Exception as ex:
        logger.info(f'ex: {ex}')
        assert(False)
    else:
        assert(True)
