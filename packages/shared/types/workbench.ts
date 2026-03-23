export type WorkbenchCommandSource = "workbench" | "chat";

export type WorkbenchFrameType = "graph" | "table" | "text" | "error";

export type WorkbenchFrameStatus = "ok" | "warning" | "error";

export type SemanticQueryMode = "exact" | "fuzzy" | "path";

export interface CypherValidationRequest {
  query: string;
  source?: WorkbenchCommandSource;
}

export interface CypherValidationResult {
  valid: boolean;
  normalizedQuery: string;
  errors: string[];
  warnings: string[];
  readonly: boolean;
}

export interface WorkbenchHistoryItem {
  command: string;
  source: WorkbenchCommandSource;
  executedAt?: string;
}

export interface GraphFramePayload {
  graph: {
    center: Record<string, unknown> | null;
    nodes: Record<string, unknown>[];
    edges: Record<string, unknown>[];
  };
  mode?: SemanticQueryMode | "cypher";
  summary?: string;
}

export interface TableFramePayload {
  columns: string[];
  rows: Record<string, unknown>[];
}

export interface TextFramePayload {
  markdown: string;
}

export interface ErrorFramePayload {
  message: string;
  details?: string[];
}

export type WorkbenchFramePayload =
  | GraphFramePayload
  | TableFramePayload
  | TextFramePayload
  | ErrorFramePayload;

export interface WorkbenchFrame {
  id: string;
  type: WorkbenchFrameType;
  title: string;
  status: WorkbenchFrameStatus;
  payload: WorkbenchFramePayload;
  command?: string;
}

export interface WorkbenchExecuteRequest {
  command: string;
  source: WorkbenchCommandSource;
  sessionId?: string;
}

export interface WorkbenchExecuteResponse {
  command: string;
  frames: WorkbenchFrame[];
  historyItem: WorkbenchHistoryItem;
}
