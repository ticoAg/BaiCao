// 白草药坛共享类型
// 这里是跨包共享类型定义的单一事实来源

// ============ 用户与权限 ============

export type UserRole = 'user' | 'expert' | 'admin'

export interface User {
  id: string
  username: string
  email: string
  role: UserRole
  isActive: boolean
  expertFields: string[]
  verifiedAt?: string
  createdAt: string
}

// ============ 来源 ============

export type SourceType = 'ancient' | 'modern' | 'patent' | 'database'

export interface Source {
  id: string
  name: string
  type: SourceType
  author?: string
  publicationDate?: string
  url?: string
  isbn?: string
  pages?: string
  citation: string
  description?: string
  createdAt: string
}

// ============ 验证 ============

export type VerificationStatus = 'pending' | 'verified' | 'rejected'

export interface Verification {
  id: string
  entityType: 'herb' | 'component' | 'variant' | 'process' | 'trait' | 'efficacy' | 'relation'
  entityId: string
  fieldName?: string
  claimedValue: string
  sourceId?: string
  status: VerificationStatus
  applicantId: string
  verifierId?: string
  verdict?: string
  verifiedAt?: string
  createdAt: string
}

export interface VerificationEvidence {
  id: string
  verificationId: string
  sourceId: string
  quote: string
  pageReference?: string
  relevanceScore: number
  createdAt: string
}

// ============ 图谱节点类型 ============

export type NodeType =
  | '药材'
  | '饮片'
  | '成分'
  | '品种'
  | '工艺'
  | '性状'
  | '功效'
  | '性味'
  | '归经'
  | '病证'
  | '症状'
  | '方剂'
  | '医案'
  | '穴位'
  | '治法'
  | '时间点'
  | '来源'
  | '证据'

export type NodeStatus = 'pending' | 'verified' | 'rejected'

// 基础节点接口
export interface BaseNode {
  id: string
  name: string
  source?: string
  importedAt: string
  status: NodeStatus
  verificationId?: string
  verifiedBy?: string
  verifiedAt?: string
}

// 药材节点
export interface HerbNode extends BaseNode {
  type: '药材'
  herbType: 'base' | 'byproduct'
  category?: string
}

// 成分节点
export interface ComponentNode extends BaseNode {
  type: '成分'
  chemicalFormula?: string
}

// 品种变种节点
export interface VariantNode extends BaseNode {
  type: '品种'
  parentHerb: string
  description?: string
}

// 加工工艺节点
export interface ProcessNode extends BaseNode {
  type: '工艺'
  description?: string
  minDuration?: string
  conditions?: string
  effect?: string
}

// 性状特征节点
export interface TraitNode extends BaseNode {
  type: '性状'
  traitCategory: 'external' | 'internal' | 'chemical'
  description?: string
  observationMethod?: string
}

// 时间点节点
export interface TimePointNode extends BaseNode {
  type: '时间点'
  years: number
  description?: string
  qualityIndicator?: string
}

// 功效节点
export interface EfficacyNode extends BaseNode {
  type: '功效'
  category?: string
}

// 性味节点
export interface FlavorNode extends BaseNode {
  type: '性味'
  nature?: string
}

// 归经节点
export interface MeridianNode extends BaseNode {
  type: '归经'
}

// 疾病节点
export interface DiseaseNode extends BaseNode {
  type: '病证'
  tcmType?: string
}

export interface SymptomNode extends BaseNode {
  type: '症状'
  category?: string
  description?: string
}

export interface FormulaNode extends BaseNode {
  type: '方剂'
  compositionText?: string
  sourceBook?: string
}

export interface MedicalCaseNode extends BaseNode {
  type: '医案'
  chiefComplaint?: string
  unitId?: string
}

export interface AcupointNode extends BaseNode {
  type: '穴位'
  meridian?: string
}

export interface TreatmentMethodNode extends BaseNode {
  type: '治法'
  category?: string
}

// 联合节点类型
export type GraphNode =
  | HerbNode
  | ComponentNode
  | VariantNode
  | ProcessNode
  | TraitNode
  | TimePointNode
  | EfficacyNode
  | FlavorNode
  | MeridianNode
  | DiseaseNode
  | SymptomNode
  | FormulaNode
  | MedicalCaseNode
  | AcupointNode
  | TreatmentMethodNode

