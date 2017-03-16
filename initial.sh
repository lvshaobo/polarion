# First, we have to check that <python-pip>, <gspread> and <oauth2client> 
# have already been installed:
# $ pip --version  &> /dev/null || sudo yum -y install python-pip
# $ pip show gspread &> /dev/null || pip install gspread
# $ pip show oauth2client &> /dev/null || pip install oauth2client
# 
# Second, we should install and configure pylarion:
# $ git clone http://git.app.eng.bos.redhat.com/git/pylarion.git
# $ cd pylarion
# $ sudo python setup.py install


pip --version  &> /dev/null || sudo yum -y install python-pip
pip show gspread &> /dev/null || sudo pip install gspread
pip show oauth2client &> /dev/null || sudo pip install oauth2client

pylarion_install() {
    git clone http://git.app.eng.bos.redhat.com/git/pylarion.git
    sleep 5s
    cd pylarion
    sudo python setup.py install
    sudo pip install -r requirements.txt
    cd ../
    sudo rm -rf ./pylarion
}

pip show pylarion &> /dev/null || pylarion_install


sudo cp ./urllib2.py /usr/lib64/python2.7/urllib2.py
