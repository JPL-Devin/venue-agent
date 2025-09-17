import requests
import time
from datetime import datetime, timezone, timedelta

from session_info import server, sessionId, exec_shared_dict, hostname

if __name__ == '__main__':

    if hostname.startswith('eurc'):
        command_strings = [
            'DDM_SET_EHA_PROD_RATE,5,5,5,5,60,60,60,60',
            'DDM_SET_DWN_TZ_CONFIG, 1000000',
            'DDM_UPDATE_NUM_TSR,0,INVALID,0,ALWAYS,1 seconds,0,RT,MEDIUM,0,AVS',
            'DDM_UPDATE_NUM_TSR,0,INVALID,0,ALWAYS,1 seconds,0,RT,MEDIUM,0,CB',
            'DDM_UPDATE_NUM_TSR,0,INVALID,0,ALWAYS,1 seconds,0,RT,CRITICAL,0,CMD',
            'DDM_UPDATE_NUM_TSR,0,INVALID,0,ALWAYS,1 seconds,0,RT,MEDIUM,0,DDM'
        ]

        for command_string in command_strings:
            print(f'command_string: {command_string}')


            url = f'{server}/cmd/fsw_cmd'
            res = requests.post(url, json={
                    'sessionId': sessionId, 
                    'commandString': command_string, 
                    'validate': True,
                    'stringSelection': 'DEFAULT',
                    'timeout': 10
                },        
                headers=exec_shared_dict['headers']
            )
            print(res.status_code)
            print(res.text)

            # throttle at 1Hz
            time.sleep(1)
    elif hostname.startswith('psyche'):
        # increase uplink speed (Psyche WSTS)
        cmd_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
        print('send sse command')
        url = f'{server}/cmd/sse'
        res = requests.post(url, json={
                'sessionId': sessionId,
                'commandString': 'cmd putp avsim.RceA.mtif.mtifUpl.uplinkRateBitPerSec value 64000',
                'timeout': 60
            },
            headers=exec_shared_dict['headers']
        )
        print(res.status_code)
        print(res.text)

        # uplink generic EHA selection criteria file

        cmd_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
        print('send file')
        url = f'{server}/cmd/binary_file'
        res = requests.post(url, json={
                'sessionId': sessionId,
                'sourceFilePath': '/teamtools/sct/parameter_files/selection_criteria/EHA_SELCRIT_SYS_NOMINAL_C5.4.0.2_TB.230331.r1.bin',
                'targetFilePath': '/eng/sys_nominal1.bin',
                'overwrite': True,
                'fileType': 0,
                'stringSelection': 'DEFAULT',
                'timeout': 60
            },
            headers=exec_shared_dict['headers']
        )
        print(res.status_code)
        print(res.text)

        elapsed_sec = 0
        utc_now = datetime.now(tz=timezone.utc)
        query_start_time = datetime.strftime(utc_now, '%Y-%jT%H:%M:%S')
        while elapsed_sec < 120:
            utc_now = datetime.now(tz=timezone.utc)
            query_end_time = datetime.strftime(utc_now, '%Y-%jT%H:%M:%S')

            print('query realtime evr')
            url = f'{server}/evr/realtime'
            res = requests.get(url, 
                json= {
                    'sessionId': sessionId, 
                    'evrName': 'UPL_MGR_EVR_FILE_CREATED', 
                    'startTime': query_start_time,
                    'endTime': query_end_time
                },
                headers=exec_shared_dict['headers']
            )
            status_code = res.status_code
            print(f'status_code: {status_code}')
            print(f'text: {res.text}')
            if status_code == 200:
                if len(res.json()) > 0:
                    print('UPL_MGR_EVR_FILE_CREATED was received')
                    break
            else:
                print('WARNING: EVR query failed')
            
            time.sleep(10)

        print('Load the TSR file')
        
        url = f'{server}/cmd/fsw_cmd'
        res = requests.post(url, json={
                'sessionId': sessionId, 
                'commandString': 'TLM_EHA_LOAD_SELCRIT_FILE,/eng/sys_nominal1.bin', 
                'validate': True,
                'stringSelection': 'DEFAULT',
                'timeout': 10
            },        
            headers=exec_shared_dict['headers']
        )
        print(res.status_code)
        print(res.text)


