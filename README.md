# SATANA

SATANA keeps the original shell CLI in `satana.sh` and adds a Python launcher plus Flask Web UI under the `satana/` package.

## Run CLI

Legacy mode remains unchanged:

```bash
sudo bash satana.sh
```

The new launcher can also start the same CLI:

```bash
python3 satana.py cli
```

Arguments after `cli` are passed to `satana.sh`.

## Run Web UI

```bash
./satana-web
```

or:

```bash
python3 satana.py web
```

Default URL:

```text
http://127.0.0.1:8080
```

Default first-run login:

```text
username: admin
password: admin
```

On first run, the Web UI writes a generated `secret_key` and password hash to `satana/config/web.json`. To set the first-run password explicitly:

```bash
SATANA_WEB_PASSWORD='new-password' ./satana-web
```

## satana.py Commands

```bash
python3 satana.py cli
python3 satana.py web
python3 satana.py status
python3 satana.py plugins
python3 satana.py reports
```

`status`, `plugins`, and `reports` print JSON for automation.

## Project Structure

```text
satana/
├── cli/
├── web/
├── plugins/
├── reports/
├── logs/
├── api/
├── config/
├── database/
└── core/
```

Key paths:

```text
satana/config/web.json       Web UI settings
satana/logs/web/             Web UI logs
satana/reports/              Web reports
satana/plugins/              Plugin files used by Python/Web
satana/database/             Database files
satana/api/routes.py         REST API routes
satana/core/                 Shared system/config/plugin/report logic
satana/web/app.py            Flask application
```

Compatibility paths are kept. The original `satana.sh` still uses the legacy shell layout, and `web/app.py` remains as a wrapper around `satana.web.app`.

