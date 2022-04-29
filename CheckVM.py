#!/usr/bin/python3

import ping3, datetime, subprocess, logging

logging.basicConfig(filename='/var/log/CheckVM.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s')

def check_vm(ip, id):

    if ping3.ping(ip):
        print(str(datetime.datetime.now()) + " VM {id} at {ip} is up".format(ip=ip, id=id))

    else:
        print(str(datetime.datetime.now()) + " VM {id} at {ip} is down".format(ip=ip, id=id))
        logging.critical(str(datetime.datetime.now()) + " VM {id} at {ip} is down".format(ip=ip, id=id))

        try:
            logging.info(str(datetime.datetime.now()) + "Attempting to unlock VM {id} at {ip}".format(ip=ip, id=id))
            subprocess.run(['qm', 'unlock', id], capture_output=True)
            logging.info(str(datetime.datetime.now()) + "Unlocked VM {id} at {ip}, now attempting to stop it".format(ip=ip, id=id))
            subprocess.run(['qm', 'stop', id], capture_output=True)
            logging.info(str(datetime.datetime.now()) + "Stopped VM {id} at {ip}, now attempting to start it".format(ip=ip, id=id))
            subprocess.run(['qm', 'start', id], capture_output=True)

        except:
            logging.critical(str(datetime.datetime.now()) + "Failed to unlock and start VM {id} at {ip}".format(ip=ip, id=id))

logging.info(str(datetime.datetime.now()) + "CheckVM.py started")
logging.info(str(datetime.datetime.now()) + "Pinging VM 106")
check_vm('192.168.18.7', '106')
