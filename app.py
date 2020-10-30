""" Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
           https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied. 
"""

# Import Section
import pathlib
from flask import Flask, render_template, request
import datetime
import requests
import json
from dotenv import load_dotenv
import os
import ssl
from suds.client import Client
from suds.xsd.doctor import Import
from suds.xsd.doctor import ImportDoctor
import sys

#it is not terribly efficient to keep the list of devices extracted from CUCM in a global variable
# this should be changed to some other mechanism for production code or if hosted on an iPaas such as Heroku or GCP
cucmDevices=[]

# Get the absolute path for the project root
project_root = os.path.abspath(os.path.dirname(__file__))

# Extend the system path to include the project root and import the env file
sys.path.insert(0, project_root)
import user_env

# Disable HTTPS certificate validation check - not recommended for production
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

# set runningLocal to False once you are ready to have the code retrieve actual device invormation from CUCM
# it is initially set to True for your testing convenience to make sure the app is installed correctly and
# you are showing the initial list of devices as you wish
runningLocal=True

if not runningLocal:
    tns = 'http://schemas.cisco.com/ast/soap/'
    imp = Import('http://schemas.xmlsoap.org/soap/encoding/')
    imp.filter.add(tns)

    axl = Client("file://" + user_env.WSDL_PATH,
                 location="https://" + user_env.CUCM_LOCATION + "/axl/",
                 faults=False, plugins=[ImportDoctor(imp)],
                 username=user_env.CUCM_USER,
                 password=user_env.CUCM_PASSWORD)


def executeQuery(thequery):
    res = axl.service.executeSQLQuery(sql=thequery)
    if res[1]['return']:
        return (res[1]['return']['row'])

# load all environment variables
load_dotenv()

#Global variables
app = Flask(__name__)

#Methods
#Returns location and time of accessing device
def getSystemTimeAndLocation():
    #request user ip
    userIPRequest = requests.get('https://get.geojs.io/v1/ip.json')
    userIP = userIPRequest.json()['ip'] 

    #request geo information based on ip
    geoRequestURL = 'https://get.geojs.io/v1/ip/geo/' + userIP + '.json'
    geoRequest = requests.get(geoRequestURL)
    geoData = geoRequest.json()

    #create info string
    location = geoData['country']
    timezone = geoData['timezone']
    current_time=datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
    timeAndLocation = "System Information: {}, {} (Timezone: {})".format(location, current_time, timezone)
    
    return timeAndLocation


#Table
@app.route('/',methods=['GET','POST'])
def index():
    global cucmDevices
    try:
        if request.method == 'GET':
            #when the page first loads, the results are unfiltered
            theFilter='All'
            initialType='All'
            if not runningLocal:
                cucmDevices=[]
                print("About to go retrieve devices.....")
                aQuery = "select tp.name, d.description, d.tkmodel, d.tkproduct ,n.dnorpattern as DN from device as d, numplan as n, devicenumplanmap as dnpm, typeproduct as tp where dnpm.fkdevice = d.pkid and dnpm.fknumplan = n.pkid and d.tkclass = 1 and tp.tkmodel = d.tkmodel"
                result = executeQuery(aQuery)
                for device in result:
                    #the device 'name' and 'type' to display map to 'description' and 'name' correspondingly from the SQL query results
                    cucmDevices.append({'name':device['description'],'type': device['name'], 'extension': device['dn']})
            else:
                # if running locally, we will populate the list of devices with some hard coded values so you
                # can test the web page and protocol handler portion of the code without having to connect to CUCM
                cucmDevices = [{'name': "Tanya Adams - 8861 MRA", 'type': "Cisco 8861", 'extension': "6024"},
                                {'name': "Bill Bahr - Dx80 MRA", 'type': "Cisco DX80", 'extension': "6015"},
                                 {'name': "Jessica Rabbit - EX60 MRA", 'type': "Cisco Telepresence EX60", 'extension': "6027"},
                                 {'name': "Hector Ramos - EX60 MRA", 'type': "Cisco Telepresence EX60", 'extension': "6027"},
                                 {'name': "Mobile Jones - Jabber MRA", 'type': "Cisco Unified Client Services Framework", 'extension': "6027"},
                                 {'name': "Maria Pincer - Jabber MRA", 'type': "Cisco Unified Client Services Framework", 'extension': "6027"},
                                 {'name': "Jan Brown - DX80 MRA", 'type': "Cisco DX80", 'extension': "6027"},
                                 {'name': "Mia Thompson - DX80 MRA", 'type': "Cisco DX80", 'extension': "6027"},
                                 {'name': "Jorge Ramos - 8845 MRA", 'type': "Cisco 8845", 'extension': "6029"},
                                {'name': "Amy Loggins - 8845 MRA", 'type': "Cisco 8845", 'extension': "6045"}]
        else:
            select = request.form.get('type_select')
            theFilter=str(select)
            initialType=theFilter

        # Here we filter the devices according to the selection before rendering the page.
        filteredDevices=[]
        typesList=[]
        for aDevice in cucmDevices:
            if aDevice['type'] not in typesList:
                typesList.append(aDevice['type'])
            if aDevice['type']==theFilter or theFilter=='All':
                filteredDevices.append(aDevice)
        return render_template('table.html', hiddenLinks=False, timeAndLocation=getSystemTimeAndLocation(), theDevices=filteredDevices, theTypes=typesList, selectedType=initialType)
    except Exception as e: 
        print(e)  
        #OR the following to show error message 
        return render_template('table.html', error=False, errormessage="CUSTOMIZE: Add custom message here.", errorcode=e, timeAndLocation=getSystemTimeAndLocation())



#Main Function
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

