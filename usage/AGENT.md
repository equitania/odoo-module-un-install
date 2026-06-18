<!--
  Capability Card — generated/maintained via the `cli-capability-card` skill.
  Audience: an LLM/agent that wants to USE this tool. Keep it dense and current.
  Regenerate the command table by re-running scripts/introspect_cli.py after any CLI change:
    .venv/bin/python <skill>/scripts/introspect_cli.py \
      --import odoo_module_un_install.odoo_module_un_install:cli \
      --root-name odoo-un-install --out /tmp/cc-odoo-un-install
-->
# odoo-un-install — Agent Capability Card

> Install, uninstall, update, and report on Odoo modules across one or more Odoo
> instances over JSON-RPC, driven by `.env` server configs and YAML module lists.

- **Invoke:** `odoo-un-install <run|status|export> [flags]`
- **Install:** `uv pip install -e .` (in the repo; needs a working `.venv` — `uv venv` if missing)
- **Version:** 1.2.0
- **Framework:** Click (Python ≥3.10)  ·  **Human docs:** `README.md`, `CLAUDE.md`, `env_examples/`, `yaml_examples/`

## Capabilities at a glance
- Install modules listed under `Install:` in a module YAML, across every configured server.
- Uninstall modules listed under `Uninstall:` — with optional dependency safety analysis.
- Update (upgrade) already-installed modules listed under `Install:`.
- Run operations against many Odoo servers in one invocation (one `.env` file per server).
- Resolve dependencies before acting (`--check_dependencies`): block unsafe uninstalls, pull in missing installs.
- Speed up per-server work with a thread pool (`--parallel`, `--max_workers`).
- Print a colored per-server module status report (installed / to-upgrade / to-install / to-remove).
- Export a server's installed modules to a category-grouped YAML file ready to feed back into `run`.
- Store credentials securely in the system keyring instead of in plaintext config.

## Command reference

| Command | Purpose | Args / Flags |
|---|---|---|
| `odoo-un-install export` | Export installed modules to YAML file | --server_path DIRECTORY, --output FILE, --include-base, --states TEXT, --verbose/-v |
| `odoo-un-install run` | Run module operations on Odoo servers | --server_path DIRECTORY, --module_path DIRECTORY, --uninstall_modules, --install_modules, --update_modules, --check_dependencies, --parallel, --max_workers INTEGER, --show_status, --verbose/-v |
| `odoo-un-install status` | Show module status information for Odoo servers | --server_path DIRECTORY, --verbose/-v |

Notation: `[ARG]` optional positional · `ARG` required positional · `a|b` choice · `--flag` boolean.

Flag detail (defaults / semantics not visible above):
- `--server_path` / `--module_path` — must be **existing directories**; prompted interactively if omitted.
- `--max_workers` — integer, default `5`; only used with `--parallel`.
- `--states` (export) — comma-separated, default `installed`; choices: `installed`, `to upgrade`, `to install`, `to remove`.
- `--include-base` (export) — off by default; includes core modules (`base`, `web`, `mail`, …) and `l10n_*`.
- `--update_modules` reads the **`Install:`** list (there is no `Update:` key).

## Configuration

**Server config — one `.env` file per server in `--server_path`** (NOT YAML, despite older docs):
```dotenv
ODOO_URL=https://odoo.example.com   # required; http://… or https://… , prefix stripped internally
ODOO_USER=admin                     # required; needs module-management rights
ODOO_PORT=0                         # optional; 0 = auto (443 HTTPS / 80 HTTP)
ODOO_PASSWORD=                      # optional; prefer keyring/env over plaintext here
ODOO_DATABASE=                      # optional; if empty + >1 DB → interactive prompt (blocks)
ODOO_USE_KEYRING=true               # optional; true|false|1|0|yes|no
```

**Module config — YAML file in `--module_path`** (only the **first** `.yaml`/`.yml` file is used):
```yaml
Install:            # consumed by --install_modules and --update_modules
  - sale_management
  - crm
Uninstall:          # consumed by --uninstall_modules
  - website_twitter
```

## Recipes

### Install modules on all configured servers
```bash
odoo-un-install run --server_path=./env_examples --module_path=./yaml_examples/modules_yaml --install_modules
```
Installs each module from `Install:`. Already-installed modules are skipped (idempotent). Prints a per-server success/failure summary.

