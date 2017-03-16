#!/usr/bin/python

#
# 1. create a google spreadsheet first, and give it a name
#
# 2. share it to testreport-1258@appspot.gserviceaccount.com
#
# 3. add a sheet with name
#    and row1 as header including (CASE, TOPO, ROLE, NIC, DRIVER, Beaker RESULT, Final RESULT, JOB, COMMENT, BZ, OWNER, VIEWER)
#
# 4. collect results of beaker jobs of owner with whiteboard
#    and put reports to google spreadsheet sheet in doc
#
# usage: gen_report --doc doc --sheet sheet -- bkr-job-list-options
# usage (include Aborted jobs): gen_report --all --doc doc --sheet sheet -- bkr-job-list-options
#
# ex.
#    python gen_report.py -d test_spreadsheet -s sheet1 -c "OWNER=qding,VIEWER=qding" -- --owner qding --whiteboard RHEL-6.8 --min-id 1276832 --max-id 1278873
#

from __future__ import print_function

import sys
import getopt
import os
import subprocess
import commands
import string
import xml.etree.ElementTree as ET
import traceback
import re

# network proxy
#os.environ["http_proxy"]="http://squid.apac.redhat.com:8080/"
#os.environ["ftp_proxy"]="http://squid.apac.redhat.com:8080/"
#os.environ["all_proxy"]="socks://squid.apac.redhat.com:8080/"
#os.environ["https_proxy"]="http://squid.apac.redhat.com:8080/"
#os.environ["no_proxy"]="localhost,127.0.0.0/8,::1,rhebs.corp.redhat.com,xenaweb-01-mgmt.lab.eng.bos.redhat.com"

# install required packages
cmd=r"""
if grep -q 'Red Hat Enterprise Linux' /etc/redhat-release && ! rpm --quiet -q epel-release; then
        rpm -ivh https://dl.fedoraproject.org/pub/epel/epel-release-latest-$(cut -f1 -d. /etc/redhat-release | sed 's/[^0-9]//g').noarch.rpm
fi
pip -V  &> /dev/null || yum -y install python-pip
pip show google-api-python-client &> /dev/null || pip install google-api-python-client
pip show gspread                  &> /dev/null || pip install gspread
pip show oauth2client             &> /dev/null || pip install oauth2client
bkr --version > /dev/null || {
        wget -O /etc/yum.repos.d/beaker-client.repo http://download.lab.bos.redhat.com/beakerrepos/beaker-client-RedHatEnterpriseLinux.repo
        yum install -y rhts-test-env beakerlib rhts-devel rhts-python beakerlib-redhat beaker-client beaker-redhat
}
"""
os.system("sudo bash -c \"%s\"" % cmd)

from oauth2client.service_account import ServiceAccountCredentials
import gspread

def RED(text):
    return "\x1B[" + "31;1m" + str(text) + "\x1B[" + "0m"


def BLUE(text):
    return "\x1B[" + "36;1m" + str(text) + "\x1B[" + "0m"


def GREEN(text):
    return "\x1B[" + "32;1m" + str(text) + "\x1B[" + "0m"

