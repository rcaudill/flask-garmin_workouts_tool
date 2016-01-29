#!/usr/bin/python

import datetime
import json
import re

import requests


#THIS NEEDS LOTS OF ERROR CHECKING!!!!
class GarminService:

    #Authenticate using stripped down version of https://github.com/cpfair/tapiriik/blob/master/tapiriik/services/GarminConnect/garminconnect.py
    def __init__(self, email, password):
        self.email = email
        self.session = requests.Session()

        data = {
        "username": email,
        "password": password,
        "_eventId": "submit",
        "embed": "true",
        }
        params = {
        "service": "https://connect.garmin.com/post-auth/login",
        "clientId": "GarminConnect",
        "consumeServiceTicket": "false"
        }

        preResp = self.session.get("https://sso.garmin.com/sso/login", params=params)
        data["lt"] = re.search("name=\"lt\"\s+value=\"([^\"]+)\"", preResp.text).groups(1)[0]
        ssoResp = self.session.post("https://sso.garmin.com/sso/login", params=params, data=data, allow_redirects=False)
        ticket_match = re.search("ticket=([^']+)'", ssoResp.text)
        ticket = ticket_match.groups(1)[0]
        gcRedeemResp = self.session.get("https://connect.garmin.com/post-auth/login", params={"ticket": ticket}, allow_redirects=False)
        expected_redirect_count = 6
        current_redirect_count = 1
        while True:
            gcRedeemResp = self.session.get(gcRedeemResp.headers["location"], allow_redirects=False)
            if current_redirect_count >= expected_redirect_count and gcRedeemResp.status_code != 200:
                raise APIException("GC redeem %d/%d error %s %s" % (current_redirect_count, expected_redirect_count, gcRedeemResp.status_code, gcRedeemResp.text))
            if gcRedeemResp.status_code == 200 or gcRedeemResp.status_code == 404:
                break
            current_redirect_count += 1
            if current_redirect_count > expected_redirect_count:
                break

    def get_email(self):
        return self.email

    def get_workouts(self):
        return self.session.get("https://connect.garmin.com/proxy/workout-service-1.0/json/workoutlist").text

    def get_workout_string(self, workoutId):
        return self.session.get("https://connect.garmin.com/proxy/workout-service-1.0/json/workout/" + workoutId).text

    def create_workout(self, json_str):
        json_str = json.dumps(json.loads(json_str), separators=(',', ':'))
        payload = {'data':json_str}
        return self.session.post("https://connect.garmin.com/proxy/workout-service-1.0/json/createWorkout",
                                 headers={"content-type": "application/x-www-form-urlencoded"}, params=payload).text

    def delete_workout(self, workoutId):
        return self.session.delete("https://connect.garmin.com/proxy/workout-service-1.0/json/deleteWorkout/" + workoutId).text

    def get_schedule(self, startCalendarDate="2016-01-01", endCalendarDate="", timeZoneOffset="0", includeTP="",
                     personalizerContext=""):
        payload = {'startCalendarDate': startCalendarDate,
                   'endCalendarDate': endCalendarDate,
                   'timeZoneOffset': timeZoneOffset,
                   'includeTP': includeTP,
                   # 'personalizerContext':personalizerContext
                   }
        return self.session.get("https://connect.garmin.com/proxy/workout-service-1.0/json/exportSchedule",
                                params=payload).text

    def set_workoutschedule(self, workoutId, calendarDate):
        payload = {'workoutId': workoutId,
                   'calendarDate': calendarDate
                   }
        return self.session.put("https://connect.garmin.com/proxy/workout-service-1.0/json/workoutschedule",
                                params=payload).text

    def delete_scheduled_workout(self, scheduleId):
        payload = {'workoutScheduleId': scheduleId}
        return self.session.delete("https://connect.garmin.com/proxy/workout-service-1.0/json/workoutschedule",
                                   params=payload).text

    def schedule_tctp_ec(self, calendarDate):
        result = ""
        payload = {'workoutId': 45443119, 'calendarDate': calendarDate}
        result += self.session.put("https://connect.garmin.com/proxy/workout-service-1.0/json/workoutschedule",
                                   params=payload).text
        result += "\n"

        payload = {'workoutId': 45443120, 'calendarDate': str(
            datetime.datetime.strptime(calendarDate, "%Y-%m-%d").date() + datetime.timedelta(days=1))}
        result += self.session.put("https://connect.garmin.com/proxy/workout-service-1.0/json/workoutschedule",
                                   params=payload).text
        result += "\n"

        payload = {'workoutId': 45443122, 'calendarDate': str(
                datetime.datetime.strptime(calendarDate, "%Y-%m-%d").date() + datetime.timedelta(days=3))}
        result += self.session.put("https://connect.garmin.com/proxy/workout-service-1.0/json/workoutschedule",
                                   params=payload).text

        result += "\n"

        payload = {'workoutId': 45443123, 'calendarDate': str(
                datetime.datetime.strptime(calendarDate, "%Y-%m-%d").date() + datetime.timedelta(days=5))}
        result += self.session.put("https://connect.garmin.com/proxy/workout-service-1.0/json/workoutschedule",
                                   params=payload).text

        result += "\n"

        payload = {'workoutId': 45443124, 'calendarDate': str(
                datetime.datetime.strptime(calendarDate, "%Y-%m-%d").date() + datetime.timedelta(days=6))}
        result += self.session.put("https://connect.garmin.com/proxy/workout-service-1.0/json/workoutschedule",
                                   params=payload).text

        return result

# gc = GarminService("rcaudill@gmail.com", "")
# gc.schedule_3_day(workoutId="41283024", calendarDate="2016-01-01")

# print gc.session.get("https://connect.garmin.com/proxy/workout-service-1.0/json/target_types").text
# print gc.session.get("https://connect.garmin.com/proxy/user-service-1.0/json/user_preferences").text
# payload = {'key': "test_key", 'value': "test_value"}
# print gc.session.post("https://connect.garmin.com/proxy/user-service-1.0/json/user_preference",params=payload).text
# print gc.session.get("https://connect.garmin.com/proxy/user-service-1.0/json/account").text
# print gc.get_workouts()
#print gc.get_schedule(startCalendarDate="2016-01-01", endCalendarDate="2016-01-25", includeTP="true")
