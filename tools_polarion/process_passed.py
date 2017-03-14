import os
import subprocess

xml_path = "./testruns"

"""
for tr_xml in os.listdir(xml_path):
    subprocess.run("curl -k -u shalv:LVshaobord@163.com -X POST -F file=@%s https://polarion.engineering.redhat.com/polarion/import/xunit" % (xml_path+tr_xml),
            shell=True,
            check=True
    )
"""
tr_xml = "Test_KN-RUN-RHEL-69-Snap2_SRIOV_bnx2x_BCM57840.xml"

subprocess.check_call("curl -k -u shalv:LVshaobord@163.com -X POST -F file=@%s https://polarion.engineering.redhat.com/polarion/import/xunit" % (xml_path+"/"+tr_xml), shell=True)
