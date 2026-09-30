"""Adapter for Beta maṣāḥǝft manuscript descriptions (TEI XML, CC BY-SA 4.0).

Source: https://github.com/BetaMasaheft/Manuscripts
Each file describes one manuscript in a `msDesc`. Only structured, unambiguous fields are
mapped. Persons or places named in text without a Beta maṣāḥǝft `ref`, roles the graph has no
relationship for, and dates that are not plain years are counted in `stats`, never guessed.

Entities the files only *refer* to (repositories INS..., works LIT..., persons PRS..., places
LOC...) become nodes labelled by their Beta maṣāḥǝft id: their names live in the project's
Institutions / Works / Persons / Places repositories, which are not loaded here.
"""
import os
import re
import xml.etree.ElementTree as ET
from collections import Counter

from . import ingest
from .schema import PUBLIC, slugify

TEI = "{http://www.tei-c.org/ns/1.0}"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
NS = {"t": "http://www.tei-c.org/ns/1.0"}
SOURCE = "Beta masahaft Manuscripts (CC BY-SA 4.0)"
ROLE_TO_REL = {"scribe": "COPIED_BY", "patron": "COMMISSIONED_BY"}
_TYPE_BY_PREFIX = (("INS", "place", "institution"), ("LOC", "place", "place"),
                   ("LIT", "text", "work"), ("PRS", "person", "person"))


def _text(el):
    return " ".join("".join(el.itertext()).split()) if el is not None else ""


def _typed(ref):
    """'INS0336EAG' -> ('place', 'institution'). Unknown prefixes are not guessed."""
    for prefix, ntype, cat in _TYPE_BY_PREFIX:
        if ref.startswith(prefix):
            return ntype, cat
    return None


_ISO = re.compile(r"^(\d{4})(-\d\d){0,2}$")


def _year(value):
    """Plain year ('0530', '1600') or ISO date ('1800-10', '1919-05-24') -> year. Anything else -> None."""
    m = _ISO.match((value or "").strip())
    return int(m.group(1)) if m else None


