import logging
logger = logging.getLogger(__name__)

from .core_utils import LogParseError, PathConverter
from datetime import datetime
from xml.etree import ElementTree as ET
from dateutil.parser import *
import json
from bitstring import BitArray
import os
import redis


def determine_if_word_is_hex(word):

    try:
        int(word, 16)
    except ValueError:
        return False
    
    return True

class XMLdictionary:
    def __init__(self, filename):
        '''
        This function parses the specified XML file and locates the individual 1553 signals
        :param filename:
        '''
        self.root = ET.parse(filename)
        # Finds the 1553 variable collection
        self.signal_container=self.root.find("mil1553_signals")
        # Finds all the 1553 variables
        self.signals=self.signal_container.findall("mil1553_signal")

        if self.root.find('extended_signals') is None:
            self.extended_signals = []
        else:
            self.extended_signals=self.root.find('extended_signals').findall("extended_signal")


    def ParseDictionary(self,parsing_variable):
        """
        This function parses the XML definitions and produces a python dictionary indexed by signal name.
        :param parsing_variable: Variable or Address, which governs the orientation of the dictionary it returns
        :return: Dictionary of the 1553 Definition
        """
        results={}

        if parsing_variable == "Extended_Signal":
            ml_id = self.extended_signals
            ml_mappings = {}

            for mapping in ml_id:
                signal_name = mapping.get("name")
                ml_mappings[signal_name] =  {
                    "remote_terminal": mapping.get("remote_terminal"),
                    "sub_address": mapping.get("sub_address"),
                    "transmit_receive": mapping.get("transmit_receive"),
                    "word_count": mapping.get("word_count")
                    }

            return ml_mappings

        for signal in self.signals:
            result = {}

            mil1553_def = signal.find("mil1553_map")
            enum_container = signal.find("enums")
            rti_map = mil1553_def.find("rtis")
            map_container = mil1553_def.find("data_word_maps")
            maps = map_container.findall("data_word_map")
            poly_container = signal.find("polynomial_expansion")

            if enum_container != None:
                enums=enum_container.findall("enum")
                enumeration={}
                for enum in enums:
                    enumeration[enum.get("numeric")]=enum.get("symbol")
                result["enumeration"]=enumeration
                result["data_type"] = "ENUM"

            if rti_map != None:
                rtis=rti_map.findall("rti")
                list_of_rtis=[]
                for rti in rtis:
                    list_of_rtis.append(int(rti.text))
            else:
                list_of_rtis = ['ALL']

            if maps != None:
                data_maps=[]
                for map in maps:
                    if map.get("word") in ["ERROR", "STATUS"]:
                        data_maps.append({"word":map.get("word"),"bit_start":int(map.get("bit_start")),
                                      "num_bits":int(map.get("num_bits"))})                        
                    else:
                        data_maps.append({"word":int(map.get("word")),"bit_start":int(map.get("bit_start")),
                                      "num_bits":int(map.get("num_bits"))})
                result["data_map"]=data_maps

            if poly_container != None:
                poly=[]
                factors=poly_container.findall("factor")
                for factor in factors:
                    try:
                        index=int(factor.get("index"))
                        coeff=float(factor.get("coeff"))
                    except:
                        raise
                    poly.append({"index":index,"coeff":coeff})
                result['polynomial']=poly
                result["data_type"] = "polynomial"
            result['type'] = signal.get("type")

            sa=int(mil1553_def.get("sub_address"))
            rt=int(mil1553_def.get("remote_terminal"))
            tr=mil1553_def.get("transmit_receive")

            if parsing_variable == 'Variable':
                result['sub_address'] = sa
                result['remote_terminal'] = rt
                result['transmit_receive'] = tr
                result["rtis"]=list_of_rtis
                results[signal.get("name")] = result
            else:
                raise TypeError("Unknown input (%s) - valid inputs include Address and Type" %parsing_variable)
        
        return results


