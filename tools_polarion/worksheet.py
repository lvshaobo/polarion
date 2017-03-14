# -*- coding: UTF-8 –*- 

from __future__ import print_function

__version__ = '0.2'
__author__ = 'Shaobo Lv'

import traceback
from log import Logger
import gspread
from oauth2client.service_account import ServiceAccountCredentials


class WorkSheet:
    __log = Logger(__name__)

    def __init__(self, doc, sheet):
        self.doc = doc
        self.sheet = sheet
        self.cases = WorkSheet.choose_worksheet(self.doc, self.sheet).get_all_values()

    @staticmethod
    def choose_worksheet(doc, sheet):
        """choose worksheet by doc, sheet"""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                './credentials/testreport-1258.json', scope
            )
            """
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                './credentials/gspread-bc0df008e072.json', scope
            )
            """
            # return gspread.Client instance
            gc = gspread.authorize(credentials)
            WorkSheet.__log.info("authorize")
            # print(green("authorize"))
        except:
            print("Fail to authorize!\n" + traceback.format_exc())
            return
        # create or choose worksheet
        try:
            # open a spreadsheet
            # parameters: a title of spreadsheet
            # return:     a Spreadsheet instance
            WorkSheet.__log.info("open_doc")
            # print(green("open_doc"))
            sh = gc.open(doc)
            try:
                # add a new worksheet
                ws = sh.add_worksheet(title=sheet, rows="100", cols="20")
            except gspread.exceptions.RequestError:
                print("worksheet already exists\n")
                # choose a worksheet
                ws = sh.worksheet(title=sheet)
            finally:
                return ws
        except:
            WorkSheet.__log.error("gspread.exceptions.SpreadsheetNotFound")
            raise

    def check_cases(self):
        expect_title = {"CASE", "TOPO", "Beaker RESULT", "Final RESULT", "COMMENT"}
        actual_title = set(self.cases[0])
        missed_title = expect_title - actual_title
        if missed_title:
            print("Missing Cols %s" % list(missed_title))
            return False
        else:
            return True
