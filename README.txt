= Polarion Automatic Upload Tool =

This tool is based on pylarion and xunit importer, the following operations are supported:

1. Generate Job Report on Google Sheet
1. Create test cases
2. Create test runs

=========== Usage Method ===========

1. installation <Please see Installation as shown below>
2. configure ~/.pylarion <Please see Configuration as shown below>
3. $ cd tools_polarion
4. $ python gen_report .py [-a] -d <doc name > -s <sheet name > [-c <columnX =valueX , columnY =valueY, ... >] -- <options for bkr job -list >
5. $ python xunit_to_polarion .py -u <user> [--password=<kerberos password>] -d <doc_name > -s <sheet name > -p <polarion project > -i <plannedin > -t <title prefix > [-n]
(参考Googlesheet-Polarion 工具说明.docx)

<Please execute "python gen_report_google.py (or xunit_to_polarion.py) -h" to get more detailed usage>


=========== Installation ===========

# The installation process can be achieved through '$ bash initial.sh', 
# which including the following steps:

1. Check and install <python-pip>, <gspread> and <oauth2client>
2. Check and install pylarion

=========== Configuration ==========

Create config file, which should looks like:

$ cat ~/.pylarion
[webservice]
url = https://polarion.engineering.redhat.com/polarion
svn_repo = https://polarion.engineering.redhat.com/repo
user = <kerberos_id>
password = <kerberos_password>
default_project = <RHEL6|OtherProject>
logstash_url = ops-qe-logstash-2.rhev-ci-vms.eng.rdu2.redhat.com
logstash_port = 9911

