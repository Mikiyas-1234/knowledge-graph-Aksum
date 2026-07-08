# CIDOC-CRM Class Glossary (for this dataset)

Every `cidoc_class` value in `nodes.csv` is one of the following. This file exists so the
data is self-documenting without needing the conversation that produced it.

| Code | Plain meaning | Used here for |
|---|---|---|
| `E53_Place` | A location, of any kind — a site, a region, a named spot within a site. | Aksum, Adulis, Seglamen, individual tombs, rock shelters. |
| `E21_Person` | An individual human being. | Kings (Ezana, Kaleb), researchers (Sernicola, Phillipson). |
| `E4_Period` | A named span of time with cultural meaning, not just a date range. | Pre-Aksumite, Aksumite, Zagwe. |
| `E22_Human-Made_Object` | A discrete, movable made object. | Coins, stelae, inscriptions, pottery. |
| `E25_Man-Made_Feature` | A built or modified feature that isn't a portable object (usually immovable, part of a structure). | Rooms, tombs-as-features, trenches. |
| `E16_Measurement` | A specific act of measuring something, with its own uncertainty. | Radiocarbon determinations (lab number, BP age, calibrated range). |

## Relationship (`relationship` column) → CIDOC property (`cidoc_property` column)

| relationship | cidoc_property | Plain meaning |
|---|---|---|
| `FOUND_AT` | `P7_took_place_at` | An object/event was found at this place. |
| `DATED_TO` / `DATES_CONTEXT_AT` | `P4_has_time-span` | This entity belongs to this period, or this measurement dates that context. |
| `EXCAVATED_BY` | `P14_carried_out_by` | This researcher carried out excavation here. |
| `MADE_OF` | `P45_consists_of` | The material composition of an object. |
| `LOCATED_AT` | `P53_has_former_or_current_location` | Spatial containment/location. |
| `PART_OF` | `P89_falls_within` | One place/area is part of another. |
| `RULED_BY` | `P14i_performed` | A place was under a ruler's authority. |
| `CREATED_BY_COMMISSION_OF` / `BEARS_NAME_OF` | `P94i_was_created_by` / `P138_represents` | Attribution of an inscribed/made object to a ruler's reign. |
| `PREDECESSOR_COMMUNITY_OF` | `P130_shows_features_of` | Interpretive continuity claim between two places over time. |
| `ASSOCIATED_WITH` | `P128_carries` / `P140i_was_attributed_by` | General or attributional association — always check the `notes` field, since this label covers both firm and contested claims. |
| `CO_OCCURS_WITH` (candidate file only) | — | No CRM property assigned — this is a raw co-mention signal, not a typed relation. See `candidate_edges.csv`. |
