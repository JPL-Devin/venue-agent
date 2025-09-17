import logging
logger = logging.getLogger(__name__)

from enum import Enum
import csv
import sys
from datetime import datetime, timedelta
import os
import traceback
from datetime import datetime, timezone
import re
import socket
import glob
from .config import SCLKSCET_LOOKBACK

import subprocess
from io import StringIO

command_type_mapping = {
  "0": "HW_COMMAND",
  "1": "FSW_COMMAND",
  "2": "BINARY_FILE" 
}

###########################################################
###### MAPPINGS BETWEEN JSON INPUTS AND CHILL INPUTS ######
###########################################################



class EVRType (Enum):
  FSW_REALTIME = "f"
  FSW_RECORDED = "r"
  SSE = "s"


class ChannelType (Enum):
  # only noting 3 of 6 possibilities
  FSW_REALTIME = "f"
  FSW_RECORDED = "r"
  SSE = "s"


class AlarmTypeMap (Enum):
  RED_ALARM = "RED"
  YELLOW_ALARM = "YELLOW"
  ANY_ALARM = "ANY"


class DpStatus (Enum):
  ALL = "" # dummy value - not really useful
  COMPLETE = "--completeOnly"
  PARTIAL = "--partialOnly"


class VenueType (Enum):
  WSTS = "WSTS"
  TESTBED = "TESTBED"
  ATLO = "ATLO"


def get_utc():
  return datetime.now(tz=timezone.utc)

def get_utc_iso():
  return get_utc().isoformat()

class TimeParsingError (Exception):
  def __init__(self, message):

    # Call the base class constructor with the parameters it needs
    super(TimeParsingError, self).__init__(message)

    # Now for your custom code...
    self.message = message

class ErrorCapturing(list):
  '''
  Context Manager for capturing errors
  '''
  def __enter__(self):
    self._stderr = sys.stderr
    sys.stderr = self._stringio = StringIO()
    return self
  def __exit__(self, *args):
    self.extend(self._stringio.getvalue().splitlines())
    del self._stringio
    sys.stderr = self._stderr

def get_last_error_from_logs (filepath,filters):
  # make sure file exists otherwise raise unique error only capable
  # of being caught by cmd_server
  if (os.path.isfile(filepath)==False):
    raise InvalidFilePathError

  cmd = ['tail', '-n', '50', filepath]
  log_tail = subprocess.check_output(cmd,stderr=subprocess.STDOUT,timeout=30).decode('utf-8')

  error_found = False
  error_list = []
  for line in reversed(log_tail.splitlines()):
    if "ERROR" in line or "FATAL" in line:
      error_found = True
      error_list.append(line)
      break
      
  if error_found is False:
    error_list = ["Error message could not be found in MTAK error logs"]

  return ("\n".join(error_list)).strip()


def update_timeout (start_time,old_timeout):
  '''
  :param start_time: time before a chunk of code was run (datetime object)
  :return: remaining timeout period  (float) , current UTC datetime
  '''
  elapsed_time = (datetime.utcnow() - start_time).total_seconds()
  if (elapsed_time >= old_timeout):
    raise TimeoutError
  else:
    return (old_timeout-elapsed_time,datetime.utcnow())

def normalize_with_microsecs (ftime):
  if '.' in ftime:
    time_segs = ftime.split('.')
    subsecond = str(time_segs[1])
    # If number of digits after decimal point is greater than 6 (e.g., nano precision),
    # truncate to the 6th digit
    if len(subsecond) > 6:
      subsecond = subsecond[0:6]
    return (time_segs[0] + '.' + subsecond)
  else:
    # exact second may not contain subsecond portion
    return ftime + '.000000'

