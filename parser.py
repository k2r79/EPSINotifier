#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
from lxml import html
import re
import datetime
from Cours import Cours
from pymongo import MongoClient
import schedule
import time

auth = {
    "username": os.environ.get("EPSI_USERNAME"),
    "password": os.environ.get("EPSI_PASSWORD"),
    "database_url": os.environ.get("DATABASE_URL")
}

days = [ "103.1200", "122.5200", "141.9200", "161.3200", "180.7200" ]

def parse_schedule(year, week_number):
    auth_session = requests.Session()
    auth_request = auth_session.post("http://ecampusbordeaux.epsi.fr/login_form", data={
        "form.submitted": "1",
        "came_from": "http://ecampusbordeaux.epsi.fr/",
        "js_enabled": "0",
        "cookies_enabled": "",
        "login_name": "",
        "pwd_empty": "0",
        "__ac_name": auth["username"],
        "__ac_password": auth["password"],
        "submit": "Se connecter"
    })

    print("Analyse de la semaine %d de l'année %s" % (week_number, year))
    date_string = "%d-W%d" % (year, week_number)
    start_date = datetime.datetime.strptime(date_string + '-0', "%Y-W%W-%w")

    planning_url = "http://ecampusbordeaux.epsi.fr/emploi_du_temps?date=%s" % start_date.strftime("%d/%m/%Y")
    print("Récupération de l'URL : %s" % planning_url)
    schedule_request = auth_session.get(planning_url)
    schedule_tree = html.fromstring(schedule_request.content)

    cours = []
    cases = schedule_tree.xpath('//div[@class="Case" and not(@id="Apres")]')
    for case_index in range(len(cases)):
        matiere = cases[case_index].xpath('.//td[@class="TCase"]/text()')[0]
        prof = cases[case_index].xpath('.//td[@class="TCProf"]/text()[1]')[0]
        horaires = cases[case_index].xpath('.//td[@class="TChdeb"]/text()')[0]
        salle = parse_salle(cases[case_index].xpath('.//td[@class="TCSalle"]/text()')[0])

        splitted_horaire = horaires.split(" - ")
        datetimes = [
            parse_datetime(cases[case_index], year, week_number, splitted_horaire[0]),
            parse_datetime(cases[case_index], year, week_number, splitted_horaire[1])
        ]

        cours.append(Cours(matiere, prof, datetimes, salle))

    return cours

def parse_salle(salle_string):
    salle_matcher = re.search(r'(F[0-9]+)', salle_string)

    return salle_matcher.group(1)

def parse_datetime(case, year, week_number, time):
    case_matcher = re.search(r'.*left:([0-9\.]*)', case.xpath("./@style")[0])
    day = days.index(case_matcher.group(1)) + 1

    return datetime.datetime.strptime('%s-%s-%s-%s' % (year, week_number, day, time), "%Y-%W-%w-%H:%M")

def job():
    print("Starting job...")

    mongo_client = MongoClient(auth["database_url"])
    mongo_db = mongo_client["cours"]
    mongo_cours = mongo_db["planning"]

    mongo_cours.remove()

    for cours in parse_schedule(datetime.date.today().year, datetime.date.today().isocalendar()[1]):
        print(cours.__dict__)
        mongo_cours.insert(cours.__dict__)

    print("Schedule parsed and inserted !")

    mongo_client.close()

schedule.every().hour.do(job)
job()

while 1:
    schedule.run_pending()
    time.sleep(3500)