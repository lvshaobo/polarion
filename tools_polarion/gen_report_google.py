from __future__ import print_function

import sys
import re
import string
import traceback
import subprocess
import xml.etree.ElementTree as ET

import gspread
from oauth2client.service_account import ServiceAccountCredentials


doc = 'A new spreadsheet'
sheet = 'A worksheet'


def red(text):
    return "\x1B[" + "31;1m" + str(text) + "\x1B[" + "0m"


def blue(text):
    return "\x1B[" + "36;1m" + str(text) + "\x1B[" + "0m"


def green(text):
    return "\x1B[" + "32;1m" + str(text) + "\x1B[" + "0m"


class Table:
    header_default = [
        'CASE',
        'TOPO',
        'ROLE',
        'DRIVER',
        'MODEL',
        'Beaker RESULT',
        'Final RESULT',
        'JOB',
        'COMMENT',
        'BZ',
        'OWNER',
        'VIEWER'
    ]

    @classmethod
    def header_default_amend(cls, column):
        if column not in cls.header_default:
            cls.header_default.append(column)

    def __init__(self):
        self.record = {}
        self.custom_columnvalue = {}
        self.record_list = []  # a list of dict to save all records
        self.record_count = 0
        self.header_default = Table.header_default
        self.header = []

    def set_custom_columnvalue(self, c, v):
        self.custom_columnvalue[c] = v

    def add_record(self, **record):
        self.record = record
        # set as '' for col in header_default if col not in self.record
        for col in self.header_default:
            if col not in self.record:
                self.record[col] = ''

        if self.custom_columnvalue:
            for c, v in self.custom_columnvalue.items():
                self.record[c] = v
        self.record_list.append(self.record)
        self.record_count += 1

    def print_records(self):
        for record in self.record_list:
            for col in self.header:
                print(record[col], end='\t')
            print()


def choose_worksheet(spreadsheet_name, worksheet_name):
    # add credentials
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]

        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            './credentials/gspread-bc0df008e072.json', scope
        )

        # return gspread.Client instance
        gc = gspread.authorize(credentials)

    except:
        print("Fail to open worksheet!\n" + traceback.format_exc())

    # create or choose worksheet
    try:
        # open a spreadsheet
        # parameters: a title of spreadsheet
        # return:     a Spreadsheet instance
        sh = gc.open(spreadsheet_name)
        sh.share('shalv@redhat.com', perm_type='user', role='writer')
        try:
            # add a new worksheet
            worksheet = sh.add_worksheet(title=worksheet_name, rows="100", cols="20")
        except gspread.exceptions.RequestError:
            print("worksheet already exists\n")
            # choose a worksheet
            worksheet = sh.worksheet(title=worksheet_name)
        finally:
            return worksheet
    except:
        print("gspread.exceptions.SpreadsheetNotFound")