def tei_to_graph(root, locator, nodes, edges, stats):
    """Adds one manuscript's nodes/edges. Returns False if the file has no msDesc."""
    ms = root.find(".//t:msDesc", NS)
    if ms is None:
        stats["skipped_no_msDesc"] += 1
        return False
    # Files are named by their Beta masahaft id; a few declare a different xml:id (e.g. Ewald7.xml says
    # "Ewald6"), so the filename is the identity and the mismatch is counted.
    bm_id = os.path.splitext(os.path.basename(locator))[0]
    if root.get(XML_ID) and root.get(XML_ID) != bm_id:
        stats["xml_id_differs_from_filename"] += 1
    if f"manuscript_{slugify(bm_id)}" in nodes:
        stats["duplicate_manuscript_id_skipped"] += 1
        return False
    ident = ms.find("t:msIdentifier", NS)
    names = []
    if ident is not None:
        names = [_text(i) for i in ident.findall("t:idno", NS)] + \
                [_text(i) for i in ident.findall("t:altIdentifier/t:idno", NS)]
    title = _text(root.find(".//t:titleStmt/t:title", NS)) or bm_id
    row = {"source_document": SOURCE, "source_locator": locator, "access_level": PUBLIC,
           "epistemic_provenance": "beta_masaheft_draft"}
    aliases = ";".join(dict.fromkeys(n for n in [bm_id, *names] if n and n != title))
    mid = ingest._node(nodes, "manuscript", title, row, "manuscript", aliases=aliases,
                       notes=f"Beta masahaft id {bm_id}", node_id=f"manuscript_{slugify(bm_id)}")

    def link(ref, rel, default_type=None, default_cat="", label=None):
        ref = (ref or "").split("#")[0].strip()
        if not ref:
            return
        typed = _typed(ref) or ((default_type, default_cat) if default_type else None)
        if typed is None:
            stats["unknown_ref_prefix"] += 1
            return
        ntype, cat = typed
        nid = ingest._node(nodes, ntype, label or ref, row, cat, notes="Beta masahaft id; name not loaded")
        if not any(e["source"] == mid and e["target"] == nid and e["relationship"] == rel for e in edges):
            ingest._edge(edges, mid, nid, rel, row)

    if ident is not None:
        repo = ident.find("t:repository", NS)  # may be an empty element: test `is not None`, not truthiness
        if repo is not None:
            link(repo.get("ref"), "HELD_AT")
    # Dates and places are taken from the manuscript's own history only; those of a part (msPart)
    # describe that part, not the whole manuscript, so they are counted, not attached.
    stats["part_dates_not_attached"] += len(ms.findall(".//t:msPart//t:history/t:origin/t:origDate", NS))
    for pn in ms.findall("t:history/t:origin/t:origPlace//t:placeName[@ref]", NS):
        link(pn.get("ref"), "PRODUCED_AT", "place", "place")
    for mat in ms.findall(".//t:supportDesc/t:support/t:material[@key]", NS):
        link(mat.get("key"), "MADE_OF", "material", "material")
    for title_el in ms.findall(".//t:msItem/t:title[@ref]", NS):
        link(title_el.get("ref"), "CONTAINS_TEXT", "text", "work")
    for od in ms.findall("t:history/t:origin/t:origDate", NS):
        lo = _year(od.get("notBefore") or od.get("from") or od.get("when"))
        hi = _year(od.get("notAfter") or od.get("to") or od.get("when"))
        if lo is None and hi is None:
            attrs = [k for k in ("notBefore", "notAfter", "from", "to", "when") if od.get(k)]
            stats["date_unreadable" if attrs else "date_element_empty"] += 1
            continue
        label = f"{lo if lo is not None else '?'}-{hi if hi is not None else '?'} CE"
        pid = ingest._node(nodes, "period", label, row, "date_range")
        if not any(e["source"] == mid and e["target"] == pid for e in edges):
            ingest._edge(edges, mid, pid, "DATED_TO", row)
    for pn in ms.iter(TEI + "persName"):
        roles = (pn.get("role") or "").split()
        ref = pn.get("ref")
        if not roles:
            continue
        for role in roles:
            rel = ROLE_TO_REL.get(role)
            if rel is None:
                stats[f"role_not_mapped:{role}"] += 1
            elif not ref:
                stats[f"{role}_without_ref"] += 1
            else:
                link(ref, rel, "person", "person")
    return True


def build_from_dir(root_dir, limit=None):
    """Walks a clone of the Manuscripts repository. Returns (nodes, edges, stats)."""
    nodes, edges, stats = {}, [], Counter()
    paths = []
    for d, dirs, files in os.walk(root_dir):
        dirs[:] = [x for x in dirs if not x.startswith(".")]
        paths += [os.path.join(d, f) for f in files if f.endswith(".xml")]
    for path in sorted(paths)[:limit]:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            stats["xml_parse_error"] += 1
            continue
        if root.tag != TEI + "TEI":
            stats["not_tei"] += 1
            continue
        if tei_to_graph(root, os.path.relpath(path, root_dir), nodes, edges, stats):
            stats["manuscripts"] += 1
    return nodes, edges, stats


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Build manuscript nodes/edges CSVs from a Beta masahaft Manuscripts clone")
    ap.add_argument("repo_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--names", nargs="*", default=[], help="clones of the Institutions, Persons and Works repositories")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    nodes, edges, stats = build_from_dir(args.repo_dir, args.limit)
    if args.names:
        from . import bm_names
        names = bm_names.load_names(args.names, stats)
        bm_names.apply_names(nodes, names, stats)
    ingest.write_graph(nodes, edges, args.out_dir)
    print(f"{len(nodes)} nodes, {len(edges)} edges")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
