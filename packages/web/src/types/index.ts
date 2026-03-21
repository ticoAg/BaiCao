// 通用类型定义

export type VerificationStatus = "pending" | "verified" | "rejected";

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

// 状态颜色与标签映射
export const statusColors: Record<string, string> = {
  pending: "gold",
  verified: "green",
  rejected: "red",
};

export const statusLabels: Record<string, string> = {
  pending: "待验证",
  verified: "已验证",
  rejected: "已拒绝",
};