class BusLogMsg:
    def __init__(self, line, time_type, query_start_time, query_end_time, logfile, irig_time="false", assumed_year=None):
        '''
        This function parses a line in the 1553 text log file into a list of variables
        :param line:  The line to parse
        :param time_type: If the 1553 Log is using an IRIG processor the time will be in a different format.
        :param query_start_time: start time for query, no log entries should be processed before this time mark
        :param query_end_time: end time for query, no log entries should be processed after this time mark
        :param logfile: name of the logfile
        :param irig_time: value can either be "true" or "false". This value is set in the venue server config file.
        :param assumed_year: given that "irig_time" is set to "true", this value is used to construct a valid datetime object
        '''

        message=line.split(" ")
        
        if irig_time.lower()=="true":
            if assumed_year != None:
                try:
                    logger.debug("irig time detected. Adding assumed year: %s" % (str(assumed_year)+":"+message[0]))
                    self.time=datetime.strptime(str(assumed_year)+":"+message[0],"%Y:%j:%H:%M:%S.%f")
                except:
                    raise Exception("Encountered unexpected time format (%s)" %message[0])
            else:
                raise Exception("Unable to process IRIG times without a provided year")
        else:
            try:
                self.time = datetime.strptime(message[0], "%Y%m%dT%H%M%S")
            except:
                raise Exception("Encountered unexpected time format (%s)" % message[0])

        self.rti=message[1]
        self.sclk=int(message[2])/1000000.0
        self.bus=message[3].split("=")[1]
        self.command=message[4].split("=")[1]
        self.status_word=message[5].split("=")[1]
        self.rt=int(message[6].split("=")[1])
        self.sa=int(message[7].split("=")[1])
        self.transmit_receive=message[8].split("=")[1]
        self.word_count=int(message[9].split("=")[1])
        self.error_code=message[10].split("=")[1]
        self.dt=message[11].split("=")[1]
        self.words=[]
        self.time_type=time_type
        self.logfile_line=line
        self.logfile=logfile
        
        try:
            # word count 0 = 32
            # logger.debug("Word Count: %s" % (self.word_count))
            # logger.debug("Message: %s" %(message))
            if self.word_count == 0:
                self.word_count = 32

            for i in range(13,13+self.word_count):
                if "\n" in message[i]:
                    break
                self.words.append(message[i])
		
            # logger.debug("Collected word list: %s" % (self.words))
        except:
            msg = "There was an error parsing the line: '%s' in logfile: '%s'" % (message, logfile)
            logger.error(msg)
            raise Exception(msg)

    def filter(self,rti=None,sa=None,start_time=None,end_time=None,transmit_receive=None, rt=None,bus=None, error=None,
               sclk_start=None, sclk_end=None):
        '''
        This function provides a filter on the Log Message.
        :param rti: List of RTIs
        :param sa:  List of Subaddresses
        :param start_time:  Start time to filter on (date time object)
        :param end_time:   End time to filter on (date time object)
        :param transmit_receive: List indicating the use of "T"ransmit and/or "R"eceive
        :param rt: List of Remote terminals
        :param bus: List of Buses
        :param error: List of Errors
        :param sclk_start: Starting SCLK (float) to filter on
        :param sclk_end: Ending SCLK (float) to filter on
        :return: (time filter passed, overall filter passed)
        '''

        '''
        This code walks through the filter criteria first assessing if the filter exists, then assessing if the
        current log meets the filter criteria. These filters are "AND'd" together so a line only meets the filter
        requirements (return true) if they are all met.
        '''

        if start_time is not None:
            if self.time < start_time:
                return False, False
       
        if end_time is not None:
            if self.time > end_time:
                return False, False

        if sclk_start is not None:
            if self.sclk < sclk_start:
                return False, False

        if sclk_end is not None:
            if self.sclk > sclk_end:
                return False, False
                
        # Is the RTI in list of RTIs?
        if rti is not None:
            if (self.rti not in rti) and ("ALL" not in rti):
                return True, False

        # Is the Subaddress in the list of Subaddresses?
        if sa is not None:
            if self.sa not in sa:
                return True, False

        # Is the Transmit / Receive in the list of either T or R (or both)?
        if transmit_receive is not None:
            if self.transmit_receive not in transmit_receive:
                return True, False

        # Is the remote terminal in the list of RTs to filter on?
        if rt is not None:
            if self.rt not in rt:
                return True, False

        # Does the 1553 bus match the provided bus filter?
        if bus is not None:
            # TODO: check bus is a list
            if self.bus not in bus:
                return True, False

        # Is the error code in the provided filter?
        if error is not None:
            # TODO: check error is a list
            if self.error_code not in error:
                return True, False

        return True, True

    def decode(self,var_name,dict_entry, multi_line_data=None):
        '''
        This function decodes a specific entry in the 1553 log message into a raw value and (optionally) a converted
        value.

        :param dict_entry: This is the dictionary definition of a single variable
        :return: Raw and converted value for the variable
        '''

        if multi_line_data is not None:
            self.words = multi_line_data

        # Extracts the word(s) and slices/joins them accordingly
        bitarray=None
        value=None
        converted_value = None
        for word in dict_entry['data_map']:
            try:
                if word['word'] in ['ERROR','STATUS']:
                    logger.debug("Found an %s word to extract" % word["word"])
                    word_to_extract = word["word"]
                else:
                    word_to_extract = int(word["word"]) - 1
                logger.debug("Word to extract: %s" % (word_to_extract))
                bit_start=int(word['bit_start'])
                logger.debug("Bit start value: %s" % (bit_start))
                num_bits=int(word['num_bits'])
                logger.debug("Number of bits to parse: %s" % (num_bits))
                start_bit=16-(bit_start+num_bits)
                logger.debug("Start bit: %s" % (start_bit))
                end_bit=start_bit+num_bits
                logger.debug("End bit: %s" % (end_bit))
                # Convert the word to a bit array
                if word_to_extract == "ERROR":
                    word_string = self.error_code
                elif word_to_extract == "STATUS":
                    word_string = self.status_word
                    is_hex = determine_if_word_is_hex(word_string)
                    if is_hex is False:
                        return word_string, converted_value
                else:
                    # attempt to extract word, if it throws an error, move to next word
                    try:
                        word_string = self.words[word_to_extract]
                    except:
                        logger.debug('Unable to extract %s from data: %s' %(var_name,self.words))
                        continue
                logger.debug("Word string: %s" % (word_string))
                word_array=BitArray("0x%s" %word_string)
                logger.debug("Word array: %s" % (word_array))
                # Slice per the bit definition
                bits=word_array[start_bit:end_bit]
                logger.debug("Sliced bits: %s" % (bits))
                bitarray = bitarray+bits
                logger.debug("Bit array: %s" % (bitarray))
            except:
                msg = "Error trying to extract word from bus log message. logfile: '%s' line: '%s'" %(self.logfile, self.logfile_line)
                raise Exception(msg)
        try:
            # Converts the value per the defined type
            if dict_entry['type']=="INT":
                value=bitarray.int
                logger.debug("Identified type 'INT': %s" % (value))
            if dict_entry['type']=="UINT":
                value = bitarray.uint
                logger.debug("Identified type 'UINT': %s" % (value))
            if dict_entry['type']=="FLOAT":
                value=bitarray.float
                logger.debug("Identified type 'FLOAT': %s" % (value))
            if dict_entry['type']=="HEX":
                value=bitarray.hex
                logger.debug("Identified type 'HEX': %s" % (value))
            if dict_entry['type'] == "BIN":
                value = bitarray.bin
                logger.debug("Identified type 'BIN': %s" % (value))
        except:
            msg = "Error trying to convert value to type: '%s'. logfile: '%s' line: '%s'" % (dict_entry['type'], self.logfile, self.logfile_line)
            logger.error(msg)
            raise Exception(msg)

        # Grab any enumerations
        enum=dict_entry.get('enumeration')
        
        # In enums are present evaluate them
        if enum != None:
            logger.debug("Enumeration found: %s" % (enum))
            # TODO: why was this being casted as a string
            lookup=enum.get(str(value))
            # If a look up value exists - grab the value, else report an error
            if lookup != None:
                converted_value=lookup
            else:
                # TODO: this needs to be bubbled up as an error message 
                converted_value="ERROR: No Enumeration Defined"
        # If a polynomial conversion is present evaluate it
        poly=dict_entry.get('polynomial')
        
        if poly != None:
            logger.debug("Polynomial found: %s" % (poly))
            converted_value=0
            # Walk through the polynomial terms and apply them
            for term in poly:
                coefficient=term['coeff']
                index=term['index']
                converted_value=converted_value+(coefficient*(value^index))

        logger.debug("Final value and converted value:")
        logger.debug("Value: %s, Converted Value: %s" % (value, converted_value))
        return value,converted_value


    def decode_by_var(self, dict_entry, query, multi_line_dict=None):
        '''
        This function filters and parses the 1553 message based on a query string that includes defined variables.

        :param dict_entry: dictionary entry for the variable
        :param variables: Query dictionary
        :return: list of decoded 1553 messages
        '''
        start_time = query.get('query_start_time')
        end_time = query.get('query_end_time')
        sclk_start = query.get('sclk_start')
        sclk_end = query.get('sclk_end')
        
        results = []

        # For each variable, extract the addresss definition, filter the line on them and decode if needed.
        var_name = query.get('variables')
        
        # Check if the variable is defined, if not skip it with an error message
        # Additional condition: 1553 Decoder should skip messages that are "NORESP" and not attempt to decode them.
        if dict_entry is None:
            return results
        elif self.status_word == 'NORESP':
            return results
        elif self.word_count != len(self.words):
            return results
        else:
            # Filter the 1553 messages per the query
            
            """
            Example of dict_entry:
            {
                "data_map": [{"word": 1, "bit_start": 0, "num_bits": 16}], 
                "type": "UINT", 
                "sub_address": 9, 
                "remote_terminal": 9, 
                "transmit_receive": "R",
                "rtis": ["ALL"]
            }
            
            Example of BusLogMsg
            {
                "time": "2023-03-28 04:09:49", 
                "rti": "3", 
                "sclk": 712597947.224609, 
                "bus": "psyche-A", 
                "command": "0x4925", 
                "status_word": "0x4800", 
                "rt": 9, 
                "sa": 9, 
                "transmit_receive": "R", 
                "word_count": 5, 
                "dt": "", 
                "words": ["cc01", "0000", "0202", "0202", "25b0"], 
                "logfile_line": "20230328T0409     49 3 712597947224609 Bus=psyche-A C=0x4925 S=0x4800 RT=09 SA=09 TR=R WC=05 Err= dt= Data= cc01 0000 0202 0202 25b0 \n", 
                "logfile": "/var/ammos/archive/2023/086/sse/psychedevingenium1/session_119/hongmank/wsts-gds.results/psyche_20230328T040308"
            }
            
            """
            time_match, match = self.filter(rti=dict_entry.get('rtis'), sa=[dict_entry.get('sub_address')], start_time=start_time,
                                end_time=end_time, transmit_receive=[dict_entry.get('transmit_receive')],
                                rt=[dict_entry.get('remote_terminal')], bus=dict_entry.get('bus'), error=dict_entry.get('error'),
                                sclk_start=sclk_start, sclk_end=sclk_end)
                            
            # If they have met the filter requirements decode the message per the definitions for the current message
            if match:
                logger.info(f'match: {match} BusLogMsg: {self}')
                try:
                    # entire conversion process must be nominal for the entry to be added to "results" list.
                    value,converted_value = self.decode(var_name, dict_entry, multi_line_dict)
                    
                    data_type = self.get_data_type(dict_entry)
                    response_object = {
                        "variable": query.get('variables'),
                        "time_scet": datetime.strftime(self.time, "%Y-%jT%H:%M:%S.%f"),
                        "time_sclk": str(self.sclk),
                        "rti": int(self.rti),
                        "bus_name": self.bus,
                        "error_status": self.error_code,
                        "status_word": self.status_word,
                        "data_value": str(value),
                        "data_type": data_type,
                        "converted_value": str(converted_value) if converted_value is not None else "",
                        "dictionary": query.get("dictionary")
                    }

                    results.append(response_object)
                except:
                    pass
            elif time_match:
                pass
                # logger.debug(f'match: {match} BusLogMsg: {self}')

        return results

    def get_data_type(self, dict_entry):
        '''
        This method uses the variable dictionary to extract the data type of the variable. The data type 
        can be [int, unsigned int, float, hex, binary, enum, or polynomial]

        :param dict_entry: This is a dictionary definition of a single variable
        :return: variable data type
        '''

        if dict_entry.get("data_type") is not None:
            return dict_entry.get("data_type")
        else:
            return dict_entry.get("type")

    def to_json(self):
        return {
            'time': str(self.time),
            'rti': self.rti,
            'sclk': self.sclk,
            'bus': self.bus,
            'command': self.command,
            'status_word': self.status_word,
            'rt': self.rt,
            'sa': self.sa,
            'transmit_receive': self.transmit_receive,
            'word_count': self.word_count,
            'dt': self.dt,
            'words': self.words,
            'logfile_line': self.logfile_line,
            'logfile': self.logfile
        }
        
            
    def __str__(self):
        return (f'time: {self.time} rti: {self.rti} sclk: {self.sclk} bus: {self.bus} command: {self.command}'
            f' status_word: {self.status_word} rt: {self.rt} sa: {self.sa} transmit_receive: {self.transmit_receive}'
            f' word_count: {self.word_count} dt: {self.dt} words: {self.words} logfile_line: {self.logfile_line}'
            f' logfile: {self.logfile}')

