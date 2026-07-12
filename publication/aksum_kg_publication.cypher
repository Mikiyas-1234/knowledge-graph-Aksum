// ============================================================
// Aksum Archaeological Knowledge Graph — Neo4j Import Script
// Version 1.0  |  CC-BY-4.0 (derived graph data)
// ============================================================
// Usage: run against a fresh Neo4j 4.x / 5.x database.
//   :source aksum_kg_publication.cypher
// Or via cypher-shell:
//   cypher-shell -u neo4j -p <password> -f aksum_kg_publication.cypher
//
// After import, filter by status property:
//   MATCH (a)-[r {status:'asserted'}]->(b) RETURN a,r,b;
//   MATCH (a)-[r {status:'candidate'}]->(b) WHERE r.co_mention_count >= 3 RETURN a,r,b;
// ============================================================

// ------------------------------------------------------------
// 0. Constraints (idempotent — safe to re-run)
// ------------------------------------------------------------
CREATE CONSTRAINT aksum_node_id IF NOT EXISTS
  FOR (n:AksumEntity) REQUIRE n.node_id IS UNIQUE;

// ------------------------------------------------------------
// 1. Nodes
// ------------------------------------------------------------

// --- Places ---
MERGE (n:AksumEntity:Place {node_id: 'place_aksum'})
  SET n.label         = 'Aksum',
      n.crm_class     = 'E27_Site',
      n.entity_type   = 'place',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.30',
      n.confidence    = 'gold',
      n.notes         = 'Capital city of the Aksumite Kingdom; modern Axum in northern Ethiopia';

MERGE (n:AksumEntity:Place {node_id: 'place_adulis'})
  SET n.label         = 'Adulis',
      n.crm_class     = 'E27_Site',
      n.entity_type   = 'place',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.32',
      n.confidence    = 'gold',
      n.notes         = 'Principal Red Sea port; near modern Massawa, Eritrea';

MERGE (n:AksumEntity:Place {node_id: 'place_beta_giyorgis'})
  SET n.label         = 'Beta Giyorgis',
      n.crm_class     = 'E27_Site',
      n.entity_type   = 'place',
      n.source        = 'sernicola_2019',
      n.page_ref      = 'p.3',
      n.confidence    = 'gold',
      n.notes         = 'Hill site on western edge of Aksum; major multi-period occupation sequence';

MERGE (n:AksumEntity:Place {node_id: 'place_gobedra'})
  SET n.label         = 'Gobedra',
      n.crm_class     = 'E27_Site',
      n.entity_type   = 'place',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.33',
      n.confidence    = 'gold',
      n.notes         = 'Rockshelter site near Aksum; Pre-Aksumite and earlier occupation';

MERGE (n:AksumEntity:Place {node_id: 'place_matara'})
  SET n.label         = 'Matara',
      n.crm_class     = 'E27_Site',
      n.entity_type   = 'place',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.35',
      n.confidence    = 'gold',
      n.notes         = 'Major Aksumite site in Eritrea; excavated 1959–1965 by Anfray';

MERGE (n:AksumEntity:Place {node_id: 'place_yeha'})
  SET n.label         = 'Yeha',
      n.crm_class     = 'E27_Site',
      n.entity_type   = 'place',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.31',
      n.confidence    = 'gold',
      n.notes         = 'Pre-Aksumite site ca. 35 km northeast of Aksum; Temple of the Moon';

MERGE (n:AksumEntity:Place {node_id: 'place_hawulti'})
  SET n.label         = 'Hawulti-Melazo',
      n.crm_class     = 'E27_Site',
      n.entity_type   = 'place',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.34',
      n.confidence    = 'gold',
      n.notes         = 'Site near Aksum with early Aksumite material; stele and votive objects';

MERGE (n:AksumEntity:Place {node_id: 'place_dungur'})
  SET n.label         = 'Dungur',
      n.crm_class     = 'E27_Site',
      n.entity_type   = 'place',
      n.source        = 'phillipson_1997',
      n.page_ref      = 'p.47',
      n.confidence    = 'gold',
      n.notes         = 'Locality in western Aksum; site of the Dungur palace complex';

MERGE (n:AksumEntity:Place {node_id: 'place_mezber'})
  SET n.label         = 'Mezber',
      n.crm_class     = 'E27_Site',
      n.entity_type   = 'place',
      n.source        = 'sernicola_2019',
      n.page_ref      = 'p.8',
      n.confidence    = 'gold',
      n.notes         = 'Site in the Tigray highlands; Pre-Aksumite and early Aksumite occupation';

MERGE (n:AksumEntity:Place {node_id: 'place_ona_nagast'})
  SET n.label         = 'Ona Nagast',
      n.crm_class     = 'E27_Site',
      n.entity_type   = 'place',
      n.source        = 'sernicola_2019',
      n.page_ref      = 'p.5',
      n.confidence    = 'gold',
      n.notes         = 'Site near Beta Giyorgis; monumental platform structure';

MERGE (n:AksumEntity:Place {node_id: 'place_nefas_mawcha'})
  SET n.label         = 'Nefas Mawcha',
      n.crm_class     = 'E27_Site',
      n.entity_type   = 'place',
      n.source        = 'phillipson_1997',
      n.page_ref      = 'p.52',
      n.confidence    = 'gold',
      n.notes         = 'Location of the fallen Great Stele (Stele 1) in the Northern Stelae Field';

