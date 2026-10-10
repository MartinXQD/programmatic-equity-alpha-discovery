# Data access

This directory contains schema documentation only. The synthetic generator lives in `src/alpha_discovery/synthetic.py` and creates artificial inputs in memory. Licensed raw data, derived market panels and signal matrices must remain outside Git and outside the publication whitelist.

See [schema.md](schema.md) and [the reproduction guide](../docs/reproduction.md). GitHub Private visibility does not grant redistribution rights to CRSP, Compustat, CCM or other licensed datasets.

Publication protection ignores every new file under `data/`, regardless of its name or extension, except these two reviewed Markdown documents. Common extract, archive, database and credential formats are also ignored elsewhere. The release audit rejects unreviewed data-directory files and tabular extracts, and checks the explicit publication whitelist. A future synthetic or otherwise legally redistributable example requires a documented provenance review and explicit whitelist/ignore exceptions before staging. These guards complement content and history review; they do not grant distribution rights.