def get_assumed_year(logfile_path):

    '''
    If irig is present on the venue the year portion of the logfile time will not be present. 
    This function will evaluate an "assumed year" if irig is true. 

    :param logfile_path: 1553 logfile paths are used to get the assumed year.
    :return: The assumed year
    '''

    file_name = logfile_path.split('/')[-1]
    datetime_str = file_name.split('_')[-1]
    log_dt = datetime.strptime(datetime_str, '%Y%m%dT%H%M%S') 
    return log_dt.year

def determine_multi_line(is_multi_line_entry, multi_line_dict, line, key=None):
    '''
    Auxiliary function for "process_file" to evaluate whether a logfile entry is a multi line entry. An entry is evaluated
    as a multi line entry if the rt, sa, and tr match the ones found in the extended signal dictionary. 

    :param is_multi_line_entry: boolean value representing whether previous entry was a mutli line entry. 
    :param multi_line_dict: dictionary of extended signals. 
    :param line: log file entry that will be evaluated
    :param key: In the case that there are more than 1 extended signal in the 1553 decode dictionary, a key is necssary to know which extended signal was identified.
    :return: tuple - boolean, extended signal key
    '''

    # If variables are present in the query, use them to process the file, otherwise process based on address
    message = line.split(" ")
    rt=message[6].split("=")[1]
    sa=message[7].split("=")[1]
    transmit_receive=message[8].split("=")[1].lower()

    if is_multi_line_entry is False:
        for key, value in multi_line_dict.items():
            if value["remote_terminal"] == rt and value["sub_address"] == sa and value["transmit_receive"].lower() == transmit_receive:
                return True, key
    else:

        mld = multi_line_dict
        if mld[key]["remote_terminal"] == rt and mld[key]["sub_address"] == sa and mld[key]['transmit_receive'].lower() == transmit_receive:
            return True, key

    return False, None

