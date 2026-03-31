// 陈皮完整图谱种子数据
// 执行方式：在 Neo4j Browser 中运行 或 `cypher-shell -u neo4j -p password < seed_chenpi.cql`

// ============ 1. 创建药材节点 ============

CREATE (h:Herb {
  id: randomUUID(),
  name: '陈皮',
  type: 'base',
  category: '理气药',
  source: '中国药典2020版',
  imported_at: datetime(),
  status: 'pending',
  verification_id: null,
  verified_by: null,
  verified_at: null
})

// ============ 2. 创建品种变种 ============

CREATE (v1:Variant {
  id: randomUUID(),
  name: '大红皮',
  parent_herb: '陈皮',
  description: '果实成熟时采收，剥取果皮，晒干或低温干燥。皮厚、色红、质柔软者为佳。',
  source: '中国药典2020版',
  imported_at: datetime(),
  status: 'pending',
  verification_id: null,
  verified_by: null,
  verified_at: null
})

CREATE (v2:Variant {
  id: randomUUID(),
  name: '二红皮',
  parent_herb: '陈皮',
  description: '果实未完全成熟时采收，色泽较淡，皮质较薄。',
  source: '中国药典2020版',
  imported_at: datetime(),
  status: 'pending',
  verification_id: null,
  verified_by: null,
  verified_at: null
})

CREATE (v3:Variant {
  id: randomUUID(),
  name: '青柑皮',
  parent_herb: '陈皮',
  description: '果实幼嫩时采收，外皮青绿色，皮薄质硬。',
  source: '中国药典2020版',
  imported_at: datetime(),
  status: 'pending',
  verification_id: null,
  verified_by: null,
  verified_at: null
})

// ============ 3. 创建成分节点 ============

CREATE (c1:Component {
  id: randomUUID(),
  name: '挥发油',
  chemical_formula: null,
  source: '中国药典2020版',
  imported_at: datetime(),
  status: 'pending',
  verification_id: null,
  verified_by: null,
  verified_at: null
})

CREATE (c2:Component {
  id: randomUUID(),
  name: '陈皮素',
  chemical_formula: 'C20H22O5',
  source: '中国药典2020版',
  imported_at: datetime(),
  status: 'pending',
  verification_id: null,
  verified_by: null,
  verified_at: null
})

CREATE (c3:Component {
  id: randomUUID(),
  name: '橙皮苷',
  chemical_formula: 'C27H32O14',
  source: '中国药典2020版',
  imported_at: datetime(),
  status: 'pending',
  verification_id: null,
  verified_by: null,
  verified_at: null
})

CREATE (c4:Component {
  id: randomUUID(),
  name: '川陈皮素',
  chemical_formula: 'C16H12O5',
  source: '现代研究',
  imported_at: datetime(),
  status: 'pending',
  verification_id: null,
  verified_by: null,
  verified_at: null
})

CREATE (c5:Component {
  id: randomUUID(),
  name: '柠檬烯',
  chemical_formula: 'C10H16',
  source: '现代研究',
  imported_at: datetime(),
  status: 'pending',
  verification_id: null,
  verified_by: null,
  verified_at: null
})

// ============ 4. 创建功效节点 ============

CREATE (e1:Efficacy {id: randomUUID(), name: '理气止痛', category: '功效', imported_at: datetime(), status: 'pending'})
CREATE (e2:Efficacy {id: randomUUID(), name: '健脾和胃', category: '功效', imported_at: datetime(), status: 'pending'})
CREATE (e3:Efficacy {id: randomUUID(), name: '燥湿化痰', category: '功效', imported_at: datetime(), status: 'pending'})
CREATE (e4:Efficacy {id: randomUUID(), name: '去痰平喘', category: '功效', imported_at: datetime(), status: 'pending'})
CREATE (e5:Efficacy {id: randomUUID(), name: '促进消化液分泌', category: '功效', imported_at: datetime(), status: 'pending'})
CREATE (e6:Efficacy {id: randomUUID(), name: '调整肠胃', category: '功效', imported_at: datetime(), status: 'pending'})
CREATE (e7:Efficacy {id: randomUUID(), name: '抗炎', category: '功效', imported_at: datetime(), status: 'pending'})
CREATE (e8:Efficacy {id: randomUUID(), name: '抗炎抗病毒', category: '功效', imported_at: datetime(), status: 'pending'})
CREATE (e9:Efficacy {id: randomUUID(), name: '扩张冠状动脉', category: '功效', imported_at: datetime(), status: 'pending'})
CREATE (e10:Efficacy {id: randomUUID(), name: '降血压', category: '功效', imported_at: datetime(), status: 'pending'})
CREATE (e11:Efficacy {id: randomUUID(), name: '维持心脏健康', category: '功效', imported_at: datetime(), status: 'pending'})

// ============ 5. 创建性味节点 ============

