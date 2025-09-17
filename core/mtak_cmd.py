import traceback
from .worker_process import WorkerProcess
from .mtak_funcs import mtak_startup_timeout_, \
  mtak_send_fsw_cmd_, mtak_send_hw_cmd_, mtak_send_sse_cmd_, \
  mtak_send_fsw_file_, mtak_send_fsw_scmf_
from datetime import datetime, timezone
import mtak.wrapper as mtk
import signal
from .core_utils import TimeoutError, get_last_error_from_logs, get_utc_iso
import logging
import atexit
logger = logging.getLogger(__name__)
mtak_worker = WorkerProcess('mtak-worker')

# A hook to shutdown any MTAK processes automatically when the main Python process exits.
# This is useful for Ingenium custom scripts that use this code as a library.
# Without this hook, when an Ingenium custom script that started MTAK ends without explicitly shutting down MTAK, 
# MtakDownlinkServerApp process may hang around.
# See ING-4470
atexit.register(mtak_worker.shutdown)

'''
Functions for starting/shutting down mtak and dispatching mtak commands
'''
# to filter out messages to the right of these exceptions in error messages
# TODO: this is not used
exception_filters = ["jpl.gds.core.cmd.exception.CommandParseException",
                     "java.io.FileNotFoundException",
                     "jpl.gds.core.cmd.exception.FileLoadParseException"]

def _handle_mtak_startup_timeout(signum, frame):
  raise TimeoutError("MTAK startup timed out")

def _handle_mtak_shutdown_timeout(signum, frame):
  raise TimeoutError("MTAK startup timed out")

def _handle_cmd_timeout(signum, frame):
  raise TimeoutError("Command timed out")


def mtak_startup_timeout(sessionIds, defaultCmdString, timeout_sec):
  '''
  :param sessionIds: session keys (list of int)
  :param defaultStringId: string ID to pass to MTAK ('A', 'B', 'AB')
  :param timeout_sec: timeout for mtak.wrapper.startup() (int)
  :return:
  '''
  
  logger.info(f'Sending MTAK startup at time: {datetime.now(tz=timezone.utc).isoformat()}')
  logger.info(f'Starting MTAK session for sessionId(s): {sessionIds} timeout_sec: {timeout_sec}')

  # TODO: handler error when starting MTAK
  mtak_worker.submit_func(mtak_startup_timeout_, sessionIds=sessionIds, defaultCmdString=defaultCmdString)
  output, msg = mtak_worker.wait_for_completion(timeout_sec)

  logger.info(f'MTAK startup response at time: {get_utc_iso()}')
  logger.info(f'MTAK startup output: {output} msg: {msg}')

  if msg:
    raise Exception(msg)

  return output

def mtak_shutdown():
  logger.info(f'Sending MTAK shutdown at time: {get_utc_iso()}')
  
  # Kill the worker process, which will shutdown MTAK processes.
  # This does not use mtak_worker.submit_func because the worker may be busy.
  # Shutdown the worker process and its child processes directly.
  mtak_worker.reset()
   
def mtak_send_fsw_cmd(sessionId, cmdString, stringSelection, validate, timeout_sec):
  '''
  :param sessionId: session key (int)
  :param cmdString: fsw command string (string)
  :param timeout_sec: timeout for mtak.wrapper.send_fsw_cmd() (int)

  :return: success - True if command transmitted succesfully (Boolean)
  '''

  logger.info(f'Sending MTAK fsw cmd at time: {get_utc_iso()} timeout_sec: {timeout_sec}')
  logger.info(f'Sending MTAK fsw cmd string: {cmdString}, with validate={validate}')
  
  mtak_worker.submit_func(
    mtak_send_fsw_cmd_, 
    sessionId=sessionId,
    cmdString=cmdString,
    stringSelection=stringSelection,
    validate=validate
  )
  output, msg = mtak_worker.wait_for_completion(timeout_sec)
  logger.info(f'MTAK FSW command response at time: {get_utc_iso()}')
  logger.info(f'MTAK FSW command output: {output} msg: {msg}')

  if msg:
    raise Exception(msg)
  
  if not output:
    raise Exception(f'Failed to send a FSW command: {cmdString}')

  return output


