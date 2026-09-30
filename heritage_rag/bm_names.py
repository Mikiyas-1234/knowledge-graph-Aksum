"""Names for Beta masahaft ids, from the project's Institutions, Persons and Works repositories.

The Manuscripts adapter labels referenced entities by id (e.g. LIT1560Gospel). This module reads the
three name repositories (same CC BY-SA 4.0 licence) and relabels those nodes: the Latin title becomes the
label; Geez-script and alternate names become aliases, so a search in either script finds the node.
Node ids never change. Placeholder records are skipped; ids with no file stay labelled by id.
"""
import os
import xml.etree.ElementTree as ET
from collections import Counter

from .betamasaheft import NS, TEI, _text
from .ocr import is_ethiopic

PLACEHOLDER_MARKERS = ("placeholder record",)


def _has_ethiopic(text):
    return any(is_ethiopic(c) for c in text)


def _names_from(root):
    """Label = first titleStmt title in Latin script (else the first title); everything else is an alias."""
    titles = [t for t in (_text(el) for el in root.findall(".//t:titleStmt/t:title", NS)) if t]
    latin = [t for t in titles if not _has_ethiopic(t)]
    label = (latin or titles or [""])[0]
    alts = list(titles)
    for tag in ("persName", "placeName", "title"):
        for el in root.findall(f".//t:text//t:{tag}", NS):
            if _text(el):
                alts.append(_text(el))
    return label, alts


def load_names(dirs, stats=None):
    """dirs: iterable of repository clone directories. Returns {bm_id: (label, [aliases])}."""
    stats = stats if stats is not None else Counter()
    names = {}
    for base in dirs:
        for d, subdirs, files in os.walk(base):
            subdirs[:] = [x for x in subdirs if not x.startswith(".")]
            for f in files:
                if not f.endswith(".xml"):
                    continue
                bm_id = f[:-4]
                try:
                    root = ET.parse(os.path.join(d, f)).getroot()
                except ET.ParseError:
                    stats["names_xml_parse_error"] += 1
                    continue
                if root.tag != TEI + "TEI":
                    continue
                title, alts = _names_from(root)
                if not title or any(m in title.lower() for m in PLACEHOLDER_MARKERS):
                    stats["names_placeholder_or_untitled"] += 1
                    continue
                aliases = [a for a in dict.fromkeys(alts) if a != title]
                names[bm_id] = (title, aliases)
                stats["names_loaded"] += 1
    return names


def apply_names(nodes, names, stats=None):
    """Relabels nodes whose label is still a Beta masahaft id. Returns the count relabelled."""
    stats = stats if stats is not None else Counter()
    done = 0
    for node in nodes.values():
        bm_id = node["label"]
        if bm_id not in names or node["category"] == "manuscript":
            continue
        title, alts = names[bm_id]
        node["label"] = title
        node["aliases"] = ";".join(dict.fromkeys([bm_id, *alts]))
        node["notes"] = f"Beta masahaft id {bm_id}; name from Beta masahaft name repositories"
        done += 1
    stats["nodes_relabelled"] += done
    return done