key_file = r'''
{
  "type": "service_account",
  "project_id": "testreport-1258",
  "private_key_id": "dff8e33eb31998e85ead4f5503e776ab556e7c32",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCqJ5X6gm3Kp+Fr\nr9+q75DVhjg9ni3oEr1c9hmeacphs3q2vEhOTXf8XZNIyele9Nu7ndU5n1vhgPrN\n2tYD+uVXYJ3+38NroGk5e6KHT3NGBqXO7hEtVTUzV2ASVgS8HI9brdCQ3beEhJlV\neyxnPfcP5aqOLunAo6qW0RADV9hGPTtFtMvgzRAkiqoaw87+5vffKQPYZgI4IRJ6\nS7KYTM77S9DiU16eGEVeEhzXp+DuxPopyXN0ID4Oq0jfSqxgXjE1erU5zui7LYuy\nzD2GuFev193D33K9tZtCcMDwSUMopdgaN1s9Z3yJxJwOnhi8XaysIFV8tmmLS203\nZKQoTbdnAgMBAAECggEACF2F3BkJeMskI/0zi93XSwgcP7tFGoHBWY6n18fvsTn3\nsIA1NdRNL9UR5qQ2mvqCywiJcRnKlJ2YtwIpP2zYVaFkYyFxJBtw0OipJunbCvhM\nso21vnrP8MQ87unXtb/ZtHIpLNYZraQvPaqeljzPprJt3iukRlpFisCgfumUsm8/\nlsNpCs8dSEOE06VYuK4auSTjAmJNq30oSrKQ3T5dhOD8i4e1yYFN3RPvKdr8Or+z\nvil5flV3v4ulUwWy6yJcqSMLUD5ndF3dob0rDtFzxs6Q3KDOasQ3RTHikbQkxssI\nRGxPgt/3e7HXdwhLqzhV/Cz2EY2n1P7lVRkZGCuEsQKBgQDnj1kEjETOYn+JkwIw\n82Z6QUn9cP82Y+R3W7S0JZzzH8C12UUHuCF7t99dIg8ecIC9FIo5VR2JUxKSIhAl\nw3QPk0ScNw0VK2EtnxeV6M5PWAGNOhkWF3ECd/FTy/K3iiX+dzjEDRgz/AJVkiQe\nB9d4BVuyXJlKaUjeFS0Ugofh6wKBgQC8HRefbU8zqiTIj9jJ5rqKEjj0WK2BehIJ\nQQEt0UxSdnAjGT6K7GR76b//m117AYeTihsusexz0Wo+ZKLGHBkGgBHUvLOMeAQk\n5tSIJ3zQ3SIjylFSrBjk9FuIMFvATVAX+MI2AIUf5nug1c0w7l2/VkkljDFaCSmf\n0caQBgWldQKBgF4nk3Kd9nxU4Lb357QvxEOBuKws/hkHlSZTS67UfHT/PES1C7SP\n0k2T/mbIKo2eATrg1zNowJHODYcOArLYPqD2qLc8Sz2IXgNG5Tg3aWwpxLfAH+Mz\ntOfkDWSdURwAOGK354UQLf81QV26BqWPWrWauCZWMJ5pIQ/sXGAykz3xAoGAO+dv\nzF8855D5Ib1dJf6JzMo8xOMwbZj4AWZn/7U0/tWkpCi31/mrjiJD+Bv7yt4T1JIY\nUehrCf7YPIJDq57rATzrcLme286kUzQG3kzk3IZvBsK43wDa9J40P8xWi4iTRu76\nucO0oRH+sJslOr3NsM7DgGeCl89vJ+vftaGVTrkCgYEAsALI+UiEZr5NmJNFnSi5\noi0rL8R03HMTXyIiP3wQ/huNZGUoci6UgoQ+uWFDMSzCcKQ+rrvmEz97eTKIT7sp\nMSMVusxikqV73w8s15cCgBCe4VjzY29K5+QxTWEwqwAHqmuRTxx1oIjd4zorRi9a\nT27n6RXsq3UDi2g0aayT6pI=\n-----END PRIVATE KEY-----\n",
  "client_email": "testreport-1258@appspot.gserviceaccount.com",
  "client_id": "105487479381239759188",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://accounts.google.com/o/oauth2/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/testreport-1258%40appspot.gserviceaccount.com"
}
'''

s,o=commands.getstatusoutput("bkr whoami")
o=eval(o)
user=o['username']

