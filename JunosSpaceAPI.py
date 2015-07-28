#!/usr/bin/python

import requests, xmltodict
import xml.etree.ElementTree as ET

class JunosSpaceAPI():

    def __init__(self, space_ip, space_auth):
        self.space_ip     = space_ip
        self.space_auth   = space_auth
        self.script_api   = "/api/space/script-management/scripts/"
        self.job_api      =    "/api/space/job-management/jobs/"

	def run(self, script_id, device_id):
        requests.packages.urllib3.disable_warnings()

        url = 'https://' + self.space_ip + self.script_api + "exec-scripts"

        data = self.buildRequest(script_id, device_id)

        headers = {'content-type': 'application/vnd.net.juniper.space.script-management.exec-scripts+xml;version=1;charset=UTF-8'}

        r = requests.post(url, headers=headers, data=data, auth=self.space_auth, verify=False)

        if r.status_code == 202:
        	# Our script job was "Accepted"
        else:
        	# throw some kind of error
    
    def buildRequest(self, script_id, device_id):

        # get the latest script version
        r = requests.get("https://" + self.space_ip + self.script_api + script_id, auth=self.space_auth, verify=False)

        rxml = xmltodict.parse(r.text, process_namespaces=False)
        script_version = rxml['script']['lastestRevision']

        # build the whole request
        xmlinput = '<scriptMgmts>' + \
                       '<scriptMgmt>' + \
                         '<scriptId>' + script_id + '</scriptId>' + \
                         '<deviceId>' + device_id + '</deviceId>' + \
                         '<scriptVersionSelected>' + script_version +'</scriptVersionSelected>' + \
                         '<scriptParams>' + \
                         '</scriptParams>' + \
                       '</scriptMgmt>' + \
                    '</scriptMgmts>'
        
        return xmlinput

    def getProgress(self, job_id):

        r = requests.get('https://' + self.space_ip + self.job_api + job_id, auth=self.space_auth, verify=False)
        requests.packages.urllib3.disable_warnings()

        element = ET.fromstring(r.text)
        job_status = element.find('job-status').text
        job_state = element.find('job-state').text

        if job_state == "DONE" and job_status == "SUCCESS":
            job_results_url = element.find('detail-link').find('name').text

            return (job_status, job_state, self.getResults(job_results_url))
        
        else:
            return (job_status, job_state, None)

    def getResults(self, job_results_url):

        # we're not done yet!
        if job_results_url == "":
            return None

        results = requests.get('https://' + self.space_ip + job_results_url, auth=self.space_auth, verify=False)

        resultsxmlstring = xmltodict.parse(results.text, process_namespaces=True)
        

        output = resultsxmlstring['script-mgmt-job-results']['script-mgmt-job-result']['job-remarks']

        print output

        result_text = re.search("<output>(.+)<\/output>", output)

        print result_text
        
        if result_text == None:
            #something screwed up
            return None
        else:
            return result_text.group(1)
