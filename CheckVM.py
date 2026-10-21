#!/usr/bin/python3
"""Ping a Proxmox VM and hard-restart it (qm stop + qm start) if it stopped answering.

Meant to run as root from cron on the Proxmox host, one line per VM.
"""

import argparse
import fcntl
import logging
import subprocess
import sys

QM = '/usr/sbin/qm'
PING = '/bin/ping'
PATH_LOG = '/var/log/CheckVM.log'
PATH_RUN_LOCK = '/run/CheckVM-{}.lock'

# Seconds before giving up on a qm call; a wedged VM can make qm hang.
QM_TIMEOUT = 300

# Proxmox config locks that are cleared before restarting. 'backup' is the one
# left behind when a VM freezes mid-backup. Any other lock (migrate, snapshot,
# clone...) means an operation a human should look at, so the VM is left alone.
CLEARABLE_LOCKS = {'backup'}

log = logging.getLogger('CheckVM')


def qm(*args):
    """Run a qm subcommand and return its stdout. Raises if it fails."""
    return subprocess.run((QM, *map(str, args)), capture_output=True, text=True,
                          check=True, timeout=QM_TIMEOUT).stdout


def parse_qm_output(text):
    """Parse qm's 'key: value' lines into a dict, skipping nested (indented) ones."""
    result = {}
    for line in text.splitlines():
        if line[:1].isspace() or ': ' not in line:
            continue
        key, value = line.split(': ', 1)
        result[key] = value
    return result


def is_reachable(host, count):
    """True if at least one of `count` pings got a reply.

    Raises instead of returning False when ping itself fails (unknown host, no
    route...), so a problem on the host side never gets a VM restarted.
    """
    result = subprocess.run((PING, '-n', '-q', '-c', str(count), '-W', '2', host),
                            capture_output=True, text=True, timeout=count * 3 + 10)
    # ping exits with 0 if it got a reply, 1 if it got none, 2 on any other error.
    if result.returncode > 1:
        result.check_returncode()
    return result.returncode == 0


def describe(error):
    """One readable line explaining why a command failed."""
    if isinstance(error, subprocess.CalledProcessError):
        output = ' '.join((error.stderr or error.stdout or '').split())
        return f"'{' '.join(error.cmd)}' exited with status {error.returncode}: {output}"
    if isinstance(error, subprocess.TimeoutExpired):
        return f"'{' '.join(error.cmd)}' timed out after {error.timeout}s"
    return str(error)


def check_vm(ip, vmid, gateway=None, pings=3, grace=300, dry_run=False):
    """Check one VM and restart it if it is running but not answering.

    Returns False when something needs a human: the VM is down but was
    deliberately left alone. Raises if a ping or qm command fails.
    """
    vm = f'VM {vmid} at {ip}'

    if is_reachable(ip, pings):
        log.info('%s is up', vm)
        return True
    log.warning('%s did not answer %d pings', vm, pings)

    if gateway and not is_reachable(gateway, pings):
        log.error('Gateway %s is not answering either, looks like a host network '
                  'problem. Not touching %s', gateway, vm)
        return False

    status = parse_qm_output(qm('status', vmid, '--verbose'))
    if status.get('status') != 'running':
        log.info('%s is %s, not touching it', vm, status.get('status', 'in an unknown state'))
        return True

    uptime = int(status['uptime']) if 'uptime' in status else None
    if uptime is not None and uptime < grace:
        log.info('%s was started %ds ago (grace period is %ds), letting it boot',
                 vm, uptime, grace)
        return True

    lock = parse_qm_output(qm('config', vmid)).get('lock')
    if lock and lock not in CLEARABLE_LOCKS:
        log.error("%s is locked ('%s'), not touching it", vm, lock)
        return False

    commands = (['unlock'] if lock else []) + ['stop', 'start']
    if dry_run:
        log.warning('Dry run, would restart %s with: %s', vm,
                    ', '.join(f'qm {command} {vmid}' for command in commands))
        return True

    log.warning('Restarting %s%s', vm, f" (clearing its '{lock}' lock)" if lock else '')
    for command in commands:
        qm(command, vmid)
        log.info('qm %s %s succeeded', command, vmid)
    log.warning('%s restarted', vm)
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Ping a Proxmox VM and hard-restart it if it does not answer.')
    parser.add_argument('-i', '--ip', required=True, help='IP address of the VM')
    parser.add_argument('-id', '--id', required=True, type=int,
                        help='Proxmox ID of the VM, e.g. 106')
    parser.add_argument('-g', '--gateway',
                        help='when the VM does not answer, also ping this address; if it '
                             'does not answer either, assume a host network problem and '
                             'leave the VM alone')
    parser.add_argument('--pings', type=int, default=3,
                        help='pings to send before declaring the VM down (default: %(default)s)')
    parser.add_argument('--grace', type=int, default=300,
                        help='seconds after the VM starts during which it is left alone '
                             'to boot (default: %(default)s)')
    parser.add_argument('--dry-run', action='store_true',
                        help='log what would be done without restarting anything')
    args = parser.parse_args()

    handlers = [logging.FileHandler(PATH_LOG)]
    if sys.stderr.isatty():
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=logging.INFO, handlers=handlers,
                        format='%(asctime)s %(levelname)s %(message)s')

    # A previous run for this VM may still be waiting on a hung qm call.
    run_lock = open(PATH_RUN_LOCK.format(args.id), 'w')
    try:
        fcntl.flock(run_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log.warning('Another CheckVM run for VM %s is still going, skipping', args.id)
        return 0

    try:
        ok = check_vm(args.ip, args.id, args.gateway, args.pings, args.grace, args.dry_run)
    except (subprocess.SubprocessError, OSError) as e:
        log.error('VM %s: %s', args.id, describe(e))
        ok = False
    except Exception:
        log.exception('Unexpected error while checking VM %s', args.id)
        ok = False
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