class Table(object):
    header_default = ['CASE',
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
        self.record_list = []   # a list of dict to save all records
        self.record_count = 0
        self.header_default = Table.header_default
        self.header_setting = []

    def set_custom_columnvalue(self, c, v):
        self.custom_columnvalue[c] = v

    def add_record(self, **record):
        self.record = record
        for col in self.header_default:
            if not col in self.record:
                self.record[col] = ''
        if self.custom_columnvalue:
            for c,v in self.custom_columnvalue.iteritems():
                self.record[c] = v
        self.record_list.append(self.record)
        self.record_count += 1

    def print_records(self):
        for record in self.record_list:
            for col in self.header_setting:
                print(record[col], end='\t')
            print()


table_old = Table()
table_new = Table()

def report(doc, sheet, bkropt, allDoc):
    aborted_jobs = ""
    not_modified_jobs = ""
    global table_old
    global table_new

    # init gspread
    try:
        key_file_json = '/dev/shm/TestReport-dff8e33eb319.json'
        f = file(key_file_json, 'w')
        f.write(key_file)
        f.close()

        SCOPES = ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(key_file_json, SCOPES)
        gss_client = gspread.authorize(credentials)
        gss = gss_client.open(doc)
        worksheet = gss.worksheet(sheet)
        download = worksheet.get_all_values()
        num_of_rows = worksheet.row_count

    except:
        print("Fail to open worksheet!\n" + traceback.format_exc())
        return

    # parse download gspread
    if len(download) <= 0:
        table_old.record_list = []
        table_old.header_setting = table_old.header_default

        # add default header for table_new
        table_new.header_setting = table_new.header_default
        table_new.record = {}
        index = 0
        for col in table_new.header_setting:
            table_new.record[col] = table_old.header_default[index]
            index += 1
        table_new.record_list.append(table_new.record)
        table_new.record_count += 1

    else:
        # set fields order - according to the download data list's index
        for i in download[0]:                      # headers of download data
            for j in table_old.header_default:
                if i == j:
                    table_old.header_setting.append(j)
        table_new.header_setting = table_old.header_setting

        header_missed = list(set(table_old.header_default) - set(table_old.header_setting))
        if header_missed:
            print("ERROR! missed column(s) in header:", end=' ')
            for i in header_missed:
                print(RED("'%s'" % i), end=' ')
            print()
            sys.exit(1)

        # save download data in table_old struct
        for row in download:
            table_old.record = {}
            index = 0
            for col in table_old.header_setting:
                table_old.record[col] = row[index]
                index += 1
            table_old.record_list.append(table_old.record)
            table_old.record_count += 1

    # analyze input beaker jobs and save to record_list
    p = subprocess.Popen('bkr job-list '+bkropt+' --format list', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout.readlines():
        line = line.rstrip()

        print(BLUE("++++ Analyze job (%s) ... ... " % (line)), end='')
        os.system("bkr job-results %s --prettyxml > /dev/shm/bkr_job_results_for_driver_team.xml" % line)
        tree = ET.parse('/dev/shm/bkr_job_results_for_driver_team.xml')
        root = tree.getroot()

        for job in root.getiterator('job'):
            job_status = job.get('status')

        job_id = job.get('id')
        job_owner = job.get('owner').replace('@redhat.com', '')
        test_job = "https://beaker.engineering.redhat.com/jobs/" + str(job_id)

        if job_status != 'Aborted' and job_status != 'Completed':
            print(BLUE("%s" % (job_status)))
            continue
        else:
            if job_status == 'Aborted':
                aborted_jobs += "\n" + test_job
                if not allDoc:
                    print(BLUE("%s" % (job_status)))
                    continue
        #if job_status == 'Aborted':
        #    aborted_jobs += "\n"+test_job
        #    print(BLUE("%s" % (job_status)))
        #    continue
        #if job_status != 'Completed':    # skip not Completed job
        #    print(BLUE("%s" % (job_status)))
        #    continue

        find_it = False
        for row in table_old.record_list:
            if row['JOB'] == test_job:
                find_it = True
                break
        if find_it:     # skip jobs already in google sheet
            print(BLUE("%s is already in google sheet" % test_job))
            continue

        print(BLUE("%s" % (job_status)))

        for task in root.getiterator('task'):
            task_name = task.get('name')
            if task_name.find('/kernel/networking') == -1: # skip tasks not for test
                continue

            test_name = task_name
            test_topo = ''
            test_role = ''
            test_driver = ''
            test_model = ''
            test_result = ''

            for param in task.getiterator('param'):
                param_name = param.get('name')
                param_value = param.get('value')
                if param_name == 'NIC_DRIVER':
                    test_driver = param_value
                elif param_name == 'NIC_MODEL':
                    test_model = param_value
                elif param_name == "NIC_SPEED" and test_model != "" and param_name != "any":
                    test_model += ("_" + param_name)
                elif param_name.find('TOPO') != -1:
                    test_topo = param_value
                elif param_name.find('MTU_VAL') != -1:
                    test_topo += ('_mtu%s' % param_value)

            test_name = task.get('name')
            test_role = task.get('role')
            test_result = task.get('result')
            test_job_sheet = test_job if job_status != "Aborted" else '=HYPERLINK("{}","{}")'.format(test_job, test_job)

            if test_name.find("openvswitch/topo") != -1 or \
                test_name.find("openvswitch/of_rules") != -1 or \
                test_name.find("openvswitch/ovn") != -1 or \
                test_name.find("vnic/sriov") != -1 or \
                test_name.find("vnic/veth") != -1 or \
                test_name.find("nic/sanity_check") != -1 or \
                test_name.find("nic/functions/offload") != -1 or \
                test_name.find("nic/functions/abnormal") != -1 or \
                test_name.find("firewall") != -1 or \
                test_name.find("netlink/iproute2") != -1 or \
                test_name.find("netsched/qdisc") != -1 or \
                test_name.find("tcp/packetdrill") != -1 or \
                test_name.find("route/icmp_redirect") != -1 or \
                test_name.find("route/mr") != -1 or \
                test_name.find("route/pmtu") != -1 or \
                test_name.find("route/route_func") != -1 or \
                test_name.find("route/ecmp") != -1 or \
                test_name.find("igmp/conformance") != -1 or \
                test_name.find("igmp/join_leave") != -1 or \
                test_name.find("igmp/igmp_variant") != -1 or \
                test_name.find("igmp/send_recv_multimsg") != -1 or \
                test_name.find("vnic/macvtap") != -1:
                results = task.find('results')

                for result in results.getiterator('result'):
                    test_topo = result.get('path')
                    test_result = result.get('result')
                    if test_topo == 'Setup' or \
                       'install_pass' in test_topo or \
                        test_topo == 'Cleanup' or \
                        test_topo == 'submit-journal-txt' or \
                        re.match('^rhts[-_].*', test_topo) != None:
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

        # if job's owner is not user, it will be added to the list not_modified_jobs
        # and give warn message
        if job_owner == user:
            os.system("bkr job-modify %s --retention-tag='active+1' --product='cpe:/o:redhat:enterprise_linux'" % line)
            retval = p.wait()
        else:
            not_modified_jobs += "\n" + test_job

        # update gspread
        if table_new.record_count <= 0:
            print(BLUE("No new record data"))
            continue

        num_of_records = table_old.record_count + table_new.record_count
        if num_of_rows < num_of_records:
            try:
                print(BLUE("++ add_rows(%u) ... ... " % (num_of_records - num_of_rows)))
                worksheet.add_rows(num_of_records - num_of_rows)
            except:
                print("Fail to add_rows!\n" + traceback.format_exc())
                return
            else:
                num_of_rows += (num_of_records - num_of_rows)

        r='A'+str(table_old.record_count+1)+':'+string.ascii_uppercase[len(table_new.header_default)-1]+str(table_old.record_count + table_new.record_count)

        print(BLUE("++ Update worksheet(%s) ... ... START" % r))
        table_new.print_records()
        row = 0
        cell = 0
        cell_list = worksheet.range(r)
        for record in table_new.record_list:
            for col in table_new.header_setting:
                if col == 'VIEWER' and record[col] == '':
                    cell_list[cell].value=r'=IF(ISERROR(INDEX(CaseViewer,MATCH($A'+str(row+1+table_old.record_count)+r',CaseName,0),1)),"",INDEX(CaseViewer,MATCH($A'+str(row+1+table_old.record_count)+r',CaseName,0),1))'
                else:
                    cell_list[cell].value = record[col]
                cell += 1
            row += 1

        try:
            worksheet.update_cells(cell_list)    # Update in batch
        except:
            return
        else:
            table_old.record_list += table_new.record_list
            table_old.record_count += table_new.record_count

        del table_new.record_list[:]
        table_new.record_count = 0
        print(BLUE("++ Update worksheet ... ... END"))
        print(BLUE("++++ Analyze job (%s) ... ... DONE" % (line)))

    if aborted_jobs != "":
        print(RED("+++Aborted jobs: %s" % aborted_jobs))
    print("\n")
    if not_modified_jobs != "":
        print(RED("+++Jobs of retention-tag not modifed: %s" % not_modified_jobs))


def usage():
    print('Usage:')
    print('  gen_report.py [-a] -d <doc name> -s <sheet name> -c <columnX=valueX,columnY=valueY,...> -- <options for bkr job-list>')
    print('\nExample:')
    print('  ./gen_report.py [-a] -d test_spreadsheet -s sheet1 -c "OWNER=qding,VIEWER=qding" -- --owner qding --whiteboard "RHEL-6.8 OVS SS3"')
    print('  ./gen_report.py [-a] -d test_spreadsheet -s sheet1 -c "OWNER=qding,VIEWER=qding" -- --min-id 1276832 --max-id 1278873 ')


def main(argv):
    doc = ''
    sheet = ''
    bkropt = ''
    allDoc = False

    for cx in range(0, len(argv)):
        if argv[cx] == '--':
            bkropt = subprocess.list2cmdline(argv[(cx+1):])
            break
    try:
        opts, args = getopt.getopt(argv, "ahd:s:c:", ["doc=", "sheet=", "customcolumn=", "all"])

    except getopt.GetoptError:
        usage()
        sys.exit(1)

    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif opt in ("-d", "--doc"):
            doc = arg
        elif opt in ("-s", "--sheet"):
            sheet = arg
        elif opt in ("-c", "--customcolumn"):
            custom_columnvalue_list = arg
        elif opt in ("-a", "--all"):
            allDoc = True

    print("doc: %s, sheet: %s, bkropt: %s\n" % (doc, sheet, bkropt))

    if 'custom_columnvalue_list' in locals():
        for i in custom_columnvalue_list.split(','):
            c, v = i.partition("=")[::2]
            Table.header_default_amend(c)
            table_new.set_custom_columnvalue(c, v)

    report(doc, sheet, bkropt, allDoc)

if __name__ == "__main__":
    main(sys.argv[1:])
