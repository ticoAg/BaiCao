// useHerbDetail - 药材详情数据加载 hook
import { useQuery } from "@tanstack/react-query";
import { herbApi, provenanceApi } from "../services/api";
import type { Herb } from "../services/api";

export interface HerbEvidence {
  evidence: Record<string, unknown>[];
  count: number;
}

export function useHerbDetail(herbId: string | undefined) {
  const {
    data: herb,
    isLoading: herbLoading,
    error: herbError,
    refetch: refetchHerb,
  } = useQuery<Herb>({
    queryKey: ["herb", herbId],
    queryFn: () => herbApi.get(herbId!),
    enabled: !!herbId,
  });

  const {
    data: evidenceData,
    isLoading: evidenceLoading,
    error: evidenceError,
    refetch: refetchEvidence,
  } = useQuery<HerbEvidence>({
    queryKey: ["herbEvidence", herbId],
    queryFn: () => provenanceApi.getEntityEvidence(herbId!),
    enabled: !!herbId,
  });

  const loading = herbLoading || evidenceLoading;
  const error = herbError || evidenceError;

  const refetch = () => {
    void refetchHerb();
    void refetchEvidence();
  };

  return {
    herb: herb ?? null,
    evidence: evidenceData?.evidence ?? [],
    evidenceCount: evidenceData?.count ?? 0,
    loading,
    error,
    refetch,
  };
}
