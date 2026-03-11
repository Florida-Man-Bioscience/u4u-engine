# U4U — Narrative

> Sasank reviews clinical framing. Curtis reviews product framing. This is a living document — if something is wrong, change it here.

---

## What we are building

U4U is a genomic interpretation platform. It takes a raw genome file — the kind you already have from 23andMe, AncestryDNA, or a clinical sequencing lab — and tells you what is actually in it, in plain English, backed by published science.

Most people who have had a genetic test have a file sitting on their computer they cannot read. The companies that ran the test gave them a simplified dashboard, told them their ancestry and a handful of traits, and stopped there. The raw data — thousands of variants that could be clinically meaningful — was never explained. U4U closes that gap.

---

## The problem

When a clinical lab sequences your genome, they are required to report a specific list of findings — the ACMG Secondary Findings gene list, currently 81 genes. If you have a pathogenic variant in one of those genes, they tell you. If your variant is uncertain, or if it is in a gene not on that list, they say nothing.

That list is the floor, not the ceiling. The published scientific literature extends well beyond it. Variants of uncertain significance may have real published data even without formal clinical consensus. Carrier status for recessive conditions is directly relevant to family planning. None of this gets communicated. U4U communicates it.

---

## How we are different

23andMe tells you about a small number of FDA-approved conditions using simplified language and deliberately incomplete results. They are constrained by regulatory approval into providing the minimum.

U4U is not a clinical diagnostic service. We collate what clinical databases and the published literature say about a person's specific variants and present it clearly, with appropriate context, with links to primary sources, and with an honest account of how certain or uncertain each finding is.

The distinction: we are an information platform, not a medical device. We are doing what a well-read, genetics-literate friend would do — explaining what the research says, without pretending the research is the final word.

---

## Who this is for

**Primary — V1:** Someone who already has a 23andMe or AncestryDNA raw data file and wants to know more than the company told them. They are health-conscious, probably 25–45, comfortable with technology, and frustrated that they paid for a test and received limited information. They do not need to understand genomics — they need to understand their results.

**Secondary — V1:** A person who received a VCF from a clinical sequencing lab and wants interpretation beyond what the lab report said. Often someone told "we found a VUS" with no useful follow-up.

**Not in scope for V1:** Clinicians ordering tests on behalf of patients. Researchers. People who do not already have a genome file. Direct-to-consumer sequencing.

---

## What we believe about the information we provide

People have the right to understand their own genomic data. The information we display is already in public databases — ClinVar, gnomAD, the ACMG guidelines, the published literature. We are not revealing anything that does not already exist. We are making it accessible.

We are deliberate about the difference between:

- **Known pathogenic:** ClinVar consensus, peer-reviewed, high confidence. We say so clearly.
- **Likely pathogenic / likely benign:** Strong evidence but not definitive. We say that too.
- **VUS:** The jury is genuinely out. We present the available data honestly — frequency, functional consequence, any relevant research — without pretending there is consensus when there isn't. We do not suppress this information. We contextualise it.
- **Carrier status:** Carrying one copy of a recessive variant typically does not cause disease. We explain this clearly and flag it separately so it is not confused with a risk finding.

Every finding that could cause alarm links to its primary source.

---

## What we are not building

- A diagnostic tool that tells people they have a disease
- A replacement for genetic counseling
- A platform that makes clinical recommendations
- A research database or clinical trial matching service (not V1)
- A sequencing service
- A local desktop app (V1 is a web application — the raw file is processed in memory server-side and discarded, never stored)

---

## Privacy

The raw genome file is processed in memory and discarded. It is never stored server-side, never logged, never retained after the pipeline completes.

What does leave the system: individual variant coordinates (chromosome, position, ref, alt) and rsIDs, sent to Ensembl VEP, NCBI ClinVar, gnomAD, and MyVariant.info during annotation. This is unavoidable — annotation requires querying external databases with variant data. Only the coordinates needed for each call are sent.

What never leaves the system: the assembled genome file, any user identity (V1 has no accounts), any genomic profile.

The previous concept of a fully local desktop app (genomic data never leaving the device at all) is not the V1 architecture. That model remains a long-term option for certain user segments. V1 is a web app with a privacy-respecting server-side architecture — not local-first, but not data-hoarding either.

---

## The moat

Every genomics tool gives a static snapshot. Upload your file, get results, done. The data is the same six months later as it was on day one.

That is not how science works. A variant that is VUS today may be reclassified next year. A gene with limited evidence in 2023 may have three new relevant papers in 2024.

U4U's subscription offering is dynamic research tracking: when new PubMed literature is published that is relevant to a specific variant in a user's stored profile, a plain-English summary of that paper surfaces in their account. Results evolve with the science.

The free tier is: upload a file, see your results. The paid tier is: your results stay current and you hear about new findings that specifically affect you.

LLMs are used only for this feature — summarizing new research. They do not classify variants, generate clinical conclusions, or touch the annotation pipeline. Pipeline outputs are deterministic and database-driven.

---

## The company

Legal entity: 40 Minute Bioscience. Consumer brand: TBD — Jeran's decision. Incorporation happens before the first paying customer.

---

## The name

U4U — "You for You." The data is yours. The interpretation is for you.

---

*This document is maintained by the team. If something here is wrong, change it — do not work around it.*
