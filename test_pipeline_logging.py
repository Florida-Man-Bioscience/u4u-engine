import logging
from engine import run_pipeline

logging.basicConfig(level=logging.INFO)

with open("peptides_genotype.csv", "rb") as f:
    run_pipeline(f.read(), "peptides_genotype.csv", filters=["acmg81_rsids.txt"])
