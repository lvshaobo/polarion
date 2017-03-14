# -*- coding: UTF-8 –*- 

from __future__ import print_function

__version__ = '0.2'
__author__ = 'Shaobo Lv'

import os
import sys
import csv
import time
import shutil
import subprocess
from getopt import getopt

from log import Logger
from color import red, blue, green
from worksheet import WorkSheet
from testcase import get_cases_ids, get_cases_results, get_cases_comments, cases_filter
from testrun import gen_runs_ids_for_cases, post_runs

from pylarion.document import Document
from pylarion.exceptions import PylarionLibException


def clear_path(path_name):
    path_name = path_name.lstrip("./").rstrip("/")
    if path_name in os.listdir("."):
        shutil.rmtree(path_name)
        os.mkdir(path_name)


def set_document(project, document_name):
    # DOC need be created before running the script
    try:
        document = Document(project, document_name, None, None, None)
    except PylarionLibException:
        print(red("Error: Can't not open \"KernelNetworkQE/KN-TC Kernel NIC Driver New Test Cases\" "
                  "to move new case into it.\n Please create it in polarion.\n"))
        raise
    else:
        return document


def usage():
    msg = """
Usage([]表示该参数为可选):
    从googlesheet导入：
    xunit_to_polarion.py -u <user> [--password=<kerberos password>] -d <doc_name> -s <sheet name> -p <polarion project> -i <planned in> -t <title prefix> [-n]

    从csv文件导入：
    xnuit_to_polarion.py -u <user> [--password=<kerberos password>] -f <file_name > -p <polarion project> -i <planned in> [-n]

    样例：
    xunit_to_polarion.py -u shalv --password=KerberosPassword -d RHEL-6.8-report -s RC -p RHEL6 -i 6_8_sn -t KN-RUN-RHEL-68-RC

    xunit_to_polarion.py -u shalv --password=KerberosPassword -f fail.csv -p RHEL6 -i 6_8_sn
    """
    print(msg)


def authentication():
    """Extract password from configuration file"""
    from ConfigParser import SafeConfigParser
    
    LOCAL_CONFIG = os.path.expanduser("~") + "/.pylarion"
    CONFIG_SECTION = "webservice"
    
    config = SafeConfigParser()
    if not config.read(LOCAL_CONFIG):
        return None
    else:
        return config.get(CONFIG_SECTION, "password")


def post(user, password, run_path):
    for file_name in os.listdir(run_path):
        subprocess.check_call(
            "curl -k -u {}:{} -X POST -F file=@{}/{} "
            "https://polarion.engineering.redhat.com/polarion/import/xunit"
            .format(user, password, run_path, file_name),
            shell=True
        )


def main(argv):
    logger = Logger(__file__)
    
    # initial parameters
    dryrun = False
    document_name = 'KernelNetworkQE/KN-Pylarion'
    case_title_prefix = 'KN-TC New-Test case Pylarion'
    run_xml_path = './testruns'
    
    try:
        opts, args = getopt(
            argv[1:], "hu:d:s:f:p:i:t:n",
            ["user=", "password=", "doc=", "sheet=", "file=", "project=", "plannedin=", "title=", "dryrun"]
        )
    except:
        usage()
        exit(-1)
    else:
        for opt, arg in opts:
            if opt == '-h':
                usage()
                exit(-1)
            elif opt in ("-u", "--user"):
                user = arg
            elif opt in ("--password", ):
                password = arg
            elif opt in ("-d", "--doc"):
                doc = arg
            elif opt in ("-s", "--sheet"):
                sheet = arg
            elif opt in ("-f", "--file"):
                csv_file = arg
            elif opt in ("-p", "--project"):
                project = arg
            elif opt in ("-i", "--plannedin"):
                run_plannedin = arg
            elif opt in ("-t", "--title"):
                run_id_prefix = arg
            elif opt in ("-n", "--dryrun"):
                dryrun = True
        if "project" not in locals() or "run_plannedin" not in locals() or project == "" or run_plannedin == "":
            usage()
            exit(-1)
        if "password" not in locals():
            password = authentication()
            print(password)
            if password is None:
                print(red("Configuration File of Pylarion Can\'t Be Found, Please Input Your Kerberos Password"))
                password = raw_input()
        if doc != '' and sheet != '':
            ws = WorkSheet(doc, sheet)
            cases = ws.cases
            if ws.check_cases() is False:
                logger.error('Missing Cols')
                exit(-1)
        elif csv_file != '':
            cases = []
            with open(csv_file, 'r') as fcsv:
                for row in csv.reader(fcsv):
                    cases.append(row)
        else:
            usage()
            exit(-1)

        logger.info('Start time: %s' % time.ctime())
        print(blue('Start time: %s' % time.ctime()))
        document = set_document(project, document_name)

        logger.info('filter_useless_cases')
        print(blue('filter_useless_cases'))
        cases = cases_filter(cases)
        
        logger.info('get_cases_ids')
        print(blue('get_cases_ids'))
        cases_ids = get_cases_ids(cases, case_title_prefix, document, project, dryrun)

        logger.info('get_cases_results_and_comments')
        print(blue('get_cases_results_and_comments'))
        cases_results = get_cases_results(cases)
        cases_comments = get_cases_comments(cases)

        logger.info('rm -rf ./testruns')
        print(blue('rm -rf ./testruns'))
        clear_path(run_xml_path)

        logger.info('Updating ./testruns')
        print(blue('Updating ./testruns'))
        runs_ids = gen_runs_ids_for_cases(cases, run_id_prefix)
        post_runs(runs_ids, cases_ids, cases_results, cases_comments, run_xml_path, project, user, run_plannedin, dryrun)

        logger.info('Post ./testruns')
        print(blue('Post ./testruns'))
        post(user, password, run_xml_path)
        
        logger.info('Ending time: %s' % time.ctime())
        print(blue('Ending time: %s' % time.ctime()))


if __name__ == '__main__':
    main(sys.argv)

"""
dryrun = False

doc = 'SN2'
sheet = 'Snapshot2'

case_title_prefix = 'KN-TC New-Test case Pylarion'
run_id_prefix = 'Test_KN-RUN-RHEL-69-Snap2'

document_name = 'KernelNetworkQE/KN-Pylarion'
project = 'RHEL6'

run_xml_path = './testruns'
login = 'shalv'
run_plannedin = '6_9_Snap_2'
"""
