import { useCallback, useMemo, useRef, useState } from "react"
import { Button, Drawer, Space, Tag, Typography } from "antd"
import { ReloadOutlined } from "@ant-design/icons"
import { useParams } from "react-router-dom"
import { graphApi } from "../services/api"
import { useGraphWorkbenchPage } from "../hooks/useGraphWorkbenchPage"
import type { GraphData, GraphNode, GraphEdge } from "../types/graph"
import { relTypeLabels } from "../types/graph"
import GraphCanvasWorkspace from "../components/graph/GraphCanvasWorkspace"
import type { GraphCanvasWorkspaceHandle } from "../components/graph/GraphCanvasWorkspace"
import GraphInspectorPanel from "../components/graph/GraphInspectorPanel"
import GraphMetadataSidebar from "../components/graph/GraphMetadataSidebar"
import GraphQueryPanel from "../components/graph/GraphQueryPanel"
import type { GraphEventCallbacks } from "../lib/graph-viz"
import { VizNode, VizRelationship, VizGraph } from "../lib/graph-viz"

const { Text } = Typography

function getGraphNodeId(node: Pick<GraphNode, "id" | "name">) {
  return node.id || node.name
}

function getGraphEdgeId(edge: GraphEdge) {
  return [
    edge.source?.id || edge.source?.name || "",
    edge.rel_type || "",
    edge.target?.id || edge.target?.name || "",
  ].join("::")
}

function mergeGraphData(
  base: GraphData | null,
  expansions: GraphData[]
): GraphData | null {
  if (!base) return null
  const nodeMap = new Map<string, GraphNode>()
  const edgeMap = new Map<string, GraphEdge>()

  const register = (g: GraphData) => {
    g.nodes.forEach((n) => nodeMap.set(getGraphNodeId(n), n))
    g.edges.forEach((e) => edgeMap.set(getGraphEdgeId(e), e))
  }

  register(base)
  expansions.forEach(register)

  return {
    center: base.center,
    nodes: Array.from(nodeMap.values()),
    edges: Array.from(edgeMap.values()),
  }
}

