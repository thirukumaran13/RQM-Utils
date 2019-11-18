#!/bin/env python3

from xml.dom import minidom
import requests
import subprocess
import os
import sys

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

main_session=requests.Session()

os.environ["PYTHONIOENCODING"]="utf8"

HOST="https://localhost"
RQMURL=HOST+"/qm/service/com.ibm.rqm.integration.service.IIntegrationService/resources/myproject/"

TPS={}

def login(USER,PASS):
	PARAMS = {'j_username':USER,'j_password':PASS } 
	r=main_session.get(HOST+"/qm/authenticated/identity",verify=False)
	r=main_session.post(HOST+'/qm/authenticated/j_security_check',params =PARAMS,verify=False)
	if(r.status_code!=200):
		print("Login Failed")
		exit(1)
		
def myrun(url):
	r=main_session.get(url,verify=False)
	if(r.status_code!=200):
		print("failed to get:"+ url)
	return r.text
	
def getTestPlanIDs():
    nextlink=RQMURL+"testplan/?fields=feed/entry/content/testplan/(title|webId|testcase)"
    file = open('TPList.csv', 'w')
    while True:
        xmldoc = minidom.parseString(myrun(nextlink))
        for entry in xmldoc.getElementsByTagName('entry'):
            title=entry.getElementsByTagName('title')[0].childNodes[0].data
            TPID=entry.getElementsByTagName('ns2:webId')[0].childNodes[0].data
            file.write(TPID+",\""+title+"\""+"\n")
        sys.stdout.write('.')
        sys.stdout.flush()
        nextlink=""
        for link in xmldoc.getElementsByTagName("link"):
            if(link.attributes["rel"].value=="next"):
                nextlink=link.attributes["href"].value
        if (nextlink==""):
            break
    file.close()
	
def getTER(TPID):
    nextlink=RQMURL+"executionworkitem/?fields=feed/entry/content/executionworkitem[testplan/@href='"+RQMURL+"testplan/urn:com.ibm.rqm:testplan:{0}']/(customAttributes|*)".format(TPID)
    file = open('TER_'+TPID+'.csv', 'w')
    file.write("TPID,TERID,TCID,TERNAME,owner,weight,CUR_TCRID,MACHINE,MISC,ITERATION,TAG\n")
    while True:
        xmldoc = minidom.parseString(myrun(nextlink))
        for entry in xmldoc.getElementsByTagName('entry'):
            # weight=entry.getElementsByTagName('ns9:weight')[0].childNodes[0].data
            weight=entry.getElementsByTagName('ns12:weight')[0].childNodes[0].data
            owner=entry.getElementsByTagName('ns3:creator')[0].childNodes[0].data
            TERID=entry.getElementsByTagName('ns2:webId')[0].childNodes[0].data
            TERNAME=entry.getElementsByTagName('ns3:title')[0].childNodes[0].data.replace('"','\\"')
            TCID=entry.getElementsByTagName('ns2:testcase')[0].attributes['href'].value.split(':')[4]
            CUR_TCRID=""
            if (entry.getElementsByTagName('ns2:currentexecutionresult')):
                try:
                    CUR_TCRID=entry.getElementsByTagName('ns2:currentexecutionresult')[0].attributes['href'].value.split(':')[4]
                except:
                    xmldoctemp = minidom.parseString(myrun(entry.getElementsByTagName('ns2:currentexecutionresult')[0].attributes['href'].value))
                    CUR_TCRID=xmldoctemp.getElementsByTagName('ns2:webId')[0].childNodes[0].data
           
            MACHINE=""
            MISC=""
            TAG=""
            for attr in entry.getElementsByTagName('ns2:customAttribute'):
                name=attr.getElementsByTagName('ns2:identifier')[0].childNodes[0].data
                value=attr.getElementsByTagName('ns2:value')[0].childNodes[0].data
                if name=="Machine":
                    MACHINE=value
                elif name=="Misc":
                    MISC=value
                elif name=="Tag":
                    TAG=value
           
            ITERATION=""
            if entry.getElementsByTagName('ns2:testphase'):
                TESTPHASE=entry.getElementsByTagName('ns2:testphase')[0].attributes['href'].value
               
                if TESTPHASE in TPS:
                    ITERATION=TPS[TESTPHASE]
                else:
                    try:
                        testphase = minidom.parseString(myrun(TESTPHASE))
                        ITERATION=testphase.getElementsByTagName('ns3:title')[0].childNodes[0].data
                        TPS[TESTPHASE]=ITERATION
                    except:
                        TPS[TESTPHASE]=""
                        pass
           
            file.write(TPID+","+TERID+","+TCID+",\""+TERNAME.encode('ascii', 'ignore').decode('ascii') +"\",\""+owner+"\","+weight + "," +CUR_TCRID+",\"" +MACHINE +"\",\""+MISC +"\",\""+ITERATION+"\",\""+TAG+"\""+"\n")
        sys.stdout.write('.')
        sys.stdout.flush()
        nextlink=""
        for link in xmldoc.getElementsByTagName("link"):
            if(link.attributes["rel"].value=="next"):
                nextlink=link.attributes["href"].value
        if (nextlink==""):
            break
    file.close()
	