// ============ 图谱边类型 ============

export type EdgeType =
  | '具有饮片'
  | '包含成分'
  | '提取自'
  | '具有品种'
  | '属于药材'
  | '经过工艺'
  | '适用于'
  | '储存时间'
  | '具有性状'
  | '观察于'
  | '具有功效'
  | '具有性味'
  | '归于经脉'
  | '治疗病证'
  | '关联药材'
  | '关联治法'
  | '关联证候'
  | '关联症状'
  | '相互作用'
  | '相似于'
  | '父类'
  | '子类'
  | '来源于'
  | '派生自'
  | '由证据支持'
  | '组成药材'
  | '使用方剂'
  | '取用穴位'
  | '采用治法'
  | '记载于医案'

export interface BaseEdge {
  status: NodeStatus
  verificationId?: string
  verifiedBy?: string
  verifiedAt?: string
}

// 成分关系
export interface ContainsEdge extends BaseEdge {
  quantity?: string
}

// 品种关系
export interface HasVariantEdge extends BaseEdge {}

// 工艺关系
export interface ProcessedByEdge extends BaseEdge {
  duration?: string
  conditions?: string
  startDate?: string
  endDate?: string
}

// 储存时间关系
export interface StoredForEdge extends BaseEdge {
  years: number
  startDate?: string
  endDate?: string
}

// 性状关系
export interface HasTraitEdge extends BaseEdge {
  value: string
  observation?: string
  yearRange?: string
}

// 联合类型
export type GraphEdge =
  | { type: '包含成分'; source: string; target: string; properties: ContainsEdge }
  | { type: '具有品种'; source: string; target: string; properties: HasVariantEdge }
  | { type: '经过工艺'; source: string; target: string; properties: ProcessedByEdge }
  | { type: '储存时间'; source: string; target: string; properties: StoredForEdge }
  | { type: '具有性状'; source: string; target: string; properties: HasTraitEdge }
  | { type: '具有功效'; source: string; target: string; properties: BaseEdge }
  | { type: '具有性味'; source: string; target: string; properties: BaseEdge }
  | { type: '归于经脉'; source: string; target: string; properties: BaseEdge }
  | { type: '治疗病证'; source: string; target: string; properties: BaseEdge }
  | { type: '关联药材'; source: string; target: string; properties: BaseEdge }
  | { type: '关联治法'; source: string; target: string; properties: BaseEdge }
  | { type: '关联证候'; source: string; target: string; properties: BaseEdge }
  | { type: '来源于'; source: string; target: string; properties: BaseEdge }
  | { type: '由证据支持'; source: string; target: string; properties: BaseEdge }
  | { type: '组成药材'; source: string; target: string; properties: BaseEdge }
  | { type: '使用方剂'; source: string; target: string; properties: BaseEdge }
  | { type: '取用穴位'; source: string; target: string; properties: BaseEdge }
  | { type: '采用治法'; source: string; target: string; properties: BaseEdge }
  | { type: '记载于医案'; source: string; target: string; properties: BaseEdge }

// ============ Graph Response Types ============

