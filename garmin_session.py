#!/usr/bin/python

import requests
import json
import urllib
import cgi
import re
import shutil
from shutil import copyfileobj
import sys
import Cookie
import os

def get_session(email=None, password=None):
    session = requests.Session()

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

    preResp = session.get("https://sso.garmin.com/sso/login", params=params)
    data["lt"] = re.search("name=\"lt\"\s+value=\"([^\"]+)\"", preResp.text).groups(1)[0]
    ssoResp = session.post("https://sso.garmin.com/sso/login", params=params, data=data, allow_redirects=False)
    ticket_match = re.search("ticket=([^']+)'", ssoResp.text)
    ticket = ticket_match.groups(1)[0]
    gcRedeemResp = session.get("https://connect.garmin.com/post-auth/login", params={"ticket": ticket}, allow_redirects=False)
    expected_redirect_count = 6
    current_redirect_count = 1
    while True:
        gcRedeemResp = session.get(gcRedeemResp.headers["location"], allow_redirects=False)
        if current_redirect_count >= expected_redirect_count and gcRedeemResp.status_code != 200:
            raise APIException("GC redeem %d/%d error %s %s" % (current_redirect_count, expected_redirect_count, gcRedeemResp.status_code, gcRedeemResp.text))
        if gcRedeemResp.status_code == 200 or gcRedeemResp.status_code == 404:
            break
        current_redirect_count += 1
        if current_redirect_count > expected_redirect_count:
            break
    return session

def get_workouts(gc):
    return gc.get("https://connect.garmin.com/proxy/workout-service-1.0/json/workoutlist").text

def get_workout_string(gc, workoutId):
    return gc.get("https://connect.garmin.com/proxy/workout-service-1.0/json/workout/" + workoutId).text

def create_workout(gc, json_str):
    json_str = json.dumps(json.loads(json_str), separators=(',', ':'))
    payload = {'data':json_str}    
    return gc.post("https://connect.garmin.com/proxy/workout-service-1.0/json/createWorkout", headers={"content-type":"application/x-www-form-urlencoded"}, params=payload)

def delete_workout(gc, workoutId):
    return gc.delete("https://connect.garmin.com/proxy/workout-service-1.0/json/deleteWorkout/" + workoutId).text
    



