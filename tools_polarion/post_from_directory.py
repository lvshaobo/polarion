# -*- coding: UTF-8 –*- 

from __future__ import print_function

__version__ = '0.2'
__author__ = 'Shaobo Lv'

import os
import sys
import time
from getopt import getopt

import subprocess
from log import Logger
from color import red, blue, green


def usage():
    msg = """
Usage([]表示该参数为可选):
    从googlesheet导入：
    xunit_to_polarion.py -u <user> --password=<kerberos password> -d <doc_name> -s <sheet name> -p <polarionproject> -i <planned in> -t <title prefix> [-n]

    从csv文件导入：
    xnuit_to_polarion.py -f <file_name > -p <polarion project> -i <planned in> [-n]

    样例：
    xunit_to_polarion.py -u shalv --password=KerberosPassword -d RHEL-6.8-report -s RC -p RHEL6 -i 6_8_sn -t KN-RUN-RHEL-68-RC

    xunit_to_polarion.py -u shalv --password=KerberosPassword -f fail.csv -p RHEL6 -i 6_8_sn
    """
    print(msg)


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
    run_xml_path = './testruns'

    try:
        opts, args = getopt(
            argv[1:], "u:p:n",
            ["user=", "password=", "dryrun"]
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
            elif opt in ("-n", "--dryrun"):
                dryrun = True
        logger.info('Start time: %s' % time.ctime())
        print(blue('Start time: %s' % time.ctime()))

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