CREATE (f1:Flavor {id: randomUUID(), name: '辛', nature: '温', imported_at: datetime(), status: 'pending'})
CREATE (f2:Flavor {id: randomUUID(), name: '苦', nature: '温', imported_at: datetime(), status: 'pending'})

// ============ 6. 创建归经节点 ============

CREATE (m1:Meridian {id: randomUUID(), name: '肺经', imported_at: datetime(), status: 'pending'})
CREATE (m2:Meridian {id: randomUUID(), name: '脾经', imported_at: datetime(), status: 'pending'})

// ============ 7. 创建工艺节点 ============

CREATE (pr1:Process {
  id: randomUUID(),
  name: '沉化',
  description: '干皮晒干储存后，随着时间沉淀，色香味和内涵物质成分发生变化',
  min_duration: '3年',
  conditions: '干皮晒干储存，置于阴凉干燥处',
  imported_at: datetime(),
  status: 'pending',
  verification_id: null,
  verified_by: null,
  verified_at: null
})

// ============ 8. 创建性状节点 ============

CREATE (t1:Trait {
  id: randomUUID(),
  name: '外皮',
  category: 'external',
  description: '外表面棕红色或红黄色，有细皱纹和多数凹入的油点',
  observation_method: '肉眼观察',
  imported_at: datetime(),
  status: 'pending'
})

CREATE (t2:Trait {
  id: randomUUID(),
  name: '内囊',
  category: 'internal',
  description: '内表面黄白色或浅棕黄色，有细筋络',
  observation_method: '肉眼观察',
  imported_at: datetime(),
  status: 'pending'
})

CREATE (t3:Trait {
  id: randomUUID(),
  name: '油室',
  category: 'external',
  description: '表皮下的油点，是陈皮的重要特征',
  observation_method: '放大镜观察',
  imported_at: datetime(),
  status: 'pending'
})

CREATE (t4:Trait {
  id: randomUUID(),
  name: '油胞',
  category: 'external',
  description: '大型油室，特指陈皮上的大型油点',
  observation_method: '放大镜观察',
  imported_at: datetime(),
  status: 'pending'
})

// ============ 9. 创建时间点节点 ============

CREATE (tp1:TimePoint {id: randomUUID(), years: 1, description: '一年陈', quality_indicator: '皮较薄，辛味较重', imported_at: datetime(), status: 'pending'})
CREATE (tp2:TimePoint {id: randomUUID(), years: 3, description: '三年陈', quality_indicator: '开始呈现陈皮特有香气', imported_at: datetime(), status: 'pending'})
CREATE (tp3:TimePoint {id: randomUUID(), years: 5, description: '五年陈', quality_indicator: '香气浓郁，口感醇厚', imported_at: datetime(), status: 'pending'})
CREATE (tp4:TimePoint {id: randomUUID(), years: 10, description: '十年陈', quality_indicator: '陈香扑鼻，药效显著', imported_at: datetime(), status: 'pending'})

// ============ 10. 创建关系 ============

// 药材-品种关系
MATCH (h:Herb {name: '陈皮'})
MATCH (v1:Variant {name: '大红皮'})
MATCH (v2:Variant {name: '二红皮'})
MATCH (v3:Variant {name: '青柑皮'})
CREATE (h)-[:具有品种 {status: 'pending', verification_id: null}]->(v1)
CREATE (h)-[:具有品种 {status: 'pending', verification_id: null}]->(v2)
CREATE (h)-[:具有品种 {status: 'pending', verification_id: null}]->(v3)
CREATE (v1)-[:属于药材 {status: 'pending'}]->(h)
CREATE (v2)-[:属于药材 {status: 'pending'}]->(h)
CREATE (v3)-[:属于药材 {status: 'pending'}]->(h);

// 品种-性状关系
MATCH (v1:Variant {name: '大红皮'})
MATCH (t1:Trait {name: '外皮'})
MATCH (t2:Trait {name: '内囊'})
MATCH (t3:Trait {name: '油室'})
MATCH (t4:Trait {name: '油胞'})
CREATE (v1)-[:具有性状 {value: '红棕色', observation: '皮厚质软', status: 'pending'}]->(t1)
CREATE (v1)-[:具有性状 {value: '黄白色', observation: '海绵状', status: 'pending'}]->(t2)
CREATE (v1)-[:具有性状 {value: '丰富', observation: '肉眼可见', status: 'pending'}]->(t3)
CREATE (v1)-[:具有性状 {value: '大', observation: '明显', status: 'pending'}]->(t4);

