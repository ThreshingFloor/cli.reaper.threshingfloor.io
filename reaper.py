#!/usr/bin/env python

from argparse import ArgumentParser
import requests
import sys
import requests
import re
import json

class Reaper:

    URI = "https://api.threshingfloor.io"
    PATTERN = '(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    PROG = re.compile(PATTERN)

    # This key is basic rate limited usage 
    # TODO: Revoke this key eventually
    API_KEY = 'zrWIksWAUj7RB5EKAQwid1xuJ6KdcCPJ9CnJQiBL'

    def __init__(self, args):
        self.filename = args.filename

        self.ports = [{'port': 80, 'proto': 'tcp'}, {'port': 8080, 'proto': 'tcp'}]
        self.scans = self._extractIps(self.filename)

        self.filter = self.queryApi()

        #print self.filter

    def reduce(self, ):
        ipcache = []
        scans = []
        printLine = True

        with open(self.filename, 'r') as f:
            # Read each line
            for line in f:

                printLine = True
                
                # Extract one or more ip's
                for ip in self._extractIp(line):
                    if ip in self.filter:
                        #print('filter item')
                        printLine = False

                if printLine:
                    print(line.strip())


    def queryApi(self, uri=URI):
        CHUNKSIZE = 100
        body = {}
        results = []

        for i in range(0, len(self.scans), CHUNKSIZE):
            body['scans'] = self.scans[i:i+CHUNKSIZE]

            # TODO: Goes over total ammount
            #print("[+] Querying items " + str(i+CHUNKSIZE) + " of " + str(len(self.scans)))

            # Send the request with scan items
            response = requests.post(uri + '/reducer/scans', data=json.dumps(body), headers={'XAPIKEY_HEADER': self.API_KEY}).json()

            for item in response['scans']:
                results.append(item['ip'])

        return results

    def _extractIps(self, filename):
        ipcache = []
        scans = []

        with open(filename, 'r') as f:
            # Read each line
            for line in f:

                # Extract one or more ip's
                for ip in self._extractIp(line):
                    record = {}

                    # If we haven't seen it already, add it to the list of scans
                    if ip not in ipcache:
                        ipcache.append(ip)

                        record['ip'] = ip
                        record['ports'] = self.ports

                        # Add it to the list of scans
                        scans.append(record)

        return scans

    def _extractIp(self, line):
        ips = []

        # See if the line matches for any ip addresses
        res = self.PROG.match(line)

        # Get each ip in the line
        for num in range(0, len(res.groups())):
            ips.append(res.group(num))
        
        return ips

    def _validateIp(self, ip):
        pass


if __name__ == '__main__':
    parser = ArgumentParser()
    
    #parser.add_argument('--type', '-t', help='Log reduction method to use', 
    #        choices=['quick', 'comprehensive'], type=str, action='store',
    #        required=True, dest='type')
    
    parser.add_argument('--file', '-f', help='Filename of log file to reduce',
            type=str, action='store', required=True, dest='filename')
    
    parser.add_argument('--noise', '-n', help='Filename to save noise',
            type=str, action='store', required=False, dest='noise_filename')
    
    args = parser.parse_args()
    
    r = Reaper(args)
    r.reduce()
    #print r
