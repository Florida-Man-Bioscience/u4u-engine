import logging
import time

from engine import run_pipeline

logging.basicConfig(level=logging.INFO)

# Run 1
start1 = time.time()
with open("peptides_genotype.csv", "rb") as f:
    run_pipeline(f.read(), "peptides_genotype.csv")
end1 = time.time()
print(f"\\nFirst run took {end1 - start1:.2f} seconds.\\n")

# Run 2
start2 = time.time()
with open("peptides_genotype.csv", "rb") as f:
    run_pipeline(f.read(), "peptides_genotype.csv")
end2 = time.time()
print(f"\\nSecond run took {end2 - start2:.2f} seconds.\\n")
