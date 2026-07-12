"""
ner_pipeline.py — Tier-1 NER/RE extraction for the Aksum Knowledge Graph.

Approach: gazetteer + regex (no trained model).
Run over plain-text versions of the four source documents and write
matches to nodes.csv (entities) and asserted_edges.csv (relations).

Usage
-----
    python ner_pipeline.py --input <text_file_or_dir> --out_dir publication/

Dependencies: standard library only (csv, re, pathlib, argparse, json).
"""

import argparse
import csv
import json
import pathlib
import re
import sys
from collections import defaultdict
from typing import Generator


# ---------------------------------------------------------------------------
# 1. Gazetteers
# ---------------------------------------------------------------------------

PLACE_GAZETTEER: dict[str, str] = {
    # canonical label  : node_id
    "Aksum": "place_aksum",
    "Axum": "place_aksum",
    "Adulis": "place_adulis",
    "Beta Giyorgis": "place_beta_giyorgis",
    "Gobedra": "place_gobedra",
    "Matara": "place_matara",
    "Yeha": "place_yeha",
    "Hawulti": "place_hawulti",
    "Hawulti-Melazo": "place_hawulti",
    "Dungur": "place_dungur",
    "Mezber": "place_mezber",
    "Ona Nagast": "place_ona_nagast",
    "Nefas Mawcha": "place_nefas_mawcha",
    "Enda Mikael": "place_enda_mikael",
    "Northern Stelae Field": "place_stele_park",
    "Stelae Park": "place_stele_park",
    "Tigray": "place_tigray",
    "Eritrea": "place_eritrea",
    "Mai Shum": "place_mai_shum",
}

PERSON_GAZETTEER: dict[str, str] = {
    "Ezana": "person_ezana",
    "King Ezana": "person_ezana",
    "Kaleb": "person_kaleb",
    "King Kaleb": "person_kaleb",
    "Endubis": "person_endubis",
    "Phillipson": "person_phillipson_d",
    "D.W. Phillipson": "person_phillipson_d",
    "D. W. Phillipson": "person_phillipson_d",
    "David Phillipson": "person_phillipson_d",
    "Fattovich": "person_fattovich",
    "R. Fattovich": "person_fattovich",
    "Sernicola": "person_sernicola",
    "L. Sernicola": "person_sernicola",
    "Bard": "person_bard",
    "K.A. Bard": "person_bard",
    "K. A. Bard": "person_bard",
}

PERIOD_GAZETTEER: dict[str, str] = {
    "Pre-Aksumite": "period_pre_aksumite",
    "pre-Aksumite": "period_pre_aksumite",
    "pre-aksumite": "period_pre_aksumite",
    "Proto-Aksumite": "period_proto_aksumite",
    "proto-Aksumite": "period_proto_aksumite",
    "Early Aksumite": "period_early_aksumite",
    "early Aksumite": "period_early_aksumite",
    "Classic Aksumite": "period_classic_aksumite",
    "classic Aksumite": "period_classic_aksumite",
    "Late Aksumite": "period_late_aksumite",
    "late Aksumite": "period_late_aksumite",
    "Post-Aksumite": "period_post_aksumite",
    "post-Aksumite": "period_post_aksumite",
    "Aksumite period": "period_aksumite",
    "Aksumite Kingdom": "period_aksumite",
}

OBJECT_GAZETTEER: dict[str, str] = {
    "Stele 1": "object_stele_1",
    "Great Stele": "object_stele_1",
    "Stele 2": "object_stele_2",
    "Stele 3": "object_stele_3",
    "Ezana Inscription": "object_ezana_inscription",
    "trilingual inscription": "object_ezana_inscription",
    "Endubis coin": "object_coin_endubis",
    "Endubis gold coin": "object_coin_endubis",
    "Ezana coin": "object_coin_ezana",
    "Aksumite fine ware": "object_aksumite_pottery",
    "fine ware": "object_aksumite_pottery",
    "lithics": "object_lithics_beta",
    "iron slag": "object_iron_slag",
    "glass beads": "object_glass_beads",
    "bronze lamp": "object_bronze_lamp",
}

ARCH_GAZETTEER: dict[str, str] = {
    "Mausoleum": "arch_mausoleum",
    "Tomb of Brick Arches": "arch_mausoleum",
    "Dungur palace": "arch_dungur_palace",
    "St. Mary of Zion": "arch_church_maryam",
    "Church of Zion": "arch_church_maryam",
    "Beta Giyorgis terrace": "arch_beta_giyorgis_terrace",
    "terrace complex": "arch_beta_giyorgis_terrace",
    "Ona Nagast platform": "arch_platform_ona_nagast",
    "Tomb of Kaleb": "arch_tomb_kaleb",
}

