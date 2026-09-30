# knowledge-graph-Aksum
A source-traceable knowledge graph of the Aksumite archaeological record (Ethiopia/Eritrea, c. 1st–7th century CE), built from four excavation reports and modeled on CIDOC-CRM. Every node and edge in this graph carries a citation back to a specific document and page/line — the graph is designed to be checked, not just trusted.

## Manuscript domain: agentic graph RAG (`heritage_rag/`)

Extends this graph with Geez manuscripts. Run the tests with `python3 -m unittest discover -s tests`.

- `ingest.py` turns catalogue rows into nodes/edges in the same CSV conventions; rows without a citation are rejected.
- `resolution.py` merges exact name variants and only *proposes* near matches for expert review.
- `access.py` + `store.py` filter nodes and edges by role inside the query, so restricted data never reaches the LLM.
- `agent.py` plans, retrieves, reports uncovered domains and cites sources; the LLM (for example Ollama) is injected.
- `data/sample_catalogue.csv` is a synthetic fixture (`TEST-MS-*`), not real manuscripts.
- `ocr.py` wraps Tesseract and scores any OCR engine against expert transcriptions (character error rate, Ethiopic share). No engine is trusted for Geez until scored on your own scans.
- `extract.py` asks an LLM for relations and keeps a claim only if its quote appears verbatim in the page; kept claims are candidate edges (confidence 0.4) for expert review.
- `vhmml.py` loads vHMML reading-room records; stubs load at confidence 0.5.
- `betamasaheft.py` reads the Beta maṣāḥǝft Manuscripts TEI corpus (CC BY-SA 4.0). Run `python3 -m heritage_rag.betamasaheft <clone-dir> <out-dir> [--names <Institutions> <Persons> <Works clones>]`; a full build takes about 5–6 minutes. Output is not committed: it is derived from CC BY-SA data and needs attribution and the same licence.
- `bm_names.py` relabels referenced institutions, persons and works with their names (Latin title as label, Geez and alternate names as aliases) from the matching Beta maṣāḥǝft repositories.