def getTCR(TPID):
    nextlink=RQMURL+"executionresult/?fields=feed/entry/content/executionresult[testplan/@href='"+RQMURL+"testplan/urn:com.ibm.rqm:testplan:{0}']/(webId|starttime|endtime|executionworkitem|owner|state|customAttributes|defect|iterations)".format(TPID)
   
    file = open('TCR_'+TPID+'.csv', 'w')
    file.write("TCRID,TERID,sdate,edate,state,owner,Location_Codes,Modifier\n")
    file2 = open('TCR_Defects_'+TPID+'.csv', 'w')
    file2.write("TCRID,Defect\n")
    while True:
        xmldoc = minidom.parseString(myrun(nextlink))
        for entry in xmldoc.getElementsByTagName('entry'):
            TCRID=entry.getElementsByTagName('ns2:webId')[0].childNodes[0].data
            sdate=entry.getElementsByTagName('ns16:starttime')[0].childNodes[0].data.replace('T',' ').split(".")[0]
            edate=""
            if (entry.getElementsByTagName('ns16:endtime')):
                edate=entry.getElementsByTagName('ns16:endtime')[0].childNodes[0].data.replace('T',' ').split(".")[0]
            TERID=""
            try:
                TERID=entry.getElementsByTagName('ns2:executionworkitem')[0].attributes['href'].value.split(':')[4]
            except:
                xmldoctemp = minidom.parseString(myrun(entry.getElementsByTagName('ns2:executionworkitem')[0].attributes['href'].value))
                TERID=xmldoctemp.getElementsByTagName('ns2:webId')[0].childNodes[0].data
               
            owner=entry.getElementsByTagName('ns5:owner')[0].childNodes[0].data
            state=entry.getElementsByTagName('ns5:state')[0].childNodes[0].data.split('.')[6]
            for d in entry.getElementsByTagName('ns2:defect'):
                defect=d.attributes['summary'].value.split(":")[0]
                file2.write(TCRID+","+defect+"\n")
           
            Location_Codes=""
            Modifier=""
            for attr in entry.getElementsByTagName('ns2:customAttribute'):
                name=attr.getElementsByTagName('ns2:identifier')[0].childNodes[0].data
                value=attr.getElementsByTagName('ns2:value')[0].childNodes[0].data
                elif name=="Location_Codes":
                    Location_Codes=value
                elif name=="com.ibm.rqm___Modifier":
                    Modifier=value
           
            file.write(TCRID+","+TERID+",\""+sdate+"\",\""+edate+"\","+state+",\""+owner+"\",\""+Location_Codes+"\",\""+Modifier+"\"" + "\n")
        sys.stdout.write('.')
        sys.stdout.flush()
        nextlink=""
        for link in xmldoc.getElementsByTagName("link"):
            if(link.attributes["rel"].value=="next"):
                nextlink=link.attributes["href"].value
        if (nextlink==""):
                break
    file.close()
    file2.close()
	
def getTC(TPID):
    nextlink=RQMURL+"testcase/?fields=feed/entry/content/testcase[testplan/@href='"+RQMURL+"testplan/urn:com.ibm.rqm:testplan:{0}']/(webId|category|requirement|title)".format(TPID)
    file = open('TC_'+TPID+'.csv', 'w')
    file2 = open('TCFn_'+TPID+'.csv', 'w')
    file3 = open('TCReq_'+TPID+'.csv', 'w')
    file.write("TCID,COMPLEXITY,TCName\n")
    file2.write("TCID,Fn\n")
    file3.write("TCID,Requirement\n")
    while True:
        xmldoc = minidom.parseString(myrun(nextlink))
        for entry in xmldoc.getElementsByTagName('entry'):
            TCID=entry.getElementsByTagName('ns2:webId')[0].childNodes[0].data
            TCName=entry.getElementsByTagName('ns3:title')[0].childNodes[0].data
           
            COMPLEXITY=""
            for cat in entry.getElementsByTagName('ns2:category'):
                term=cat.attributes["term"].value
                value=cat.attributes["value"].value
                if(term=="Complexity"):
                    COMPLEXITY=value
                    COMPLEXITY=value
                elif(term=="Function"):
                    FUNCTION=value
                    file2.write(TCID+","+FUNCTION+"\n")
           
            for req in entry.getElementsByTagName('ns2:requirement'):
                summary=req.attributes["summary"].value.replace(" ",' ')
                file3.write(TCID+",\""+summary+"\"\n")
           
            file.write(TCID+",\""+COMPLEXITY+"\",\""+TCName+"\"\n")
           
        sys.stdout.write('.')
        sys.stdout.flush()   
        nextlink=""
        for link in xmldoc.getElementsByTagName("link"):
            if(link.attributes["rel"].value=="next"):
                nextlink=link.attributes["href"].value
        if (nextlink==""):
            break
    file.close()
    file2.close()
    file3.close()	
	
def main():
	# This is only example
	U = sys.argv[1] 
	P = sys.argv[2]
	T = sys.argv[3]
	ID = sys.argv[4]
	
	#login 
	login(U,P)
	
	# get details
	if(T == "getter"):
		getTER(ID)
	elif(T == "gettcr"):
		getTCR(ID)
	elif(T == "gettc"):
		getTC(ID)
	elif(T == "gettp"):
		getTestPlanIDs()
	else:
		print("Invalid argument")
		
if __name__ == "__main__":
	main()
	
