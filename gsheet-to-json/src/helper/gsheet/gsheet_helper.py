#!/usr/bin/env python3

import sys
import pygsheets

import httplib2

from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient import discovery
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from helper.logger import *
from helper.gsheet.gsheet_util import *
from helper.gsheet.gsheet_reader import *
from helper.gsheet.gsheet_writer import *

class GsheetHelper(object):

    __instance = None

    def __new__(cls):
        # we only need one singeton instance of this class
        if GsheetHelper.__instance is None:
            GsheetHelper.__instance = object.__new__(cls)

        return GsheetHelper.__instance

    def init(self, config):
        # as we go further we put everything inside a single dict _context
        self._context = {}

        debug(1)
        _G = pygsheets.authorize(service_account_file=config['files']['google-cred'])
        self._context['_G'] = _G
        debug(2)

        credentials = ServiceAccountCredentials.from_json_keyfile_name(config['files']['google-cred'], scopes=['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets'])
        credentials.authorize(httplib2.Http())
        debug(3)

        self._context['service'] = discovery.build('sheets', 'v4', credentials=credentials)
        debug(4)

        gauth = GoogleAuth()
        gauth.credentials = credentials

        self._context['drive'] = GoogleDrive(gauth)
        self._context['tmp-dir'] = config['dirs']['temp-dir']
        self._context['index-worksheet'] = config['index-worksheet']
        self._context['gsheet-read-wait-seconds'] = config['gsheet-read-wait-seconds']
        self._context['gsheet-read-try-count'] = config['gsheet-read-try-count']

    def process_gsheet(self, gsheet_name, parent=None):
        wait_for = self._context['gsheet-read-wait-seconds']
        try_count = self._context['gsheet-read-try-count']
        gsheet = None
        for i in range(0, try_count):
            try:
                gsheet = self._context['_G'].open(gsheet_name)
                break
            except:
                warn(f"gsheet read request (attempt {i}) failed, waiting for {wait_for} seconds before trying again")
                time.sleep(float(wait_for))

        if gsheet is None:
            error('gsheet read request failed, quiting')
            sys.exit(1)

        return process_sheet(self._context, gsheet, parent)
