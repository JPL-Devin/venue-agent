import logging
logger = logging.getLogger(__name__)

from .core_utils import query_process
from .config import SHORT_TIMEOUT, REVERSE_SCMF_TIMEOUT

'''
Functions for building and dispatching chill commands/queries
'''

chill_error_statuses = ['FATAL', 'ERROR', 'CRITICAL']

def chill_get_evr (sessionId: str, evrTypes: str=None, evrNames: str=None, eventId: str=None,
                    evrLevel: str=None, evrModule: str=None, timeType: str=None,
                    startTime: str=None, endTime: str=None, timeout:int=None) -> str:
  """
  Runs chill_get_evrs with the provided filters and return its output in string

  Parameters
  ----------
  sessionId: 
    AMPCS session id. This can be a comma separated list
  evrTypes: 
    EVR types to query (ex: f for FSW realtime, s for SSE, r for FSW recorded, fs, etc.)
  evrNames: 
    EVR name or pattern
  eventId: 
    eventId of EVR
  evrLevel: 
    level of EVR
  evrModule: 
    FSW module of EVR
  timeType: 
    SCLK, ERT, or SCET
  startTime: 
    query start time
  endTime: 
    query end time
  timeout: 
    how long to wait for results in seconds

  Returns
  ------------
  str
      output of chill_get_evrs

  """

  # construct query query
  cmd = ['chill_get_evrs']
  cmd.extend(['--testKey',sessionId]) if (sessionId is not None) else None
  cmd.extend(['--evrTypes',evrTypes]) if (evrTypes is not None) else None
  cmd.extend(['--namePattern',evrNames]) if (evrNames is not None) else None
  cmd.extend(['--eventId',eventId]) if (eventId is not None) else None
  cmd.extend(['--level',evrLevel]) if (evrLevel is not None) else None
  cmd.extend(['--modulePattern',evrModule]) if (evrModule is not None) else None
  if startTime is not None or endTime is not None:
    cmd.extend(['--timeType',timeType])
    cmd.extend(['--beginTime',startTime]) if (startTime is not None) else None
    cmd.extend(['--endTime',endTime]) if (endTime is not None) else None

  # send chill query & return response
  return query_process (cmd, timeout)


def chill_get_eha (sessionId: str, channelIds: str=None, channelTypes: str=None,
                    timeType: str=None, startTime: str=None, endTime: str=None,
                    inAlarmFilter: str=None, timeout: int=None) -> str:
  """
  Runs chill_get_chanvals with the provided filters and return its output in string

  Parameters
  ----------
  sessionId: 
    AMPCS session id. This can be a comma separated list
  channelIds: 
    a comma separated list of channel ids
  channelTypes: 
    Channels types to query (ex: f for FSW realtime, s for SSE, r for FSW recorded, fs, etc.)
  timeType: 
    SCLK, ERT, or SCET
  startTime: 
    query start time
  endTime: 
    query end time
  inAlarmFilter: 
    alarm filter (examples: RED, YELLOW, ANY)
  timeout: 
    how long to wait for results in seconds

  Returns
  ------------
  str
      output of chill_get_chanvals

  """
  # construct chanval query
  cmd = ['chill_get_chanvals']
  cmd.extend(['--testKey', sessionId]) if (sessionId is not None) else None
  cmd.extend(['--channelTypes',channelTypes]) if (channelTypes is not None) else None
  cmd.extend(['--channelIds',channelIds]) if (channelIds is not None) else None
  cmd.extend(['--alarmOnly',inAlarmFilter]) if (inAlarmFilter is not None) else None
  if startTime is not None or endTime is not None:
    cmd.extend(['--timeType',timeType])
    cmd.extend(['--beginTime',startTime]) if (startTime is not None) else None
    cmd.extend(['--endTime',endTime]) if (endTime is not None) else None

  # send chill query & return response
  return query_process (cmd, timeout=timeout)


def chill_get_dp (sessionId: str, dpStatus: str=None, apIds: str=None,
                    timeType: str=None, startTime: str=None, endTime: str=None,
                    timeout: int=None) -> str:
  """
  Runs chill_get_products with the provided filters and return its output in string

  Parameters
  ----------
  sessionId: 
    AMPCS session id. This can be a comma separated list
  dpStatus: 
    status filter (ex: "--completeOnly", "--partialOnly")
  apIds:
    comma separated list of AP IDs of data products
  timeType: 
    SCLK, ERT, or SCET
  startTime: 
    query start time
  endTime: 
    query end time
  timeout: 
    how long to wait for results in seconds

  Returns
  ------------
  str
      output of chill_get_products

  """

  # construct chill command
  cmd = ['chill_get_products']
  cmd.extend(['--testKey', sessionId]) if (sessionId is not None) else None
  cmd.extend([dpStatus]) if (dpStatus is not None and dpStatus != "") else None
  cmd.extend(['--productApid',apIds]) if (apIds is not None) else None
  #TODO: no dpName argument in chill_get_products
  if startTime is not None or endTime is not None:
    cmd.extend(['--timeType',timeType])
    cmd.extend(['--beginTime',startTime]) if (startTime is not None) else None
    cmd.extend(['--endTime',endTime]) if (endTime is not None) else None

  # send chill query & return response
  return query_process (cmd, timeout=timeout)

