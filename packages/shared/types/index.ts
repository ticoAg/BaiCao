// BaiCao ShiTan Shared Types
// These types are the SSOT for type definitions across packages

// ============ User & Auth ============

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

// ============ Source ============

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

// ============ Verification ============

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

// ============ Graph Node Types ============

export type NodeType =
  | 'Herb'
  | 'Component'
  | 'Variant'
  | 'Process'
  | 'Trait'
  | 'Efficacy'
  | 'Flavor'
  | 'Meridian'
  | 'Disease'
  | 'TimePoint'

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
  type: 'Herb'
  herbType: 'base' | 'byproduct'
  category?: string
}

// 成分节点
export interface ComponentNode extends BaseNode {
  type: 'Component'
  chemicalFormula?: string
}

// 品种变种节点
export interface VariantNode extends BaseNode {
  type: 'Variant'
  parentHerb: string
  description?: string
}

// 加工工艺节点
export interface ProcessNode extends BaseNode {
  type: 'Process'
  description?: string
  minDuration?: string
  conditions?: string
  effect?: string
}

// 性状特征节点
export interface TraitNode extends BaseNode {
  type: 'Trait'
  traitCategory: 'external' | 'internal' | 'chemical'
  description?: string
  observationMethod?: string
}

// 时间点节点
export interface TimePointNode extends BaseNode {
  type: 'TimePoint'
  years: number
  description?: string
  qualityIndicator?: string
}

// 功效节点
export interface EfficacyNode extends BaseNode {
  type: 'Efficacy'
  category?: string
}

// 性味节点
export interface FlavorNode extends BaseNode {
  type: 'Flavor'
  nature?: string
}

// 归经节点
export interface MeridianNode extends BaseNode {
  type: 'Meridian'
}

// 疾病节点
export interface DiseaseNode extends BaseNode {
  type: 'Disease'
  tcmType?: string
}

// 联合类型
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

// ============ Graph Edge Types ============

export type EdgeType =
  | 'CONTAINS'
  | 'EXTRACTED_FROM'
  | 'HAS_VARIANT'
  | 'VARIANT_OF'
  | 'PROCESSED_BY'
  | 'APPLIES_TO'
  | 'STORED_FOR'
  | 'HAS_TRAIT'
  | 'OBSERVED_IN'
  | 'HAS_EFFICACY'
  | 'HAS_FLAVOR'
  | 'ENTERS_MERIDIAN'
  | 'TREATS'
  | 'INTERACTS_WITH'
  | 'SIMILAR_TO'

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
  | { type: 'CONTAINS'; source: string; target: string; properties: ContainsEdge }
  | { type: 'HAS_VARIANT'; source: string; target: string; properties: HasVariantEdge }
  | { type: 'PROCESSED_BY'; source: string; target: string; properties: ProcessedByEdge }
  | { type: 'STORED_FOR'; source: string; target: string; properties: StoredForEdge }
  | { type: 'HAS_TRAIT'; source: string; target: string; properties: HasTraitEdge }
  | { type: 'HAS_EFFICACY'; source: string; target: string; properties: BaseEdge }
  | { type: 'HAS_FLAVOR'; source: string; target: string; properties: BaseEdge }
  | { type: 'ENTERS_MERIDIAN'; source: string; target: string; properties: BaseEdge }
  | { type: 'TREATS'; source: string; target: string; properties: BaseEdge }

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
