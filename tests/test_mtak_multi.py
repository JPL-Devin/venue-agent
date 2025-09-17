import venue_client as vc
import time
from datetime import datetime, timezone

def test_start_shutdown():

    assert vc.session_id_a > 0
    assert vc.session_id_b > 0

    res = vc.start_mtak(server=vc.server_1, sessionIds=[vc.session_id_a, vc.session_id_b])
    assert res.status_code == 200
    print(res.json())

    query_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')

    # send a command to session A
    res = vc.send_fsw_cmd(server=vc.server_1, sessionId=vc.session_id_a, commandString=vc.CMD_NO_OP, 
        validate=False, stringSelection='DEFAULT', timeout=10)
    assert res.status_code == 200
    print(res.json())

    # send a command to session B
    res = vc.send_fsw_cmd(server=vc.server_1, sessionId=vc.session_id_b, commandString=vc.CMD_NO_OP, 
        validate=False, stringSelection='DEFAULT', timeout=10)
    assert res.status_code == 200
    print(res.json())

    time0 = time.time()
    evrs_a = []
    evrs_b = []
    for i in range(10):
        time.sleep(3)
        query_end_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')

        res = vc.query_rt_evr(server=vc.server_1, sessionId=vc.session_id_a, evrName=vc.CMD_COMP_EVR, 
            startTime=query_start_time, endTime=query_end_time)
        assert res.status_code == 200
        evrs_a = sorted(res.json(), key=lambda evr: evr['ert'])

        elapsed_sec = time.time() - time0
        print(f'elapsed sec: {elapsed_sec:.1f} evrs_a: {evrs_a}')

        res = vc.query_rt_evr(server=vc.server_1, sessionId=vc.session_id_b, evrName=vc.CMD_COMP_EVR, 
            startTime=query_start_time, endTime=query_end_time)
        assert res.status_code == 200
        evrs_b = sorted(res.json(), key=lambda evr: evr['ert'])

        elapsed_sec = time.time() - time0
        print(f'elapsed sec: {elapsed_sec:.1f} evrs_b: {evrs_b}')
        
        if len(evrs_a) > 0 and len(evrs_b) > 0:
            break
    
    assert len(evrs_a) == 1
    assert len(evrs_b) == 1

    res = vc.shutdown_mtak(server=vc.server_1)
    assert res.status_code == 204
    print(f'res.text: {res.text}')

