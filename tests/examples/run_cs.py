import requests
import time
import sys
import json
from datetime import datetime, timezone, timedelta
from session_info import server, sessionId, exec_shared_dict

if __name__ == '__main__':    
    # send a FSW command
    cs_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
    print('start CS')
    url = f'{server}/custom_script/start'
    print(f'url: {url}')
    start_input = {
        "scriptName": "crc32_checksum_file", 
        "scriptPath": "current/tools/common/ing_cs/crc32_checksum_file/crc32_checksum_file.py", 
        "scriptHash": "02968946506afde4b58a4d6c7f6d4784a054e76d87827285c3cea7c5a5cf5f30", 
        "inputs": {
            "username": "", 
            "inputs": {}, 
            "entries": [
                {
                    "entry_inputs": {
                        "path": "/home/hongmank/tests/test1.txt", 
                        "predict_crc32": "a107fce7"
                    },
                    "entry_inputs": {
                        "path": "/home/hongmank/tests/test2.txt", 
                        "predict_crc32": "8a2aaf24"
                    },
                    "entry_inputs": {
                        "path": "/home/hongmank/tests/test3.txt", 
                        "predict_crc32": "93319e65"
                    }
                }
            ]
        }, 
        "outputs": {
            "custom_script_status": "PENDING", 
            "inputs": {}, 
            "entries": [
                {
                    "verification_status": "PENDING", 
                    "entry_inputs": {
                        "path": "/home/hongmank/tests/test1.txt", 
                        "predict_crc32": "a107fce7"
                    }, 
                    "entry_outputs": {
                        "actual_crc32": ""
                    }, 
                    "entry_output_array": []
                }
            ], 
            "outputs": {}, 
            "output_array": []
        }
    }

    res = requests.post(url, json=start_input, headers=exec_shared_dict['headers'])
    print(res.status_code)
    print(res.text)
    res_dict = res.json()
    script_run_id = res_dict['scriptRunId']

    #sys.exit(1)

    # check status
    url = f'{server}/custom_script/status'
    status_input = {
        'scriptRunId': script_run_id
    }
    res = requests.get(url, json=status_input, headers=exec_shared_dict['headers'])
    print(res.status_code)
    print(res.text)

    time.sleep(1)

    # check status again
    url = f'{server}/custom_script/status'
    status_input = {
        'scriptRunId': script_run_id
    }
    res = requests.get(url, json=status_input, headers=exec_shared_dict['headers'])
    print(res.status_code)
    print(res.text)

    # download output and log files
    print('download tar.gz')
    url = f'{server}/custom_script/{script_run_id}/files'

    res = requests.get(url, headers=exec_shared_dict['headers'])
    print(res.status_code)

    zname = f'cs-files.tar.gz'
    zfile = open(zname, 'wb')
    zfile.write(res.content)
    zfile.close()

    # Run it again
    print('run CS again')
    url = f'{server}/custom_script/start'
    print(f'url: {url}')
    res = requests.post(url, json=start_input, headers=exec_shared_dict['headers'])
    print(res.status_code)
    print(res.text)
    res_dict = res.json()
    script_run_id = res_dict['scriptRunId']

    # Halt
    print('Halt CS')
    url = f'{server}/custom_script/halt'
    print(f'url: {url}')
    halt_input = {
        'scriptRunId': script_run_id
    }
    res = requests.post(url, json=halt_input, headers=exec_shared_dict['headers'])
    print(res.status_code)
    print(res.text)

    # check status
    print('Check status will fail')
    url = f'{server}/custom_script/status'
    status_input = {
        'scriptRunId': script_run_id
    }
    res = requests.get(url, json=status_input, headers=exec_shared_dict['headers'])
    print(res.status_code)
    print(res.text)