### Safely uninstall modules (dependency-aware)
```bash
odoo-un-install run --server_path=./servers --module_path=./modules --uninstall_modules --check_dependencies
```
Modules that still have installed dependents are reported and **skipped**, not cascade-removed. Without `--check_dependencies`, Odoo will cascade-uninstall dependents — destructive, no confirmation. See Guardrails.

### Update (upgrade) installed modules
```bash
odoo-un-install run --server_path=./servers --module_path=./modules --update_modules
```
Upgrades each module from the `Install:` list that is currently installed; non-installed entries are reported as failures.

### Inspect module status before acting
```bash
odoo-un-install status --server_path=./servers
```
Read-only. Prints installed / to-upgrade / to-install / to-remove per server. No `--module_path` needed.

### Export a server's installed modules to a reusable YAML
```bash
odoo-un-install export --server_path=./servers --output=./modules/current.yaml
# include core/l10n modules, or widen the state filter:
odoo-un-install export --server_path=./servers --output=./all.yaml --include-base --states="installed,to upgrade"
```
Uses **only the first** server in `--server_path`. Output is a category-grouped `Install:` list (with `Uninstall: []`) — feed it straight back into `run`.

### Combined run with parallelism and post-run status
```bash
odoo-un-install run --server_path=./servers --module_path=./modules \
  --install_modules --update_modules --uninstall_modules \
  --check_dependencies --parallel --max_workers=10 --show_status
```
Operation order per server: uninstall → install → update → status. Modules within one server run concurrently; servers are processed sequentially.

## Guardrails & gotchas
- **Destructive, no dry-run, no confirmation:** `--uninstall_modules` calls `button_immediate_uninstall()` live. Without `--check_dependencies`, dependent modules are cascade-uninstalled by Odoo. Always pair uninstall with `--check_dependencies` unless you intend the cascade.
- **Interactive prompts block in non-TTY/automation:**
  - Database selection when `ODOO_DATABASE` is empty **and** the server has >1 database → set `ODOO_DATABASE` to avoid hanging.
  - Password entry via `getpass` when none is resolvable, plus a follow-up "Save password in keyring? (y/n)" prompt → set `ODOO_PASSWORD` or pre-seed the keyring.
  - Missing `--server_path` / `--module_path` are prompted → always pass them explicitly.
- **Password resolution order (actual):** 1) env var `ODOO_PASSWORD` → 2) system keyring (service `odoo_module_un_install`, key `user@server_url`) → 3) interactive prompt. (CLAUDE.md's stated order is outdated.)
- **Prerequisites:** `--server_path` and `--module_path` must be existing directories (Click `Path(exists=True, dir_okay=True)`); at least one `.env` file and one module YAML must be present.
- **Sharp edges:**
  - Only the **first** YAML file in `--module_path` is read; others are silently ignored.
  - `export` uses only the **first** `.env` server; additional servers are warned and skipped.
  - `--update_modules` reads the `Install:` key (no `Update:` key exists).
  - Server config is `.env`, not YAML — older README/CLAUDE.md examples are wrong.
  - Logs go to `tempfile.gettempdir()/odoo_module_un_install.log`; override the directory with env var `ODOO_MODULE_LOG_DIR`.
  - No explicit logout/close; sessions end with the process.
- **`run` with no operation flag** (`--install/--uninstall/--update`) connects but performs nothing.

## Machine-readable outputs
- `odoo-un-install export --output=FILE.yaml` → YAML with header comments (server, DB, count, states) followed by a category-grouped `Install:` list and `Uninstall: []`. Modules and categories sorted alphabetically; German Odoo categories mapped to English. This is the only structured/file output — there is no JSON mode.
- `run` / `status` print human-oriented colored console text only (no `--json`).

## Deeper docs
- `README.md` — overview and usage examples.
- `CLAUDE.md` — project conventions (note: server-config-as-YAML and password-order claims are stale; this card reflects the code).
- `env_examples/` (`template.env`) — annotated server `.env` template.
- `yaml_examples/modules_yaml/` (`template.yaml`, `complex_example.yaml`) — module list examples.
