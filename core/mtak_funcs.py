# Functions that are executed in ProcessPoolExecutor
# Keep them in this separate module to avoid pickle error when having complex Python objects in module

import traceback
from file_read_backwards import FileReadBackwards
import mtak.wrapper as mtk
import time

import logging
logger = logging.getLogger(__name__)

def get_last_lines(file_path, num_lines):
  lines = []
  try:
    with FileReadBackwards(file_path, encoding="utf-8") as frb:
      while len(lines) < num_lines:
        line = frb.readline()
        if line:
          if len(line) > 1024:
            lines.append(line[:1024])
          else:
            lines.append(line)
        else:
            break
  except:
    print(traceback.format_exc())

  lines.reverse()
    
  return lines

def get_last_error_from_logs (filepath):  
  lines = get_last_lines(filepath, 50)

  for line in reversed(lines):
    if "ERROR" in line or "FATAL" in line:
      return line

  return ''

def get_mtak_error(error, mtak_log_path):
  if mtak_log_path:
    error_in_log = get_last_error_from_logs(mtak_log_path)
    if error_in_log:
      return f'{error} --- Error from MTAK log ({mtak_log_path}: {error_in_log})'
  
  return error

def mtak_startup_timeout_(sessionIds, defaultCmdString):
  logger.info(f'mtak_startup_timeout_ sessionIds: {sessionIds} defaultCmdString: {defaultCmdString}')

  try:
    # mtk.startup does not return anything.
    mtk.startup(
      sessionKeys=sessionIds,
      defaultStringId=defaultCmdString,
      receiveEha=False,
      receiveEvrs=False,
      receiveProducts=False,
      receiveSse=False,
      receiveFsw=False,
      enableFileLog=True, #just being explicit here...
      throwOnError=True
    )
  except SystemExit:
    error = get_mtak_error(f'mtak_startup_timeout_ SystemExit: ${traceback.format_exc()}', mtk._logFile)
    logger.error(error)
    return (False, error)
  except Exception as ex:
    error = get_mtak_error(f'Error in mtak_startup_timeout_: ${traceback.format_exc()}', mtk._logFile)
    logger.error(error)
    return (False, error)

  return (True, None)

def mtak_send_fsw_cmd_(sessionId, cmdString, stringSelection, validate):
  logger.info("mtak_send_fsw_cmd_")

  try:
    output = mtk.send_fsw_cmd(command=cmdString,
                                validate=validate,
                                stringId=stringSelection,
                                throwOnError=True,
                                sessionKey=sessionId)
    return (output, None)
  except SystemExit as ex:
    error = get_mtak_error(f'mtak_send_fsw_cmd_ SystemExit: ${traceback.format_exc()}', mtk._logFile)
    logger.error(error)
    return (False, error)
  except Exception as ex:
    error = get_mtak_error(f'Error in mtak_send_fsw_cmd_: ${traceback.format_exc()}', mtk._logFile)
    logger.error(error)
    return (False, error)

def mtak_send_hw_cmd_(sessionId, cmdStem, stringSelection):
  logger.info("mtak_send_hw_cmd_")

  try:
    output = mtk.send_hw_cmd(command=cmdStem,
                            throwOnError=True,
                            stringId=stringSelection,
                            sessionKey=sessionId)
    return (output, None)
  except SystemExit as ex:
    error = get_mtak_error(f'mtak_send_hw_cmd_ SystemExit: ${traceback.format_exc()}', mtk._logFile)
    logger.error(error)
    return (False, error)
  except Exception as ex:
    error = get_mtak_error(f'Error in mtak_send_hw_cmd_: ${traceback.format_exc()}', mtk._logFile)
    logger.error(error)
    return (False, error)
  
def mtak_send_sse_cmd_(sessionId, cmdString):
  logger.info("mtak_send_sse_cmd_")

  try:
    # a special SSE command that is used for testing
    if cmdString == 'dummy_sse_cmd_for_timeout':
      time.sleep(240)
      return (True, None)
    else:
      output = mtk.send_sse_cmd(command=cmdString,
                                throwOnError=True,
                                sessionKey=sessionId)
      return (output, None)
  except SystemExit as ex:
    error = get_mtak_error(f'mtak_send_sse_cmd_ SystemExit: ${traceback.format_exc()}', mtk._logFile)
    logger.error(error)
    return (False, error)
  except Exception as ex:
    error = get_mtak_error(f'Error in mtak_send_sse_cmd_: ${traceback.format_exc()}', mtk._logFile)
    logger.error(error)
    return (False, error)
    
def mtak_send_fsw_file_(sessionId, sourcePath, targetLoc, fileType, overwrite, stringSelection):
  logger.info("mtak_send_fsw_file_")

  try:
    output = mtk.send_fsw_file (source=sourcePath,
                                 target=targetLoc,
                                 type=fileType,
                                 overwrite=overwrite,
                                 throwOnError=True,
                                 stringId=stringSelection,
                                 sessionKey=sessionId)
    return (output, None)
  except SystemExit as ex:
    error = get_mtak_error(f'mtak_send_fsw_file_ SystemExit: ${traceback.format_exc()}', mtk._logFile)
    logger.error(error)
    return (False, error)
  except Exception as ex:
    error = get_mtak_error(f'Error in mtak_send_fsw_file_: ${traceback.format_exc()}', mtk._logFile)
    logger.error(error)
    return (False, error)
  
def mtak_send_fsw_scmf_(sessionId, filePath, disableChecks):
  logger.info("mtak_send_fsw_scmf_")

  try:
    output = mtk.send_fsw_scmf(filename=filePath,
                                disableChecks=disableChecks,
                                throwOnError=True,
                                sessionKey=sessionId)
    
    return (output, None)
  except SystemExit as ex:
    error = get_mtak_error(f'mtak_send_fsw_scmf_ SystemExit: ${traceback.format_exc()}', mtk._logFile)
    logger.error(error)
    return (False, error)
  except Exception as ex:
    error = get_mtak_error(f'Error in mtak_send_fsw_scmf_: ${traceback.format_exc()}', mtk._logFile)
    logger.error(error)
    return (False, error)