def mtak_send_hw_cmd(sessionId, cmdStem, stringSelection, timeout_sec):
  '''
  :param sessionId: session key (int)
  :param cmdStem: hw command stem (string)
  :param timeout_sec: timeout for mtak.wrapper.send_hw_cmd() (int)

  :return: success - True if command transmitted succesfully (Boolean)
  '''

  logger.info(f'Sending MTAK hw cmd at time: {get_utc_iso()} timeout_sec: {timeout_sec}')
  logger.info(f'Sending MTAK hw cmd stem: {cmdStem}')

  mtak_worker.submit_func(
    mtak_send_hw_cmd_, 
    sessionId=sessionId,
    cmdStem=cmdStem,
    stringSelection=stringSelection
  )

  output, msg = mtak_worker.wait_for_completion(timeout_sec)
  logger.info(f'MTAK HW command response at time: {get_utc_iso()}')
  logger.info(f'MTAK HW command output: {output} msg: {msg}')

  if msg:
    raise Exception(msg)
  
  if not output:
    raise Exception(f'Failed to send a HW command: {cmdStem}')

  return output

def mtak_send_sse_cmd(sessionId, cmdString, timeout_sec):
  '''
  :param sessionId: session key (int)
  :param cmdString: fsw command string (string)
  :param timeout_sec: timeout for mtak.wrapper.send_sse_cmd() (int)

  :return: success - True if command transmitted succesfully (Boolean)
  '''
  logger.info(f'Sending MTAK sse cmd at time: {get_utc_iso()} timeout_sec: {timeout_sec}')
  logger.info(f'Sending MTAK sse cmd string: {cmdString}')

  mtak_worker.submit_func(
    mtak_send_sse_cmd_, 
    sessionId=sessionId,
    cmdString=cmdString
  )

  output, msg = mtak_worker.wait_for_completion(timeout_sec)
  logger.info(f'MTAK SSE command response at time: {get_utc_iso()}')
  logger.info(f'MTAK SSE command output: {output} msg: {msg}')

  if msg:
    raise Exception(msg)
  
  if not output:
    raise Exception(f'Failed to send a SSE command: {cmdString}')

  return output

def mtak_send_fsw_file(sessionId, sourcePath, targetLoc, fileType, overwrite, stringSelection, timeout_sec):
  '''
  :param sessionId: session key (int)
  :param sourcePath: full path on venue's file system to locate the file (string)
  :param targetLoc: full path on the vehicle's file system to send the file (string)
  :param fileType: file type to build binary file into SCMF (int)
  :param overwrite: True if this file should overwrite existing file in targetLoc (boolean)
  :param timeout_sec: timeout on the dispatch process (int)

  :return: success - True if command transmitted succesfully (Boolean)
  '''
  logger.info(f'Sending MTAK fsw file at time: {get_utc_iso()} timeout_sec: {timeout_sec}')
  logger.info(f'Sending MTAK fsw file sourcePath={sourcePath}, targetLoc={targetLoc}, fileType={fileType}, overwrite={overwrite}')

  mtak_worker.submit_func(
    mtak_send_fsw_file_,
    sessionId=sessionId,
    sourcePath=sourcePath,
    targetLoc=targetLoc,
    fileType=fileType,
    overwrite=overwrite,
    stringSelection=stringSelection
  )

  output, msg = mtak_worker.wait_for_completion(timeout_sec)
  logger.info(f'MTAK FSW file response at time: {get_utc_iso()}')
  logger.info(f'MTAK FSW file output: {output} msg: {msg}')

  if msg:
    raise Exception(msg)
  
  if not output:
    raise Exception(f'Failed to send a FSW file: {sourcePath}')

  return output

def mtak_send_scmf_file(sessionId, filePath, disableChecks, timeout_sec):
  '''
  :param sessionId: session key (int)
  :param filePath: abs path
  :param disableChecks: disables AMPCS check of the scmf (boolean)
  :param timeout_sec: timeout for mtak.wrapper.send_sse_cmd() (int)

  :return: success - True if command transmitted succesfully (Boolean)
  '''

  logger.info(f'Sending MTAK scmf cmd at time: {get_utc_iso()} timeout_sec: {timeout_sec}')
  logger.info(f'Sending MTAK scmf filePath: {filePath}  disableChecks: {disableChecks}')

  mtak_worker.submit_func(
    mtak_send_fsw_scmf_, 
    sessionId=sessionId,
    filePath=filePath,
    disableChecks=disableChecks
  )

  output, msg = mtak_worker.wait_for_completion(timeout_sec)
  logger.info(f'MTAK SCMF command response at time: {get_utc_iso()}')
  logger.info(f'MTAK SCMF command output: {output} msg: {msg}')

  if msg:
    raise Exception(msg)
  
  if not output:
    raise Exception(f'Failed to send a SCMF command: {filePath}')

  return output