MERGE (n:AksumEntity:Place {node_id: 'place_enda_mikael'})
  SET n.label         = 'Enda Mikael',
      n.crm_class     = 'E27_Site',
      n.entity_type   = 'place',
      n.source        = 'phillipson_1997',
      n.page_ref      = 'p.53',
      n.confidence    = 'gold',
      n.notes         = 'Locality in Aksum with sub-surface architectural remains';

MERGE (n:AksumEntity:Place {node_id: 'place_stele_park'})
  SET n.label         = 'Northern Stelae Field',
      n.crm_class     = 'E27_Site',
      n.entity_type   = 'place',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.36',
      n.confidence    = 'gold',
      n.notes         = 'Monumental cemetery zone north of Aksum town centre; UNESCO World Heritage Site';

MERGE (n:AksumEntity:Place {node_id: 'place_tigray'})
  SET n.label         = 'Tigray region',
      n.crm_class     = 'E27_Site',
      n.entity_type   = 'place',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.30',
      n.confidence    = 'gold',
      n.notes         = 'Northern Ethiopian highland region; core territory of the Aksumite Kingdom';

MERGE (n:AksumEntity:Place {node_id: 'place_eritrea'})
  SET n.label         = 'Eritrea',
      n.crm_class     = 'E27_Site',
      n.entity_type   = 'place',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.30',
      n.confidence    = 'gold',
      n.notes         = 'Modern state; northern periphery of Aksumite territory';

MERGE (n:AksumEntity:Place {node_id: 'place_mai_shum'})
  SET n.label         = 'Mai Shum',
      n.crm_class     = 'E27_Site',
      n.entity_type   = 'place',
      n.source        = 'phillipson_1997',
      n.page_ref      = 'p.61',
      n.confidence    = 'gold',
      n.notes         = 'Locality in Aksum; site of a large rock-cut reservoir';

// --- Persons ---
MERGE (n:AksumEntity:Person {node_id: 'person_ezana'})
  SET n.label         = 'King Ezana',
      n.crm_class     = 'E21_Person',
      n.entity_type   = 'person',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.37',
      n.confidence    = 'gold',
      n.notes         = 'Aksumite king r. c. 325–360 CE; issued trilingual inscription; converted to Christianity';

MERGE (n:AksumEntity:Person {node_id: 'person_kaleb'})
  SET n.label         = 'King Kaleb',
      n.crm_class     = 'E21_Person',
      n.entity_type   = 'person',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.38',
      n.confidence    = 'gold',
      n.notes         = 'Aksumite king r. c. 514–540 CE; led campaign into South Arabia';

MERGE (n:AksumEntity:Person {node_id: 'person_endubis'})
  SET n.label         = 'King Endubis',
      n.crm_class     = 'E21_Person',
      n.entity_type   = 'person',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.36',
      n.confidence    = 'gold',
      n.notes         = 'Earliest Aksumite king known to have minted coins; c. late 3rd century CE';

MERGE (n:AksumEntity:Person {node_id: 'person_phillipson_d'})
  SET n.label         = 'David W. Phillipson',
      n.crm_class     = 'E21_Person',
      n.entity_type   = 'person',
      n.source        = 'phillipson_1997',
      n.page_ref      = 'p.1',
      n.confidence    = 'gold',
      n.notes         = 'British archaeologist; directed 1993–1997 BIEA excavations at Aksum';

MERGE (n:AksumEntity:Person {node_id: 'person_fattovich'})
  SET n.label         = 'Rodolfo Fattovich',
      n.crm_class     = 'E21_Person',
      n.entity_type   = 'person',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.33',
      n.confidence    = 'gold',
      n.notes         = 'Italian archaeologist; directed excavations at Mezber and Ona Nagast';

MERGE (n:AksumEntity:Person {node_id: 'person_sernicola'})
  SET n.label         = 'Luisa Sernicola',
      n.crm_class     = 'E21_Person',
      n.entity_type   = 'person',
      n.source        = 'sernicola_2019',
      n.page_ref      = 'p.1',
      n.confidence    = 'gold',
      n.notes         = 'Italian archaeologist; excavations at Beta Giyorgis and Ona Nagast';

MERGE (n:AksumEntity:Person {node_id: 'person_bard'})
  SET n.label         = 'Kathryn A. Bard',
      n.crm_class     = 'E21_Person',
      n.entity_type   = 'person',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.33',
      n.confidence    = 'gold',
      n.notes         = 'American archaeologist; co-director of Aksum-area survey and excavations';

// --- Periods ---
MERGE (n:AksumEntity:Period {node_id: 'period_pre_aksumite'})
  SET n.label         = 'Pre-Aksumite period',
      n.crm_class     = 'E4_Period',
      n.entity_type   = 'period',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.31',
      n.confidence    = 'gold',
      n.date_range    = 'c. 800–100 BCE',
      n.notes         = 'Characterised by South Arabian cultural influences; temple architecture at Yeha';

MERGE (n:AksumEntity:Period {node_id: 'period_proto_aksumite'})
  SET n.label         = 'Proto-Aksumite period',
      n.crm_class     = 'E4_Period',
      n.entity_type   = 'period',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.31',
      n.confidence    = 'gold',
      n.date_range    = 'c. 100 BCE–100 CE',
      n.notes         = 'Transitional phase; emergence of distinctly Aksumite material culture';

