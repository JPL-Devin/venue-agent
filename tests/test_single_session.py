import pytest
from datetime import datetime, timezone, timedelta
import time
import sys
import venue_client as vc

@pytest.fixture(scope='module')
def mtak_proc():
    assert vc.session_id_a > 0
    res = vc.start_mtak(server=vc.server_1, sessionIds=[vc.session_id_a])
    print(res.status_code, res.json())
    yield res

    res = vc.shutdown_mtak(server=vc.server_1)
    print(res.status_code)

@pytest.fixture(scope='module')
def tsr(mtak_proc):
    if vc.hostname.startswith('eurc'):
        command_strings = [
            'DDM_SET_EHA_PROD_RATE,5,5,5,5,60,60,60,60',
            'DDM_SET_DWN_TZ_CONFIG, 2000000',
            'DDM_UPDATE_NUM_TSR,0,INVALID,0,ALWAYS,1 seconds,0,RT,MEDIUM,0,AVS',
            'DDM_UPDATE_NUM_TSR,0,INVALID,0,ALWAYS,1 seconds,0,RT,MEDIUM,0,CB',
            'DDM_UPDATE_NUM_TSR,0,INVALID,0,ALWAYS,1 seconds,0,RT,CRITICAL,0,CMD',
            'DDM_UPDATE_NUM_TSR,0,INVALID,0,ALWAYS,1 seconds,0,RT,MEDIUM,0,DDM'
        ]

        for command_string in command_strings:
            print(f'command_string: {command_string}')
            res = vc.send_fsw_cmd(server=vc.server_1, sessionId=vc.session_id_a, commandString=command_string, 
                validate=False, stringSelection='DEFAULT', timeout=10)
            print(res.json())

            # throttle at 1Hz
            time.sleep(1)
    elif vc.hostname.startswith('psyche'):
        # increase uplink speed (Psyche WSTS)
        command_string = 'cmd putp avsim.RceA.mtif.mtifUpl.uplinkRateBitPerSec value 64000'
        print(f'send sse command: {command_string}')

        res = vc.send_sse_cmd(server=vc.server_1, sessionId=vc.session_id_a, commandString=command_string, 
            timeout=10)
        print(res.json())


        # uplink generic EHA selection criteria file
        print('send file')
        res = vc.send_file(server=vc.server_1, 
            sessionId=vc.session_id_a, 
            sourceFilePath='/teamtools/sct/parameter_files/selection_criteria/EHA_SELCRIT_SYS_NOMINAL_C5.4.0.2_TB.230331.r1.bin',
            targetFilePath='/eng/sys_nominal1.bin',
            overwrite=True,
            fileType=0,
            stringSelection='DEFAULT',
            timeout=60)
        print(res.json())


        elapsed_sec = 0
        utc_now = datetime.now(tz=timezone.utc)
        query_start_time = datetime.strftime(utc_now, '%Y-%jT%H:%M:%S')
        while elapsed_sec < 120:
            utc_now = datetime.now(tz=timezone.utc)
            query_end_time = datetime.strftime(utc_now, '%Y-%jT%H:%M:%S')

            print('query realtime evr')
            res = vc.query_rt_evr(server=vc.server_1, sessionId=vc.session_id_a, evrName='UPL_MGR_EVR_FILE_CREATED', 
                startTime=query_start_time, endTime=query_end_time)
            status_code = res.status_code
            print(f'status_code: {status_code}')

            if status_code == 200:
                if len(res.json()) > 0:
                    print('UPL_MGR_EVR_FILE_CREATED was received')
                    break
            else:
                print('WARNING: EVR query failed')
            
            time.sleep(10)
        
        print('Load the TSR file')
        res = vc.send_fsw_cmd(
            server=vc.server_1, 
            sessionId=vc.session_id_a, 
            commandString='TLM_EHA_LOAD_SELCRIT_FILE,/eng/sys_nominal1.bin', 
            validate=True, 
            stringSelection='DEFAULT', 
            timeout=10
        )

        print(res.status_code)
        print(res.json())

        time0 = time.time()
        query_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
        evrs = []
        for i in range(10):
            time.sleep(10)
            query_end_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
            res = vc.query_rt_evr(server=vc.server_1, sessionId=vc.session_id_a, evrName='EHA_SVC_EVR_SELCRIT_FILE_APPLIED', 
                startTime=query_start_time, endTime=query_end_time)
            assert res.status_code == 200

            evrs = res.json()
            elapsed_sec = time.time() - time0
            print(f'waiting for EHA_SVC_EVR_SELCRIT_FILE_APPLIED elapsed sec: {elapsed_sec:.1f}  evrs: {evrs}')
            
            if len(evrs) > 0:
                break


