// Verification hook - react-query
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { message } from "antd";
import { verificationApi } from "../services/api";
import type { Verification } from "../services/api";

export function useVerification(params?: {
  status?: string;
  entity_type?: string;
  limit?: number;
  offset?: number;
}) {
  const queryClient = useQueryClient();

  const {
    data,
    isLoading: loading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["verifications", params],
    queryFn: () => verificationApi.list(params),
  });

  const createMutation = useMutation({
    mutationFn: verificationApi.create,
    onSuccess: () => {
      message.success("验证申请已提交");
      void queryClient.invalidateQueries({ queryKey: ["verifications"] });
    },
    onError: () => {
      message.error("提交失败");
    },
  });

  const verifyMutation = useMutation({
    mutationFn: ({
      id,
      verifierId,
      status,
      verdict,
    }: {
      id: string;
      verifierId?: string;
      status: "verified" | "rejected";
      verdict: string;
    }) => verificationApi.verify(id, verifierId, status, verdict),
    onSuccess: (_data, variables) => {
      message.success(
        `已${variables.status === "verified" ? "通过" : "拒绝"}验证`,
      );
      void queryClient.invalidateQueries({ queryKey: ["verifications"] });
    },
    onError: () => {
      message.error("操作失败");
    },
  });

  return {
    verifications: data?.items ?? [],
    total: data?.total ?? 0,
    loading,
    error,
    refetch,
    createVerification: createMutation.mutateAsync,
    verifyItem: verifyMutation.mutateAsync,
    isCreating: createMutation.isPending,
    isVerifying: verifyMutation.isPending,
  };
}
