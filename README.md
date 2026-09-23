<div align="center">

# mt-permess

[![License](https://img.shields.io/badge/LICENSE-MIT-5C9E31?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/PYTHON-3.9+-3776AB?style=for-the-badge)](https://www.python.org/)
[![Built by](https://img.shields.io/badge/BUILT%20BY-JEAN%20GALEA-8A2BE2?style=for-the-badge)](https://github.com/jgalea)

**CLI for Malta planning permits via the [permess.mt](https://permess.mt/) public API.**

</div>

permess.mt is a third-party index of public Planning Authority applications. This tool wraps its JSON endpoints.

```bash
pip install -e .
mt-permess stats
mt-permess near --place sliema --radius 400
```

## Install

Works on macOS, Linux and Windows. Python 3.9+, no third-party dependencies.

```bash
pipx install git+https://github.com/jgalea/mt-permess
```

`uv tool install git+https://github.com/jgalea/mt-permess` does the same.

From a clone on macOS or Linux:

```bash
cd mt-permess
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

mt-permess stats
```

On Windows, in PowerShell:

```powershell
cd mt-permess
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .

mt-permess stats
```

The Windows steps haven't been tested on a real Windows machine yet; if something breaks, open an issue.

Or without installing:

```bash
PYTHONPATH=src python3 -m mt_permess stats
```

On Windows: `$env:PYTHONPATH = "src"; py -m mt_permess stats`.

## Commands

```bash
# national totals
mt-permess stats
mt-permess stats --format json

# permits near a place or coordinate
mt-permess near --place valletta --radius 300
mt-permess near --latlon 35.90,14.51 --radius 500 --limit 20
mt-permess near --lat 35.91 --lon 14.50 --radius 200 --format urls

# bounding box (lon,lat for each corner)
mt-permess area --nw 14.48,35.92 --se 14.52,35.89 --start-year 2025
mt-permess area --nw 14.50,35.91 --se 14.52,35.89 --year 2026 --format json

# heatmap + weekly activity
mt-permess heatmap --start-year 2026 --top 15
mt-permess weekly --nw 14.48,35.92 --se 14.52,35.89 --year 2026

# AI filters + place shortcuts
mt-permess filters
mt-permess places
```

### Output formats

| Flag | Meaning |
|------|---------|
| `--format table` | Human-readable (default) |
| `--format json` | Full API payload or rows |
| `--format csv` | CSV (`near` / `area`) |
| `--format urls` | One PA case URL per line |

### Places

Built-in centers for `--place`: valletta, sliema, stjulians, msida, birkirkara, mosta, rabat, mdina, gozo, victoria, marsaskala, naxxar, mellieha, and more (`mt-permess places`).

## API

Base: `https://permess.mt`

| Endpoint | Command |
|----------|---------|
| `GET /api/stats` | `stats` |
| `GET /api/permits/radius` | `near` |
| `GET /api/permits/area` | `area` |
| `GET /api/permits/heatmap` | `heatmap` |
| `GET /api/stats/weekly/area` | `weekly` |
| `GET /api/ai/filters` | `filters` |

OpenAPI: https://permess.mt/openapi.json  
Docs: https://permess.mt/docs

Public area responses include up to ~100 full permit records even when `count` is higher. Radius returns point markers (year/type/url), not full descriptions.

## Notes

- Data is maintained by a third party (Simon Agius Muscat / permess.mt), not the Planning Authority.
- Be polite with rate limits; this is a public side project.
- Official case pages: `https://www.pa.org.mt/PAcasedetails?SystemKey=…`

## License

MIT
