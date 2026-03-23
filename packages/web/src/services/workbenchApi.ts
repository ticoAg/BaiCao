import axios from "axios";
import type {
  CypherValidationRequest,
  CypherValidationResult,
  WorkbenchExecuteRequest,
  WorkbenchExecuteResponse,
} from "../types/workbench";

const API_BASE = "/api/v1";

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

export const workbenchApi = {
  execute: async (payload: WorkbenchExecuteRequest): Promise<WorkbenchExecuteResponse> => {
    const requestBody = {
      command: payload.command,
      source: payload.source,
      session_id: payload.sessionId,
    };
    const { data } = await api.post("/workbench/execute", requestBody);
    return {
      command: data.command,
      frames: data.frames,
      historyItem: {
        command: data.history_item.command,
        source: data.history_item.source,
        executedAt: data.history_item.executed_at,
      },
    };
  },

  validateCypher: async (
    payload: CypherValidationRequest,
  ): Promise<CypherValidationResult> => {
    const { data } = await api.post("/workbench/validate-cypher", {
      query: payload.query,
      source: payload.source ?? "workbench",
    });
    return {
      valid: data.valid,
      normalizedQuery: data.normalized_query,
      errors: data.errors,
      warnings: data.warnings,
      readonly: data.readonly,
    };
  },
};