def query_process (cmd, timeout):
  ''' Create a subprocess to send chill queries and return response'''
  # try to send query and return response
  logger.info("Starting subprocess at time: "+datetime.utcnow().isoformat())
  logger.info("Subprocess query command: " + str(cmd))
  resp = subprocess.check_output(cmd,stderr=subprocess.STDOUT,timeout=timeout).decode('utf-8')
  logger.info("Received response at time: "+datetime.utcnow().isoformat())
  if resp:
    # Fix for ING-4207
    # rsyslogd limits to 2048 bytes per message by default.
    # Show only 1024 chars to be conservative.
    if len(resp) > 1024:
      abridged_resp = resp[:512] + '\n ...... \n' + resp[-512:]
      logger.info("QUERY RESPONSE (abridged from %s chars): %s" % (len(resp), abridged_resp))
    else:
      logger.info("QUERY RESPONSE: %s" % resp)
  else:  
    logger.info("QUERY RESPONSE: %s" % resp)
  return resp

def get_csv_row_reader (csv_str):
  rows = csv_str.splitlines()
  reader = csv.reader(rows)
  return reader

def get_hostname():
  '''
  Returns hostname of the current machine
  '''
  return socket.gethostname()

def get_venue_type() -> VenueType:
  '''
  Returns venue type (WSTS, ATLO, or TESTBED) as enums
  '''
  vtype = os.environ.get("INGENIUM_VENUE_TYPE").upper()
  if (vtype=="WSTS" or vtype=="ATLO" or vtype=="TESTBED"):
    return VenueType(vtype)
  elif vtype is None or vtype == "":
    raise VenueTypeNotFound("INGENIUM_VENUE_TYPE environment variable is unassigned.")
  else:
    raise VenueTypeNotFound("Environment variable INGENIUM_VENUE_TYPE=%s. "
                            "Expecting WSTS, ATLO, or TESTBED."%(vtype))

def get_testbed_name():
  '''
  Returns testbed name, either string if it exists or None
  '''
  tb_name = os.environ.get("INGENIUM_TESTBED_NAME")
  if (tb_name is None or tb_name.strip()==""):
    return None
  else:
    return tb_name


def get_sse_hostname():
  '''
  Returns hostname of the venue where sse and vxworks are being run
  '''
  sse_host = os.environ.get("INGENIUM_SSE_HOSTNAME")
  if (sse_host is None or sse_host.strip()==""):
    return None
  else:
    return sse_host

def str_to_datetime (doy_or_iso_str,must_have_Z=False):
  '''

  :param doy_or_iso_str: DOY or ISO formatted string (accepts with or without Z or milliseconds)
  :return: datetime if string matches DOY or ISO. Else raises valueError if not found
  '''
  try:
    return iso_to_datetime(doy_or_iso_str,must_have_Z)
  except ValueError:
    pass
  return doy_to_datetime(doy_or_iso_str)