def test_rt_evr(mtak_proc):
    query_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
    res = vc.send_fsw_cmd(server=vc.server_1, sessionId=vc.session_id_a, commandString=vc.CMD_NO_OP, 
        validate=False, stringSelection='DEFAULT', timeout=10)
    assert res.status_code == 200
    print(res.json())

    time0 = time.time()
    evrs = []
    for i in range(10):
        time.sleep(3)
        query_end_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
        res = vc.query_rt_evr(server=vc.server_1, sessionId=vc.session_id_a, evrName=vc.CMD_COMP_EVR, 
            startTime=query_start_time, endTime=query_end_time)
        assert res.status_code == 200

        evrs = sorted(res.json(), key=lambda evr: evr['ert'])
        elapsed_sec = time.time() - time0
        print(f'elapsed sec: {elapsed_sec:.1f} evrs: {evrs}')
        
        if len(evrs) > 0:
            break
    
    assert len(evrs) > 0


def test_chill_evr(mtak_proc):
    query_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
    res = vc.send_fsw_cmd(server=vc.server_1, sessionId=vc.session_id_a, commandString=vc.CMD_NO_OP, 
        validate=False, stringSelection='DEFAULT', timeout=10)
    assert res.status_code == 200
    print(res.json())

    time0 = time.time()
    evrs = []
    for i in range(10):
        time.sleep(3)
        query_end_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
        res = vc.query_chill_evr(server=vc.server_1, sessionId=vc.session_id_a, evrName=vc.CMD_COMP_EVR, 
            startTime=query_start_time, endTime=query_end_time)
        assert res.status_code == 200

        evrs = sorted(res.json(), key=lambda evr: evr['ert'])
        elapsed_sec = time.time() - time0
        print(f'elapsed sec: {elapsed_sec:.1f} evrs: {evrs}')
        
        if len(evrs) > 0:
            break
    
    assert len(evrs) > 0

def test_rt_eha(tsr):

    ehas = []

    cmd_count0 = 0
    query_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
    time0 = time.time()
    # sleep to give time to update command counter for any previous commands from other tests
    time.sleep(15)
    for i in range(15):
        query_end_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
        print(f'before i: {i} query_rt_eha channelId: {vc.CMD_COUNTER_EHA} startTime: {query_start_time} endTime: {query_end_time}')
        res = vc.query_rt_eha(server=vc.server_1, sessionId=vc.session_id_a, channelId=vc.CMD_COUNTER_EHA, 
            startTime=query_start_time, endTime=query_end_time)

        assert res.status_code == 200
        ehas = sorted(res.json(), key=lambda eha: eha['ert'])
        print(f'ehas: {ehas}')

        if len(ehas) > 0:
            cmd_count0 = int(ehas[-1]['dn'])
            break
        time.sleep(10)

    assert cmd_count0 > 0

    res = vc.send_fsw_cmd(server=vc.server_1, sessionId=vc.session_id_a, commandString=vc.CMD_NO_OP, 
        validate=False, stringSelection='DEFAULT', timeout=10)
    assert res.status_code == 200
    print(f'send_fsw_cmd: {res.json()}')

    query_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
    time0 = time.time()
    eha_diff = 0
    for i in range(15):
        time.sleep(10)
        query_end_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
        print(f'after i: {i} query_rt_eha channelId: {vc.CMD_COUNTER_EHA} startTime: {query_start_time} endTime: {query_end_time}')
        res = vc.query_rt_eha(server=vc.server_1, sessionId=vc.session_id_a, channelId=vc.CMD_COUNTER_EHA, 
            startTime=query_start_time, endTime=query_end_time)
        assert res.status_code == 200

        ehas = sorted(res.json(), key=lambda eha: eha['ert'])
        elapsed_sec = time.time() - time0
        print(f'rt elapsed sec: {elapsed_sec:.1f} ehas: {ehas}')
        
        if len(ehas) > 0:
            cmd_count = int(ehas[-1]['dn'])

            eha_diff = cmd_count - cmd_count0

            if eha_diff >= 1:
                break
    assert eha_diff == 1

def test_chill_eha(tsr):

    ehas = []

    cmd_count0 = 0
    query_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
    time0 = time.time()

    # sleep to give time to update command counter for any previous commands from other tests
    time.sleep(15)
    for i in range(15):
        query_end_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
        print(f'query_chill_eha channelId: {vc.CMD_COUNTER_EHA} startTime: {query_start_time} endTime: {query_end_time}')
        res = vc.query_chill_eha(server=vc.server_1, sessionId=vc.session_id_a, channelId=vc.CMD_COUNTER_EHA, 
            startTime=query_start_time, endTime=query_end_time)

        assert res.status_code == 200
        ehas = sorted(res.json(), key=lambda eha: eha['ert'])
        print(f'before i: {i} ehas: {ehas}')

        if len(ehas) > 0:
            cmd_count0 = int(ehas[-1]['dn'])
            break
        time.sleep(10)

    assert cmd_count0 > 0

    res = vc.send_fsw_cmd(server=vc.server_1, sessionId=vc.session_id_a, commandString=vc.CMD_NO_OP, 
        validate=False, stringSelection='DEFAULT', timeout=10)
    assert res.status_code == 200
    print(f'send_fsw_cmd: {res.json()}')

    query_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
    time0 = time.time()
    eha_diff = 0
    for i in range(15):
        time.sleep(10)
        query_end_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
        print(f'query_chill_eha channelId: {vc.CMD_COUNTER_EHA} startTime: {query_start_time} endTime: {query_end_time}')
        res = vc.query_chill_eha(server=vc.server_1, sessionId=vc.session_id_a, channelId=vc.CMD_COUNTER_EHA, 
            startTime=query_start_time, endTime=query_end_time)
        assert res.status_code == 200

        ehas = sorted(res.json(), key=lambda eha: eha['ert'])
        elapsed_sec = time.time() - time0
        print(f'after i: {i} rt elapsed sec: {elapsed_sec:.1f} ehas: {ehas}')
        
        if len(ehas) > 0:
            cmd_count = int(ehas[-1]['dn'])

            eha_diff = cmd_count - cmd_count0
            if eha_diff >= 1:
                break
    assert eha_diff == 1

