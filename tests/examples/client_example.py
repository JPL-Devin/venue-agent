import requests
import time
import json
from datetime import datetime, timezone, timedelta
from session_info import server, sessionId, exec_shared_dict

if __name__ == '__main__':
    url = f'{server}/eha/realtime'
    
    utc_now = datetime.now(tz=timezone.utc)

    query_start_time = datetime.strftime(utc_now - timedelta(seconds=10), '%Y-%jT%H:%M:%S')
    query_end_time = datetime.strftime(utc_now, '%Y-%jT%H:%M:%S')

    print(f'query realtime eha. query_start_time: {query_start_time} query_end_time: {query_end_time}')
    
    # record command counter
    res = requests.get(url, 
        json= {
            'sessionId': sessionId, 
            'channelId': 'CMD-0027', 
            'startTime': query_start_time,
            'endTime': query_end_time
        },
        headers=exec_shared_dict['headers']
    )
    status_code = res.status_code
    print(f'status_code: {status_code}')
    
    if status_code == 200:
        ehas = res.json()
        # print(json.dumps(ehas, indent=4))

        if len(ehas) < 1:
            raise Exception('Failed to get initial command counter')
    else:
        raise Exception(f'EVR GLAD query failed. status_code: {status_code}. Details: {res.text}')

    cmd_counter0 = int(ehas[0]['dn'])
    cmd_counter = cmd_counter0

    # send a FSW command
    cmd_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
    print('send command')
    url = f'{server}/cmd/fsw_cmd'
    res = requests.post(url, 
        json={
            'sessionId': sessionId, 
            'commandString': 'CMD_NO_OP', 
            'validate': True,
            'stringSelection': 'DEFAULT',
            'timeout': 10
        },
        headers=exec_shared_dict['headers']
    )
    print(res.status_code)
    print(res.text)

    # Check realtime EVR
    for i in range(5):
        time.sleep(2)
        query_end_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')

        print('query realtime evr')
        url = f'{server}/evr/realtime'
        res = requests.get(url, 
            json= {
                'sessionId': sessionId, 
                'evrName': 'CMD_SVC_EVR_CMD_COMPLETED_SUCCESS', 
                'startTime': cmd_start_time,
                'endTime': query_end_time
            },
            headers=exec_shared_dict['headers']
        )
        status_code = res.status_code
        print(f'status_code: {status_code}')
        if status_code == 200:
            evrs = res.json()
            # print(json.dumps(evrs, indent=4))

            if len(evrs) > 0:
                print('EVR was found')
                break

    # Check CHILL EVR
    for i in range(0):
        time.sleep(2)
        query_end_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')

        print('query chill evr')
        url = f'{server}/evr/chill'
        res = requests.get(url, 
            json= {
                'sessionId': sessionId, 
                'evrName': 'CMD_SVC_EVR_CMD_COMPLETED_SUCCESS', 
                'startTime': cmd_start_time,
                'endTime': query_end_time
            },
            headers=exec_shared_dict['headers']
        )
        status_code = res.status_code
        print(f'status_code: {status_code}')
        if status_code == 200:
            evrs = res.json()
            # print(json.dumps(evrs, indent=4))

            if len(evrs) > 0:
                print('EVR was found')
                break
        else:
            raise Exception(f'EVR CHILL query failed. status_code: {status_code}. Details: {res.text}')

    # Check real time EHA
    query_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
    # check the change of command counter
    for i in range(5):
        time.sleep(3)
        query_end_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')

        print('query realtime eha')
        url = f'{server}/eha/realtime'
        res = requests.get(url, 
            json= {
                'sessionId': sessionId, 
                'channelId': 'CMD-0027', 
                'startTime': query_start_time,
                'endTime': query_end_time
            },
            headers=exec_shared_dict['headers']
        )
        status_code = res.status_code
        print(f'status_code: {status_code}')

        if status_code == 200:
            ehas = res.json()
            print(f'ehas count: {len(ehas)}')
            #print(json.dumps(ehas, indent=4))

            # sort by ert
            ehas.sort(key=lambda eha: eha['ert'], reverse=True)
            # print(json.dumps(ehas, indent=4))
            if len(ehas) > 0:
                cmd_counter = int(ehas[0]['dn'])
                print(f'cmd_counter0: {cmd_counter0} cmd_counter: {cmd_counter}')
                if cmd_counter == (cmd_counter0 + 1):
                    print('Command counter was increased by one')
                    break
        else:
            raise Exception(f'EHA GLAD query failed. status_code: {status_code}. Details: {res.text}')
        
    if cmd_counter != (cmd_counter0 + 1):
        raise Exception(f'Command counter was not increased by one. cmd_counter0: {cmd_counter0} cmd_counter: {cmd_counter}')
    
    # EHA Chill query
    print('query chill eha')
    url = f'{server}/eha/chill'
    res = requests.get(url, 
        json= {
            'sessionId': sessionId, 
            'channelIds': ['CMD-0027'], 
            'startTime': query_start_time,
            'endTime': query_end_time
        },
        headers=exec_shared_dict['headers']
    )
    status_code = res.status_code
    print(f'status_code: {status_code}')
    ehas = res.json()

    if status_code == 200:
        print(f'ehas count: {len(ehas)}')
        # sort by ert
        ehas.sort(key=lambda eha: eha['ert'], reverse=True)
        # print(json.dumps(ehas, indent=4))
    else:
        raise Exception(f'EHA CHILL query failed. status_code: {status_code}. Details: {res.text}')


    if len(ehas) > 0:
        cmd_counter2 = int(ehas[0]['dn'])
        print(f'cmd_counter0: {cmd_counter0} cmd_counter2: {cmd_counter2}')
        if cmd_counter2 == (cmd_counter0 + 1):
            print('Command counter was increased by one')
        else:
            raise Exception('Command counter was not increased by one')
    else:
        raise Exception('Failed to get CHILL EHA')


    print('send hw command')
    url = f'{server}/cmd/hw_cmd'
    res = requests.post(url, 
        json={
            'sessionId': sessionId, 
            'commandStem': 'HDW_CLEAR_ZOMBIE', 
            'stringSelection': 'DEFAULT',
            'timeout': 10
        },
        headers=exec_shared_dict['headers']
    )
    print(res.status_code)
    print(res.text)