def iso_to_datetime (doy,must_have_Z=False):
  '''
  :param iso time - can have with or without Zs (string)
  :return: datetime
  '''
  if (doy.endswith('Z')):
    try:
      return datetime.strptime(doy, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
      pass
    return datetime.strptime(doy, "%Y-%m-%dT%H:%M:%SZ")
  elif (not doy.endswith('Z') and must_have_Z):
    raise ValueError
  else:
    try:
      return datetime.strptime(doy, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
      pass
    return datetime.strptime(doy, "%Y-%m-%dT%H:%M:%S")

def doy_to_datetime (doy):
  '''
  :param doy (string)
  :return: datetime
  '''
  try:
    return datetime.strptime(doy, "%Y-%jT%H:%M:%S.%f")
  except ValueError:
    pass

  return datetime.strptime(doy, "%Y-%jT%H:%M:%S")

def datetime_to_doy (dt,res=None):
  if res == None:
    dtstr = datetime.strftime(dt,'%Y-%jT%H:%M:%S')
  elif res == 'millis':
    dtstr = datetime.strftime(dt, '%Y-%jT%H:%M:%S.%f')
    dtstr = dtstr[:-3]
  elif res == 'micros':
    dtstr = datetime.strftime(dt, '%Y-%jT%H:%M:%S.%f')
  return dtstr

def datetime_to_isoZ (dt,res=None):
  if res == None:
    dtstr = datetime.strftime(dt,'%Y-%m-%dT%H:%M:%S')
  elif res == 'millis':
    dtstr = datetime.strftime(dt, '%Y-%m-%dT%H:%M:%S.%f')
    dtstr = dtstr[:-3]
  elif res == 'micros':
    dtstr = datetime.strftime(dt, '%Y-%m-%dT%H:%M:%S.%f')
  return dtstr

def utc_now_doy():
  utc_now = datetime.utcnow()
  utc_doy = datetime.strftime(utc_now, "%Y-%jT%H:%M:%S.%f")
  return utc_doy

def doyToIsoZ (doy):
  '''
  doy time in string
  '''
  dt = datetime.strptime(doy, "%Y-%jT%H:%M:%S.%f")
  down_to_micro_sec = datetime.strftime(dt,'%Y-%m-%dT%H:%M:%S.%f')
  down_to_milli_sec = down_to_micro_sec[:-3]
  return down_to_milli_sec + 'Z'

def get_msg_with_traceback(details):
  err_msg = "Error: " + details + "\nTRACEBACK:" + traceback.format_exc()
  return err_msg

def get_now_isoZ():
  return normalize_with_microsecs(datetime.utcnow().isoformat())[:-3] + 'Z'

def get_sclkscet_times():

  # remember to format as DOY

  # end time: now
  end_time_utc = datetime.utcnow()
  end_time = datetime.strftime(end_time_utc, '%Y-%jT%H:%M:%S')

  # start time: 30 seconds ago
  start_time_utc = datetime.utcnow() - timedelta(seconds=SCLKSCET_LOOKBACK)
  start_time = datetime.strftime(start_time_utc, '%Y-%jT%H:%M:%S')

  # return both start and end times
  return start_time, end_time

def most_recent_datetime(query_response):

  latest_datetime = None

  for res in query_response:

    if latest_datetime is None:
      latest_datetime = res
    elif res["sclk"] > latest_datetime["sclk"]:
      latest_datetime = res
    else:
      pass

  return latest_datetime

def return_validated_start_end_times(start_time, end_time, time_type, duration):

  if start_time is not None:
    try:
      validated_start_time_type, start_time = validate_time(start_time)
    except TimeParsingError:
      raise TimeParsingError("Start time is in an invalid format: %s"% start_time)
  if end_time is not None:
    try:
      validated_end_time_type, end_time = validate_time(end_time)
    except TimeParsingError:
      raise TimeParsingError("End time is in an invalid format: %s"% end_time)
  if duration is not None:
    if start_time is not None and end_time is not None:
      raise TimeParsingError("Cannot have both a start time and end time with a duration.")
    if start_time is not None:
      if time_type == "SCET":
        end_time = start_time + timedelta(seconds=duration)
      else:
        end_time = start_time + duration
    
    if end_time is not None:
      if time_type == "SCET":
        start_time = end_time - timedelta(seconds=duration)
      else:
        start_time = end_time - duration

    if end_time < start_time:
      raise TimeParsingError("End time is earlier than start time.")

  return start_time, end_time

def validate_time(input_time):
  """
  This function will attempt to parse the provided time and will return either a datetime object if
  successful (depending on format).
  """

  parsing=True
  if parsing:
    try:
      converted_time=datetime.strptime(input_time,"%Y-%jT%H:%M:%S.%f")
      time_type = "SCET"
      parsing=False
    except:
      pass
  if parsing:
    try:
      converted_time=datetime.strptime(input_time,"%Y-%jT%H:%M:%S")
      time_type = "SCET"
      parsing = False
    except:
      pass
  if parsing:
    try:
      converted_time=datetime.strptime(input_time,"%Y-%m-%dT%H:%M:%S")
      time_type = "SCET"
      parsing=False
    except:
      pass
  if parsing:
    try:
      converted_time=datetime.strptime(input_time,"%Y-%m-%dT%H:%M:%S.%f")
      time_type = "SCET"
      parsing=False
    except:
      pass
  if parsing:
    try:
      converted_time=float(input_time)
      time_type = "SCLK"
      parsing=False
    except:
      pass
  if parsing:
    try:
      if "-" in input_time:
        split_time = input_time.split("-")
        if len(split_time) != 2:
          pass
        else:
          for item in split_time:
            int(item)
          time_type = "SCLK"
          parsing=False
      else:
        pass
    except:
      pass
  if parsing:
    raise TimeParsingError("Time parsing error")
  return time_type, converted_time

def str2bool (item):
  if (type(item) == bool):
    return item
  elif type(item) == str:
    return (True if item.lower() == 'true' else False)

class PathConverter(object):
  # variables that only contain single value
  _sse_host_key = '$SSE_HOSTNAME'
  _gds_host_key = '$GDS_HOSTNAME'
  _tbname_key = '$TESTBED_NAME'
  _user_key = '$USER'
  _chill_sess_name_key = '$CHILL_SESS_NAME'
  _side_key = '$SIDE'
  _yr_key = '$YYYY'
  _doy_key = '$DOY'

  _single_arg_vars = {_sse_host_key:get_sse_hostname(),
                      _gds_host_key:get_hostname(),
                      _tbname_key:get_testbed_name(),
                      _user_key:None,
                      _chill_sess_name_key:None,
                      _side_key:None}

  # variables that accept multiple arguments/list
  # ex: $DOY can be replaced by list of DOYs like [001,002,003, etc.]
  _multi_arg_vars = {_yr_key:[],
                     _doy_key:[]}

  def __init__ (self, path_template, chill_sess_name="*", side="*", username="*", yyyy_list=[], doy_list=[], start_time=None, end_time=None):
    '''
    :param path_template: path template that conforms to sse config schema
    :param chill_sess_name: name of chill session if known (string). if not known, enter wildcard "*"
    :param side: side if known (string). Enter 'A' or 'B' if dual string setup, else "*"
    :param username: username if known (string). If not known, enter wildcard "*"
    :param yyyy_list: list of acceptable 4-digit years
    :param doy_list: list of acceptable 3-digit DOYs
    '''

    # if start and end dates are not none, parse start and end time for list of yyyy and doy. Not all uses of 
    # PathConverter require start and end time parameters
    self.start_time = start_time 
    self.end_time = end_time
    if start_time and end_time:
      yyyy_list, doy_list = self.retrieve_year_and_doy_list()
      logger.info("Retrieved year list: %s" % yyyy_list)
      logger.info("Retrieved doy list: %s" % doy_list)

    self._path_template = path_template
    self._single_arg_vars[self._chill_sess_name_key] = chill_sess_name
    self._single_arg_vars[self._side_key] = side
    self._single_arg_vars[self._user_key] = username
    self._multi_arg_vars[self._yr_key] = yyyy_list
    self._multi_arg_vars[self._doy_key] = doy_list

    # paths to return after all variables have been resolved
    self.paths = []

  def retrieve_year_and_doy_list(self):
    # start_time comes in as a strptime 
    if self.start_time is None:
      raise Exception("A start time was not provided to PathConverter")

    # start and end time come into this class as datetime objects
    year_and_doy = self.start_time.strftime("%Y-%j").split("-")
    year_list = [year_and_doy[0]]

    # get yesterday and today's doy
    today = year_and_doy[1]
    # Updated logic to use datetime to better determine yesterday and last year (ING-3981)
    yesterdate = self.start_time - timedelta(days=1)
    yesterday = yesterdate.strftime("%j")
    last_year = yesterdate.strftime("%Y")
    if year_and_doy[0] != last_year:
      year_list.insert(0, last_year)

    doy_list =[yesterday, today]

    return year_list, doy_list


  def set_side(self,side):
    self._single_arg_vars['$SIDE'] = side

  def set_years(self, yyyy_list):
    self._multi_arg_vars['$YYYY'] = yyyy_list

  def set_doys(self,doy_list):
    self._multi_arg_vars['$DOY'] = doy_list

  def set_username(self,side):
    self._single_arg_vars['$USER'] = side

  def _resolve_single_arg_vars (self):
    path_template = self._path_template
    for var in list(self._single_arg_vars.keys()):
      #print (var+":"+str(self._single_arg_vars[var]))
      if (self._single_arg_vars[var] is not None):
        path_template = path_template.replace(var,self._single_arg_vars[var])
    return path_template

  def _resolve_multi_arg_vars (self,single_resolved_path):
    paths = [single_resolved_path]

    def _expand_paths(paths_to_expand,key,vals):
      # replaces all instances of a schema key in list of paths with its values
      resolved_paths = []
      for path in paths_to_expand:
        if (key in path):
          tmp_paths = [path.replace(key,str(val)) for val in vals]
          resolved_paths.extend(tmp_paths)
        else:
          resolved_paths.append(path)
      return resolved_paths

    for var in list(self._multi_arg_vars.keys()):
      paths = _expand_paths(paths,var,self._multi_arg_vars[var])

    return paths

  def get_date_from_logfile_path(self, logfile):
    '''
    This helper method will extract the datetime stamp from the 1553 bus logfile path 
    and parse the datetime into a python datetime object. 
    
    Assumption is that the datetime stamp in the path name is the time the log was created.
    example logfile name: "psyche_20200722T204208"

    '''
    date_from_path = logfile.split("/")[-1].split("_")[-1]
    # logger.debug("Date extracted from logfile path: %s" % date_from_path)    

    parsed_datetime = datetime.strptime(date_from_path, '%Y%m%dT%H%M%S')

    return parsed_datetime

  def determine_logfile_path_position(self,log_dt):

    '''
    This function will determine if the currently observed log is one of three positions:
    1. "before": before the query start time 
    2. "within": within the boundaries of the start and end time 
    3. "after": after the query end time

    log_dt: parsed datetime object of the datetime stamp taken from the bus logfile path
    '''
    
    if log_dt < self.start_time: 
      return "before"
    
    if log_dt > self.end_time:
      return "after"

    return "within"


  def filter_1553_log_files(self, logfile_paths):
    '''
    1553 bus log files can be very large. In order to make the API endpoint more efficient, the log files are filtered
    to see if they are within the query start and end time. 

    start and end time are datetime objects in order to do the datetime comparison.

    '''
    logger.info("Further filtering of 1553 bus logfiles by start and end datetime")
    logger.debug("length of list: %s" % len(logfile_paths))

    # Walk through logfile_paths and determine if logfile is within the query start time and query end time
    # Assumption: logfile_paths are in ascending order by time
    
    selected_idxs = []
    first_after_idx = None
    # Step 1: Find log files that were created within the query start and end times      
    for idx, logfile_path in enumerate(logfile_paths):
      log_dt = self.get_date_from_logfile_path(logfile_path)
      pos = self.determine_logfile_path_position(log_dt)

      #logger.debug(f'logfile_path: {logfile_path} pos: {pos}')

      if pos == 'within':
        selected_idxs.append(idx)
      elif pos == "after":
        first_after_idx = idx
        break
    
    # Step 2: Check the log file that is just before the selected ones so far
    if len(logfile_paths) > 0:
      if len(selected_idxs) > 0:
        first_selected_idx = selected_idxs[0]
        if first_selected_idx > 0:
          prev_idx = first_selected_idx - 1
          # prepend it
          selected_idxs.insert(0, prev_idx)
      else:
        # If no log file is selected so far, need to figure out when it switches from before to after.
        if first_after_idx is not None:
          prev_after_idx = first_after_idx - 1
          log_dt = self.get_date_from_logfile_path(logfile_paths[prev_after_idx])
          pos = self.determine_logfile_path_position(log_dt)
          
          if pos == 'before':
            selected_idxs.append(prev_after_idx)
        else:
          # If no log file is selected so far, check the last log file
          last_idx = len(logfile_paths)-1
          log_dt = self.get_date_from_logfile_path(logfile_paths[last_idx])
          pos = self.determine_logfile_path_position(log_dt)
          # include the last log file unless it was created after the query end time
          # or before the query start time
          if pos != 'after':
            selected_idxs.append(last_idx)
    
    selected_logfile_paths = [logfile_paths[i] for i in selected_idxs]
    return selected_logfile_paths

  def get_schema_resolved_paths (self):
    '''
    :return: paths with all the keys in the schema resolved (list of strings)
    '''
    resolved_path = self._resolve_single_arg_vars()
    return self._resolve_multi_arg_vars(resolved_path)

  def get_1553_bus_logs(self):
    # init function has loaded the yyyy list and doy list 

    # Get filtered list of logfile paths (today and yesterday)
    doy_filtered_logfile_paths = self.get_matching_paths(get_bus_logs=True)
    # logger.debug("DOY filtered logfile paths: %s" % doy_filtered_logfile_paths)
    # filter again using start and end time as parameters 
    filtered_logfile_paths = self.filter_1553_log_files(logfile_paths=doy_filtered_logfile_paths)

    return filtered_logfile_paths

  def get_matching_paths (self, filters=[], get_bus_logs=False):
    '''
    :param filters: only return paths containing these filters (list of strings)
    :param get_bus_logs: since this method is used outside of retrieving bus logs, this flag will allow for additional
    functions to be executed within this function.

    :return: paths with all keys in path template resolved, and path names fully
     expanded using glob (list of strings)
    '''
    schema_resolved_paths = self.get_schema_resolved_paths()
    fully_resolved_paths = []

    logger.debug("SCHEMA RESOLVED PATHS: {}".format(schema_resolved_paths))

    for unexpanded_path in schema_resolved_paths:
      logger.debug("UNEXPANDED PATH: {}".format(unexpanded_path))
      valid_paths = glob.glob(unexpanded_path)
      # logger.debug("VALID PATH: {}".format(valid_paths))
      if (filters):
        tmp_paths = []
        for path in valid_paths:
          met_all_filters = True
          for filter in filters:
            if (filter not in path):
              met_all_filters = False
              break
          if (met_all_filters):
            tmp_paths.append(path)
        valid_paths = tmp_paths

      if (valid_paths):
        fully_resolved_paths.extend(valid_paths)
        
    # sort ascending
    if get_bus_logs is True:
      fully_resolved_paths = self.sort_ascending_logfile_paths(fully_resolved_paths)
      # logger.debug("Sorted paths (ascending): %s" % fully_resolved_paths)
    
    return fully_resolved_paths

  def sort_ascending_logfile_paths(self, resolved_paths):
    
    sorted_paths = sorted(resolved_paths, key=lambda date: datetime.strptime(date.split("/")[-1].split("_")[-1], '%Y%m%dT%H%M%S'))
    return sorted_paths

def get_env (env_var,cast_type=str):
  val = os.environ.get(env_var)
  if (val is not None and val.strip() != ''):
    if (cast_type == str):
      return str(val)
    elif (cast_type == int):
      return int(val)
  return None

def ints_to_doy(nums):
  '''
  convert list of POSITIVE integers to list 3-digit DOY strings
  :param nums: list of integers
  :return: list of 3-digit DOY strings
  '''
  doys = []
  for num in nums:
    if num <= 9:
      doys.append('00'+str(num))
    elif num <= 99:
      doys.append('0'+str(num))
    else:
      doys.append(str(num))
  return doys

def doys_for_lookback (lookback_days):
  '''
  Returns a dictionary of year:[doys] mapping

  :param lookback_days: number of days to look back (int)
  :return: dictionary in following form {<4-digit-year (string)>:<list_of_DOY_strings>}
  '''
  date_dict = {}
  curr_yr_num = int(datetime.utcnow().strftime("%Y"))
  curr_doy_num = int(datetime.utcnow().strftime("%j"))
  #curr_yr_search = {curr_yr_num: range(1,curr_doy_num+1)}
  if (curr_doy_num - lookback_days < 1):
    rem = lookback_days - curr_doy_num
    date_dict[curr_yr_num - 1] = list(range(366-rem,366))
    date_dict[curr_yr_num] = list(range(1, curr_doy_num+1))
  else:
    date_dict[curr_yr_num] = list(range(curr_doy_num-lookback_days,curr_doy_num+1))

  # convert doys to 3-digit strings
  date_dict_str = {}
  for yr in date_dict:
    date_dict_str[str(yr)]=ints_to_doy(date_dict[yr])
  return date_dict_str


class TimeoutError(Exception):
  pass

class InvalidFilePathError(Exception):
  pass

class ConsolePortFileNotFound (Exception):
  pass

class VenueTypeNotFound (Exception):
  pass

class SocketConnectionError (Exception):
  pass

class TimeParsingError (Exception):
  def __init__(self, message):

    # Call the base class constructor with the parameters it needs
    super(TimeParsingError, self).__init__(message)

    # Now for your custom code...
    self.message = message

class LogParseError (Exception):
  pass


