"""Plan -> retrieve -> coverage check -> answer, with the LLM injected.

The LLM is a plain callable `llm(prompt) -> str`, so the same loop runs on Ollama
locally or on a stub in tests. Answers cite the source_document/source_locator of
every edge used and say which requested domains had no evidence.
"""
import json
import urllib.request
from .access import allowed_levels, generalise_place

DOMAINS = ("manuscript", "archaeology", "ethnography")


def ollama_llm(model="llama3.1", host="http://localhost:11434", json_mode=False):
    def call(prompt):
        body = {"model": model, "stream": False, "messages": [{"role": "user", "content": prompt}]}
        if json_mode:
            body["format"] = "json"
        req = urllib.request.Request(f"{host}/api/chat", json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.load(resp)["message"]["content"]
    return call


def plan(llm, question):
    """Ask for search terms and domains. Bad model output falls back to the raw question."""
    raw = llm('Return JSON {"terms": [...], "domains": [...]} for this heritage question. '
              f'Domains come from {list(DOMAINS)}. Question: {question}')
    try:
        data = json.loads(raw)
        terms = [t for t in data.get("terms", []) if isinstance(t, str) and t.strip()]
        domains = [d for d in data.get("domains", []) if d in DOMAINS]
    except (ValueError, AttributeError):
        terms, domains = [], []
    return {"terms": terms or [question], "domains": domains or ["manuscript"]}


def retrieve(graph, terms, levels):
    evidence, seen = [], set()
    for term in terms:
        for node in graph.find_nodes(term, levels):
            for edge, target in graph.neighbours(node["id"], levels):
                key = (edge["source"], edge["relationship"], edge["target"])
                if key not in seen:
                    seen.add(key)
                    evidence.append({"from": generalise_place(node, levels), "edge": edge,
                                     "to": generalise_place(target, levels)})
    return evidence


def coverage(evidence, wanted):
    """A domain counts as covered when some evidence edge touches a node of that domain."""
    have = {e["to"].get("domain") or e["from"].get("domain") or "manuscript" for e in evidence}
    return sorted(set(wanted) - have)


def answer(graph, llm, question, role="public"):
    levels = allowed_levels(role)
    p = plan(llm, question)
    evidence = retrieve(graph, p["terms"], levels)
    gaps = coverage(evidence, p["domains"])
    if not evidence:
        return {"answer": "No records available to this role match the question.",
                "citations": [], "gaps": gaps, "plan": p}
    facts = "\n".join(f'- {e["from"]["label"]} {e["edge"]["relationship"]} {e["to"]["label"]} '
                      f'[{e["edge"]["source_document"]} {e["edge"]["source_locator"]}]' for e in evidence)
    text = llm("Answer using only these facts and cite the bracketed sources. "
               f"Say if the facts are insufficient.\nFacts:\n{facts}\nQuestion: {question}")
    cites = sorted({(e["edge"]["source_document"], e["edge"]["source_locator"]) for e in evidence})
    return {"answer": text, "citations": cites, "gaps": gaps, "plan": p}