def set_word_counter(word_count_counter, multi_line_dict, ml_dict_key):
    '''
    Auxiliary function for "process_file", if at the beginning of the multi line entry, a word counter must be set
    in order to keep track and to know when the end of the multi line entry has been reached. 

    :param word_count_counter: external variable that stores the word counter for the given multi line entry. 
    :param multi_line_dict: dictionary of extended signals. 
    :param ml_dict_key: extended signal dictionary key 
    :return: word count counter
    '''
    word_count = int(multi_line_dict[ml_dict_key]["word_count"])
    
    if word_count_counter is None:
        word_count_counter = word_count

    return word_count_counter


def split_line_data_and_append_to_list(line, data_list, word_count_counter):
    '''
    Auxiliary function for "process_file", each multi line entry data must be added to an extended list of data.


    :param line: multi line logfile entry  
    :param data_list: external variable that contains collected data from all multi line entries.
    :param word_count_counter: external variable that stores the word counter for the given multi line entry. 
    :return: tuple - data list, word count counter
    '''
    message = line.split(" ")
    word_count = int(message[9].split("=")[1])
    split_data = []

    for i in range(13,13+word_count):
        if "\n" in message[i]:
            break
        split_data.append(message[i])

    word_count_counter = word_count_counter - word_count

    for data in split_data:
        data_list.append(data)
    
    return data_list, word_count_counter
    

