from engine.parsers import parse_file
from engine.quality_filter import apply_quality_filter
from engine.filters import filter_variants

file_path = "genome_Noah_Jones_v5_Full_20230322090041.txt"
with open(file_path, "rb") as f:
    raw = parse_file(f.read(), file_path)

qf = apply_quality_filter(raw)
pf = filter_variants(qf, ["acmg81_rsids.txt"], "data")

import json
print(json.dumps([v["rsid"] for v in pf]))
