// Neo4j 初始化脚本 - 完整数据模型
// 创建约束和索引

// ============ 约束（唯一性） ============

// Herb 约束
CREATE CONSTRAINT herb_id IF NOT EXISTS
FOR (h:Herb) REQUIRE h.id IS UNIQUE;

CREATE CONSTRAINT herb_name IF NOT EXISTS
FOR (h:Herb) REQUIRE h.name IS UNIQUE;

// Component 约束
CREATE CONSTRAINT component_id IF NOT EXISTS
FOR (c:Component) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT component_name IF NOT EXISTS
FOR (c:Component) REQUIRE c.name IS UNIQUE;

// Variant 约束
CREATE CONSTRAINT variant_id IF NOT EXISTS
FOR (v:Variant) REQUIRE v.id IS UNIQUE;

CREATE CONSTRAINT variant_name IF NOT EXISTS
FOR (v:Variant) REQUIRE v.name IS UNIQUE;

// Process 约束
CREATE CONSTRAINT process_id IF NOT EXISTS
FOR (p:Process) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT process_name IF NOT EXISTS
FOR (p:Process) REQUIRE p.name IS UNIQUE;

// Trait 约束
CREATE CONSTRAINT trait_id IF NOT EXISTS
FOR (t:Trait) REQUIRE t.id IS UNIQUE;

CREATE CONSTRAINT trait_name IF NOT EXISTS
FOR (t:Trait) REQUIRE t.name IS UNIQUE;

// TimePoint 约束
CREATE CONSTRAINT timepoint_id IF NOT EXISTS
FOR (t:TimePoint) REQUIRE t.id IS UNIQUE;

// Efficacy 约束
CREATE CONSTRAINT efficacy_id IF NOT EXISTS
FOR (e:Efficacy) REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT efficacy_name IF NOT EXISTS
FOR (e:Efficacy) REQUIRE e.name IS UNIQUE;

// Flavor 约束
CREATE CONSTRAINT flavor_id IF NOT EXISTS
FOR (f:Flavor) REQUIRE f.id IS UNIQUE;

CREATE CONSTRAINT flavor_name IF NOT EXISTS
FOR (f:Flavor) REQUIRE f.name IS UNIQUE;

// Meridian 约束
CREATE CONSTRAINT meridian_id IF NOT EXISTS
FOR (m:Meridian) REQUIRE m.id IS UNIQUE;

CREATE CONSTRAINT meridian_name IF NOT EXISTS
FOR (m:Meridian) REQUIRE m.name IS UNIQUE;

// Disease 约束
CREATE CONSTRAINT disease_id IF NOT EXISTS
FOR (d:Disease) REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT disease_name IF NOT EXISTS
FOR (d:Disease) REQUIRE d.name IS UNIQUE;

// ============ 索引 ============

// 名称索引（加速按名称查询）
CREATE INDEX herb_name_index IF NOT EXISTS
FOR (h:Herb) ON (h.name);

CREATE INDEX component_name_index IF NOT EXISTS
FOR (c:Component) ON (c.name);

CREATE INDEX variant_name_index IF NOT EXISTS
FOR (v:Variant) ON (v.name);

CREATE INDEX variant_parent_herb_index IF NOT EXISTS
FOR (v:Variant) ON (v.parent_herb);

CREATE INDEX process_name_index IF NOT EXISTS
FOR (p:Process) ON (p.name);

CREATE INDEX trait_name_index IF NOT EXISTS
FOR (t:Trait) ON (t.name);

CREATE INDEX trait_category_index IF NOT EXISTS
FOR (t:Trait) ON (t.category);

CREATE INDEX timepoint_years_index IF NOT EXISTS
FOR (t:TimePoint) ON (t.years);

CREATE INDEX efficacy_name_index IF NOT EXISTS
FOR (e:Efficacy) ON (e.name);

CREATE INDEX flavor_name_index IF NOT EXISTS
FOR (f:Flavor) ON (f.name);

CREATE INDEX meridian_name_index IF NOT EXISTS
FOR (m:Meridian) ON (m.name);

CREATE INDEX disease_name_index IF NOT EXISTS
FOR (d:Disease) ON (d.name);

// 状态索引（加速按验证状态查询）
CREATE INDEX herb_status_index IF NOT EXISTS
FOR (h:Herb) ON (h.status);

CREATE INDEX component_status_index IF NOT EXISTS
FOR (c:Component) ON (c.status);

CREATE INDEX variant_status_index IF NOT EXISTS
FOR (v:Variant) ON (v.status);

CREATE INDEX process_status_index IF NOT EXISTS
FOR (p:Process) ON (p.status);

CREATE INDEX trait_status_index IF NOT EXISTS
FOR (t:Trait) ON (t.status);

CREATE INDEX efficacy_status_index IF NOT EXISTS
FOR (e:Efficacy) ON (e.status);

CREATE INDEX flavor_status_index IF NOT EXISTS
FOR (f:Flavor) ON (f.status);

CREATE INDEX meridian_status_index IF NOT EXISTS
FOR (m:Meridian) ON (m.status);

CREATE INDEX disease_status_index IF NOT EXISTS
FOR (d:Disease) ON (d.status);

// 关系状态索引
CREATE INDEX relationship_status_index IF NOT EXISTS
FOR ()-[r]->() ON (r.status);

// 来源索引
CREATE INDEX herb_source_index IF NOT EXISTS
FOR (h:Herb) ON (h.source);

CREATE INDEX component_source_index IF NOT EXISTS
FOR (c:Component) ON (c.source);

CREATE INDEX variant_source_index IF NOT EXISTS
FOR (v:Variant) ON (v.source);

// ============ 复合索引 ============

// 药材-品种联合索引
CREATE INDEX variant_parent_status_index IF NOT EXISTS
FOR (v:Variant) ON (v.parent_herb, v.status);

// 成分-含量索引
CREATE INDEX contains_quantity_index IF NOT EXISTS
FOR ()-[r:CONTAINS]->() ON (r.quantity);

// 性状-年份范围索引
CREATE INDEX has_trait_year_range_index IF NOT EXISTS
FOR ()-[r:HAS_TRAIT]->() ON (r.year_range);