def process_file(start_time, end_time, dict_entry, extended_signals, logfile, query):
    '''
    Main function that iterates through each 1553 bug log file. This version has the ability to interpret and process 
    multi line entries. 

    :param logger: logger object for recording to log(s) 
    :param start_time: query start time
    :param end_time: query end time
    :param dict_entry: dictionary info of the variable
    :param extended_signals: dictionary of parsed extended signal channels
    :param file: list of 1553 log files that will be parsed
    :param query: dictionary of essential information needed to parse
    :return: list of parsed entries
    '''

    is_multi_line_entry = False 
    ml_dict_key = None
    word_count_counter = None
    data_list = []
    response_list = []

    # test code
    counter = 0
    
    logger.info("Check logfile list: %s" % logfile)

    for single_file in logfile:
        
        logger.info(f'Parsing logfile: {single_file}')
	
        with open(single_file, "r") as infile:
            lines = infile.readlines()
            
            logger.info(f'Line count: {len(lines)}')
            for index,line in enumerate(lines):
                # logger.debug("Line to parse: %s" % (line))

                # implementation note: adding some protection against empty line.
                if not line:
                    logger.info("Intended to parse a line, but the line was empty. It is possible that the 1553 log has a newline at the end of the log file.")
                    continue

                is_multi_line_entry, ml_dict_key = determine_multi_line(is_multi_line_entry, extended_signals, line, ml_dict_key)

                if is_multi_line_entry is True and word_count_counter is None:
                    word_count_counter = set_word_counter(word_count_counter, extended_signals, ml_dict_key)

                    # append data to data list and subtract data count from word_count_counter          
                    data_list, word_count_counter = split_line_data_and_append_to_list(line, data_list, word_count_counter)

                    # if word count is less than or equal zero:
                    if word_count_counter < 0:
                        err_msg = "There is more data than specified in the extended signal word count"
                        logger.exception(err_msg)
                        raise Exception(err_msg)

                    elif word_count_counter == 0:
                        # proceed to decode data
                        results=BusLogMsg(line, query.get('time_type'), start_time, end_time, single_file, query.get('irig_status'), query.get('assumed_year')).decode_by_var(dict_entry, query, data_list)
                        
                        if results:
                            for result in results:
                                result.update({"log_file": single_file})
                                response_list.append(result)
                    else:
                        continue   

                
                elif is_multi_line_entry is True and word_count_counter is not None:

                    # append data to data list and subtract data count from word_count_counter          
                    data_list, word_count_counter = split_line_data_and_append_to_list(line, data_list, word_count_counter)

                    # if word count is less than or equal zero:
                    if word_count_counter < 0:
                        err_msg = "There is more data than specified in the extended signal word count"
                        logger.exception(err_msg)
                        raise Exception(err_msg)

                    elif word_count_counter == 0:
                        # proceed to decode data
                        results=BusLogMsg(line, query.get('time_type'), start_time, end_time, single_file, query.get('irig_status'), query.get('assumed_year')).decode_by_var(dict_entry, query, data_list)
                        # reset variables to default state 
                        is_multi_line_entry = False 
                        ml_dict_key = None
                        word_count_counter = None
                        data_list = []                    

                        if results:
                            counter = counter + 1
                            for result in results:
                                result.update({"log_file": single_file})
                                response_list.append(result)                
                    else:
                        continue          

                elif is_multi_line_entry is False:

                    results=BusLogMsg(line, query.get('time_type'), start_time, end_time, single_file, query.get('irig_status'), query.get('assumed_year')).decode_by_var(dict_entry, query, multi_line_dict=None)

                    # reset variables to default state 
                    is_multi_line_entry = False 
                    ml_dict_key = None
                    word_count_counter = None
                    data_list = []                    

                    if results:
                        counter = counter + 1
                        for result in results:
                            result.update({"log_file": single_file})
                            response_list.append(result)      
                else:
                    err_msg = "There was an error parsing the logfile"
                    logger.exception(err_msg)
                    raise Exception(err_msg)          
                
                # logger.debug("Completed parsing line: %s" % (index + 1))

    return response_list