def test_dp(mtak_proc):

    dps = []

    res = vc.send_fsw_cmd(server=vc.server_1, sessionId=vc.session_id_a, commandString=vc.CMD_DOWN_DP, 
        validate=False, stringSelection='DEFAULT', timeout=10)
    assert res.status_code == 200
    print(f'send_fsw_cmd: {res.json()}')

    query_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
    
    time0 = time.time()
    evrs = []
    for i in range(10):
        time.sleep(3)
        query_end_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
        res = vc.query_rt_evr(server=vc.server_1, sessionId=vc.session_id_a, evrName=vc.CMD_COMP_EVR, 
            startTime=query_start_time, endTime=query_end_time)
        assert res.status_code == 200

        evrs = sorted(res.json(), key=lambda evr: evr['ert'])
        elapsed_sec = time.time() - time0
        print(f'elapsed sec: {elapsed_sec:.1f} evrs: {evrs}')
        
        if len(evrs) > 0:
            break
    
    assert len(evrs) > 0


    query_start_time = datetime.strftime(datetime.now(tz=timezone.utc) - timedelta(seconds=7200), '%Y-%jT%H:%M:%S')

    time0 = time.time()
    for i in range(10):
        time.sleep(5)
        query_end_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
        print(f'query_dp startTime: {query_start_time} endTime: {query_end_time}')
        res = vc.query_dp(server=vc.server_1, sessionId=vc.session_id_a,  
            startTime=query_start_time, endTime=query_end_time)
        print(res.text)
        assert res.status_code == 200

        dps = sorted(res.json(), key=lambda dp: dp['ert'])
        elapsed_sec = time.time() - time0
        print(f'dp elapsed sec: {elapsed_sec:.1f} dps: {dps}')
        
        if len(dps) > 0:
            break

    assert len(dps) > 0

    query_end_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
    print(f'query_dp startTime: {query_start_time} endTime: {query_end_time}')
    res = vc.query_dp(server=vc.server_1, sessionId=vc.session_id_a, dpStatus='COMPLETE', 
        startTime=query_start_time, endTime=query_end_time)
    print(res.text)
    assert res.status_code == 200

    dps = sorted(res.json(), key=lambda dp: dp['ert'])
    for dp in dps:
        assert 'COMPLETE' in dp['dpStatus']
    
    query_end_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
    print(f'query_dp startTime: {query_start_time} endTime: {query_end_time}')
    res = vc.query_dp(server=vc.server_1, sessionId=vc.session_id_a, dpStatus='PARTIAL', 
        startTime=query_start_time, endTime=query_end_time)
    print(res.text)
    assert res.status_code == 200

    dps = sorted(res.json(), key=lambda dp: dp['ert'])
    for dp in dps:
        assert 'COMPLETE' not in dp['dpStatus']

    query_end_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
    print(f'query_dp apid startTime: {query_start_time} endTime: {query_end_time}')
    apIds = [vc.DP_AP_ID]
    res = vc.query_dp(server=vc.server_1, sessionId=vc.session_id_a, apIds=apIds,
        startTime=query_start_time, endTime=query_end_time)
    print(res.text)
    assert res.status_code == 200

    dps = sorted(res.json(), key=lambda dp: dp['ert'])
    for dp in dps:
        dp['apId'] in apIds

def test_scmf(mtak_proc):
    if vc.hostname.startswith('psyche'):
        print('send SCMF file')
        res = vc.send_scmf_file(
            server=vc.server_1,
            sessionId=vc.session_id_a, 
            filePath='/teamtools/atlo/production/uplink-files/scmfs/ctt22/10_cmd_no_ops_a.scmf'
        )
        print(res.text)
        assert res.status_code == 200
        
        query_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
        evrs = []
        time0 = time.time()
        for i in range(10):
            time.sleep(3)
            query_end_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
            res = vc.query_rt_evr(server=vc.server_1, sessionId=vc.session_id_a, evrName=vc.CMD_COMP_EVR, 
                startTime=query_start_time, endTime=query_end_time)
            assert res.status_code == 200

            evrs = sorted(res.json(), key=lambda evr: evr['ert'])
            elapsed_sec = time.time() - time0
            print(f'elapsed sec: {elapsed_sec:.1f} evrs: {evrs}')
            
            if len(evrs) == 10:
                break
        
        assert len(evrs) == 10

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
    
