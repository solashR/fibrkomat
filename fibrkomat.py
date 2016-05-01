#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import os.path
import datetime
import argparse

import requests
import BeautifulSoup


class TimeNet(object):

    _SITE = 'http://checkin.timewatch.co.il/'

    def __init__(self, company, user, password):
        self._company = company
        self._user = user
        self._password = password
        self._employee_id = None
        self._session = requests.session()

    def login(self):
        url = os.path.join(self._SITE, 'punch/punch2.php')
        credentials = {'comp': self._company, 'name': self._user,
                       'pw': self._password}
        res = self._session.post(url, credentials)
        if 'The login details you entered are incorrect!' in res.text:
            raise AssertionError('incorrect credentials')

        self._employee_id = int(BeautifulSoup.BeautifulSoup(res.text).find(
            'input', id='ixemplee').get('value'))

    def expected_times(self, year, month):
        url = os.path.join(self._SITE, 'punch/po_presence.php')
        data = {'tl': self._employee_id, 'ee': self._employee_id,
                'e': self._company, 'm': month, 'y': year}
        res = self._session.get(url, params=data)

        html = BeautifulSoup.BeautifulSoup(res.text)
        days = html.findAll('td', attrs={'class': 'cb_date'})[1:]

        for day in days:
            hours = day.parent.find('td', attrs={'class': 'cb_stdHours'})
            hours_min = hours.text.replace('&nbsp;', '')
            if not hours_min:
                # not a working day
                continue

            hours, minutes = hours_min.split(':')
            work_time = int(hours) * 3600 + int(minutes) * 60

            date, _ = day.find('font').string.split(' ')
            date_obj = datetime.datetime.strptime(date, '%d-%m-%Y').date()
            yield date_obj, work_time

    def set_day_time(self, date, start, end):
        date_str = '{y}-{m}-{d}'.format(y=date.year, m=date.month, d=date.day)
        data = {'e': self._employee_id, 'tl': self._employee_id,
                'c': self._company, 'd': date_str,
                'task0': 0, 'taskdescr0': '', 'what0': 1,
                'emm0': _sec_min_part(start), 'ehh0': _sec_hours_part(start),
                'xmm0': _sec_min_part(end), 'xhh0': _sec_hours_part(end)}

        url = os.path.join(self._SITE, 'punch/editwh3.php')
        res = self._session.post(url, data)
        if 'TimeWatch - Reject' in res.text:
            raise AssertionError('set date={} time failed'.format(data))


def _sec_hours_part(sec):
    return sec // 3600


def _sec_min_part(sec):
    return (sec % 3600) // 60


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('company', type=int)
    parser.add_argument('user_number', type=int)
    parser.add_argument('password')
    parser.add_argument('-m', '--month', type=int)
    parser.add_argument('-s', '--start-hour', type=int, default=34200,
                        help='seconds since 00:00')
    return parser.parse_args()


def main():
    args = _parse_args()
    if args.month is None:
        year_month = datetime.date.today()
        year, month = year_month.year, year_month.month
    else:
        year_month = datetime.date.today()
        year, month = year_month.year, args.month

    t = TimeNet(args.company, args.user_number, args.password)
    t.login()
    for date, work_time in t.expected_times(year, month):
        t.set_day_time(date, args.start_hour, args.start_hour + work_time)


if __name__ == '__main__':
    main()
