# disease-front

A strategy-game-style map of human diseases. See [CONTEXT.md](CONTEXT.md) and [docs/spec/v1.md](docs/spec/v1.md).

## Running it

Needs Python 3.11+ and Node 20+.

```bash
python -m pipeline all       # stages 1, 3, 8: download ICD-11, build data/tree.json, build site/public/map.json
python -m unittest discover -s tests -t .
cd site && npm install && npm run dev
```

Each stage skips itself when its outputs are newer than its inputs; add `--force` to rerun. `data/raw/` is git-ignored.

ICD-11 content: International Classification of Diseases, Eleventh Revision (ICD-11), World Health Organization (WHO) 2019 https://icd.who.int/browse11. Licensed under the Creative Commons Attribution-NoDerivatives 3.0 IGO licence (CC BY-ND 3.0 IGO).