MERGE (n:AksumEntity:Period {node_id: 'period_early_aksumite'})
  SET n.label         = 'Early Aksumite period',
      n.crm_class     = 'E4_Period',
      n.entity_type   = 'period',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.32',
      n.confidence    = 'gold',
      n.date_range    = 'c. 100–350 CE',
      n.notes         = 'First coinage (Endubis); monumental stelae erected';

MERGE (n:AksumEntity:Period {node_id: 'period_classic_aksumite'})
  SET n.label         = 'Classic Aksumite period',
      n.crm_class     = 'E4_Period',
      n.entity_type   = 'period',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.37',
      n.confidence    = 'gold',
      n.date_range    = 'c. 350–550 CE',
      n.notes         = 'Apogee of Aksumite power; coinage of Ezana; Christianisation';

MERGE (n:AksumEntity:Period {node_id: 'period_late_aksumite'})
  SET n.label         = 'Late Aksumite period',
      n.crm_class     = 'E4_Period',
      n.entity_type   = 'period',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.38',
      n.confidence    = 'gold',
      n.date_range    = 'c. 550–700 CE',
      n.notes         = 'Aksumite power contracting; decline of Red Sea trade';

MERGE (n:AksumEntity:Period {node_id: 'period_aksumite'})
  SET n.label         = 'Aksumite period',
      n.crm_class     = 'E4_Period',
      n.entity_type   = 'period',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.30',
      n.confidence    = 'gold',
      n.date_range    = 'c. 1st–7th century CE',
      n.notes         = 'General label for the entire kingdom span';

MERGE (n:AksumEntity:Period {node_id: 'period_post_aksumite'})
  SET n.label         = 'Post-Aksumite period',
      n.crm_class     = 'E4_Period',
      n.entity_type   = 'period',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.39',
      n.confidence    = 'gold',
      n.date_range    = 'c. 700–1000 CE',
      n.notes         = 'Period following fragmentation of centralised Aksumite authority';

// --- Objects ---
MERGE (n:AksumEntity:Object {node_id: 'object_stele_1'})
  SET n.label         = 'Great Stele (Stele 1)',
      n.crm_class     = 'E22_Man-Made_Object',
      n.entity_type   = 'object',
      n.source        = 'phillipson_1997',
      n.page_ref      = 'p.55',
      n.confidence    = 'gold',
      n.notes         = 'Tallest Aksumite obelisk at c. 33 m; now fallen and broken';

MERGE (n:AksumEntity:Object {node_id: 'object_stele_2'})
  SET n.label         = 'Stele 2',
      n.crm_class     = 'E22_Man-Made_Object',
      n.entity_type   = 'object',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.36',
      n.confidence    = 'gold',
      n.notes         = 'Second-tallest obelisk; removed to Rome 1937; returned 2008';

MERGE (n:AksumEntity:Object {node_id: 'object_stele_3'})
  SET n.label         = 'Stele 3',
      n.crm_class     = 'E22_Man-Made_Object',
      n.entity_type   = 'object',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.36',
      n.confidence    = 'gold',
      n.notes         = 'Third-tallest obelisk still standing at Aksum; c. 21 m';

MERGE (n:AksumEntity:Object {node_id: 'object_ezana_inscription'})
  SET n.label         = 'Ezana Inscription',
      n.crm_class     = 'E22_Man-Made_Object',
      n.entity_type   = 'object',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.37',
      n.confidence    = 'gold',
      n.notes         = "Trilingual royal inscription (Ge'ez / Sabaean / Greek)";

MERGE (n:AksumEntity:Object {node_id: 'object_coin_endubis'})
  SET n.label         = 'Endubis gold coin',
      n.crm_class     = 'E22_Man-Made_Object',
      n.entity_type   = 'object',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.36',
      n.confidence    = 'gold',
      n.notes         = 'Earliest known Aksumite coinage type; c. late 3rd century CE';

MERGE (n:AksumEntity:Object {node_id: 'object_coin_ezana'})
  SET n.label         = 'Ezana coin (pre-Christian)',
      n.crm_class     = 'E22_Man-Made_Object',
      n.entity_type   = 'object',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.37',
      n.confidence    = 'gold',
      n.notes         = 'Bronze coin of Ezana bearing crescent-and-disc symbol';

MERGE (n:AksumEntity:Object {node_id: 'object_aksumite_pottery'})
  SET n.label         = 'Aksumite fine ware',
      n.crm_class     = 'E22_Man-Made_Object',
      n.entity_type   = 'object',
      n.source        = 'sernicola_2019',
      n.page_ref      = 'p.11',
      n.confidence    = 'gold',
      n.notes         = 'Handmade buff-ware ceramics from Beta Giyorgis excavation contexts';

MERGE (n:AksumEntity:Object {node_id: 'object_lithics_beta'})
  SET n.label         = 'Beta Giyorgis lithics',
      n.crm_class     = 'E22_Man-Made_Object',
      n.entity_type   = 'object',
      n.source        = 'sernicola_2019',
      n.page_ref      = 'p.6',
      n.confidence    = 'gold',
      n.notes         = 'Obsidian and chert knapped stone assemblage from Pre-Aksumite levels';

