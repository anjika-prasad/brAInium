# Building a demo document set

For a convincing demo, prepare 4–6 short documents (1-2 pages each) that all
reference the *same* one or two equipment tags, so the graph traversal has
something real to show. Suggested set:

1. **Work order** — routine maintenance on `P-101`, mentions technician name and date.
2. **SOP excerpt** — lockout-tagout procedure referencing `V-204A`, tied to `P-101`'s isolation valve.
3. **Inspection report** — findings on `P-101`, references a prior work order.
4. **Incident report** — a seal failure on `P-101`, with a root-cause note.
5. **A second incident report** — another `P-101` failure a few months later, different root cause.
6. *(optional)* A regulatory excerpt (e.g. a PESO/OISD clause) referencing the
   inspection frequency required for pressure vessels like `P-101`.

This gives you:
- A vector-search question ("what does the SOP say about lockout for V-204A")
- A graph-traversal question ("how many times has P-101 failed and why")
- A visually satisfying graph neighborhood when you load `P-101` in the Graph tab

Real anonymized samples (with names/dates changed) will look far more convincing
to judges than synthetic filler text — if you have access to any real plant
documents, even partial ones, prioritize those.
