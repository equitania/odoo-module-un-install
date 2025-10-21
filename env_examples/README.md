# .env Configuration Examples

This directory contains example `.env` configuration files for Odoo server connections.

## Quick Start

1. Copy `template.env` to your configuration directory
2. Rename it to match your server (e.g., `production.env`, `staging.env`)
3. Fill in the required fields (`ODOO_URL`, `ODOO_USER`)
4. Customize optional fields as needed

## Configuration Format

```env
# Required
ODOO_URL=https://your-odoo-server.com
ODOO_USER=admin

# Optional
ODOO_PORT=443
ODOO_PASSWORD=
ODOO_DATABASE=your_database
ODOO_USE_KEYRING=true
```

## Available Fields

### Required

| Field | Description | Example |
|-------|-------------|---------|
| `ODOO_URL` | Server URL with protocol | `https://odoo.example.com` |
| `ODOO_USER` | Username with module management rights | `admin` |

### Optional

| Field | Description | Default | Example |
|-------|-------------|---------|---------|
| `ODOO_PORT` | Server port | `0` (auto-detect) | `443`, `8069` |
| `ODOO_PASSWORD` | User password | *(prompt or keyring)* | `your-password` |
| `ODOO_DATABASE` | Database name | *(select interactively)* | `production_db` |
| `ODOO_USE_KEYRING` | Store password in keyring | `true` | `true`, `false` |

## Security Best Practices

### Password Management Priority

The tool uses passwords in this order:

1. **Environment variable** `ODOO_PASSWORD` (if set in .env)
2. **System keyring** (if `ODOO_USE_KEYRING=true`)
3. **Interactive prompt** (fallback)

### Recommendations

**For Production:**
```env
ODOO_URL=https://production.example.com
ODOO_USER=admin
ODOO_PASSWORD=              # Leave empty
ODOO_USE_KEYRING=true      # Use keyring
```

**For Development:**
```env
ODOO_URL=http://localhost
ODOO_USER=admin
ODOO_PASSWORD=admin        # OK for local dev
ODOO_USE_KEYRING=false     # Optional for dev
```

**For CI/CD:**
```env
ODOO_URL=https://staging.example.com
ODOO_USER=ci_user
ODOO_PASSWORD=${CI_ODOO_PASSWORD}  # From CI secrets
ODOO_USE_KEYRING=false
```

## Example Files

### `template.env`
Complete template with all available options and documentation.

### `production.env`
Example configuration for production server with keyring.

### `localhost.env`
Example configuration for local development.

## Usage

Place your `.env` files in a directory and point the tool to it:

```bash
# Using .env files
odoo-un-install run \
  --server_path=./env_configs \
  --module_path=./modules \
  --install_modules

# Tool automatically detects both .env and .yaml files
# You can mix both formats in the same directory
```

## File Naming

The `.env` file naming is flexible. Common patterns:

- `production.env` - Production server
- `staging.env` - Staging server
- `dev.env` or `localhost.env` - Development
- `server1.env`, `server2.env` - Multiple servers

All files ending with `.env` in the directory will be loaded.

## Backward Compatibility

The tool still supports YAML configuration files. You can:

- Use only `.env` files
- Use only `.yaml` files
- **Mix both formats** in the same directory

The tool will automatically detect and load both formats.

## Security Note

⚠️ **Never commit `.env` files with passwords to version control!**

Add to your `.gitignore`:
```
*.env
!template.env
!*.env.example
```

## Environment Variables

You can also set configuration via environment variables directly:

```bash
export ODOO_URL=https://odoo.example.com
export ODOO_USER=admin
export ODOO_PASSWORD=secret

# Then run without .env file
odoo-un-install run --server_path=./servers --module_path=./modules --install_modules
```

Note: Direct environment variables take precedence over .env files.
