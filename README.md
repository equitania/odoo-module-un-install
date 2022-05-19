# Odoo-module-un-install
====================================================================================    
This is a simple python library to install/uninstall modules in an Odoo environment.  
It is a helper tool for our Odoo modules. https://www.myodoo.de/myodoo-grundpaket.  

## Installation

### Odoo-module-un-install requires:

- Python (>= 3.6)
- click (>= 8.1.3)
- OdooRPC (>= 0.8.0)
- PyYaml (>= 6.0)

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install odoo-module-un-install.

```bash
pip install odoo-module-un-install-equitania
```

---

## Usage

```bash
$ odoo-un-install --help
usage: odoo-un-install [--help] [--server_path] [--module_path] [--uninstall_modules] [--install_modules]
```
```bash
Optional arguments:
  --server_path       Server configuration folder
  --module_path       Modules folder
  --uninstall_modules Uninstall modules (y/n)
  --install_modules   Install modules (y/n)
  --help              Show this message and exit.
```
---

## Example
```bash
odoo-un-install --server_path=./connection_yaml --module_path=./module_yaml --uninstall_modules=y --install_modules=y
# v12 basis dbs
odoo-un-install --server_path=$HOME/gitbase/dev-helpers/yaml/v12-yaml-con --module_path=$HOME/gitbase/helper_script/v12/yaml --uninstall_modules=y --install_modules=y
# v13 basis dbs
odoo-un-install --server_path=$HOME/gitbase/dev-helpers/yaml/v13-yaml-con --module_path=$HOME/gitbase/helper_script/v13/yaml --uninstall_modules=y --install_modules=y
```

This project is licensed under the terms of the **AGPLv3** license.
