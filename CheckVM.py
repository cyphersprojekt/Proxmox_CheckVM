#!/usr/bin/python3

PATH_QM_BIN='/usr/bin/qm'
PATH_LOG='/var/log/CheckVM.log'

import ping3, datetime, subprocess, logging

logging.basicConfig(filename=PATH_LOG,
                    filemode='a', 
                    format='%(name)s - %(levelname)s - %(message)s')

def info(s):
    logging.info(str(datetime.datetime.now()) + ' ' + s)

def warn(s):
    logging.critical(str(datetime.datetime.now()) + ' ' + s )

def check_vm(ip, id):       
    vm = f'VM {id} at {ip}'

    if ping3.ping(ip):
        info(f"{vm} is up")

    else:
        warn(f"{vm} is down")

        def run(*args):
            subprocess.run([PATH_QM_BIN]+args, capture_output=True, check=True)
            
        try:
            info(f"Attempting to unlock {vm}")
            run('unlock', id)
            info(f"Unlocked {vm}, now attempting to stop it")
            run('stop', id)
            info(f"Stopped {vm}, now attempting to start it")
            run('start', id)
        except:
            warn(f"Failed to unlock and start {vm}")

if __name__ == '__main__':
    info("CheckVM.py started")
    info("Pinging VM 106")
    check_vm('192.168.18.7', '106')