def create_table(worksheet, owner, allDoc):
    # init aborted jobs
    aborted_jobs = ""

    # init tables
    table_old = Table()
    table_new = Table()

    contents_of_worksheet = worksheet.get_all_values()
    # num_of_rows = worksheet.row_count

    if len(contents_of_worksheet) == 0:
        table_old.record_list = []
        table_old.header = table_old.header_default
        table_new.header = table_new.header_default
        table_new.record = dict(zip(table_new.header_default, table_new.header_default))
        table_new.record_list.append(table_new.record)
        table_new.record_count += 1
    else:
        table_old.header = [h for h in contents_of_worksheet[0] if h in table_old.header_default]
        table_new.header = table_old.header

        header_missed = list(set(table_old.header_default) - set(table_old.header))
        if header_missed:
            print("ERROR! missed columns(s) in header" + "\n")
            for i in header_missed:
                print(red("%s" % i))
            print()
            sys.exit(1)
        for row in contents_of_worksheet:
            record = dict(zip(table_old.header, row))
            table_old.record_list.append(record)
            table_old.record_count += 1

            # all record_list
            # table_new.record_list = table_old.record_list

    # add new rows to table_new
    # beaker
    job_id_list = eval(subprocess.check_output(
        "bkr job-list --owner=%s "
        "--min-id 800000 --max-id 900000" % owner,
        shell=True
    ))
    for job_id in job_id_list:
        job = ET.fromstring(subprocess.check_output(
            "bkr job-results %s "
            "--prettyxml" % job_id,
            shell=True
        ))
        job_status = job.get("status")
        print(job_status)
        job_owner = job.get("owner").rstrip("@redhat.com")

        job_id_value = job_id.split(":")[1]
        # job_id_value = job.get("id")
        test_job = "https://beaker.engineering.redhat.com/jobs/" + str(job_id_value)

        if job_status not in ['Aborted', 'Completed']:
            continue
        if job_status == 'Aborted':
            aborted_jobs += "\n" + test_job
            if not allDoc:
                continue

        find_it = False
        for row in table_old.record_list:
            if row['JOB'] == test_job:
                find_it = True
                break
        if find_it:  # skip jobs already in google sheet
            print(blue("%s is already in google sheet" % test_job))
            continue

        for task in job.iter("task"):
            task_name = task.get("name")
            print(task_name)
            # skip tasks not for test
            if "/kernel/networking" not in task_name:
                continue

            test_topo = ''
            test_role = ''
            test_driver = ''
            test_model = ''
            test_result = ''

            for param in task.iter('param'):
                param_name = param.get('name')
                param_value = param.get('value')
                if param_name == 'NIC_DRIVER':
                    test_driver = param_value
                elif param_name == 'NIC_MODEL':
                    test_model = param_value
                elif param_name == "NIC_SPEED" and test_model != "" and param_name != "any":
                    test_model += ("_" + param_name)
                elif 'TOPO' in param_name:
                    test_topo = param_value
                elif 'MTU_VAL' in param_name:
                    test_topo += ('_mtu%s' % param_value)

            test_name = task_name
            test_role = task.get('role')
            test_result = task.get('result')
            test_job_sheet = test_job if job_status != "Aborted" else '=HYPERLINK("{}","{}")'.format(test_job, test_job)
            if job_status != "Aborted":
                test_job_sheet = test_job
            else:
                test_job_sheet = '=HYPERLINK("{}","{}")'.format(test_job, test_job)

            key_words = [
                "openvswitch/topo", "openvswitch/of_rules", "openvswitch/ovn",
                "vnic/sriov", "vnic/veth", "nic/sanity_check", "nic/functions/offload",
                "nic/functions/abnormal", "firewall", "netlink/iproute2", "netsched/qdisc",
                "tcp/packetdrill", "route/icmp_redirect", "route/mr", "route/pmtu",
                "route/route_func", "route/ecmp", "igmp/conformance", "igmp/join_leave",
                "igmp/igmp_variant", "igmp/send_recv_multimsg", "vnic/macvtap"
            ]

            key_words_flag = False

            for word in key_words:
                if word in test_name:
                    key_words_flag = True
                    break

            print(key_words_flag)

            if key_words_flag:
                results = task.find("results")
                for result in results.iter('result'):
                    test_topo = result.get('path')
                    test_result = result.get('result')
                    if test_topo == 'Setup' or \
                                    'install_pass' in test_topo or \
                                    test_topo == 'Cleanup' or \
                                    test_topo == 'submit-journal-txt' or \
                                    re.match('^rhts[-_].*', test_topo) is not None:
                        continue

                    # handle the case when test fails with
                    # /kernel/networking/nic/functions/offload/LOCALWATCHDOG
                    test_topo = test_topo.replace(test_name, "")

                    test_record = {
                        'CASE': test_name,
                        'TOPO': test_topo,
                        'ROLE': test_role,
                        'DRIVER': test_driver,
                        'MODEL': test_model,
                        'Beaker RESULT': test_result,
                        'JOB': test_job_sheet,
                        'OWNER': job_owner
                    }
                    table_new.add_record(**test_record)
            else:
                test_record = {
                    'CASE': test_name,
                    'TOPO': test_topo,
                    'ROLE': test_role,
                    'DRIVER': test_driver,
                    'MODEL': test_model,
                    'Beaker RESULT': test_result,
                    'JOB': test_job_sheet,
                    'OWNER': job_owner
                }
                table_new.add_record(**test_record)
            print(table_new.record_list)

    return table_old, table_new


def update_gspread(worksheet, table_old, table_new):
    num_of_worksheet = worksheet.row_count
    num_of_records = table_old.record_count + table_new.record_count
    if num_of_records > num_of_worksheet:
        try:
            worksheet.add_rows(num_of_records - num_of_worksheet)
        except:
            print("Fail to add_rows!\n" + traceback.format_exc())

    print(num_of_records)
    print(num_of_worksheet)
    table_new.print_records()


def report(doc, sheet, owner, allDoc):
    # select worksheet
    worksheet = choose_worksheet(doc, sheet)
    # beaker results
    table_old, table_new = create_table(worksheet, owner, allDoc)

    update_gspread(worksheet, table_old, table_new)

    r = 'A' + str(table_old.record_count + 1) + ':' \
        + string.ascii_uppercase[len(table_new.header_default) - 1] \
        + str(table_old.record_count + table_new.record_count)

    row = 0
    cell = 0
    cell_list = worksheet.range(r)
    for record in table_new.record_list:
        for col in table_new.header:
            if col == 'VIEWER' and record[col] == '':
                cell_list[cell].value = r'=IF(ISERROR(INDEX(CaseViewer,MATCH($A' + str(row + 1 + table_old.record_count) \
                                        + r',CaseName,0),1)),"",INDEX(CaseViewer,MATCH($A' + str(
                    row + 1 + table_old.record_count) \
                                        + r',CaseName,0),1))'
            else:
                cell_list[cell].value = record[col]
            cell += 1
        row += 1

    try:
        worksheet.update_cells(cell_list)  # Update in batch
    except:
        return
    else:
        table_old.record_list += table_new.record_list
        table_old.record_count += table_new.record_count

    del table_new.record_list[:]
    table_new.record_count = 0
    print(blue("++ Update worksheet ... ... END"))


report(doc, sheet, "qding", True)

# get username
"""
user_and_email = eval(subprocess.check_output("bkr whoami", shell=True))
user = user_and_email["username"]
print(user)
"""


def create_new_spreadsheet():
    # Create a new spreadsheet
    # parameters: a title of new spreadsheet
    # return:     a Spreadsheet instance
    sh = gc.create('A new spreadsheet')
    sh.share('shalv@redhat.com', perm_type='user', role='writer')
    worksheet = sh.add_worksheet(title="A worksheet", rows="100", cols="20")
    print(sh.title)