# Combine all gazetteers for co-mention detection
ALL_GAZETTEERS: list[dict[str, str]] = [
    PLACE_GAZETTEER,
    PERSON_GAZETTEER,
    PERIOD_GAZETTEER,
    OBJECT_GAZETTEER,
    ARCH_GAZETTEER,
]

# Build a single flat lookup: surface form -> node_id
SURFACE_TO_NODE: dict[str, str] = {}
for g in ALL_GAZETTEERS:
    SURFACE_TO_NODE.update(g)

# Radiocarbon lab-number pattern (OxA-, Beta-, GrN-, AA-, etc.)
C14_PATTERN = re.compile(
    r"\b(OxA|Beta|GrN|AA|Wk|GX|UB|QL|GAK|ISGS|I|SRR|UtC|Ua|TL|VERA|ETH)"
    r"[-‐]\d{3,6}\b"
)


# ---------------------------------------------------------------------------
# 2. Relation patterns (regex on sentence text after entity detection)
# ---------------------------------------------------------------------------

# Each pattern: (compiled_re, relation_label, crm_property, source_role, target_role)
# source_role / target_role = 'place' | 'object' | 'person' | 'period' | 'any'
RELATION_PATTERNS: list[tuple] = [
    (
        re.compile(r"\bfound\s+(?:in|at|within)\b", re.I),
        "found at",
        "P53_has_former_or_current_location",
        "object",
        "place",
    ),
    (
        re.compile(r"\brecovered\s+from\b", re.I),
        "found at",
        "P53_has_former_or_current_location",
        "object",
        "place",
    ),
    (
        re.compile(r"\bexcavated\s+(?:by|at)\b", re.I),
        "excavated by",
        "P14i_performed",
        "place",
        "person",
    ),
    (
        re.compile(r"\bdirected\s+by\b", re.I),
        "excavated by",
        "P14i_performed",
        "place",
        "person",
    ),
    (
        re.compile(r"\bdated\s+to\b", re.I),
        "dated to",
        "P4_has_time-span",
        "any",
        "period",
    ),
    (
        re.compile(r"\bassigned\s+to\b", re.I),
        "dated to",
        "P4_has_time-span",
        "any",
        "period",
    ),
    (
        re.compile(r"\blocated\s+(?:in|at|within)\b", re.I),
        "located at",
        "P53_has_former_or_current_location",
        "any",
        "place",
    ),
    (
        re.compile(r"\bsituated\s+(?:in|at)\b", re.I),
        "located at",
        "P53_has_former_or_current_location",
        "any",
        "place",
    ),
    (
        re.compile(r"\breigned\s+(?:during|in)\b", re.I),
        "reigned during",
        "P4_has_time-span",
        "person",
        "period",
    ),
    (
        re.compile(r"\battributed\s+to\b", re.I),
        "attributed to",
        "P14i_performed",
        "any",
        "person",
    ),
]


# ---------------------------------------------------------------------------
# 3. Sentence splitter (simple — adequate for well-structured academic text)
# ---------------------------------------------------------------------------

def split_sentences(text: str) -> Generator[str, None, None]:
    """Yield sentences split on '. ', '! ', '? ' boundaries."""
    # Collapse whitespace / newlines first
    text = re.sub(r"\s+", " ", text).strip()
    for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text):
        if sentence.strip():
            yield sentence.strip()


# ---------------------------------------------------------------------------
# 4. Entity detection in a sentence
# ---------------------------------------------------------------------------

def detect_entities(sentence: str) -> list[str]:
    """Return list of node_ids mentioned in sentence."""
    found: list[str] = []
    seen_ids: set[str] = set()

    # Sort surface forms longest-first to prefer multi-word matches.
    # Use word-boundary matching (\b) to avoid substring false positives
    # (e.g. "Aksum" matching inside "Aksumite").
    for surface in sorted(SURFACE_TO_NODE.keys(), key=len, reverse=True):
        pattern = re.compile(r"\b" + re.escape(surface) + r"\b", re.I)
        if pattern.search(sentence):
            nid = SURFACE_TO_NODE[surface]
            if nid not in seen_ids:
                found.append(nid)
                seen_ids.add(nid)

    # Radiocarbon lab numbers
    for m in C14_PATTERN.finditer(sentence):
        lab_num = m.group(0)
        # Normalise to a slug; keep as a note if not in gazetteer
        slug = "c14_" + lab_num.lower().replace("-", "_")
        if slug not in seen_ids:
            found.append(slug)
            seen_ids.add(slug)

    return found


# ---------------------------------------------------------------------------
# 5. Relation extraction within a sentence
# ---------------------------------------------------------------------------

