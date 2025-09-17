import logging
import json
logger = logging.getLogger(__name__)

from typing import List, Dict
from lad import client, gdsclient
#from lad.gdsClient import flattenDict
from .core_utils import TimeoutError, get_sclkscet_times
from .schema import TimeType
import requests
import socket
from multiprocessing import Process
from datetime import datetime, timedelta
import os


def get_lad_https_protocol():

  lad_protocol = os.environ.get("LAD_HTTPS", "")
  
  # in order to properly set this argument variable in the LadClient() function. The environment variable needs to be cast into the boolean type.
  if lad_protocol.lower() == "true":
    return True
  else:
    return False

'''
Functions for building and dispatching globallad commands/queries
'''
# environment variable: LAD_HTTPS can either be True or False and will be used as an argument value in the LadClient function
_LAD_HTTPS = get_lad_https_protocol()
# environment variable: LAD_HOST should be in the format "<hostname>.jpl.nasa.gov"
_LAD_HOST = os.environ.get("LAD_HOST", os.environ.get("HOSTNAME"))
_LAD_PORT = int(os.environ.get("LAD_PORT", 8887))
_LAD_TIMEOUT_SEC = 60

def _handle_lad_timeout(signum, frame):
  raise TimeoutError("GlobalLad query timed out")


def lad_get_evr (sessionId, timeout=None, evrName=None, eventId=None,
                 evrLevel=None, timeType:TimeType=TimeType.ERT, startTime=None,
                 endTime=None):
  '''

  :param sessionId: session number to filter on (int)
  :param evrName: evr name to filter on (string)
  :param eventId: evr numeric event Id to filter on (int)
  :param evrLevel: evr level to filter on (string)
  :param timeType: evr time type to filter on (TimeType)
  :param startTime: evr begin time for query time range (string)
  :param endTime: evr end time for query time range (string)
  :return: json object with list of all matching realtime evrs
  '''

  evrq = client.EvrQuery()

  # Fix for ING-4206
  # The default is 100 EVR per level. Increase it to 1000
  # to match the typical GLAD set up.
  # GLAD EVR query results are not ordered, which may miss EVRs if there are many EVRs in the query range.
  evrq.setMaxResults(1000)

  if evrName is not None:
    evrq.addEvrName(evrName)

  if evrLevel is not None:
    evrq.addEvrLevel(evrLevel)

  if eventId is not None:
    evrq.addEventId(eventId)

  if timeType == TimeType.ERT:
    evrq.useErt()
  elif timeType == TimeType.SCET:
    evrq.useScet()
  elif timeType == TimeType.SCLK:
    evrq.useSclk()

  if endTime is not None:
    evrq.before(endTime)

  if timeout is not None:
    lad_timeout = timeout
  else:
    lad_timeout = _LAD_TIMEOUT_SEC

  evrq.addSessionNumber(sessionId)
  # per ticket: ING-2279 - need to remove message pattern in order to 
  # properly get back EVR response from AMPCS
  # evrq.addMessagePattern('*')
  evrq.after(startTime)
  evrq.realtimeOnly()

  logger.info("Set realtime EVR query timeout to %d seconds"%lad_timeout)

  logger.info("Querying realtime evr at time: "+datetime.utcnow().isoformat())
  logger.info("Opening connection to GlobalLad. https=%s Host=%s Port=%d"%(_LAD_HTTPS,_LAD_HOST,_LAD_PORT))
  c = client.LadClient(host=_LAD_HOST, port=_LAD_PORT, https=_LAD_HTTPS)
  logger.info("URI:%s"%str(evrq.getUri()))
  logger.info("Parameters:%s"%str(evrq.getParams()))
  resp = gdsclient.flattenDict(c.fetchEvrs(evrQuery=evrq, timeout=lad_timeout))
  logger.info("Got response at time: "+datetime.utcnow().isoformat())

  return resp

def lad_get_evr_multi (sessionId: int, timeout=None, evrNames: List[str]=[], eventIds: List[int]=[],
                 evrLevels: List[str]=[], timeType:TimeType=None, startTime=None,
                 endTime=None) -> List[Dict]:
  '''
  Queries for EVR using GLAD. More than one EVR name can be queried.
  Time format for all time types except SCLK is YYYY-DOYThh:mm:ss.ttt

  Parameters
  ------------------
  sessionId:
    AMPCS session id
  timeout:
    Time to wait in seconds before timeout
  evrNames:
    names of evrs to match. No wildcard is supported.
  eventIds:
    EVR event ids
  evrLevels:
    EVR levels
  timeType:
    Should be one of TimeType
  startTime:
    Begin time of query range
  endTime:
    End time of query range


  Returns:
  List[Dict]
    list of evrs in dict
  '''

  evrq = client.EvrQuery()

  # Fix for ING-4206
  # The default is 100 EVR per level. Increase it to 1000
  # to match the typical GLAD set up.
  # GLAD EVR query results are not ordered, which may miss EVRs if there are many EVRs in the query range.
  evrq.setMaxResults(1000)

  evrq.addSessionNumber(sessionId)

  for evrName in evrNames:
    evrq.addEvrName(evrName)

  for eventId in eventIds:
    evrq.addEventId(eventId)

  for evrLevel in evrLevels:
    evrq.addEvrLevel(evrLevel)

  # TODO: handle SCET and SCET
  if timeType == TimeType.ERT:
    evrq.useErt()

  if endTime is not None:
    evrq.before(endTime)

  if timeout is not None:
    lad_timeout = timeout
  else:
    lad_timeout = _LAD_TIMEOUT_SEC


  # per ticket: ING-2279 - need to remove message pattern in order to 
  # properly get back EVR response from AMPCS
  # evrq.addMessagePattern('*')

  evrq.after(startTime)
  evrq.realtimeOnly()

  logger.info("Set realtime EVR query timeout to %d seconds"%lad_timeout)

  logger.info("Querying realtime evr at time: "+datetime.utcnow().isoformat())
  logger.info("Opening connection to GlobalLad. https=%s Host=%s Port=%d"%(_LAD_HTTPS,_LAD_HOST,_LAD_PORT))
  c = client.LadClient(host=_LAD_HOST, port=_LAD_PORT, https=_LAD_HTTPS)
  logger.info("URI:%s"%str(evrq.getUri()))
  logger.info("Parameters:%s"%str(evrq.getParams()))
  resp = gdsclient.flattenDict(c.fetchEvrs(evrQuery=evrq, timeout=lad_timeout))
  logger.info("Got response at time: "+datetime.utcnow().isoformat())

  return resp

