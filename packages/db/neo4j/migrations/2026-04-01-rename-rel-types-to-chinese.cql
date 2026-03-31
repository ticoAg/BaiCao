// Rename legacy English relationship types to Chinese truth-source values.
MATCH (a)-[r:CONTAINS]->(b)
CREATE (a)-[r2:包含成分]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:EXTRACTED_FROM]->(b)
CREATE (a)-[r2:提取自]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:HAS_VARIANT]->(b)
CREATE (a)-[r2:具有品种]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:VARIANT_OF]->(b)
CREATE (a)-[r2:属于药材]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:PROCESSED_BY]->(b)
CREATE (a)-[r2:经过工艺]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:APPLIES_TO]->(b)
CREATE (a)-[r2:适用于]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:STORED_FOR]->(b)
CREATE (a)-[r2:储存时间]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:HAS_TRAIT]->(b)
CREATE (a)-[r2:具有性状]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:OBSERVED_IN]->(b)
CREATE (a)-[r2:观察于]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:HAS_EFFICACY]->(b)
CREATE (a)-[r2:具有功效]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:HAS_FLAVOR]->(b)
CREATE (a)-[r2:具有性味]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:ENTERS_MERIDIAN]->(b)
CREATE (a)-[r2:归于经脉]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:TREATS]->(b)
CREATE (a)-[r2:治疗病证]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:INTERACTS_WITH]->(b)
CREATE (a)-[r2:相互作用]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:SIMILAR_TO]->(b)
CREATE (a)-[r2:相似于]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:PARENT_OF]->(b)
CREATE (a)-[r2:父类]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:CHILD_OF]->(b)
CREATE (a)-[r2:子类]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:ORIGINATED_FROM]->(b)
CREATE (a)-[r2:来源于]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:DERIVED_FROM]->(b)
CREATE (a)-[r2:派生自]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:HAS_PREPARED_FORM]->(b)
CREATE (a)-[r2:具有饮片]->(b)
SET r2 = properties(r)
DELETE r;

MATCH (a)-[r:SUPPORTED_BY]->(b)
CREATE (a)-[r2:由证据支持]->(b)
SET r2 = properties(r)
DELETE r;
