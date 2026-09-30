"""Role-based access. Applied inside the query, before anything reaches the LLM."""
from .schema import PUBLIC, RESTRICTED

ROLE_LEVELS = {
    "public": {PUBLIC},
    "researcher": {PUBLIC},
    "custodian": {PUBLIC, RESTRICTED},
}


def allowed_levels(role: str) -> set:
    """Unknown roles get public only: fail closed."""
    return set(ROLE_LEVELS.get(role, {PUBLIC}))


def generalise_place(node: dict, levels: set) -> dict:
    """Drop precise coordinates unless the caller may see restricted data."""
    out = dict(node)
    if RESTRICTED not in levels:
        for key in ("lat", "lon", "coordinates"):
            out.pop(key, None)
    return out
