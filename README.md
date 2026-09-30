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

### Running it on a real Neo4j

```bash
# 1. Start Neo4j (choose your own password; this one is local-only)
docker run -d --name neo4j-heritage -p 7687:7687 -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/<your-password> neo4j:5-community

# 2. Build the manuscript graph from a clone of BetaMasaheft/Manuscripts (+ Institutions, Persons, Works)
python3 -m heritage_rag.betamasaheft <Manuscripts> out --names <Institutions> <Persons> <Works>

# 3. Load it (about 20 seconds) and check the counts
NEO4J_PASSWORD=<your-password> python3 -m heritage_rag.load_neo4j out

# 4. Optional: check that Neo4j and the in-memory store agree (writes and removes `itest_` nodes only)
NEO4J_PASSWORD=<your-password> python3 -m unittest tests.integration_neo4j
```
Needs `pip install neo4j`. Nodes carry `:Entity` plus their CIDOC class as a label, as in `aksum_kg_publication.cypher`.
