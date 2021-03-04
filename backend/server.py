import os
import time
import base64
import json
from datetime import datetime, timedelta
from flask import *
from flask_cors import CORS


with open('settings.json') as f:
    settings = json.load(f)

app = Flask(__name__, )
CORS(app, resources=r'/*')


@app.route("/test/", methods=['GET'])
def test_page():
    messages = {"statusCode": 200}

    response = make_response(jsonify(messages))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'OPTIONS,HEAD,GET,POST'
    response.headers['Access-Control-Allow-Headers'] = 'x-requested-with'
    return response


@app.route("/reserve/", methods=['POST'])
def reserve():
    result_text = {"statusCode": 200}
    name = request.form.get('name')
    ...
    response = make_response(jsonify(result_text))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'OPTIONS,HEAD,GET,POST'
    response.headers['Access-Control-Allow-Headers'] = 'x-requested-with'
    return response


@app.route("/list/", methods=['GET'])
def in_progress():
    def get_data():
        with open('in_progress.json') as f:
            appointments = json.load(f)
        return appointments

    messages = {'statusCode': 200}

    try:
        messages['inProgress'] = get_data()
    except Exception as e:
        print(e)
        messages['statusCode'] = 500

    response = make_response(jsonify(messages))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'OPTIONS,HEAD,GET,POST'
    response.headers['Access-Control-Allow-Headers'] = 'x-requested-with'
    return response


@app.route("/available/", methods=['GET'])
def available():
    def get_data(max_days=10):
        with open('available.json') as f:
            schedule = json.load(f)

        dates = sorted(list(schedule.keys()), key=lambda z: datetime.strptime(z, settings['time_format']))
        if not dates or datetime.strptime(dates[0], settings['time_format']) < datetime.now() or \
                datetime.strptime(dates[-1], settings['time_format']) < datetime.now() + timedelta(days=max_days):
            print('update schedule')
            schedule_new = {}
            for day in range(max_days):
                d = (datetime.now() + timedelta(days=day)).strftime(settings['time_format'])
                schedule_new[d] = {}
                for hour in settings['work_start']:
                    h = settings['work_hours'].format(hour)
                    if d in dates and h in list(schedule[d].keys()):
                        schedule_new[d][h] = schedule[d][h]
                    else:
                        schedule_new[d][h] = 1
            with open('available.json', 'w') as f:
                json.dump(schedule_new, f)
            schedule = schedule_new

        date = sorted(list(schedule.keys()), key=lambda z: datetime.strptime(z, settings['time_format']))
        hour = sorted(list(schedule[list(schedule.keys())[0]].keys()), key=lambda z: int(z[:2]))

        return schedule, date, hour

    messages = {"statusCode": 200}
    try:
        data = get_data()
        messages['date'] = data[1]
        messages['hour'] = data[2]
        messages['schedule'] = data[0]
        messages['teachers'] = settings['teachers']
    except Exception as e:
        print(e)
        messages['statusCode'] = 500

    response = make_response(jsonify(messages))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'OPTIONS,HEAD,GET,POST'
    response.headers['Access-Control-Allow-Headers'] = 'x-requested-with'
    return response


if __name__ == '__main__':
    app.run(port=2333)
