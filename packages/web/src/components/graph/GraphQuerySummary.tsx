import { Space, Statistic, Tag, Typography } from "antd";
import type { GraphQuerySummary as GraphQuerySummaryType } from "../../types/graph";

const { Text } = Typography;

type GraphQuerySummaryProps = {
  summary: GraphQuerySummaryType;
};

const GraphQuerySummary = ({ summary }: GraphQuerySummaryProps) => {
  return (
    <div
      data-testid="graph-query-summary"
      style={{
        borderRadius: 22,
        border: "1px solid rgba(85, 104, 92, 0.14)",
        background:
          "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(244,247,244,0.98) 100%)",
        boxShadow: "0 18px 42px rgba(44, 58, 50, 0.08)",
        padding: 20,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: 16,
          marginBottom: 16,
          flexWrap: "wrap",
        }}
      >
        <div>
          <Text strong style={{ fontSize: 16, color: "#223128" }}>
            高级图谱查询结果
          </Text>
          <div style={{ marginTop: 6 }}>
            <Text type="secondary">
              当前展示的是条件命中的子图结果，不对应单一药材详情页。
            </Text>
          </div>
        </div>
        <Space size={[8, 8]} wrap>
          <Tag color="processing">模式: {summary.mode}</Tag>
          <Tag color={summary.truncated ? "warning" : "success"}>
            {summary.truncated ? "结果已截断" : "结果完整"}
          </Tag>
        </Space>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
          gap: 12,
          marginBottom: 16,
        }}
      >
        <div
          style={{
            borderRadius: 16,
            padding: 14,
            background: "rgba(242, 247, 243, 0.9)",
            border: "1px solid rgba(74, 109, 88, 0.1)",
          }}
        >
          <Statistic title="命中节点" value={summary.matched_nodes} valueStyle={{ color: "#2F5A46" }} />
        </div>
        <div
          style={{
            borderRadius: 16,
            padding: 14,
            background: "rgba(242, 247, 243, 0.9)",
            border: "1px solid rgba(74, 109, 88, 0.1)",
          }}
        >
          <Statistic title="命中边数" value={summary.matched_edges} valueStyle={{ color: "#2F5A46" }} />
        </div>
        <div
          style={{
            borderRadius: 16,
            padding: 14,
            background: "rgba(242, 247, 243, 0.9)",
            border: "1px solid rgba(74, 109, 88, 0.1)",
          }}
        >
          <Statistic
            title="Active Filters"
            value={summary.active_filters.length}
            valueStyle={{ color: "#2F5A46" }}
          />
        </div>
      </div>

      <div>
        <Text strong style={{ color: "#2C4135" }}>
          Active Filters
        </Text>
        <Space size={[8, 8]} wrap style={{ marginTop: 10 }}>
          {summary.active_filters.length ? (
            summary.active_filters.map((filter) => (
              <Tag
                key={filter}
                style={{
                  borderRadius: 999,
                  paddingInline: 10,
                  paddingBlock: 4,
                  borderColor: "rgba(70, 96, 81, 0.18)",
                  background: "rgba(247, 250, 248, 0.98)",
                }}
              >
                {filter}
              </Tag>
            ))
          ) : (
            <Text type="secondary">本次查询未附加过滤条件。</Text>
          )}
        </Space>
      </div>
    </div>
  );
};

export default GraphQuerySummary;
