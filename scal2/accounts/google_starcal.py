# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

developerKey = 'AI39si4QJ0bmdZJd7nVz0j3zuo1JYS3WUJX8y0f2mvGteDtiKY8TUSzTsY4oAcGlYAM0LmOxHmWWyFLU'## FIXME

import sys
from os.path import splitext
import socket
import BaseHTTPServer

try:
    from urlparse import parse_qsl
except ImportError:
    from cgi import parse_qsl

import gflags
import httplib2
from httplib2 import *

from scal2.paths import *

sys.path.append(join(rootDir, 'google_api_client'))## FIXME


from apiclient.discovery import build
from apiclient.http import HttpRequest

from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow


from scal2.utils import toUnicode, toStr
from scal2.ics import *
from scal2.locale_man import tr as _
from scal2 import core
from scal2.core import to_jd, jd_to, DATE_GREG, getCompactTime, compressLongInt

from scal2 import event_man
from scal2.event_man import Account

from scal2.ui import openUrl ## FIXME

auth_local_webserver = True
auth_host_name = 'localhost'
auth_host_port = [8080, 8090]


getNewRemoteEventId = lambda event: 'starcal#%s#%s#%s'%(
    event.name,
    compressLongInt(event.eid),
    getCompactTime(),
)

def exportEvent(event):
    icsData = event.getIcsData()
    if not icsData:
        return
    gevent = {
        'kind': 'calendar#event',
        'summary': toUnicode(event.summary),
        'description': toUnicode(event.description),
        #'id': getNewRemoteEventId(event),
        'attendees': [],
        'status': 'confirmed',
        'visibility': 'default',
        'guestsCanModify': False,
        'reminders': {
            'overrides': {
                'minutes': event.getNotifyBeforeMin(),
                'method': 'popup',## FIXME
            },
        },
    }
    for key, value in icsData:
        if key=='DTSTART':
            gevent['start'] = {
                ('dateTime' if 'T' in value else 'date'): value,
            }            
        elif key=='DTEND':
            gevent['end'] = {
                ('dateTime' if 'T' in value else 'date'): value,
            }            
        elif key in ('RRULE', 'RDATE', 'EXRULE', 'EXDATE'):
            if not 'recurrence' in gevent:
                gevent['recurrence'] = []
            gevent['recurrence'].append(key + ':' + value)
    return gevent
    
#def exportToEvent(event, group, gevent):## FIXME


def importEvent(gevent):
    pass


def setEtag(gevent):
    gevent['etag'] = compressLongInt(abs(hash(repr(gevent))))

class ClientRedirectServer(BaseHTTPServer.HTTPServer):
  """A server to handle OAuth 2.0 redirects back to localhost.

  Waits for a single request and parses the query parameters
  into query_params and then stops serving.
  """
  query_params = {}


class ClientRedirectHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  """A handler for OAuth 2.0 redirects back to localhost.

  Waits for a single request and parses the query parameters
  into the servers query_params and then stops serving.
  """

  def do_GET(s):
    """Handle a GET request.

    Parses the query parameters and prints a message
    if the flow has completed. Note that we can't detect
    if an error occurred.
    """
    s.send_response(200)
    s.send_header("Content-type", "text/html")
    s.end_headers()
    query = s.path.split('?', 1)[-1]
    query = dict(parse_qsl(query))
    s.server.query_params = query
    s.wfile.write("<html><head><title>Authentication Status</title></head>")
    s.wfile.write("<body><p>The authentication flow has completed.</p>")
    s.wfile.write("</body></html>")

  def log_message(self, format, *args):
    """Do not log messages to stdout while running as command line program."""
    pass


