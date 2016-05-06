#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import random
import os.path
import datetime
import argparse

import requests
import BeautifulSoup


class TimeNet(object):

    _SITE = 'http://checkin.timewatch.co.il/'

    _WORK_PREFIX = ('--------------- NEW CHANGE - ROW 441 - SHOW ALL PUNCH '
                    '---------------------&nbsp;')
    _WORK_SUFFIX = '--------------- END NEW CHANGE ---------------------'

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

    def expected_times(self, year, month, skip_filled_days):
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

            date, _ = day.find('font').string.split(' ')
            date_obj = datetime.datetime.strptime(date, '%d-%m-%Y').date()

            if skip_filled_days and self._should_skip_day(day, date_obj):
                continue

            hours, minutes = hours_min.split(':')
            work_time = int(hours) * 3600 + int(minutes) * 60

            yield date_obj, work_time

    def set_day(self, date, start, end, comment=''):
        start_minutes = _sec_min_part(start) if start else ''
        start_hours = _sec_hours_part(start) if start else ''
        end_minutes = _sec_min_part(end) if end else ''
        end_hours = _sec_hours_part(end) if end else ''

        date_str = '{y}-{m}-{d}'.format(y=date.year, m=date.month, d=date.day)
        data = {'e': self._employee_id, 'tl': self._employee_id,
                'c': self._company, 'd': date_str,
                'task0': 0, 'taskdescr0': '', 'what0': 1,
                'emm0': start_minutes, 'ehh0': start_hours,
                'xmm0': end_minutes, 'xhh0': end_hours,
                'remark': comment}

        url = os.path.join(self._SITE, 'punch/editwh3.php')
        res = self._session.post(url, data)
        if 'TimeWatch - Reject' in res.text:
            raise AssertionError('set date={} time failed'.format(data))

    def _should_skip_day(self, day, timestamp):
        if self._was_time_reported(day):
            print 'skipped {} as already filled'.format(timestamp)
            return True

        comment_filled, comment = self._was_comment_filled(day)
        if comment_filled:
            print 'skipped {} as has comment {}'.format(timestamp, comment)
            return True

        return False

    def _was_time_reported(self, day):
        reported = day.parent.find('td', attrs={'class': 'cb_attHours'}).text
        if not (reported.startswith(self._WORK_PREFIX) and
                reported.endswith(self._WORK_SUFFIX)):
            raise AssertionError('unknown format for reported work time')
        filled_time = reported[
                      len(self._WORK_PREFIX): len(self._WORK_SUFFIX) * -1]
        return filled_time

    @staticmethod
    def _was_comment_filled(day):
        comments = day.parent.find('td', attrs={'class': 'cb_remarks'})
        filled = '&nbsp;' != comments.text
        return filled, comments.text


def _sec_hours_part(sec):
    return sec // 3600


def _sec_min_part(sec):
    return (sec % 3600) // 60


def str_to_date(val):
    try:
        return datetime.datetime.strptime(val, '%d-%m-%Y').date()
    except ValueError:
        pass

    today = datetime.date.today()
    try:
        tmp = datetime.datetime.strptime(val, '%d-%m')
        return datetime.date(today.year, tmp.month, tmp.day)
    except ValueError:
        pass

    tmp = datetime.datetime.strptime(val, '%d')
    return datetime.date(today.year, today.month, tmp.day)


def key_list(val):
    splitted = val.split(',')
    if len(splitted) < 2:
        raise ValueError('should have at least comment & 1 day')
    comment = splitted[0]
    days = [str_to_date(d) for d in splitted[1:]]
    return comment, days


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('company', type=int)
    parser.add_argument('user_number', type=int)
    parser.add_argument('password')
    parser.add_argument('-m', '--month', type=int)
    parser.add_argument('-s', '--start-hour', type=int, default=34200,
                        help='seconds since 00:00')
    parser.add_argument('-r', '--random', type=int, default=0,
                        help='define the fabricate time randome range')
    parser.add_argument('-o', '--overwrite', action='store_true')
    parser.add_argument(
        '-a', '--absence', type=key_list, action='append', default=[],
        help='specify dates where should have comment instead of work time, '
             'format= -a vacation,<date1>,<date2>,... date format can be: '
             '<day> , <day>-<month>, <day>-<month>-<year>')

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
    for date, work_time in t.expected_times(year, month, not args.overwrite):

        start_hour = random.randint(args.start_hour,
                                    args.start_hour + args.random)
        end_hour = random.randint(start_hour + work_time,
                                  start_hour + work_time + args.random)

        t.set_day(date, start_hour, end_hour)

    for comment, days in args.absence:
        for day in days:
            t.set_day(day, start='', end='', comment=comment)


if __name__ == '__main__':
    main()
