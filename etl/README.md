# How to use the ETL scripts

## Setup

```bash
cd etl
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Usage

1. Download the latest source data:

```bash
python scripts/update_source.py
```

This downloads `EdStats_CSV.zip` from World Bank DataBank and extracts it to `source/`.

2. Generate the DDF dataset:

```bash
python scripts/etl.py
```

This reads the source files and generates:
- `ddf--concepts.csv` - All indicators with metadata
- `ddf--entities--country.csv` - Countries/regions with metadata
- `datapoints/` - One CSV file per indicator

3. Validate and generate datapackage.json:

```bash
cd ..
validate-ddf-ng -p
```