MERGE (n:AksumEntity:Object {node_id: 'object_iron_slag'})
  SET n.label         = 'Iron slag assemblage',
      n.crm_class     = 'E22_Man-Made_Object',
      n.entity_type   = 'object',
      n.source        = 'sernicola_2019',
      n.page_ref      = 'p.12',
      n.confidence    = 'gold',
      n.notes         = 'Iron-working debris from Aksumite activity surfaces at Ona Nagast';

MERGE (n:AksumEntity:Object {node_id: 'object_glass_beads'})
  SET n.label         = 'Glass bead assemblage',
      n.crm_class     = 'E22_Man-Made_Object',
      n.entity_type   = 'object',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.35',
      n.confidence    = 'gold',
      n.notes         = 'Mediterranean or South Asian import trade goods at Matara and Adulis';

MERGE (n:AksumEntity:Object {node_id: 'object_bronze_lamp'})
  SET n.label         = 'Aksumite bronze lamp',
      n.crm_class     = 'E22_Man-Made_Object',
      n.entity_type   = 'object',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.37',
      n.confidence    = 'gold',
      n.notes         = 'Cast bronze lamp of Aksumite type recovered from urban Aksum context';

// --- Architectural features ---
MERGE (n:AksumEntity:ArchitecturalFeature {node_id: 'arch_mausoleum'})
  SET n.label         = 'Mausoleum (Tomb of Brick Arches)',
      n.crm_class     = 'E25_Man-Made_Feature',
      n.entity_type   = 'architectural_feature',
      n.source        = 'phillipson_1997',
      n.page_ref      = 'p.57',
      n.confidence    = 'gold',
      n.notes         = 'Subterranean royal tomb complex beneath the Northern Stelae Field';

MERGE (n:AksumEntity:ArchitecturalFeature {node_id: 'arch_dungur_palace'})
  SET n.label         = 'Dungur palace',
      n.crm_class     = 'E25_Man-Made_Feature',
      n.entity_type   = 'architectural_feature',
      n.source        = 'phillipson_1997',
      n.page_ref      = 'p.47',
      n.confidence    = 'gold',
      n.notes         = 'Large multi-roomed stone structure; interpreted as elite residence c. 4th–6th century CE';

MERGE (n:AksumEntity:ArchitecturalFeature {node_id: 'arch_church_maryam'})
  SET n.label         = 'Church of St. Mary of Zion',
      n.crm_class     = 'E25_Man-Made_Feature',
      n.entity_type   = 'architectural_feature',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.38',
      n.confidence    = 'gold',
      n.notes         = 'Cathedral attributed to 4th-century construction under Ezana; rebuilt multiple times';

MERGE (n:AksumEntity:ArchitecturalFeature {node_id: 'arch_beta_giyorgis_terrace'})
  SET n.label         = 'Beta Giyorgis terrace complex',
      n.crm_class     = 'E25_Man-Made_Feature',
      n.entity_type   = 'architectural_feature',
      n.source        = 'sernicola_2019',
      n.page_ref      = 'p.4',
      n.confidence    = 'gold',
      n.notes         = 'Sequence of artificial terraces on Beta Giyorgis hill slopes; Pre-Aksumite to Aksumite';

MERGE (n:AksumEntity:ArchitecturalFeature {node_id: 'arch_platform_ona_nagast'})
  SET n.label         = 'Ona Nagast platform structure',
      n.crm_class     = 'E25_Man-Made_Feature',
      n.entity_type   = 'architectural_feature',
      n.source        = 'sernicola_2019',
      n.page_ref      = 'p.5',
      n.confidence    = 'gold',
      n.notes         = 'Monumental stone-built platform; possibly Proto-Aksumite ceremonial';

MERGE (n:AksumEntity:ArchitecturalFeature {node_id: 'arch_tomb_kaleb'})
  SET n.label         = 'Tomb of Kaleb and Gebre Meskel',
      n.crm_class     = 'E25_Man-Made_Feature',
      n.entity_type   = 'architectural_feature',
      n.source        = 'phillipson_2011',
      n.page_ref      = 'p.38',
      n.confidence    = 'gold',
      n.notes         = 'Rock-cut tomb complex north of Aksum; traditionally attributed to King Kaleb';

// --- Radiocarbon measurements ---
MERGE (n:AksumEntity:RadiocarbonMeasurement {node_id: 'c14_beta1_oxf'})
  SET n.label         = 'OxA-7846 charcoal Beta Giyorgis',
      n.crm_class     = 'E16_Measurement',
      n.entity_type   = 'radiocarbon',
      n.source        = 'phillipson_1997',
      n.page_ref      = 'p.615',
      n.confidence    = 'gold',
      n.lab_number    = 'OxA-7846',
      n.lab_material  = 'charcoal',
      n.bp_age        = '2150 ± 35',
      n.cal_68pct     = '200–120 BCE',
      n.cal_95pct     = '370–70 BCE',
      n.notes         = 'Layer 4, Beta Giyorgis; Proto-Aksumite context; calibrated IntCal20';

MERGE (n:AksumEntity:RadiocarbonMeasurement {node_id: 'c14_beta2_oxf'})
  SET n.label         = 'OxA-7847 charcoal Beta Giyorgis',
      n.crm_class     = 'E16_Measurement',
      n.entity_type   = 'radiocarbon',
      n.source        = 'phillipson_1997',
      n.page_ref      = 'p.615',
      n.confidence    = 'gold',
      n.lab_number    = 'OxA-7847',
      n.lab_material  = 'charcoal',
      n.bp_age        = '1750 ± 40',
      n.cal_68pct     = '240–330 CE',
      n.cal_95pct     = '210–390 CE',
      n.notes         = 'Layer 2, Beta Giyorgis; Early Aksumite context; calibrated IntCal20';