// 药材-成分关系
MATCH (h:Herb {name: '陈皮'})
MATCH (c1:Component {name: '挥发油'})
MATCH (c2:Component {name: '陈皮素'})
MATCH (c3:Component {name: '橙皮苷'})
MATCH (c4:Component {name: '川陈皮素'})
MATCH (c5:Component {name: '柠檬烯'})
CREATE (h)-[:包含成分 {quantity: '约1-2%', status: 'pending'}]->(c1)
CREATE (h)-[:包含成分 {quantity: '约2-3%', status: 'pending'}]->(c2)
CREATE (h)-[:包含成分 {quantity: '约5-10%', status: 'pending'}]->(c3)
CREATE (h)-[:包含成分 {quantity: '微量', status: 'pending'}]->(c4)
CREATE (h)-[:包含成分 {quantity: '约90%', status: 'pending'}]->(c5);

// 成分-功效关系
MATCH (c1:Component {name: '挥发油'})
MATCH (c2:Component {name: '陈皮素'})
MATCH (c3:Component {name: '橙皮苷'})
MATCH (e4:Efficacy {name: '去痰平喘'})
MATCH (e5:Efficacy {name: '促进消化液分泌'})
MATCH (e6:Efficacy {name: '调整肠胃'})
MATCH (e7:Efficacy {name: '抗炎'})
MATCH (e8:Efficacy {name: '抗炎抗病毒'})
MATCH (e9:Efficacy {name: '扩张冠状动脉'})
MATCH (e10:Efficacy {name: '降血压'})
CREATE (c1)-[:具有功效 {status: 'pending'}]->(e4)
CREATE (c1)-[:具有功效 {status: 'pending'}]->(e5)
CREATE (c2)-[:具有功效 {status: 'pending'}]->(e6)
CREATE (c2)-[:具有功效 {status: 'pending'}]->(e7)
CREATE (c3)-[:具有功效 {status: 'pending'}]->(e8)
CREATE (c3)-[:具有功效 {status: 'pending'}]->(e9)
CREATE (c3)-[:具有功效 {status: 'pending'}]->(e10);

// 药材-功效关系
MATCH (h:Herb {name: '陈皮'})
MATCH (e1:Efficacy {name: '理气止痛'})
MATCH (e2:Efficacy {name: '健脾和胃'})
MATCH (e3:Efficacy {name: '燥湿化痰'})
CREATE (h)-[:具有功效 {status: 'pending'}]->(e1)
CREATE (h)-[:具有功效 {status: 'pending'}]->(e2)
CREATE (h)-[:具有功效 {status: 'pending'}]->(e3);

// 药材-性味关系
MATCH (h:Herb {name: '陈皮'})
MATCH (f1:Flavor {name: '辛'})
MATCH (f2:Flavor {name: '苦'})
CREATE (h)-[:具有性味 {status: 'pending'}]->(f1)
CREATE (h)-[:具有性味 {status: 'pending'}]->(f2);

// 药材-归经关系
MATCH (h:Herb {name: '陈皮'})
MATCH (m1:Meridian {name: '肺经'})
MATCH (m2:Meridian {name: '脾经'})
CREATE (h)-[:归于经脉 {status: 'pending'}]->(m1)
CREATE (h)-[:归于经脉 {status: 'pending'}]->(m2);

// 药材-工艺关系
MATCH (h:Herb {name: '陈皮'})
MATCH (pr1:Process {name: '沉化'})
CREATE (h)-[:经过工艺 {duration: '3年以上', conditions: '干皮晒干储存', status: 'pending'}]->(pr1);

// 药材-时间关系
MATCH (h:Herb {name: '陈皮'})
MATCH (tp1:TimePoint {years: 1})
MATCH (tp2:TimePoint {years: 3})
MATCH (tp3:TimePoint {years: 5})
MATCH (tp4:TimePoint {years: 10})
CREATE (h)-[:储存时间 {years: 1, status: 'pending'}]->(tp1)
CREATE (h)-[:储存时间 {years: 3, status: 'pending'}]->(tp2)
CREATE (h)-[:储存时间 {years: 5, status: 'pending'}]->(tp3)
CREATE (h)-[:储存时间 {years: 10, status: 'pending'}]->(tp4);

// 药材-性状关系
MATCH (h:Herb {name: '陈皮'})
MATCH (t1:Trait {name: '外皮'})
MATCH (t2:Trait {name: '内囊'})
MATCH (t3:Trait {name: '油室'})
MATCH (t4:Trait {name: '油胞'})
CREATE (h)-[:具有性状 {value: '棕红色，有细皱纹', observation: '质柔软', year_range: '3年以上', status: 'pending'}]->(t1)
CREATE (h)-[:具有性状 {value: '黄白色', observation: '有细筋络', year_range: '3年以上', status: 'pending'}]->(t2)
CREATE (h)-[:具有性状 {value: '丰富', observation: '凹入的油点', year_range: '10年以上更明显', status: 'pending'}]->(t3)
CREATE (h)-[:具有性状 {value: '大', observation: '油胞明显', year_range: '10年以上更明显', status: 'pending'}]->(t4);

RETURN '陈皮图谱创建完成!'
