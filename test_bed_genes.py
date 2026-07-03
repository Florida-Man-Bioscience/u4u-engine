from engine.filters import filter_variants_by_bed

mock_vars = [{"chrom": "17", "pos": "50179337", "rsid": "rs1875675"}]
filtered = filter_variants_by_bed(mock_vars, "peptide_genes.bed", "data")
print(filtered)