def read_dict(dictionary):
    '''
    Function parses the 1553 dictionary and returns two dictionaries: variables & extended signals

    :param dictionary: 1553 parsing dictionary location
    :return: tuple - variable & extended signals dictionary
    '''

    dictionary=XMLdictionary(dictionary)
    # Removed Address parsed dictionary, since requests will be directed towards variables
    variable_dictionary=dictionary.ParseDictionary("Variable")
    es_dictionary = dictionary.ParseDictionary("Extended_Signal")

    return variable_dictionary, es_dictionary


def decode_1553_log_files(info, dictionary_path):
    # diff between europa and m2020 gds, since logfile directory convention is diff. (there are already functions for this)
    '''
    Main function that parses 1553 parsing dictionary and processes the file. It returns the list that will be returned to the user.

    :param logger: your average, ordinary logger. It logs
    :param info: dictionary that represents essential information to help with processing logs.
    :param dictionary_path: this is the location on the GDS host where the 1553 dictionary xml can be found. This will be parsed and then used.
    :return: response list
    '''

    var, extended_signals = read_dict(dictionary_path)

    # TODO: this needs to be refactored or a better solution should be implemented.
    # r = redis.StrictRedis(host="localhost", port=6379, db=0)
    # var = json.loads(r.get("variable_dictionary"))
    # extended_signals = json.loads(r.get("extended_signals"))

    # Error Catch: If a variable name cannot be found in the variable dictionary.
    
    dict_entry = var.get(info.get("variables"))
    if dict_entry is None:
        err_msg = "Variable name: %s,could not be found in the variable dictionary" % info.get("variables")
        logger.exception(err_msg)
        raise Exception(err_msg) 

    logger.debug(f'Searching for this variable: {dict_entry}')
    response_list = process_file(info.get('query_start_time'), info.get('query_end_time'), dict_entry, extended_signals, info.get('logfile'), info)
    logger.info("Completed parsing of 1553 log files")
    # sorted() accounts for empty list
    sorted_response_list = sorted(response_list, key=lambda date: datetime.strptime(date.get("time_scet"), '%Y-%jT%H:%M:%S.%f'), reverse=True)
    return sorted_response_list



