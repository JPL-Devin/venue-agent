import pytest
from datetime import datetime, timezone, timedelta
import time
import sys
import venue_client as vc



@pytest.fixture(scope='module')

# TODO add a test CS to tests

def test_cs():
    if vc.hostname.startswith('eurc'):
        startInput = {
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
    elif vc.hostname.startswith('psyche'):
        startInput = {
            'scriptName': 'git_hash', 
            'scriptPath': 'testbed/production/ing-cs/git_hash/git_hash.py', 
            'scriptHash': '01d0ce8cc77ec6bbe5642d71c35d35f27137ca0eef53e83d20c6fa8532e8c6a4', 
            'inputs': {
                'username': 'hongmank', 
                'inputs': {
                    'folder_path': '/home/lattimor/Sandbox/ing-cs/git_hash'
                }
            }, 
            'outputs': {
                'custom_script_status': 'PENDING', 
                'inputs': {
                    'folder_path': '/home/lattimor/Sandbox/ing-cs/git_hash'
                },
                'outputs': {
                    'hash': ''
                }
            }
        }
        
    res = vc.run_custom_script(server=vc.server_1, startInput=startInput)
    assert res.status_code == 200
    print(res.text)
    res_dict = res.json()
    scriptRunId = res_dict['scriptRunId']

    statusInput = {
        'scriptRunId': scriptRunId
    }
    res = vc.get_custom_script_status(server=vc.server_1, statusInput=statusInput)
    assert res.status_code == 200
    print(res.text)

    time.sleep(2)

    res = vc.get_custom_script_status(server=vc.server_1, statusInput=statusInput)
    assert res.status_code == 200
    print(res.text)

    res = vc.download_custom_script_files(server=vc.server_1, scriptRunId=scriptRunId)
    assert res.status_code == 200
    zname = f'cs-files.tar.gz'
    zfile = open(zname, 'wb')
    zfile.write(res.content)
    zfile.close()

    # Run it again

    res = vc.run_custom_script(server=vc.server_1, startInput=startInput)
    assert res.status_code == 200
    print(res.text)
    res_dict = res.json()
    scriptRunId = res_dict['scriptRunId']
    
    # halt it
    haltInput = {
        'scriptRunId': scriptRunId
    }
    res = vc.halt_custom_script(server=vc.server_1, haltInput=haltInput)
    assert res.status_code == 204

    # script process has been killed. Cannot get status of CS.
    statusInput = {
        'scriptRunId': scriptRunId
    }
    res = vc.get_custom_script_status(server=vc.server_1, statusInput=statusInput)
    assert res.status_code == 400
    print(res.text)
    res_dict = res.json()
    
