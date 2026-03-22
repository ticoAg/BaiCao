// Provenance hook - TanStack Query
import { useQuery } from "@tanstack/react-query";
import { provenanceApi } from "../services/api";
import type { ProvenanceEvidence, LineageChain } from "../services/api";

export type { ProvenanceEvidence, LineageChain };

export interface CompletenessResult {
  entity: Record<string, unknown>;
  has_evidence: boolean;
  has_source: boolean;
  chain_complete: boolean;
}

export interface EvidenceResult {
  evidence: Record<string, unknown>[];
  count: number;
}

/**
 * useProvenance - entity provenance query hook
 *
 * @param entityId - entity ID
 * @param options.enabled - enable or disable queries (default: entityId truthy)
 */
export function useProvenance(
  entityId: string | undefined,
  options?: { enabled?: boolean },
) {
  const enabled = options?.enabled ?? !!entityId;

  const {
    data: lineage,
    isLoading: lineageLoading,
    error: lineageError,
  } = useQuery<LineageChain>({
    queryKey: ["provenance", "lineage", entityId],
    queryFn: () => provenanceApi.getEntityLineage(entityId!),
    enabled: enabled && !!entityId,
  });

  const {
    data: evidenceData,
    isLoading: evidenceLoading,
    error: evidenceError,
  } = useQuery<EvidenceResult>({
    queryKey: ["provenance", "evidence", entityId],
    queryFn: () => provenanceApi.getEntityEvidence(entityId!),
    enabled: enabled && !!entityId,
  });

  const {
    data: completeness,
    isLoading: completenessLoading,
    error: completenessError,
  } = useQuery<CompletenessResult>({
    queryKey: ["provenance", "completeness", entityId],
    queryFn: () => provenanceApi.checkCompleteness(entityId!),
    enabled: enabled && !!entityId,
  });

  return {
    lineage: lineage ?? null,
    evidence: evidenceData?.evidence ?? [],
    evidenceCount: evidenceData?.count ?? 0,
    completeness: completeness ?? null,
    loading: lineageLoading || evidenceLoading || completenessLoading,
    lineageLoading,
    evidenceLoading,
    completenessLoading,
    error: lineageError || evidenceError || completenessError,
  };
}

/**
 * useEvidenceDetail - single evidence query hook
 */
export function useEvidenceDetail(
  evidenceId: string | undefined,
  options?: { enabled?: boolean },
) {
  const enabled = options?.enabled ?? !!evidenceId;

  const { data, isLoading, error } = useQuery<ProvenanceEvidence>({
    queryKey: ["provenance", "evidenceDetail", evidenceId],
    queryFn: () => provenanceApi.getEvidence(evidenceId!),
    enabled: enabled && !!evidenceId,
  });

  return {
    evidence: data ?? null,
    loading: isLoading,
    error,
  };
}
