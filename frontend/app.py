from flask import Flask, redirect, url_for, request, render_template
import requests
import submit_transaction
import register_task
import registration
import get_upload_model_list
import os
import time
from threading import Thread
import threading
from array import *
import base64
import cbor
app = Flask(__name__)


@app.route('/')
def render():
    return render_template("index.html")


@app.route('/success/')
def success():
    return 'welcome'


@app.route('/register_task', methods=['POST'])
def register_task1():
    private_key = request.form['private_key']
    hardware = request.form['hardware']
    dataset = request.form['dataset']
    task_id = request.form['task_id']
    register_task.submit_transaction(private_key, hardware, dataset, task_id)
    return render_template("success.html")


@app.route('/register_task/', methods=['GET'])
def register_task2():
    return render_template("register_task.html")

# @app.route('/get-upload-model-list', methods=['POST'])
# def registration1():
#     private_key = request.form['private_key']
#     authentication_type = request.form['authentication_type']
#     registration.submit_transaction(private_key, authentication_type)
#     return render_template("success.html")


@app.route('/get_model/', methods=['GET'])
def get_model_0():
    url = "http://172.18.0.5:8008/state"
    data = []
    try:
        state = requests.get(url)
        if state.status_code == 404:
            print("oke")
        else:
            for i in state.json()['data']:
                if i['address'][0:6] == 'fb0a7f':
                    data_ = cbor.loads(base64.b64decode(i['data'])).split(';')
                    for j in data_:
                        temp1 = j.strip("{")
                        temp2 = temp1.strip("}")
                        temp3 = temp2.split(",")
                        task_ID = temp3[1][9:]
                        model = temp3[0][7:]
                        temp4 = {
                            "model": model,
                            "task ID": task_ID
                        }
                        data.append(temp4)
        print(data)
        return render_template("result.html", data=data)
    except ValueError as e:
        raise Exception('Invalid json: {}'.format(e)) from None
        return("err")


@app.route('/get_model', methods=['POST'])
def get_model_1():
    ID = request.form['task_id']
    print(ID)
    url = "http://172.18.0.5:8008/state"
    data = []
    try:
        state = requests.get(url)
        if state.status_code == 404:
            print("oke")
        else:
            for i in state.json()['data']:
                if i['address'][0:6] == 'fb0a7f':
                    data_ = cbor.loads(base64.b64decode(i['data'])).split(';')
                    for j in data_:
                        temp1 = j.strip("{")
                        temp2 = temp1.strip("}")
                        temp3 = temp2.split(",")
                        task_ID = temp3[1][9:]
                        model = temp3[0][7:]
                        temp4 = {
                            "model": model,
                            "task ID": task_ID
                        }
                        if task_ID == ID:
                            data.append(temp4)
        return render_template("result.html", data=data)
    except ValueError as e:
        raise Exception('Invalid json: {}'.format(e)) from None
        return("err")


@app.route('/registration', methods=['POST'])
def registration1():
    private_key = request.form['private_key']
    authentication_type = request.form['authentication_type']
    registration.submit_transaction(private_key, authentication_type)
    return render_template("success.html")


@app.route('/registration/', methods=['GET'])
def registration0():
    return render_template("registration.html")


@app.route('/login', methods=['POST', 'GET'])
def login():
    # uploaded_file = request.files['file']
    # if uploaded_file.filename != '':
    #     uploaded_file.save(uploaded_file.filename)
    # return redirect(url_for('index'))
    print(request.method)
    data = request

    uploaded_file = data.files["model"]
    private_key = data.form["private_key"]
    task_id = data.form["task_id"]
    if uploaded_file.filename != '':
        uploaded_file.save(uploaded_file.filename)
    files = {'model': open(uploaded_file.filename, 'rb')}
    r = requests.post(
        "http://localhost:3000/upload-model", files=files)
    os.remove(uploaded_file.filename)
    hash = r.content.decode("utf-8")
    submit_transaction.submit_txn(private_key, hash, task_id)


if __name__ == '__main__':
    app.run(debug=True)