MERGE (n:AksumEntity:RadiocarbonMeasurement {node_id: 'c14_dungur_beta'})
  SET n.label         = 'Beta-95230 organic Dungur',
      n.crm_class     = 'E16_Measurement',
      n.entity_type   = 'radiocarbon',
      n.source        = 'phillipson_1997',
      n.page_ref      = 'p.617',
      n.confidence    = 'gold',
      n.lab_number    = 'Beta-95230',
      n.lab_material  = 'organic material',
      n.bp_age        = '1450 ± 35',
      n.cal_68pct     = '560–650 CE',
      n.cal_95pct     = '530–680 CE',
      n.notes         = 'Floor context, Dungur palace; Classic/Late Aksumite; calibrated IntCal20';

MERGE (n:AksumEntity:RadiocarbonMeasurement {node_id: 'c14_gobedra_1'})
  SET n.label         = 'OxA-1023 charcoal Gobedra',
      n.crm_class     = 'E16_Measurement',
      n.entity_type   = 'radiocarbon',
      n.source        = 'phillipson_1997',
      n.page_ref      = 'p.619',
      n.confidence    = 'gold',
      n.lab_number    = 'OxA-1023',
      n.lab_material  = 'charcoal',
      n.bp_age        = '2650 ± 45',
      n.cal_68pct     = '820–760 BCE',
      n.cal_95pct     = '900–690 BCE',
      n.notes         = 'Gobedra rockshelter; Pre-Aksumite Iron Age context; calibrated IntCal20';

// ------------------------------------------------------------
// 2. Asserted edges (status: 'asserted')
// ------------------------------------------------------------

MATCH (a:AksumEntity {node_id: 'place_aksum'}), (b:AksumEntity {node_id: 'place_tigray'})
MERGE (a)-[r:P89_FALLS_WITHIN {edge_id: 'ae_001'}]->(b)
  SET r.relation_label     = 'falls within',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.30',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'place_adulis'}), (b:AksumEntity {node_id: 'place_eritrea'})
MERGE (a)-[r:P89_FALLS_WITHIN {edge_id: 'ae_002'}]->(b)
  SET r.relation_label     = 'falls within',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.32',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'place_beta_giyorgis'}), (b:AksumEntity {node_id: 'place_aksum'})
MERGE (a)-[r:P89_FALLS_WITHIN {edge_id: 'ae_003'}]->(b)
  SET r.relation_label     = 'falls within',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'sernicola_2019',
      r.page_ref           = 'p.3',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'place_gobedra'}), (b:AksumEntity {node_id: 'place_aksum'})
MERGE (a)-[r:P89_FALLS_WITHIN {edge_id: 'ae_004'}]->(b)
  SET r.relation_label     = 'falls within',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.33',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'arch_dungur_palace'}), (b:AksumEntity {node_id: 'place_dungur'})
MERGE (a)-[r:P53_HAS_LOCATION {edge_id: 'ae_005'}]->(b)
  SET r.relation_label     = 'located at',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_1997',
      r.page_ref           = 'p.47',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'arch_mausoleum'}), (b:AksumEntity {node_id: 'place_stele_park'})
MERGE (a)-[r:P53_HAS_LOCATION {edge_id: 'ae_006'}]->(b)
  SET r.relation_label     = 'located at',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_1997',
      r.page_ref           = 'p.57',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'arch_church_maryam'}), (b:AksumEntity {node_id: 'place_aksum'})
MERGE (a)-[r:P53_HAS_LOCATION {edge_id: 'ae_007'}]->(b)
  SET r.relation_label     = 'located at',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.38',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'arch_tomb_kaleb'}), (b:AksumEntity {node_id: 'place_aksum'})
MERGE (a)-[r:P53_HAS_LOCATION {edge_id: 'ae_008'}]->(b)
  SET r.relation_label     = 'located at',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.38',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'arch_beta_giyorgis_terrace'}), (b:AksumEntity {node_id: 'place_beta_giyorgis'})
MERGE (a)-[r:P53_HAS_LOCATION {edge_id: 'ae_009'}]->(b)
  SET r.relation_label     = 'located at',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'sernicola_2019',
      r.page_ref           = 'p.4',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'arch_platform_ona_nagast'}), (b:AksumEntity {node_id: 'place_ona_nagast'})
MERGE (a)-[r:P53_HAS_LOCATION {edge_id: 'ae_010'}]->(b)
  SET r.relation_label     = 'located at',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'sernicola_2019',
      r.page_ref           = 'p.5',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'object_stele_1'}), (b:AksumEntity {node_id: 'place_stele_park'})
MERGE (a)-[r:P53_HAS_LOCATION {edge_id: 'ae_011'}]->(b)
  SET r.relation_label     = 'found at',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_1997',
      r.page_ref           = 'p.55',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'object_stele_2'}), (b:AksumEntity {node_id: 'place_stele_park'})
MERGE (a)-[r:P53_HAS_LOCATION {edge_id: 'ae_012'}]->(b)
  SET r.relation_label     = 'found at',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.36',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'object_stele_3'}), (b:AksumEntity {node_id: 'place_stele_park'})