const GraphPage = () => {
  const { name } = useParams<{ name: string }>()
  const {
    graphData,
    querySummary,
    mode,
    loading,
    scene,
    metaSummary,
    metaLabels,
    metaRelationshipTypes,
    metaPropertyKeys,
    metaSchema,
    metaLoading,
    metaError,
    selectedItem,
    highlightedLabel,
    highlightedRelationshipType,
    highlightLabel,
    highlightRelationshipType,
    selectNode,
    selectEdge,
    clearSelection,
    depth,
    setDepth,
    refetch,
    runAdvancedQuery,
    resetAdvancedQuery,
  } = useGraphWorkbenchPage(name)

  const [isQueryDrawerOpen, setIsQueryDrawerOpen] = useState(false)
  const [expandedSubgraphs, setExpandedSubgraphs] = useState<
    Record<string, GraphData>
  >({})
  const canvasRef = useRef<GraphCanvasWorkspaceHandle>(null)

  // 数据变更时清除展开子图
  const baseGraphSceneKey = useMemo(() => {
    if (!graphData) return null
    const nk = graphData.nodes.map((n) => getGraphNodeId(n)).join("|")
    const ek = graphData.edges.map((e) => getGraphEdgeId(e)).join("|")
    return `${nk}::${ek}`
  }, [graphData])

  // 基础图数据变化时，清除展开子图
  useMemo(() => {
    if (baseGraphSceneKey) {
      setExpandedSubgraphs((c) => (Object.keys(c).length ? {} : c))
    }
  }, [baseGraphSceneKey])

  const displayGraphData = useMemo(
    () => mergeGraphData(graphData, Object.values(expandedSubgraphs)),
    [expandedSubgraphs, graphData]
  )

  const graphOverview = useMemo(() => {
    if (!displayGraphData)
      return {
        labelStats: [] as Array<{ key: string; count: number }>,
        relTypeStats: [] as Array<{
          key: string
          count: number
          label: string
        }>,
      }
    const lc = new Map<string, number>()
    const rc = new Map<string, number>()
    displayGraphData.nodes.forEach((n) => {
      const l = n.labels?.[0] || "Unknown"
      lc.set(l, (lc.get(l) ?? 0) + 1)
    })
    displayGraphData.edges.forEach((e) => {
      const r = e.rel_type || "UNKNOWN"
      rc.set(r, (rc.get(r) ?? 0) + 1)
    })
    return {
      labelStats: Array.from(lc.entries()).map(([key, count]) => ({
        key,
        count,
      })),
      relTypeStats: Array.from(rc.entries()).map(([key, count]) => ({
        key,
        count,
        label: relTypeLabels[key] || key,
      })),
    }
  }, [displayGraphData])

  const eventCallbacks = useMemo<GraphEventCallbacks>(
    () => ({
      onNodeSelected: (vizNode: VizNode) => {
        selectNode(vizNode.data)
      },
      onRelationshipSelected: (vizRel: VizRelationship) => {
        selectEdge(vizRel.data)
      },
      onCanvasClicked: () => {
        clearSelection()
      },
      onNodeHover: () => {},
      onRelationshipHover: () => {},
      onNodeDblClicked: async (vizNode: VizNode) => {
        const nodeId = vizNode.id
        // 切换展开/收起
        if (expandedSubgraphs[nodeId]) {
          setExpandedSubgraphs((current) => {
            const next = { ...current }
            delete next[nodeId]
            return next
          })
          // 收起后需要更新图
          const viz = canvasRef.current?.getVisualization()
          const graph = canvasRef.current?.getGraph()
          if (viz && graph) {
            graph.collapseNode(vizNode)
            viz.update({
              updateNodes: true,
              updateRelationships: true,
              restartSimulation: true,
            })
          }
          return
        }

        const expansionGraph = await graphApi.expandNodeGraph(nodeId, 1, 20)
        if (!expansionGraph.center) return

        setExpandedSubgraphs((current) => ({
          ...current,
          [nodeId]: expansionGraph,
        }))

        // 直接在 VizGraph 上添加新节点和关系
        const viz = canvasRef.current?.getVisualization()
        const graph = canvasRef.current?.getGraph()
        if (viz && graph) {
          const newNodes = expansionGraph.nodes
            .filter((n) => !graph.findNode(n.id || n.name))
            .map((n) => {
              const vn = new VizNode(n)
              // 初始位置在展开源节点附近
              const angle =
                Math.random() * Math.PI * 2
              vn.x = vizNode.x + Math.cos(angle) * 170
              vn.y = vizNode.y + Math.sin(angle) * 170
              return vn
            })

          graph.addNodes(newNodes)

          const newRels = expansionGraph.edges
            .map((edge, idx) => {
              const srcId = edge.source?.id || edge.source?.name || ""
              const tgtId = edge.target?.id || edge.target?.name || ""
              const src = graph.findNode(srcId)
              const tgt = graph.findNode(tgtId)
              if (!src || !tgt) return null
              return new VizRelationship(
                src,
                tgt,
                edge,
                edge.id || `exp-${nodeId}-${idx}`
              )
            })
            .filter(Boolean) as VizRelationship[]

          graph.addRelationships(newRels)
          vizNode.expanded = true

          viz.update({
            updateNodes: true,
            updateRelationships: true,
            restartSimulation: true,
          })
        }
      },
    }),
    [clearSelection, expandedSubgraphs, selectEdge, selectNode]
  )

  const openQueryDrawer = useCallback(() => setIsQueryDrawerOpen(true), [])
  const closeQueryDrawer = useCallback(() => setIsQueryDrawerOpen(false), [])

  if (loading) {
    return (
      <div
        style={{
          height: "calc(100vh - 64px)",
          display: "grid",
          placeItems: "center",
        }}
      >
        <Text type="secondary">图谱工作台加载中...</Text>
      </div>
    )
  }

  return (
    <div
      data-testid="graph-workbench-page"
      style={{
        height: "calc(100vh - 64px)",
        display: "grid",
        gridTemplateColumns: "288px minmax(0, 1fr) 312px",
        gap: 16,
        padding: 16,
        background:
          "linear-gradient(180deg, rgba(244, 248, 245, 0.96) 0%, rgba(239, 245, 241, 0.98) 100%)",
        boxSizing: "border-box",
      }}
    >
      <GraphMetadataSidebar
        summary={metaSummary}
        labels={metaLabels}
        relationshipTypes={metaRelationshipTypes}
        propertyKeys={metaPropertyKeys}
        schema={metaSchema}
        loading={metaLoading}
        error={metaError}
        onHighlightLabel={highlightLabel}
        onHighlightRelationshipType={highlightRelationshipType}
      />

      <div
        style={{
          position: "relative",
          minWidth: 0,
          minHeight: 0,
          padding: 14,
          border: "1px solid rgba(163, 185, 169, 0.45)",
          borderRadius: 28,
          background:
            "linear-gradient(180deg, rgba(252, 253, 252, 0.98) 0%, rgba(247, 250, 248, 0.96) 100%)",
          boxShadow:
            "0 1px 0 rgba(255, 255, 255, 0.75) inset, 0 18px 44px rgba(27, 56, 36, 0.08), 0 2px 10px rgba(27, 56, 36, 0.06)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: 26,
            left: 26,
            right: 26,
            zIndex: 2,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            pointerEvents: "none",
          }}
        >
          <div style={{ pointerEvents: "auto" }}>
            <Text strong style={{ fontSize: 20, color: "#203127" }}>
              {mode === "advanced-query" ? "当前查询" : "当前图谱"}
            </Text>
            <Space size={[8, 8]} wrap style={{ display: "flex", marginTop: 10 }}>
              <Tag>{displayGraphData?.nodes.length ?? 0} 个节点</Tag>
              <Tag>{displayGraphData?.edges.length ?? 0} 条关系</Tag>
              {scene.truncated || querySummary?.truncated ? (
                <Tag color="warning">结果已截断</Tag>
              ) : null}
            </Space>
          </div>
          <Space style={{ pointerEvents: "auto" }}>
            <Button onClick={openQueryDrawer}>打开查询器</Button>
            <Button icon={<ReloadOutlined />} onClick={refetch}>
              刷新
            </Button>
          </Space>
        </div>

        <GraphCanvasWorkspace
          ref={canvasRef}
          graphData={displayGraphData}
          eventCallbacks={eventCallbacks}
          onOpenQuery={openQueryDrawer}
        />
      </div>

      <GraphInspectorPanel
        selectedItem={selectedItem}
        nodeCount={displayGraphData?.nodes.length ?? 0}
        relationshipCount={displayGraphData?.edges.length ?? 0}
        labelStats={graphOverview.labelStats}
        relTypeStats={graphOverview.relTypeStats}
        onHighlightLabel={highlightLabel}
        onHighlightRelationshipType={highlightRelationshipType}
      />

      <Drawer
        title="图谱查询器"
        placement="left"
        open={isQueryDrawerOpen}
        onClose={closeQueryDrawer}
        width={420}
      >
        <GraphQueryPanel
          depth={depth}
          loading={loading}
          onDepthChange={setDepth}
          onSubmit={async (request) => {
            await runAdvancedQuery(request)
            closeQueryDrawer()
          }}
          onReset={() => {
            resetAdvancedQuery()
            closeQueryDrawer()
          }}
        />
      </Drawer>
    </div>
  )
}

export default GraphPage