class GoogleAccount(Account):
    name = 'google'
    desc = _('Google')
    def __init__(self, aid=None, email=''):
        Account.__init__(self, aid)
        self.authFile = splitext(self.file)[0] + '.oauth2'
        self.email = email
        self.flow = OAuth2WebServerFlow(
            client_id='536861675971.apps.googleusercontent.com',
            client_secret='BviBsCKTbXrzY0hZbioS6FAt',
            scope=[
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/tasks',
            ],
            user_agent='StarCalendar 2.0.0',
        )
    def getData(self):
        data = Account.getData(self)
        data.update({
            'email', self.email,
        })
        return data
    def setData(self, data):
        Account.setData(self, data)
        for attr in ('email',):
            try:
                setattr(self, attr, data[attr])
            except KeyError:
                pass
    def askVerificationCode(self):
        return raw_input('Enter verification code: ').strip()
    def showError(self, error):
        sys.stderr.write(error+'\n')
    def authenticate(self):
        global auth_local_webserver
        storage = Storage(self.authFile)
        credentials = storage.get()
        if credentials and not credentials.invalid:
            return credentials

        if auth_local_webserver:
            success = False
            port_number = 0
            for port in auth_host_port:
                port_number = port
                try:
                    httpd = ClientRedirectServer(
                        (auth_host_name, port),
                        ClientRedirectHandler,
                    )
                except socket.error, e:
                    pass
                else:
                    success = True
                    break
            auth_local_webserver = success

        if auth_local_webserver:
            oauth_callback = 'http://%s:%s/' % (auth_host_name, port_number)
        else:
            oauth_callback = 'oob'
        openUrl(self.flow.step1_get_authorize_url(oauth_callback))

        code = None
        if auth_local_webserver:
            httpd.handle_request()
            if 'error' in httpd.query_params:
                self.showError('Authentication request was rejected.')
                return
            if 'code' in httpd.query_params:
                code = httpd.query_params['code']
            else:
                self.showError('Failed to find "code" in the query parameters of the redirect.')
                return
        else:
            code = self.askVerificationCode()
        try:
            credential = self.flow.step2_exchange(code)
        except Exception, e:
            self.showError('Authentication has failed: %s'%e)
            return
        storage.put(credential)
        credential.set_store(storage)
        return credentials
    def getHttp(self):
        credentials = self.authenticate()
        if not credentials:
            return False
        http = httplib2.Http()
        #http = HttpRequest()
        return credentials.authorize(http)
    def getCalendarService(self):
        http = self.getHttp()
        #print 'getCalendarService: http=%s'%http
        return build(
            serviceName='calendar',
            version='v3',
            http=http,
            developerKey=developerKey,
        )
    def getTasksService(self):
        http = self.getHttp()
        return build(
            serviceName='tasks',
            version='v1',
            http=http,
            developerKey=developerKey,
        )
    def addNewGroup(self, title):
        service = self.getCalendarService()
        service.calendars().insert(body={
            'kind': 'calendar#calendar',
            'summary': title,
        }).execute()
        return True
    def fetchGroups(self):
        service = self.getCalendarService()
        groups = []
        for group in service.calendarList().list().execute()['items']:
            #print 'group =', group
            groups.append({
                'id': group['id'],
                'title': group['summary'],
            })
        self.remoteGroups = groups
        return True
    def pull(self, group, remoteGroupId, resPerPage=50):
        service = self.getCalendarService()
        ## if remoteGroupId=='tasks':## FIXME
        lastPull = group.getLastPull()
        kwargs = dict(
            calendarId=remoteGroupId,
            orderBy='updated',
            showDeleted=True,## with event.status == 'cancelled',
            maxResults=resPerPage,
            #timeZone="GMT",
            #pageToken=0,
        )
        if lastPull:
            kwargs['updatedMin'] = getIcsTimeByEpoch(lastPull)
        eventsRes = service.events().list(**kwargs).execute()
        events = eventsRes['items']


        return True
    def push(self, group, remoteGroupId):
        service = self.getCalendarService()
        ## if remoteGroupId=='tasks':## FIXME
        lastPush = group.getLastPush()
        for event in group:
            remoteEventId = None
            if event.remoteIds:
                if event.remoteIds[0]==self.aid and event.remoteIds[1]==remoteGroupId:
                    remoteEventId = event.remoteIds[2]
            if remoteEventId:
                if lastPush and event.modified < lastPush:
                    continue
            gevent = exportEvent(event)
            if gevent is None:
                continue
            setEtag(gevent)
            #print 'etag = %r'%gevent['etag']            
            gevent.update({
                'calendarId': remoteGroupId,
                'sequence': group.index(event.eid),
                'organizer': = {
                    'displayName': self.email,## FIXME
                    'email': self.email,
                },
            })
            if remoteEventId:
                #gevent['id'] = remoteEventId
                #if not 'recurrence' in gevent:
                #    gevent['recurrence'] = None ## or [] FIXME
                service.events().patch(## patch or update? FIXME
                    eventId=remoteEventId,
                    body=gevent,
                ).execute()
            else:## FIXME
                remoteEventId = getNewRemoteEventId(event)
                gevent['id'] = remoteEventId
                request = service.events().insert(
                    body=gevent,
                    calendarId=remoteGroupId,
                    #sendNotifications=False,
                )
                #headers={'applicationName': 'StarCalendar/2.0.0'},
                #print dir(request)
                #print 'headers =', request.headers
                #request.headers['application-name'] = 'StarCalendar/2.0.0'
                open('/tmp/starcal-request', 'w').write('uri=%r\nmethod=%r\nheaders=%r\nbody=%r'%(
                    request.uri,
                    request.method,
                    request.headers,
                    request.body,
                ))
                request.execute()
                return
            event.remoteIds = [self.aid, remoteGroupId, remoteEventId]
            event.save()
            group.eventIdByRemoteIds[event.remoteIds] = event.eid
        group.afterPush()## FIXME
        group.save()## FIXME
        return True


if __name__=='__main__':
    from pprint import pprint, pformat
    from scal2 import ui
    account = GoogleAccount(aid=1)
    account.load()
    #account.addNewGroup('StarCalendar')
    #account.fetchGroups()
    #account.save()
    #print 'remoteGroups = %s'%pformat(account.remoteGroups)
    ui.eventGroups.load()
    account.push(
        ui.eventGroups[8],
        u'93mfmsvanup0tllng6tgpm1g88@group.calendar.google.com',
    )
    