MERGE (a)-[r:P53_HAS_LOCATION {edge_id: 'ae_013'}]->(b)
  SET r.relation_label     = 'found at',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.36',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'object_ezana_inscription'}), (b:AksumEntity {node_id: 'place_aksum'})
MERGE (a)-[r:P53_HAS_LOCATION {edge_id: 'ae_014'}]->(b)
  SET r.relation_label     = 'found at',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.37',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'person_ezana'}), (b:AksumEntity {node_id: 'period_classic_aksumite'})
MERGE (a)-[r:P4_HAS_TIME_SPAN {edge_id: 'ae_015'}]->(b)
  SET r.relation_label     = 'reigned during',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.37',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'person_kaleb'}), (b:AksumEntity {node_id: 'period_classic_aksumite'})
MERGE (a)-[r:P4_HAS_TIME_SPAN {edge_id: 'ae_016'}]->(b)
  SET r.relation_label     = 'reigned during',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.38',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'person_endubis'}), (b:AksumEntity {node_id: 'period_early_aksumite'})
MERGE (a)-[r:P4_HAS_TIME_SPAN {edge_id: 'ae_017'}]->(b)
  SET r.relation_label     = 'reigned during',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.36',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'object_coin_endubis'}), (b:AksumEntity {node_id: 'period_early_aksumite'})
MERGE (a)-[r:P4_HAS_TIME_SPAN {edge_id: 'ae_018'}]->(b)
  SET r.relation_label     = 'dated to',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.36',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'object_coin_ezana'}), (b:AksumEntity {node_id: 'period_classic_aksumite'})
MERGE (a)-[r:P4_HAS_TIME_SPAN {edge_id: 'ae_019'}]->(b)
  SET r.relation_label     = 'dated to',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.37',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'period_pre_aksumite'}), (b:AksumEntity {node_id: 'period_proto_aksumite'})
MERGE (a)-[r:PRECEDES {edge_id: 'ae_020'}]->(b)
  SET r.relation_label     = 'precedes',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.31',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'period_proto_aksumite'}), (b:AksumEntity {node_id: 'period_early_aksumite'})
MERGE (a)-[r:PRECEDES {edge_id: 'ae_021'}]->(b)
  SET r.relation_label     = 'precedes',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.31',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'period_early_aksumite'}), (b:AksumEntity {node_id: 'period_classic_aksumite'})
MERGE (a)-[r:PRECEDES {edge_id: 'ae_022'}]->(b)
  SET r.relation_label     = 'precedes',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.32',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'period_classic_aksumite'}), (b:AksumEntity {node_id: 'period_late_aksumite'})
MERGE (a)-[r:PRECEDES {edge_id: 'ae_023'}]->(b)
  SET r.relation_label     = 'precedes',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.37',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'place_beta_giyorgis'}), (b:AksumEntity {node_id: 'person_phillipson_d'})
MERGE (a)-[r:P14I_EXCAVATED_BY {edge_id: 'ae_024'}]->(b)
  SET r.relation_label     = 'excavated by',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_1997',
      r.page_ref           = 'p.1',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'place_dungur'}), (b:AksumEntity {node_id: 'person_phillipson_d'})
MERGE (a)-[r:P14I_EXCAVATED_BY {edge_id: 'ae_025'}]->(b)
  SET r.relation_label     = 'excavated by',
      r.status             = 'asserted',
      r.evidence_type      = 'asserted',
      r.source             = 'phillipson_1997',
      r.page_ref           = 'p.47',
      r.extraction_method  = 'hand_curated';

MATCH (a:AksumEntity {node_id: 'object_aksumite_pottery'}), (b:AksumEntity {node_id: 'place_beta_giyorgis'})
MERGE (a)-[r:P53_HAS_LOCATION {edge_id: 'ae_026'}]->(b)
  SET r.relation_label     = 'found at',
      r.status             = 'asserted',
      r.evidence_type      = 'automated',
      r.source             = 'sernicola_2019',
      r.page_ref           = 'p.11',
      r.extraction_method  = 'regex_match';

MATCH (a:AksumEntity {node_id: 'object_lithics_beta'}), (b:AksumEntity {node_id: 'place_beta_giyorgis'})
MERGE (a)-[r:P53_HAS_LOCATION {edge_id: 'ae_027'}]->(b)
  SET r.relation_label     = 'found at',
      r.status             = 'asserted',
      r.evidence_type      = 'automated',
      r.source             = 'sernicola_2019',
      r.page_ref           = 'p.6',
      r.extraction_method  = 'regex_match';

MATCH (a:AksumEntity {node_id: 'object_iron_slag'}), (b:AksumEntity {node_id: 'place_ona_nagast'})
MERGE (a)-[r:P53_HAS_LOCATION {edge_id: 'ae_028'}]->(b)
  SET r.relation_label     = 'found at',
      r.status             = 'asserted',
      r.evidence_type      = 'automated',
      r.source             = 'sernicola_2019',
      r.page_ref           = 'p.12',
      r.extraction_method  = 'regex_match';

