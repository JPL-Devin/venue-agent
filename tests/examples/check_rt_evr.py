import requests
import time
import json
from datetime import datetime, timezone, timedelta
from session_info import server, sessionId, exec_shared_dict, CMD_COMP_EVR, CMD_DISPATCHED_EVR

def run_evr_query():
    utc_now = datetime.now(tz=timezone.utc)

    query_start_time = datetime.strftime(utc_now - timedelta(seconds=120), '%Y-%jT%H:%M:%S')
    query_end_time = datetime.strftime(utc_now, '%Y-%jT%H:%M:%S')

    print('query realtime evr')
    url = f'{server}/evr/realtime'
    res = requests.get(url, 
        json= {
            'sessionId': sessionId, 
            'evrName': CMD_COMP_EVR,
            'startTime': query_start_time,
            'endTime': query_end_time
        },
        headers=exec_shared_dict['headers']
    )
    status_code = res.status_code
    print(f'status_code: {status_code}')
    if status_code == 200:
        print(f'respose: {json.dumps(res.json(), indent=4)}')        
    else:
        print(f'text: {res.text}')

def run_wildcard_query():
    utc_now = datetime.now(tz=timezone.utc)

    query_start_time = datetime.strftime(utc_now - timedelta(seconds=3600), '%Y-%jT%H:%M:%S')
    query_end_time = datetime.strftime(utc_now, '%Y-%jT%H:%M:%S')

    print('query realtime evr')
    url = f'{server}/evr/realtime'
    res = requests.get(url, 
        json= {
            'sessionId': sessionId, 
            'evrName': '*COMPLE*', 
            'startTime': query_start_time,
            'endTime': query_end_time
        },
        headers=exec_shared_dict['headers']
    )
    status_code = res.status_code
    print(f'status_code: {status_code}')
    if status_code == 200:
        print(f'respose: {json.dumps(res.json(), indent=4)}')        
    else:
        print(f'text: {res.text}')

def run_evr_multi_query():
    utc_now = datetime.now(tz=timezone.utc)

    query_start_time = datetime.strftime(utc_now - timedelta(seconds=3600), '%Y-%jT%H:%M:%S')
    query_end_time = datetime.strftime(utc_now, '%Y-%jT%H:%M:%S')

    print('query CHILL evr (multi)')
    url = f'{server}/evr/realtime_multi'
    res = requests.get(url, 
        json= {
            'sessionId': sessionId, 
            'evrNames': [CMD_COMP_EVR, CMD_DISPATCHED_EVR], 
            'startTime': query_start_time,
            'endTime': query_end_time
        },
        headers=exec_shared_dict['headers']
    )
    status_code = res.status_code
    print(f'status_code: {status_code}')
    if status_code == 200:
        print(f'respose: {json.dumps(res.json(), indent=4)}')        
    else:
        print(f'text: {res.text}')

    res = requests.get(url, 
        json= {
            'sessionId': sessionId, 
            'eventIds': [67895318, 67895316], 
            'startTime': query_start_time,
            'endTime': query_end_time
        },
        headers=exec_shared_dict['headers']
    )
    status_code = res.status_code
    print(f'status_code: {status_code}')
    if status_code == 200:
        print(f'respose: {json.dumps(res.json(), indent=4)}')        
    else:
        print(f'text: {res.text}')

    res = requests.get(url, 
        json= {
            'sessionId': sessionId, 
            'evrLevels': ['WARNING_LO', 'COMMAND'], 
            'startTime': query_start_time,
            'endTime': query_end_time
        },
        headers=exec_shared_dict['headers']
    )
    status_code = res.status_code
    print(f'status_code: {status_code}')
    if status_code == 200:
        print(f'respose: {json.dumps(res.json(), indent=4)}')        
    else:
        print(f'text: {res.text}')

if __name__ == '__main__':    
    #run_evr_query()
    #run_wildcard_query()
    run_evr_multi_query()