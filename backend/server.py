import json
import requests
from datetime import datetime, timedelta

from flask import *
from flask_cors import CORS

with open('data/settings.json') as f_obj:
    settings = json.load(f_obj)


def date_lang(date: str, lang: (str, str) = ('en', 'zh')) -> str:
    languages = {
        'en': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        'zh': ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
    }
    for i in range(len(languages['en'])):
        date = date.replace(languages[lang[0]][i], languages[lang[1]][i])
    return date


def construct_response(msg):
    response = make_response(jsonify(msg))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'OPTIONS,HEAD,GET,POST'
    response.headers['Access-Control-Allow-Headers'] = 'x-requested-with'
    return response


app = Flask(__name__, )
CORS(app, resources=r'/*')


@app.route("/", methods=['GET'])
def index():
    messages = {"statusCode": 200, 'GitHub': 'bugstop', 'copyright': 2021}
    return construct_response(messages)


@app.route("/uid/", methods=['POST'])
def get_uid():
    code = request.json.get('code')
    url = 'https://api.weixin.qq.com/sns/jscode2session?appid={}&secret={}&js_code={}&grant_type=authorization_code'
    rc = requests.get(url.format('wxdefe17992df5e3fb', '7380e978aeec60c86fd23e97e184f250', code))
    print(rc.json())
    messages = {"statusCode": 200, 'wx': rc.json().get('openid')}
    return construct_response(messages)


@app.route("/verify/", methods=['POST'])
def admin_verification():
    messages = {"statusCode": 200 if settings['password'] == request.json.get('password') else 500}
    return construct_response(messages)


@app.route("/reserve/", methods=['POST'])
def reserve():
    def check_data(data):
        with open('data/available.json') as f:
            schedule = json.load(f)

        if not all([data.get('wx'), data.get('name'), data.get('sex'), data.get('id'), data.get('mobile'),
                    data.get('teacher'), data.get('date'), data.get('hour'), data.get('detail')]) \
                or schedule[data['date']][data['hour']] < 1:
            print('check failed')
            raise RuntimeError

        schedule[data['date']][data['hour']] -= 1
        with open('data/available.json', 'w') as f:
            json.dump(schedule, f)

    def write_data(data):
        with open('data/in_progress.json') as f:
            appointments = json.load(f)

        tickets = sorted(list(appointments.keys()), key=lambda z: int(z.split('@')[0]))
        ticket_id = 1 if not tickets else int(tickets[-1].split('@')[0]) + 1
        new_ticket = settings['ticket_format'].format(ticket_id, datetime.now().strftime('%Y%m%d%M%S'))

        data['timestamp'] = datetime.now().strftime(settings['timestamp'])
        appointments[new_ticket] = data

        with open('data/in_progress.json', 'w') as f:
            json.dump(appointments, f)

    post = request.json
    print(post)
    messages = {"statusCode": 200}

    try:
        check_data(post)
        print('write data')
        write_data(post)
    except Exception as e:
        print(e)
        messages['statusCode'] = 500

    return construct_response(messages)


@app.route("/list/", methods=['POST'])
def in_progress():
    def get_data(user_filter: str = None):
        with open('data/in_progress.json') as f:
            appointments = json.load(f)

        tickets = sorted(list(appointments.keys()), key=lambda z: datetime.strptime(
            date_lang(appointments[z]['date'] + appointments[z]['hour'], ('zh', 'en')), settings['sort_helper']))

        if user_filter != settings['password']:
            tickets_filtered = [ticket for ticket in tickets if appointments[ticket].get('wx') == user_filter]
            appointments_filtered = {ticket: appointments[ticket] for ticket in tickets_filtered}
            appointments, tickets = appointments_filtered, tickets_filtered

        return appointments, tickets

    messages = {'statusCode': 200}

    try:
        username = request.json.get('user')
        data = get_data(username)
        messages['tickets'] = data[1]
        messages['inProgress'] = data[0]
    except Exception as e:
        print(e)
        messages['statusCode'] = 500

    return construct_response(messages)


@app.route("/available/", methods=['GET'])
def available():
    def get_data(max_days=10):
        with open('data/available.json') as f:
            schedule = json.load(f)

        dates = [date_lang(key, ('zh', 'en')) for key in list(schedule.keys())]
        dates.sort(key=lambda z: datetime.strptime(z, settings['time_format']))

        if not dates or len(dates) != max_days or \
                datetime.strptime(dates[0], settings['time_format']) < \
                datetime.now() - timedelta(days=1) or \
                datetime.strptime(dates[-1], settings['time_format']) < \
                datetime.now() + timedelta(days=max_days - 2):
            print('update schedule')

            schedule_new = {}
            for day in range(max_days):
                d = date_lang((datetime.now() + timedelta(days=day)).strftime(settings['time_format']))
                schedule_new[d] = {}
                for hour in settings['work_start']:
                    h = settings['work_hours'].format(hour, hour)

                    if d in dates and h in list(schedule[d].keys()):
                        schedule_new[d][h] = schedule[d][h]
                    else:
                        schedule_new[d][h] = settings['max_capacity']

            with open('data/available.json', 'w') as f:
                json.dump(schedule_new, f)
            schedule = schedule_new

        date = sorted(list(schedule.keys()), key=lambda z: datetime.strptime(
            date_lang(z, ('zh', 'en')), settings['time_format']))
        hour = sorted(list(schedule[list(schedule.keys())[0]].keys()), key=lambda z: int(z[:2]))

        date = [d for d in date if any(work_day in d for work_day in settings['work_days'])]
        schedule = {d: schedule[d] for d in date}

        return schedule, date, hour

    messages = {"statusCode": 200}

    try:
        data = get_data(settings['max_days'])
        messages['date'] = data[1]
        messages['hour'] = data[2]
        messages['schedule'] = data[0]
        messages['teachers'] = settings['teachers']
        print(messages['date'])
    except Exception as e:
        print(e)
        messages['statusCode'] = 500

    return construct_response(messages)


if __name__ == '__main__':
    app.run(port=2333)
