#!/usr/bin/python3

QM='/usr/sbin/qm'
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
            subprocess.run((QM,)+args, capture_output=True, check=True)
            return subprocess.run((QM,)+args, capture_output=True, check=True)
            
        try:
            info(f"Attempting to unlock {vm}")
            run('unlock', id)
        except:
            warn(f"Failed to unlock {vm}")
            warn(str(sys.exc_info()[0]) + " occurred.")
        try:
            info(f"Unlocked {vm}, now attempting to stop it")
            run('stop', id)
        except:
            warn(f"Failed to stop {vm}")
            warn(str(sys.exc_info()[1]) + " occurred.")
        try:
            info(f"Stopped {vm}, now attempting to start it")
            run('start', id)
        except:
            warn(f"Failed to start {vm}")
            warn(str(sys.exc_info()[2]) + " occurred.")

if __name__ == '__main__':

    print('CheckVM.py started'
          + '\n\n')
    
    parser = argparse.ArgumentParser(description='Check VM status')
    parser.add_argument('-i', '--ip', type=str, help='IP address of VM')
    parser.add_argument('-id', '--id', type=str, help='ID of VM')
    
    args = parser.parse_args(sys.argv[1:])
    
    print('Checking VM ' + args.id + ' at ' + args.ip)
    check_vm(args.ip, args.id)