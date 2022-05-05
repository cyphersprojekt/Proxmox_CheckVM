# Proxmox_CheckVM

### Made to run from within Proxmox.
### Pings your desired IP. If it succeeds, it does nothing. If it fails, it attempts to restart the VM.

## Requires:

* python3
* python3-pip (to install ping3 & argparse)
* ping3
* argparse

## Usage:

* git clone https://github.com/cyphersprojekt/Proxmox_CheckVM.git
* cd Proxmox_CheckVM/
* chmod a+x CheckVM.py

* ./CheckVM.py --ip 'your VMs IP' --id 'your VMs QM ID'