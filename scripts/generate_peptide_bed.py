import json
import logging
import time
import urllib.request
import urllib.error

# Genes targeted by our peptide mapper
TARGET_GENES = [
    "COL1A1", "COL1A2", "SMYD3",  # Tissue repair
    "GHSR",                       # Growth hormone
    "NOS3",                       # Angiogenesis
    "ADRB3",                      # Weight / Lipolysis
    "TERT",                       # Longevity
    "TLR2", "TLR4", "TLR9",       # Immune
    "IRF4",                       # Skin
    "SNAP25", "SV2C",             # Neuromodulation
    "GLP1R", "GIPR", "TCF7L2"     # GLP-1 / incretin (Semaglutide, Tirzepatide, Liraglutide)
]
# Not resolving mtDNA m.1382A>C (MT-RNR1) via Ensembl directly for now, 
# as mitochondrial variants are often handled differently in generic pipelines.
# The user's nuclear gene coordinates cover the bulk of the panel.

ENSEMBL_REST_URL = "https://rest.ensembl.org/lookup/symbol/homo_sapiens/{}?expand=0"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("generate_bed")

def fetch_gene_coords(gene_synonym: str) -> dict | None:
    url = ENSEMBL_REST_URL.format(gene_synonym)
    req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data
    except urllib.error.HTTPError as e:
        log.error(f"Error fetching {gene_synonym}: HTTP {e.code}")
    except Exception as e:
        log.error(f"Error fetching {gene_synonym}: {e}")
    return None

def main():
    bed_entries = []
    
    for gene in TARGET_GENES:
        log.info(f"Looking up {gene}...")
        data = fetch_gene_coords(gene)
        
        if data and "seq_region_name" in data and "start" in data and "end" in data:
            chrom = data["seq_region_name"]
            start = data["start"]
            end = data["end"]
            
            # Ensembl gives exact transcript boundaries. Add a 5kbp padding
            # to capture proximal promoter/regulatory variants (like Sp1 sites in COL1A1)
            pad = 5000
            padded_start = max(1, start - pad)
            padded_end = end + pad
            
            bed_entries.append((chrom, padded_start, padded_end, gene))
        else:
            log.warning(f"Could not resolve coordinates for {gene}")
        
        time.sleep(0.1) # Respect Ensembl rate limits

    # Write BED file
    out_path = "data/peptide_genes.bed"
    with open(out_path, "w") as f:
        for chrom, start, end, gene in bed_entries:
            f.write(f"{chrom}\t{start}\t{end}\t{gene}\n")
    
    log.info(f"Wrote {len(bed_entries)} regions to {out_path}")

if __name__ == "__main__":
    main()
