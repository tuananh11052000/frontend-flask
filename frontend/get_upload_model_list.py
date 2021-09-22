import requests
import hashlib
import base64
import cbor
import array


def run_func():
    url = "http://172.18.0.5:8008/state"
    data = array("d", [])
    try:
        state = requests.get(url)
        if state.status_code == 404:
            print("oke")
        else:
            for i in state.json()['data']:
                if i['address'][0:6] == 'fb0a7f':
                    print(i['data'])
                    data.append(cbor.loads(base64.b64decode(i['data'])))
        print(data)
        return data
    except ValueError as e:
        raise Exception('Invalid json: {}'.format(e)) from None
        return("err")