def _entity_type(node_id: str) -> str:
    prefix = node_id.split("_")[0]
    if prefix == "place":
        return "place"
    if prefix == "person":
        return "person"
    if prefix in ("period",):
        return "period"
    if prefix in ("object",):
        return "object"
    if prefix in ("arch",):
        return "architectural_feature"
    if prefix in ("c14",):
        return "radiocarbon"
    return "any"


def extract_relations(
    sentence: str,
    entity_ids: list[str],
    source_id: str,
    page_ref: str,
    edge_counter: list[int],
) -> list[dict]:
    """Attempt to extract typed relations from a sentence."""
    edges: list[dict] = []
    if len(entity_ids) < 2:
        return edges

    for pattern, rel_label, crm_prop, src_role, tgt_role in RELATION_PATTERNS:
        if not pattern.search(sentence):
            continue
        # Heuristic: first matched entity is source, second is target
        # This is a Tier-1 approximation — see methods_statement.md
        for i, src in enumerate(entity_ids):
            src_type = _entity_type(src)
            if src_role != "any" and src_type != src_role:
                continue
            for tgt in entity_ids[i + 1 :]:
                tgt_type = _entity_type(tgt)
                if tgt_role != "any" and tgt_type != tgt_role:
                    continue
                edge_counter[0] += 1
                edges.append(
                    {
                        "edge_id": f"auto_{edge_counter[0]:04d}",
                        "source_node_id": src,
                        "target_node_id": tgt,
                        "relation_type": crm_prop,
                        "relation_label": rel_label,
                        "evidence_type": "automated",
                        "source": source_id,
                        "page_ref": page_ref,
                        "extraction_method": "regex_match",
                        "notes": f"sentence: {sentence[:120]}",
                    }
                )
    return edges


# ---------------------------------------------------------------------------
# 6. Co-mention (candidate) extraction
# ---------------------------------------------------------------------------

def extract_comentions(
    sentence: str,
    entity_ids: list[str],
    source_id: str,
    page_ref: str,
    co_counts: dict,
) -> None:
    """Accumulate co-mention counts for candidate edge generation."""
    if len(entity_ids) < 2:
        return
    for i, a in enumerate(entity_ids):
        for b in entity_ids[i + 1 :]:
            key = (min(a, b), max(a, b), source_id)
            if key not in co_counts:
                co_counts[key] = {
                    "count": 0,
                    "page_ref": page_ref,
                    "sentence_context": sentence[:160],
                }
            co_counts[key]["count"] += 1


# ---------------------------------------------------------------------------
# 7. Page-number inference (simple heuristic for paginated plain text)
# ---------------------------------------------------------------------------

PAGE_MARKER = re.compile(r"^\s*[–\-—]\s*(\d+)\s*[–\-—]\s*$|^\s*(\d+)\s*$")


def infer_page(line: str, current_page: list[int]) -> None:
    """Update current_page[0] if line looks like a page number."""
    m = PAGE_MARKER.match(line.strip())
    if m:
        pg = int(m.group(1) or m.group(2))
        if 1 <= pg <= 2000:
            current_page[0] = pg


# ---------------------------------------------------------------------------
# 8. Main processing loop
# ---------------------------------------------------------------------------

def process_file(
    path: pathlib.Path,
    source_id: str,
    edge_counter: list[int],
    co_counts: dict,
) -> tuple[list[dict], list[dict]]:
    """
    Process one plain-text source file.
    Returns (asserted_edges, new_node_defs).
    New nodes are only returned for radiocarbon lab numbers not in the gazetteer.
    """
    asserted: list[dict] = []
    new_nodes: list[dict] = []
    seen_lab_nums: set[str] = set()

    current_page: list[int] = [0]
    text = path.read_text(encoding="utf-8", errors="replace")

    for line in text.splitlines():
        infer_page(line, current_page)

    for sentence in split_sentences(text):
        page_ref = f"p.{current_page[0]}" if current_page[0] else "p.?"
        entity_ids = detect_entities(sentence)

        # Register previously-unseen radiocarbon lab numbers as new nodes
        for nid in entity_ids:
            if nid.startswith("c14_") and nid not in SURFACE_TO_NODE.values():
                lab_raw = nid.replace("c14_", "").upper().replace("_", "-")
                if lab_raw not in seen_lab_nums:
                    seen_lab_nums.add(lab_raw)
                    new_nodes.append(
                        {
                            "node_id": nid,
                            "label": f"{lab_raw} (auto-detected)",
                            "crm_class": "E16_Measurement",
                            "entity_type": "radiocarbon",
                            "source": source_id,
                            "page_ref": page_ref,
                            "confidence": "automated",
                            "bp_age": "",
                            "cal_68pct": "",
                            "cal_95pct": "",
                            "lab_material": "",
                            "notes": "Auto-detected lab number; BP age and calibration not yet extracted",
                        }
                    )

        asserted.extend(
            extract_relations(
                sentence, entity_ids, source_id, page_ref, edge_counter
            )
        )
        extract_comentions(sentence, entity_ids, source_id, page_ref, co_counts)

    return asserted, new_nodes


