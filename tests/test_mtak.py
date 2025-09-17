import venue_client as vc


def test_start_shutdown():

    res = vc.start_mtak(server=vc.server_1, sessionIds=[vc.session_id_a])
    assert res.status_code == 200
    print(res.json())

    res = vc.send_fsw_cmd(server=vc.server_1, sessionId=vc.session_id_a, commandString=vc.CMD_NO_OP, 
        validate=False, stringSelection='DEFAULT', timeout=10)
    assert res.status_code == 200
    print(res.json())

    res = vc.shutdown_mtak(server=vc.server_1)
    assert res.status_code == 204
    print(f'res.text: {res.text}')

def test_wrong_session_id():

    res = vc.start_mtak(server=vc.server_1, sessionIds=[0])
    assert res.status_code == 400
    print(f'res.text: {res.text}')

def test_short_timeout():

    res = vc.start_mtak(server=vc.server_1, sessionIds=[vc.session_id_a], timeout=10)
    assert res.status_code == 400
    print(f'res.text: {res.text}')