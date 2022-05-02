#!/usr/bin/python3

PATH_QM_BIN='/usr/bin/qm'
PATH_LOG='/var/log/CheckVM.log'

import ping3, datetime, subprocess, logging, argparse, sys

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
        except:
            warn(f"Failed to unlock {vm}")
        try:
            info(f"Unlocked {vm}, now attempting to stop it")
            run('stop', id)
        except:
            warn(f"Failed to stop {vm}")
        try:
            info(f"Stopped {vm}, now attempting to start it")
            run('start', id)
        except:
            warn(f"Failed to start {vm}")

if __name__ == '__main__':
    info("CheckVM.py started")
    parser = argparse.ArgumentParser(description='Check VM status')
    parser.add_argument('-i', '--ip', type=str, help='IP address of VM')
    parser.add_argument('-id', '--id', type=str, help='ID of VM')
    args = parser.parse_args(sys.argv[1:])
    info("Pinging VM {id} at {ip}")
    check_vm(args.ip, args.id)