export type WorkbenchCommandSource = "workbench" | "chat";

export type WorkbenchFrameType = "graph" | "table" | "text" | "error";

export type WorkbenchFrameStatus = "ok" | "warning" | "error";

export interface WorkbenchHistoryItem {
  command: string;
  source: WorkbenchCommandSource;
  executedAt?: string;
}

export interface WorkbenchFrame {
  id: string;
  type: WorkbenchFrameType;
  title: string;
  status: WorkbenchFrameStatus;
  payload: Record<string, unknown>;
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
