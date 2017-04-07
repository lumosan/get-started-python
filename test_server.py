from hello import app
import json

testapp = app.test_client()


def test_index():
    response = testapp.get('/')
    assert response.status_code == 200
    assert b'Bienvenido seas.' in response.data


def test_ajax():
    response = testapp.post('/api/visitors',
                            data=json.dumps({'name': "Jose"}),
                            content_type='application/json'
                            )
    assert response.status_code == 200
    assert b'Jose' in response.data