def lad_get_eha (sessionId: int, timeout: int=None, channelId: str=None, timeType:TimeType=None,
                 startTime: str=None, endTime: str=None):
  '''

  :param sessionId: session number to filter on (int)
  :param channelId: EHA channel Id to filter on (string)
  :param timeType: evr time type to filter on (TimeType)
  :param startTime: evr begin time for query time range (string)
  :param endTime: evr end time for query time range (string)
  :return: json object with list of all matching realtime ehas
  '''

  ehaq = client.ChanValQuery()

  if channelId is not None:
    ehaq.addChannelId(channelId)

  if timeType == TimeType.ERT:
    ehaq.useErt()

  if endTime is not None:
    ehaq.before(endTime)

  if startTime is not None:
    ehaq.after(startTime)

  if timeout is not None:
    lad_timeout = timeout
  else:
    lad_timeout = _LAD_TIMEOUT_SEC

  ehaq.addSessionNumber(sessionId)
  ehaq.realtimeOnly()

  logger.info("Set realtime EHA query timeout to %d seconds"%lad_timeout)

  logger.info("Querying realtime evr at time: "+datetime.utcnow().isoformat())
  logger.info("Opening connection to GlobalLad. https=%s Host=%s Port=%d"%(_LAD_HTTPS,_LAD_HOST,_LAD_PORT))
  c = client.LadClient(host=_LAD_HOST, port=_LAD_PORT, https=_LAD_HTTPS)
  logger.info("URI:%s"%str(ehaq.getUri()))
  logger.info("Parameters:%s"%str(ehaq.getParams()))
  resp = gdsclient.flattenDict(c.fetchChannels(chanValQuery=ehaq, timeout=lad_timeout))
  logger.info("Got response at time: "+datetime.utcnow().isoformat())

  return resp

def lad_get_eha_multi (sessionId: int, timeout=None, channelIds: List[str]=[], timeType:TimeType=TimeType.ERT,
                 startTime=None, endTime=None) -> List[Dict]:
  '''
  Queries for EHA using GLAD. More than one EHA ids can be queried.
  Time format for all time types except SCLK (in GMT) is YYYY-DOYThh:mm:ss.ttt

  Parameters
  ------------------
  sessionId:
    AMPCS session id
  timeout:
    Time to wait in seconds before timeout
  channelIds:
    EHA channel ids
  timeType:
    Should be one of TimeType
  startTime:
    Begin time of query range
  endTime:
    End time of query range

  Returns:
  List[Dict]
    list of channel values in dict
  '''

  ehaq = client.ChanValQuery()

  for channelId in channelIds:
    ehaq.addChannelId(channelId)

  if timeType == TimeType.ERT:
    ehaq.useErt()
  elif timeType == TimeType.SCET:
    ehaq.useScet()
  elif timeType == TimeType.SCLK:
    ehaq.useSclk()

  if endTime is not None:
    ehaq.before(endTime)

  if startTime is not None:
    ehaq.after(startTime)

  if timeout is not None:
    lad_timeout = timeout
  else:
    lad_timeout = _LAD_TIMEOUT_SEC

  ehaq.addSessionNumber(sessionId)
  
  ehaq.realtimeOnly()

  logger.info("Set realtime EHA query timeout to %d seconds"%lad_timeout)

  logger.info("Querying realtime evr at time: "+datetime.utcnow().isoformat())
  logger.info("Opening connection to GlobalLad. https=%s Host=%s Port=%d"%(_LAD_HTTPS,_LAD_HOST,_LAD_PORT))
  c = client.LadClient(host=_LAD_HOST, port=_LAD_PORT, https=_LAD_HTTPS)
  logger.info("URI:%s"%str(ehaq.getUri()))
  logger.info("Parameters:%s"%str(ehaq.getParams()))
  resp = gdsclient.flattenDict(c.fetchChannels(chanValQuery=ehaq, timeout=lad_timeout))
  logger.info("Got response at time: "+datetime.utcnow().isoformat())

  return resp

def lad_get_sclkscet(sessionId):
  '''
  
  :param sessionId: session number to filter on (int)
  :return: json object with list of all matching realtime ehas
  
  '''


  # declare variables for start/end times for last 30 seconds
  start_time, end_time = get_sclkscet_times()
  ehas = lad_get_eha(sessionId, timeType='ERT', startTime=start_time, endTime=end_time)

  return ehas
