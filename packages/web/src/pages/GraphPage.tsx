import { useCallback, useMemo } from "react";
import {
  Button,
  Divider,
  Empty,
  Select,
  Space,
  Spin,
  Tag,
  Typography,
} from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import { useParams } from "react-router-dom";
import { NetworkGraph } from "@ant-design/graphs";
import { useGraphWorkspace } from "../hooks/useGraphWorkspace";
import {
  labelColorMap,
  labelTagColors,
  nodeStyleMap,
  defaultNodeStyle,
  relTypeLabels,
} from "../types/graph";
import NodeDetail from "../components/graph/NodeDetail";
import EdgeDetail from "../components/graph/EdgeDetail";
import GraphQueryPanel from "../components/graph/GraphQueryPanel";
import GraphQuerySummary from "../components/graph/GraphQuerySummary";

const { Title, Text } = Typography;

const workspaceMinHeight = "calc(100vh - 160px)";

const panelSurfaceStyle = {
  borderRadius: 24,
  border: "1px solid rgba(78, 97, 84, 0.12)",
  background:
    "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(247,249,247,0.98) 100%)",
  boxShadow: "0 20px 48px rgba(44, 58, 50, 0.08)",
};

const GraphPage = () => {
  const { name } = useParams<{ name: string }>();
  const {
    graphData,
    querySummary,
    mode,
    loading,
    selected,
    setSelected,
    depth,
    setDepth,
    refetch,
    runAdvancedQuery,
  } = useGraphWorkspace(name);

  const nodeCount = graphData?.nodes.length ?? 0;
  const edgeCount = graphData?.edges.length ?? 0;

  const pageTitle =
    mode === "advanced-query"
      ? "高级图谱查询结果"
      : name || graphData?.center?.name || "图谱分析工作台";

  const pageSubtitle =
    mode === "advanced-query"
      ? "保留图谱视觉上下文，围绕条件命中的节点与关系进行分析。"
      : name
        ? `当前默认加载 ${name} 的知识图谱。`
        : "在左侧组合节点、关系与属性条件，构建你的图谱分析视角。";

  const g6Data = useMemo(() => {
    if (!graphData) {
      return { nodes: [], edges: [] };
    }

    const centerId = graphData.center?.id || graphData.center?.name;

    const nodes = graphData.nodes.map((node) => {
      const nodeId = node.id || node.name;
      const primaryLabel = node.labels?.[0] || "Unknown";
      const isCenter = nodeId === centerId;
      const style = nodeStyleMap[primaryLabel] || defaultNodeStyle;

      return {
        id: nodeId,
        data: { ...node },
        style: {
          size: isCenter ? 56 : primaryLabel === "Herb" ? 40 : 30,
          fill: style.fill,
          stroke: style.stroke,
          lineWidth: isCenter ? 3 : 2,
          labelText: node.name,
          labelFontSize: isCenter ? 14 : 11,
          labelFill: style.textColor,
          labelPlacement: "bottom" as const,
          labelOffsetY: 4,
          ...(isCenter && {
            shadowColor: style.fill,
            shadowBlur: 15,
            shadowOffsetX: 0,
            shadowOffsetY: 0,
          }),
        },
      };
    });

    const edges = graphData.edges.map((edge, index) => {
      const sourceId = edge.source?.id || edge.source?.name || "";
      const targetId = edge.target?.id || edge.target?.name || "";
      const isVerified = edge.status === "verified";

      return {
        id: edge.id || `edge-${index}`,
        source: sourceId,
        target: targetId,
        data: {
          ...edge,
          sourceName: edge.source?.name,
          targetName: edge.target?.name,
        },
        style: {
          stroke: isVerified ? "#8DCC93" : "#A5ABB6",
          lineWidth: isVerified ? 2 : 1,
          ...(isVerified ? {} : { lineDash: [4, 4] }),
          labelText: relTypeLabels[edge.rel_type || ""] || edge.rel_type || "",
          labelFontSize: 10,
          labelFill: "#555",
          labelBackground: true,
          labelBackgroundFill: "#fff",
          labelBackgroundOpacity: 0.85,
          labelBackgroundRadius: 4,
          endArrow: true,
          endArrowSize: 6,
        },
      };
    });

    return { nodes, edges };
  }, [graphData]);

  const graphOptions = useMemo(
    () => ({
      data: g6Data,
      animation: true,
      behaviors: (behaviors: any[]) => [
        ...behaviors,
        { key: "drag-element", type: "drag-element" },
        { key: "hover-activate", type: "hover-activate" },
      ],
      plugins: [
        {
          key: "background",
          type: "background",
          background: "#F8F9FA",
        },
        {
          key: "grid-line",
          type: "grid-line",
          follow: false,
          lineWidth: 0.5,
          stroke: "#E0E5E2",
        },
        {
          key: "tooltip",
          type: "tooltip",
          getContent: (_evt: any, items: any[]) => {
            const item = items?.[0];
            if (!item) {
              return "";
            }

            const data = item.data || {};

            if (item.source !== undefined && item.target !== undefined) {
              const relLabel = relTypeLabels[data.rel_type || ""] || data.rel_type || "";
              return `<div style="padding:6px 10px;font-size:13px;line-height:1.5">
                <b>${relLabel}</b><br/>
                <span style="color:#888">${data.sourceName || "?"} → ${data.targetName || "?"}</span>
              </div>`;
            }

            const label = data.labels?.[0] || "";
            return `<div style="padding:6px 10px;font-size:13px;line-height:1.5">
              <b>${data.name || item.id}</b>
              ${label ? `<span style="margin-left:6px;padding:1px 6px;border-radius:3px;background:#f0f0f0;font-size:11px;color:#666">${label}</span>` : ""}
            </div>`;
          },
        },
      ],
    }),
    [g6Data],
  );

  const handleReady = useCallback(
    (graph: any) => {
      if (!graphData) {
        return;
      }

      graph.on("node:click", (event: any) => {
        const nodeId = event.target?.id;
        if (!nodeId) {
          return;
        }

        const node = graphData.nodes.find((item) => (item.id || item.name) === nodeId);
        if (node) {
          setSelected({ type: "node", data: node });
        }
      });

      graph.on("edge:click", (event: any) => {
        const edgeId = event.target?.id;
        if (!edgeId) {
          return;
        }

        const edgeModel = graph.getEdgeData(edgeId);
        if (edgeModel?.data) {
          setSelected({
            type: "edge",
            data: {
              ...edgeModel.data,
              sourceName: edgeModel.data.sourceName || edgeModel.data.source?.name,
              targetName: edgeModel.data.targetName || edgeModel.data.target?.name,
            },
          });
        }
      });
    },
    [graphData, setSelected],
  );

  if (loading) {
    return (
      <div
        style={{
          minHeight: workspaceMinHeight,
          display: "grid",
          placeItems: "center",
        }}
      >
        <Space direction="vertical" size="middle" align="center">
          <Spin size="large" />
          <Text type="secondary">加载图谱工作区中...</Text>
        </Space>
      </div>
    );
  }

  return (
    <div
      data-testid="graph-workspace"
      style={{
        minHeight: workspaceMinHeight,
        display: "grid",
        gridTemplateColumns: "minmax(280px, 320px) minmax(0, 1fr) minmax(280px, 320px)",
        gap: 16,
        alignItems: "stretch",
        overflowX: "auto",
      }}
    >
      <aside
        style={{
          ...panelSurfaceStyle,
          display: "flex",
          flexDirection: "column",
          minHeight: 0,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: "22px 20px 18px",
            borderBottom: "1px solid rgba(78, 97, 84, 0.08)",
            background:
              "linear-gradient(180deg, rgba(247,250,248,0.98) 0%, rgba(255,255,255,0.98) 100%)",
          }}
        >
          <Text strong style={{ display: "block", fontSize: 18, color: "#203127" }}>
            图谱条件查询
          </Text>
          <Text type="secondary" style={{ display: "block", marginTop: 6, lineHeight: 1.6 }}>
            将节点、属性与关系约束编织成一次图谱分析查询。
          </Text>
        </div>
        <div style={{ padding: "18px 20px 20px", overflowY: "auto", minHeight: 0 }}>
          <GraphQueryPanel
            depth={depth}
            loading={loading}
            onSubmit={runAdvancedQuery}
            onDepthChange={setDepth}
          />
        </div>
      </aside>

      <section style={{ display: "flex", flexDirection: "column", minWidth: 0, gap: 16 }}>
        <div
          style={{
            ...panelSurfaceStyle,
            padding: "18px 22px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 16,
            flexWrap: "wrap",
          }}
        >
          <div>
            <Space size={[8, 8]} wrap style={{ marginBottom: 8 }}>
              <Tag color={mode === "advanced-query" ? "processing" : "blue"}>
                {mode === "advanced-query" ? "查询结果视图" : "默认图谱视图"}
              </Tag>
              <Tag>{nodeCount} 节点</Tag>
              <Tag>{edgeCount} 关系</Tag>
              {querySummary?.truncated && <Tag color="warning">结果已截断</Tag>}
            </Space>
            <Title level={3} style={{ margin: 0, color: "#203127" }}>
              {pageTitle}
            </Title>
            <Text type="secondary" style={{ display: "block", marginTop: 6 }}>
              {pageSubtitle}
            </Text>
          </div>

          <Space align="center" wrap>
            <Text type="secondary">图谱深度</Text>
            <Select
              value={depth}
              options={[1, 2, 3].map((value) => ({ label: `${value}`, value }))}
              onChange={(value) => setDepth(value)}
              style={{ width: 96 }}
            />
            <Button
              icon={<ReloadOutlined />}
              onClick={refetch}
              disabled={mode === "idle"}
            >
              刷新
            </Button>
          </Space>
        </div>

        {mode === "advanced-query" && querySummary && (
          <GraphQuerySummary summary={querySummary} />
        )}

        <div
          style={{
            ...panelSurfaceStyle,
            flex: 1,
            minHeight: 0,
            padding: 12,
            overflow: "hidden",
          }}
        >
          {graphData ? (
            <div
              data-testid="graph-canvas-shell"
              style={{
                minHeight: "calc(100vh - 280px)",
                height: "100%",
                borderRadius: 20,
                overflow: "hidden",
                background:
                  "radial-gradient(circle at top left, rgba(240,246,242,0.92), rgba(248,249,250,0.98) 42%, rgba(244,247,245,0.98) 100%)",
              }}
            >
              <NetworkGraph {...graphOptions} onReady={handleReady} />
            </div>
          ) : (
            <div
              data-testid="graph-canvas-shell"
              style={{
                minHeight: "calc(100vh - 280px)",
                display: "grid",
                placeItems: "center",
                borderRadius: 20,
                border: "1px dashed rgba(92, 108, 97, 0.22)",
                background:
                  "radial-gradient(circle at top, rgba(244,248,245,0.98), rgba(249,250,249,0.98) 58%, rgba(245,247,246,0.98) 100%)",
              }}
            >
              <Empty
                description={
                  <Space direction="vertical" size={4}>
                    <Text strong style={{ color: "#23362B" }}>
                      等待一张新的图谱视图
                    </Text>
                    <Text type="secondary">
                      左侧可以直接发起高级查询；如果访问 `/graph/药材名`，则会加载默认药材图谱。
                    </Text>
                  </Space>
                }
              />
            </div>
          )}
        </div>
      </section>

      <aside
        style={{
          ...panelSurfaceStyle,
          display: "flex",
          flexDirection: "column",
          minHeight: 0,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: "22px 20px 18px",
            borderBottom: "1px solid rgba(78, 97, 84, 0.08)",
            background:
              "linear-gradient(180deg, rgba(251,252,251,0.98) 0%, rgba(247,249,247,0.98) 100%)",
          }}
        >
          <Text strong style={{ display: "block", fontSize: 18, color: "#203127" }}>
            图谱详情
          </Text>
          <Text type="secondary" style={{ display: "block", marginTop: 6, lineHeight: 1.6 }}>
            节点、关系和图例在这里收束成可读的分析上下文。
          </Text>
        </div>

        <div style={{ padding: "18px 20px 20px", overflowY: "auto", minHeight: 0 }}>
          {selected?.type === "node" && <NodeDetail node={selected.data} />}
          {selected?.type === "edge" && <EdgeDetail edge={selected.data} />}
          {!selected && (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="点击中间图谱中的节点或关系查看详情"
            />
          )}

          <Divider />

          <div>
            <Text strong>图例</Text>
            <div
              style={{
                marginTop: 12,
                display: "flex",
                flexWrap: "wrap",
                gap: 6,
              }}
            >
              {Object.entries(labelColorMap).map(([label, color]) => (
                <Tag key={label} color={labelTagColors[label] || "default"}>
                  <span
                    style={{
                      display: "inline-block",
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      background: color,
                      marginRight: 4,
                    }}
                  />
                  {label}
                </Tag>
              ))}
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
};

export default GraphPage;