def get_dict_path(path_template, side_str, sess_name, username):

  logger.info(f'get_dict_path path_template: {path_template}')

  files = []
  # populate all schema variables in path template and expand paths
  pc = PathConverter(path_template=path_template,
                      chill_sess_name=sess_name,
                      username=username,
                      side=side_str)
  result = pc.get_schema_resolved_paths()  

  files.extend(pc.get_matching_paths())
  logger.info(f'dict_paths: {files}')
  
  try:
    latest_file = files[0]
  except Exception as ex:
    raise LogParseError(ex)
  logger.info (f'dict_path: {latest_file}')
  return latest_file


def get_most_recent_1553_logfiles(path_template, side_str, sess_name, username, start_time, end_time):

  logger.info('Setting variables and paths:')
  logger.info(f'Path template: {path_template}')
  logger.info(f'Side: {side_str}')
  logger.info(f'Session Name: {sess_name}')
  logger.info(f'Username: {username}')
  logger.info(f'start_time: {start_time}')
  logger.info(f'end_time: {end_time}')

  logfiles = []
  # populate all schema variables in path template and expand paths
  pc = PathConverter(path_template=path_template,
                    chill_sess_name=sess_name,
                    username=username,
                    side=side_str,
                    start_time=start_time, 
                    end_time=end_time)

  # TODO: create another method in PathConverter that takes in a start and end time and returns exact   
  logfiles = pc.get_1553_bus_logs()

  # files.extend(pc.get_matching_paths())
  logger.info(f'RETURNED RESOLVED PATHS: {logfiles}')
  
  return logfiles
  
