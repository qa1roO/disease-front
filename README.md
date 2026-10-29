# disease-front

A strategy-game-style map of human diseases. See [CONTEXT.md](CONTEXT.md) and [docs/spec/v1.md](docs/spec/v1.md).

## Running it

Needs Python 3.11+ and Node 20+.

```bash
pip install -r requirements.txt
python -m pipeline all       # stages 1-4 and 8: ICD-11, GBD check, tree, cross-walk and burden, site/public/map.json
python -m unittest discover -s tests -t .
cd site && npm install && npm run dev
```

Each stage skips itself when its outputs are newer than its inputs; add `--force` to rerun. `data/raw/` is git-ignored.

Stage 2 (GBD data) runs from a Claude session with the IHME GBD connector, not from Python: see [pipeline/STAGE2.md](pipeline/STAGE2.md). Stage 4 prints a coverage report and writes `data/crosswalk-review.yaml`, whose tie resolutions you edit by hand.

Province sizes: GBD 2023 DALYs. Source: Institute for Health Metrics and Evaluation. Used with permission. All rights reserved. The ICD-11 → GBD cause cross-walk (`data/crosswalk.json`, `data/gbd-extra-codes.yaml`) is this project's own work, not a WHO or IHME product.

ICD-11 content: International Classification of Diseases, Eleventh Revision (ICD-11), World Health Organization (WHO) 2019 https://icd.who.int/browse11. Licensed under the Creative Commons Attribution-NoDerivatives 3.0 IGO licence (CC BY-ND 3.0 IGO).