# ---------------------------------------------------------------------------
# 9. CLI entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Tier-1 NER/RE pipeline for the Aksum Knowledge Graph"
    )
    p.add_argument(
        "--input",
        required=True,
        help="Path to a plain-text file or directory of plain-text files",
    )
    p.add_argument(
        "--out_dir",
        default="publication",
        help="Output directory for CSV files (default: publication/)",
    )
    p.add_argument(
        "--source_map",
        default=None,
        help=(
            "JSON file mapping filename stems to source IDs "
            "(e.g. {'phillipson_2011': 'phillipson_2011'}). "
            "If omitted, the filename stem is used as the source ID."
        ),
    )
    p.add_argument(
        "--candidate_threshold",
        type=int,
        default=1,
        help="Minimum co-mention count for a candidate edge to be written (default: 1)",
    )
    p.add_argument(
        "--append",
        action="store_true",
        help="Append to existing CSVs instead of overwriting",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    input_path = pathlib.Path(args.input)
    if input_path.is_dir():
        files = sorted(input_path.glob("*.txt"))
    elif input_path.is_file():
        files = [input_path]
    else:
        print(f"Error: {input_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    source_map: dict[str, str] = {}
    if args.source_map:
        source_map = json.loads(pathlib.Path(args.source_map).read_text())

    # Shared state
    edge_counter: list[int] = [0]
    co_counts: dict = {}

    all_asserted: list[dict] = []
    all_new_nodes: list[dict] = []

    for f in files:
        source_id = source_map.get(f.stem, f.stem)
        print(f"Processing {f.name} → source_id={source_id}")
        asserted, new_nodes = process_file(f, source_id, edge_counter, co_counts)
        all_asserted.extend(asserted)
        all_new_nodes.extend(new_nodes)
        print(f"  {len(asserted)} asserted edges, {len(new_nodes)} new nodes")

    # Deduplicate asserted edges by (source, target, relation_type)
    seen_edges: set[tuple] = set()
    deduped_asserted: list[dict] = []
    for e in all_asserted:
        key = (e["source_node_id"], e["target_node_id"], e["relation_type"])
        if key not in seen_edges:
            seen_edges.add(key)
            deduped_asserted.append(e)

    # Build candidate edges from co-mention counts
    ce_counter = 0
    candidate_edges: list[dict] = []
    for (src, tgt, src_doc), info in sorted(co_counts.items()):
        if info["count"] >= args.candidate_threshold:
            ce_counter += 1
            candidate_edges.append(
                {
                    "edge_id": f"auto_ce_{ce_counter:04d}",
                    "source_node_id": src,
                    "target_node_id": tgt,
                    "co_mention_count": info["count"],
                    "source": src_doc,
                    "page_ref": info["page_ref"],
                    "sentence_context": info["sentence_context"],
                    "notes": "",
                }
            )

    # Write outputs
    mode = "a" if args.append else "w"
    _write_csv(
        out_dir / "asserted_edges_auto.csv",
        deduped_asserted,
        [
            "edge_id",
            "source_node_id",
            "target_node_id",
            "relation_type",
            "relation_label",
            "evidence_type",
            "source",
            "page_ref",
            "extraction_method",
            "notes",
        ],
        mode,
    )
    _write_csv(
        out_dir / "candidate_edges_auto.csv",
        candidate_edges,
        [
            "edge_id",
            "source_node_id",
            "target_node_id",
            "co_mention_count",
            "source",
            "page_ref",
            "sentence_context",
            "notes",
        ],
        mode,
    )
    if all_new_nodes:
        _write_csv(
            out_dir / "nodes_auto.csv",
            all_new_nodes,
            [
                "node_id",
                "label",
                "crm_class",
                "entity_type",
                "source",
                "page_ref",
                "confidence",
                "bp_age",
                "cal_68pct",
                "cal_95pct",
                "lab_material",
                "notes",
            ],
            mode,
        )

    print(
        f"\nDone. {len(deduped_asserted)} asserted edges, "
        f"{len(candidate_edges)} candidate edges, "
        f"{len(all_new_nodes)} new nodes written to {out_dir}/"
    )


def _write_csv(
    path: pathlib.Path, rows: list[dict], fieldnames: list[str], mode: str
) -> None:
    write_header = mode == "w" or not path.exists()
    with open(path, mode, newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(rows)
    print(f"  Written {len(rows)} rows → {path}")


if __name__ == "__main__":
    main()