export interface GraphData {
  center: GraphNode | null
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface SearchResult {
  node: GraphNode
  labels: string[]
}

// ============ API Response Types ============

export interface ApiResponse<T> {
  data: T
  requestId: string
  timestamp: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

// ============ Chat Types ============

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  reasoningChain?: ReasoningStep[]
  sources?: Source[]
  createdAt: string
}

export interface ReasoningStep {
  step: number
  description: string
  entities?: string[]
  relations?: string[]
  confidence?: number
}

export interface ChatSession {
  id: string
  messages: ChatMessage[]
  createdAt: string
  updatedAt: string
}

// SSE 流式事件
export type SSEEventType = 'session' | 'reasoning' | 'sources' | 'token' | 'done' | 'error'

export interface SSEEvent {
  type: SSEEventType
  data: Record<string, unknown>
}

// ============ Verification Request Types ============

export interface VerificationRequest {
  entityType: string
  entityId: string
  fieldName?: string
  claimedValue: string
  sourceId?: string
  evidence: {
    sourceId: string
    quote: string
    pageReference?: string
    relevanceScore: number
  }[]
}

// ============ Pipeline Review & Export ============

export type ReviewSessionStatus = 'draft' | 'confirmed' | 'rejected'

export type ReviewItemDecision = 'pending' | 'confirm' | 'reject' | 'edit'

export interface PipelineReviewItem {
  item_key: string
  node_type?: string | null
  original_payload: Record<string, unknown>
  revised_payload: Record<string, unknown>
  decision: ReviewItemDecision
  comment?: string | null
}

export interface ReviewSession {
  id: string
  run_id: string
  step: string
  status: ReviewSessionStatus
  items: PipelineReviewItem[]
  comment?: string | null
  confirmed_at?: string | null
}

export type ExportRecordStatus =
  | 'pending'
  | 'snapshot_written'
  | 'partial_failed'
  | 'completed'
  | 'failed'

export type GraphWriteStatus = 'pending' | 'succeeded' | 'failed'

export interface ExportRecord {
  id: string
  run_id: string
  review_session_id: string
  status: ExportRecordStatus
  graph_write_status: GraphWriteStatus
  snapshot_bucket?: string | null
  snapshot_object_key?: string | null
  snapshot_checksum?: string | null
  snapshot_size?: number | null
  error_message?: string | null
  retry_count: number
}

export interface VerificationVerdict {
  verificationId: string
  status: 'verified' | 'rejected'
  verdict: string
}

// ============ Herb (PostgreSQL) ============

export interface Herb {
  id: string
  name: string
  latinName?: string
  englishName?: string
  category: string
  description?: string
  alias?: string[]
  efficacy?: string[]
  flavor?: string[]
  meridian?: string[]
  dosage?: string
  contraindications?: string
  createdAt: string
  updatedAt: string
}

// ============ Evidence (溯源证据) ============

export interface Evidence {
  id: string
  herbId: string
  sourceId: string
  content: string
  quote?: string
  chapter?: string
  pageNumber?: string
  verificationStatus: 'pending' | 'verified' | 'rejected'
  confidenceScore: number
  extractionMethod: string
  createdAt: string
}

// ============ Provenance Graph API ============
// 对外契约保持 content / source_name / page_reference；图谱存储映射为
// 标识 / 名称 / 证据原文 / 状态，以及兼容属性 来源 / 页码。不泄漏中文存储键。
// 关系存储类型使用 由证据支持、来源于。

export type ProvenanceRelationType = Extract<EdgeType, '由证据支持' | '来源于'>

export interface ProvenanceNode {
  id: string
  name: string
  status: NodeStatus
}

export interface ProvenanceEvidenceNode {
  id: string
  content: string
  source_name: string
  page_reference?: string
  status: NodeStatus
}

export interface CreateProvenanceEvidenceRequest {
  content: string
  source_name: string
  page_reference?: string
}

export interface LinkProvenanceSourceRequest {
  source_id: string
}

export interface ProvenanceRelationship {
  type: ProvenanceRelationType
  status: NodeStatus
  evidence_id?: string
  source_id?: string
}

export interface ProvenanceLineageChain {
  entity: ProvenanceNode
  evidence: ProvenanceEvidenceNode | null
  source: ProvenanceNode
}

export interface ProvenanceEvidenceCollectionItem {
  evidence: ProvenanceEvidenceNode
  source: ProvenanceNode | null
}

export interface ProvenanceLineageCompleteness {
  entity: ProvenanceNode
  evidence: ProvenanceEvidenceNode | null
  source: ProvenanceNode | null
  has_evidence: boolean
  has_source: boolean
  chain_complete: boolean
}

export interface ProvenanceSourceDerivationsResponse {
  derivations: ProvenanceLineageChain[]
  count: number
}

export interface ProvenanceEvidenceCollectionResponse {
  evidence: ProvenanceEvidenceCollectionItem[]
  count: number
}

export interface LinkProvenanceSourceResponse {
  relationship: ProvenanceRelationship
  message: string
}

// ============ Pipeline Source Ingestion ============

export type PipelineSourceType = 'huggingface_repo' | 'remote_url' | 'local_upload'

export interface PipelineSourceDefinition {
  source_type: PipelineSourceType
  source_input: Record<string, unknown>
}

export interface PipelineUploadResponse {
  upload_token: string
  filename: string
  stored_path: string
  content_type?: string
}

export * from './graph-workbench'
export * from './workbench'
