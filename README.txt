= Polarion Automatic Upload Tool =

This is tool is based on pylarion and xunit importer, the following operations are supported:

1. Generate Job Report on Google Sheet
1. Create test cases
2. Create test runs

=========== Usage Method ===========

1. installation <Please see Installation as shown below>
2. configure ~/.pylarion <Please see Configuration as shown below>
3. $ cd tools_polarion
4. $ python gen_report_google.py ~~~ 
5. $ python xunit_to_polarion.py ~~~

<Please execute "python gen_report_google.py (or xunit_to_polarion.py) -h" to get more detailed usage>


=========== Installation ===========

# The installation process can be achieved through '$ bash initial.sh', 
# which including the following steps:

1. Check and install <python-pip>, <gspread> and <oauth2client>
2. Check and install pylarion
3. # Replace

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

