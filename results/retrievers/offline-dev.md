
## dev split, params {'bm25': {'top_k': 8, 'min_ratio': 0.25}, 'emb': {'top_k': 5, 'min_sim': 0.45}, 'emb-bge': {'top_k': 8, 'min_sim': 0.6}}

| variant | recall | cases at 100% | precision | mean ctx tokens | add-item | literal-ripple | local | paraphrase-ripple | remove-item | rename | schema-ripple | status |
| regex | 100.0% | 69/69 | 21.6% | 2499 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| bm25 | 96.5% | 65/69 | 24.7% | 2303 | 100% | 90% | 100% | 100% | 100% | 100% | 100% | 89% |
| regex+bm25 | 100.0% | 69/69 | 18.2% | 2578 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| emb | 92.5% | 60/69 | 19.0% | 2251 | 100% | 100% | 100% | 100% | 100% | 100% | 97% | 44% |
| all | 100.0% | 69/69 | 16.3% | 2617 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| emb-bge | 93.8% | 61/69 | 15.0% | 2358 | 100% | 91% | 100% | 100% | 100% | 100% | 100% | 67% |
| all-bge | 100.0% | 69/69 | 14.2% | 2720 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
  miss [bm25] adr-S-deprecate: ['s3.s1.i1']
  miss [bm25] adr-S-switch-tech: ['s4.s3.i1', 's4.s4.i1', 's4.s4.i2', 's4.s4.i3', 's4.s4.i4']
  miss [bm25] adr-M-supersede: ['s17.s1.i1']
  miss [bm25] adr-M-switch-tech: ['s22.s3.i1', 's22.s4.i1', 's22.s4.i2', 's22.s4.i3', 's22.s4.i4']
  miss [emb] adr-S-supersede: ['s4.s1.i1']
  miss [emb] adr-S-deprecate: ['s3.s1.i1']
  miss [emb] adr-M-supersede: ['s17.s1.i1']
  miss [emb] adr-M-deprecate: ['s12.s1.i1']
  miss [emb] adr-L-supersede: ['s97.s1.i1']
  miss [emb] adr-L-deprecate: ['s65.s1.i1']
  miss [emb] real-adr-backstage-supersede: ['s8']
  miss [emb] real-adr-backstage-luxon: ['s13.s2.i1']
  miss [emb] real-adr-govuk-supersede: ['s21.s1.i1']
  miss [emb-bge] adr-S-supersede: ['s4.s1.i1']
  miss [emb-bge] adr-S-deprecate: ['s3.s1.i1']
  miss [emb-bge] adr-S-switch-tech: ['s4.s4.i1', 's4.s4.i2', 's4.s4.i3', 's4.s4.i4']
  miss [emb-bge] adr-M-supersede: ['s17.s1.i1']
  miss [emb-bge] adr-M-deprecate: ['s12.s1.i1']
  miss [emb-bge] adr-M-switch-tech: ['s22.s3.i1', 's22.s4.i1', 's22.s4.i2', 's22.s4.i3', 's22.s4.i4']
  miss [emb-bge] adr-L-supersede: ['s97.s1.i1']
  miss [emb-bge] adr-L-deprecate: ['s65.s1.i1']