MATCH (a:AksumEntity {node_id: 'object_glass_beads'}), (b:AksumEntity {node_id: 'place_matara'})
MERGE (a)-[r:P53_HAS_LOCATION {edge_id: 'ae_029'}]->(b)
  SET r.relation_label     = 'found at',
      r.status             = 'asserted',
      r.evidence_type      = 'automated',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.35',
      r.extraction_method  = 'regex_match';

MATCH (a:AksumEntity {node_id: 'place_beta_giyorgis'}), (b:AksumEntity {node_id: 'person_sernicola'})
MERGE (a)-[r:P14I_EXCAVATED_BY {edge_id: 'ae_030'}]->(b)
  SET r.relation_label     = 'excavated by',
      r.status             = 'asserted',
      r.evidence_type      = 'automated',
      r.source             = 'sernicola_2019',
      r.page_ref           = 'p.1',
      r.extraction_method  = 'regex_match';

MATCH (a:AksumEntity {node_id: 'place_ona_nagast'}), (b:AksumEntity {node_id: 'person_sernicola'})
MERGE (a)-[r:P14I_EXCAVATED_BY {edge_id: 'ae_031'}]->(b)
  SET r.relation_label     = 'excavated by',
      r.status             = 'asserted',
      r.evidence_type      = 'automated',
      r.source             = 'sernicola_2019',
      r.page_ref           = 'p.5',
      r.extraction_method  = 'regex_match';

MATCH (a:AksumEntity {node_id: 'place_mezber'}), (b:AksumEntity {node_id: 'person_fattovich'})
MERGE (a)-[r:P14I_EXCAVATED_BY {edge_id: 'ae_032'}]->(b)
  SET r.relation_label     = 'excavated by',
      r.status             = 'asserted',
      r.evidence_type      = 'automated',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.33',
      r.extraction_method  = 'regex_match';

MATCH (a:AksumEntity {node_id: 'c14_beta1_oxf'}), (b:AksumEntity {node_id: 'period_proto_aksumite'})
MERGE (a)-[r:P4_HAS_TIME_SPAN {edge_id: 'ae_033'}]->(b)
  SET r.relation_label     = 'dated to',
      r.status             = 'asserted',
      r.evidence_type      = 'automated',
      r.source             = 'phillipson_1997',
      r.page_ref           = 'p.615',
      r.extraction_method  = 'regex_match';

MATCH (a:AksumEntity {node_id: 'c14_dungur_beta'}), (b:AksumEntity {node_id: 'period_classic_aksumite'})
MERGE (a)-[r:P4_HAS_TIME_SPAN {edge_id: 'ae_034'}]->(b)
  SET r.relation_label     = 'dated to',
      r.status             = 'asserted',
      r.evidence_type      = 'automated',
      r.source             = 'phillipson_1997',
      r.page_ref           = 'p.617',
      r.extraction_method  = 'regex_match';

MATCH (a:AksumEntity {node_id: 'object_bronze_lamp'}), (b:AksumEntity {node_id: 'place_aksum'})
MERGE (a)-[r:P53_HAS_LOCATION {edge_id: 'ae_035'}]->(b)
  SET r.relation_label     = 'found at',
      r.status             = 'asserted',
      r.evidence_type      = 'automated',
      r.source             = 'phillipson_2011',
      r.page_ref           = 'p.37',
      r.extraction_method  = 'regex_match';

// ------------------------------------------------------------
// 3. Candidate edges (status: 'candidate')
// ------------------------------------------------------------

MATCH (a:AksumEntity {node_id: 'person_ezana'}), (b:AksumEntity {node_id: 'place_aksum'})
MERGE (a)-[r:CO_MENTIONED {edge_id: 'ce_001'}]->(b)
  SET r.status              = 'candidate',
      r.co_mention_count    = 4,
      r.source              = 'phillipson_2011',
      r.page_ref            = 'p.37',
      r.sentence_context    = 'Ezana ... Aksum ... inscription ... campaign';

MATCH (a:AksumEntity {node_id: 'person_kaleb'}), (b:AksumEntity {node_id: 'arch_church_maryam'})
MERGE (a)-[r:CO_MENTIONED {edge_id: 'ce_002'}]->(b)
  SET r.status              = 'candidate',
      r.co_mention_count    = 2,
      r.source              = 'phillipson_2011',
      r.page_ref            = 'p.38',
      r.sentence_context    = 'Kaleb ... church ... Zion ... construction';

MATCH (a:AksumEntity {node_id: 'object_stele_2'}), (b:AksumEntity {node_id: 'place_adulis'})
MERGE (a)-[r:CO_MENTIONED {edge_id: 'ce_003'}]->(b)
  SET r.status              = 'candidate',
      r.co_mention_count    = 2,
      r.source              = 'phillipson_2011',
      r.page_ref            = 'p.36',
      r.sentence_context    = 'stele ... Adulis ... Rome ... removed';

MATCH (a:AksumEntity {node_id: 'place_yeha'}), (b:AksumEntity {node_id: 'period_pre_aksumite'})
MERGE (a)-[r:CO_MENTIONED {edge_id: 'ce_004'}]->(b)
  SET r.status              = 'candidate',
      r.co_mention_count    = 3,
      r.source              = 'phillipson_2011',
      r.page_ref            = 'p.31',
      r.sentence_context    = 'Yeha ... Pre-Aksumite ... temple ... South Arabian';

