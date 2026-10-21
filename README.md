# Proxmox_CheckVM

Made to run from within Proxmox, as root.
Pings a VM. If it answers, it does nothing. If it doesn't, it hard-restarts the VM (`qm stop` + `qm start`).

It leaves the VM alone when:

* the VM is stopped (so a VM you shut down on purpose stays down)
* the VM was started less than `--grace` seconds ago (so a VM that is still booting isn't killed again)
* the VM holds a Proxmox lock other than `backup` (a migration, snapshot, clone...). A stale `backup` lock is cleared before restarting.
* `--gateway` is given and doesn't answer either (so a host network problem doesn't restart every VM)
* another run for the same VM is still going

## Requires

* python3 (already on Proxmox; no extra packages needed)

## Usage

```
git clone https://github.com/cyphersprojekt/Proxmox_CheckVM.git
cd Proxmox_CheckVM/
chmod a+x CheckVM.py

./CheckVM.py --ip 'your VMs IP' --id 'your VMs QM ID' --dry-run
```

`--dry-run` goes through every check and logs what it would do, without restarting anything. Drop it once you're happy.

| Option | Default | |
|---|---|---|
| `-i`, `--ip` | required | IP address of the VM |
| `-id`, `--id` | required | Proxmox ID of the VM |
| `-g`, `--gateway` | | Also ping this address when the VM is down; if it doesn't answer either, leave the VM alone |
| `--pings` | 3 | Pings to send before declaring the VM down |
| `--grace` | 300 | Seconds after the VM starts during which it's left alone to boot |
| `--dry-run` | | Log what would be done without doing it |

Exit status is 0 when the VM is fine, was restarted, or was deliberately left alone because it's stopped or booting. It is 1 when something needs a human: the restart failed, or the VM is down but was left alone because of a lock or a gateway problem.

## Running it from cron

One line per VM in root's crontab (`crontab -e`):

```
* * * * * /root/Proxmox_CheckVM/CheckVM.py --ip 192.168.18.7 --id 106 --gateway 192.168.18.1
```

The script prints nothing unless something unexpected breaks, so cron won't email you on every run.

## Logs

Everything goes to `/var/log/CheckVM.log` (and to the terminal when run by hand). Every run logs at least one line, so rotate it, e.g. with `/etc/logrotate.d/CheckVM`:

```
/var/log/CheckVM.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
```

## See also

If the VMs freeze because the guest kernel hangs, Proxmox can handle it natively with a virtual watchdog: `qm set <id> --watchdog model=i6300esb,action=reset`, plus a watchdog daemon (or systemd's `RuntimeWatchdogSec`) inside the guest.
