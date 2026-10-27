
## fresh2 split, params {'bm25': {'top_k': 8, 'min_ratio': 0.25}, 'emb': {'top_k': 5, 'min_sim': 0.45}, 'emb-bge': {'top_k': 8, 'min_sim': 0.6}}

| variant | recall | cases at 100% | precision | mean ctx tokens | add-item | literal-ripple | local | paraphrase-ripple | remove-item | rename | status |
| regex | 70.8% | 17/24 | 12.2% | 1061 | 100% | 100% | 0% | 100% | 50% | 100% | 67% |
| bm25 | 82.6% | 19/24 | 17.8% | 859 | 100% | 93% | 100% | 50% | 75% | 72% | 67% |
| regex+bm25 | 95.8% | 23/24 | 15.6% | 1228 | 100% | 100% | 100% | 100% | 75% | 100% | 100% |
| emb | 87.5% | 20/24 | 17.6% | 875 | 100% | 87% | 100% | 100% | 100% | 56% | 67% |
| all | 95.8% | 23/24 | 13.0% | 1293 | 100% | 100% | 100% | 100% | 75% | 100% | 100% |
| emb-bge | 97.2% | 22/24 | 10.0% | 1051 | 100% | 93% | 100% | 100% | 100% | 89% | 100% |
| all-bge | 100.0% | 24/24 | 7.9% | 1379 | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
  miss [regex] fresh2-adr-log4brains-reword: ['s5.s1.i1']
  miss [regex] fresh2-adr-log4brains-supersede: ['s5.i1']
  miss [regex] fresh2-adr-log4brains-remove: ['s5.s2.i2']
  miss [regex] fresh2-adr-govuk-infra-reword: ['s15.s2.i1']
  miss [regex] fresh2-contract-bonterms-reword: ['s6.i1']
  miss [regex] fresh2-contract-bonterms-remove: ['s14.i5']
  miss [regex] fresh2-cv-best-resume-reword: ['s2.s3.i1']
  miss [bm25] fresh2-adr-log4brains-remove: ['s5.s2.i2']
  miss [bm25] fresh2-adr-govuk-infra-supersede: ['s10.s1.i1']
  miss [bm25] fresh2-adr-govuk-infra-rename: ['s7.s2.s2.i1', 's7.s2.s2.i3', 's7.s3.i1', 's7.s4.i4', 's7.s4.i5']
  miss [bm25] fresh2-contract-bonterms-xref: ['s16.i9']
  miss [bm25] fresh2-contract-bonterms-term: ['s14.i1']
  miss [regex+bm25] fresh2-adr-log4brains-remove: ['s5.s2.i2']
  miss [emb] fresh2-adr-govuk-infra-supersede: ['s10.s1.i1']
  miss [emb] fresh2-contract-bonterms-xref: ['s14.i7', 's16.i9']
  miss [emb] fresh2-contract-bonterms-rename: ['s14.i10']
  miss [emb] fresh2-cv-best-resume-rename: ['s2.s2']
  miss [all] fresh2-adr-log4brains-remove: ['s5.s2.i2']
  miss [emb-bge] fresh2-contract-bonterms-xref: ['s16.i9']
  miss [emb-bge] fresh2-contract-bonterms-rename: ['s14.i10']