MATCH (a:AksumEntity {node_id: 'place_hawulti'}), (b:AksumEntity {node_id: 'period_proto_aksumite'})
MERGE (a)-[r:CO_MENTIONED {edge_id: 'ce_005'}]->(b)
  SET r.status              = 'candidate',
      r.co_mention_count    = 2,
      r.source              = 'phillipson_2011',
      r.page_ref            = 'p.34',
      r.sentence_context    = 'Hawulti-Melazo ... early material ... transition';

MATCH (a:AksumEntity {node_id: 'object_aksumite_pottery'}), (b:AksumEntity {node_id: 'period_early_aksumite'})
MERGE (a)-[r:CO_MENTIONED {edge_id: 'ce_006'}]->(b)
  SET r.status              = 'candidate',
      r.co_mention_count    = 2,
      r.source              = 'sernicola_2019',
      r.page_ref            = 'p.11',
      r.sentence_context    = 'fine ware ... early Aksumite ... stratum';

MATCH (a:AksumEntity {node_id: 'person_fattovich'}), (b:AksumEntity {node_id: 'place_matara'})
MERGE (a)-[r:CO_MENTIONED {edge_id: 'ce_007'}]->(b)
  SET r.status              = 'candidate',
      r.co_mention_count    = 2,
      r.source              = 'phillipson_2011',
      r.page_ref            = 'p.33',
      r.sentence_context    = 'Fattovich ... Matara ... survey ... excavation';

MATCH (a:AksumEntity {node_id: 'place_mezber'}), (b:AksumEntity {node_id: 'period_proto_aksumite'})
MERGE (a)-[r:CO_MENTIONED {edge_id: 'ce_008'}]->(b)
  SET r.status              = 'candidate',
      r.co_mention_count    = 2,
      r.source              = 'sernicola_2019',
      r.page_ref            = 'p.8',
      r.sentence_context    = 'Mezber ... Proto-Aksumite ... levels ... ceramics';

MATCH (a:AksumEntity {node_id: 'object_glass_beads'}), (b:AksumEntity {node_id: 'place_adulis'})
MERGE (a)-[r:CO_MENTIONED {edge_id: 'ce_009'}]->(b)
  SET r.status              = 'candidate',
      r.co_mention_count    = 2,
      r.source              = 'phillipson_2011',
      r.page_ref            = 'p.35',
      r.sentence_context    = 'glass beads ... Adulis ... trade ... Mediterranean';

MATCH (a:AksumEntity {node_id: 'arch_dungur_palace'}), (b:AksumEntity {node_id: 'person_kaleb'})
MERGE (a)-[r:CO_MENTIONED {edge_id: 'ce_010'}]->(b)
  SET r.status              = 'candidate',
      r.co_mention_count    = 1,
      r.source              = 'phillipson_1997',
      r.page_ref            = 'p.47',
      r.sentence_context    = 'Dungur palace ... Kaleb ... 6th century ... royal';

MATCH (a:AksumEntity {node_id: 'place_gobedra'}), (b:AksumEntity {node_id: 'period_pre_aksumite'})
MERGE (a)-[r:CO_MENTIONED {edge_id: 'ce_011'}]->(b)
  SET r.status              = 'candidate',
      r.co_mention_count    = 3,
      r.source              = 'phillipson_2011',
      r.page_ref            = 'p.33',
      r.sentence_context    = 'Gobedra ... rockshelter ... pre-Aksumite ... Iron Age';

MATCH (a:AksumEntity {node_id: 'arch_beta_giyorgis_terrace'}), (b:AksumEntity {node_id: 'period_proto_aksumite'})
MERGE (a)-[r:CO_MENTIONED {edge_id: 'ce_012'}]->(b)
  SET r.status              = 'candidate',
      r.co_mention_count    = 2,
      r.source              = 'sernicola_2019',
      r.page_ref            = 'p.4',
      r.sentence_context    = 'terrace ... Proto-Aksumite ... construction ... Beta Giyorgis';

MATCH (a:AksumEntity {node_id: 'object_iron_slag'}), (b:AksumEntity {node_id: 'place_beta_giyorgis'})
MERGE (a)-[r:CO_MENTIONED {edge_id: 'ce_013'}]->(b)
  SET r.status              = 'candidate',
      r.co_mention_count    = 1,
      r.source              = 'sernicola_2019',
      r.page_ref            = 'p.12',
      r.sentence_context    = 'iron slag ... Beta Giyorgis ... Ona Nagast ... working';

MATCH (a:AksumEntity {node_id: 'person_bard'}), (b:AksumEntity {node_id: 'place_mezber'})
MERGE (a)-[r:CO_MENTIONED {edge_id: 'ce_014'}]->(b)
  SET r.status              = 'candidate',
      r.co_mention_count    = 1,
      r.source              = 'phillipson_2011',
      r.page_ref            = 'p.33',
      r.sentence_context    = 'Bard ... Mezber ... Fattovich ... survey';

MATCH (a:AksumEntity {node_id: 'c14_beta2_oxf'}), (b:AksumEntity {node_id: 'place_beta_giyorgis'})
MERGE (a)-[r:CO_MENTIONED {edge_id: 'ce_015'}]->(b)
  SET r.status              = 'candidate',
      r.co_mention_count    = 2,
      r.source              = 'phillipson_1997',
      r.page_ref            = 'p.615',
      r.sentence_context    = 'OxA-7847 ... Beta Giyorgis ... layer 2 ... charcoal';

// End of import script
