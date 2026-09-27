import { useCallback, useEffect, useMemo, useState } from "react"
import { Button, Drawer, Space, Tag, Typography } from "../components/ui/index"
import { ReloadOutlined } from "../components/ui/icons"
import { useParams } from "react-router-dom"
import { graphApi } from "../services/api"
import { useGraphWorkbenchPage } from "../hooks/useGraphWorkbenchPage"
import type { GraphData, GraphNode, GraphEdge } from "../types/graph"
import { relTypeLabels } from "../types/graph"
import GraphCanvasWorkspace from "../components/graph/GraphCanvasWorkspace"
import GraphInspectorPanel from "../components/graph/GraphInspectorPanel"
import GraphQueryPanel from "../components/graph/GraphQueryPanel"

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
    sceneError,
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
  const [expansionError, setExpansionError] = useState(false)
  const [expandedSubgraphs, setExpandedSubgraphs] = useState<
    Record<string, GraphData>
  >({})

  // 数据变更时清除展开子图
  const baseGraphSceneKey = useMemo(() => {
    if (!graphData) return null
    const nk = graphData.nodes.map((n) => getGraphNodeId(n)).join("|")
    const ek = graphData.edges.map((e) => getGraphEdgeId(e)).join("|")
    return `${nk}::${ek}`
  }, [graphData])

  // 基础图数据变化时，清除展开子图
  useEffect(() => {
    if (baseGraphSceneKey) {
      setExpandedSubgraphs({})
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

  const onNodeDoubleClick = useCallback(async (node: GraphNode) => {
    const id = getGraphNodeId(node)
    if (expandedSubgraphs[id]) {
      setExpandedSubgraphs((current) => {
        const next = { ...current }
        delete next[id]
        return next
      })
      return
    }

    // ponytail: 局部展开最多展示 40 个节点；需要更大图时改为分页探索。
    const remaining = 40 - (displayGraphData?.nodes.length ?? 0)
    if (remaining <= 0) return
    try {
      const expansion = await graphApi.expandNodeGraph(id, 1, Math.min(10, remaining))
      if (expansion.center) {
        setExpansionError(false)
        setExpandedSubgraphs((current) => ({ ...current, [id]: expansion }))
      }
    } catch {
      setExpansionError(true)
    }
  }, [displayGraphData, expandedSubgraphs])

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
      className={`graph-page${displayGraphData ? "" : " graph-page--empty"}`}
    >
      <div
        className="graph-main"
      >
        <div
          className="graph-header"
        >
          <div>
            <Text strong style={{ fontSize: 18, color: "#203127" }}>
              {mode === "advanced-query" ? "查询结果" : name ? `${name} · 关联图谱` : "知识图谱"}
            </Text>
            <Space size={[8, 8]} wrap style={{ display: "flex", marginTop: 6 }}>
              <Tag>{displayGraphData?.nodes.length ?? 0} 个节点</Tag>
              <Tag>{displayGraphData?.edges.length ?? 0} 条关系</Tag>
              {scene.truncated || querySummary?.truncated ? (
                <Tag color="warning">仅展示部分结果</Tag>
              ) : null}
              {(displayGraphData?.nodes.length ?? 0) >= 40 ? <Tag color="warning">已达 40 节点上限</Tag> : null}
              {sceneError ? <Tag color="warning">图谱加载失败</Tag> : null}
              {expansionError ? <Tag color="warning">展开节点失败</Tag> : null}
            </Space>
          </div>
          <Space>
            <Button onClick={openQueryDrawer}>打开查询器</Button>
            <Button icon={<ReloadOutlined />} onClick={refetch}>
              刷新
            </Button>
          </Space>
        </div>

        <div className="graph-canvas-area">
          <GraphCanvasWorkspace
            graphData={displayGraphData}
            highlightedLabel={highlightedLabel}
            highlightedRelationshipType={highlightedRelationshipType}
            onNodeSelect={selectNode}
            onEdgeSelect={selectEdge}
            onCanvasClick={clearSelection}
            onNodeDoubleClick={onNodeDoubleClick}
            onOpenQuery={openQueryDrawer}
          />
        </div>
      </div>

      {displayGraphData ? (
        <GraphInspectorPanel
          selectedItem={selectedItem}
          nodeCount={displayGraphData.nodes.length}
          relationshipCount={displayGraphData.edges.length}
          labelStats={graphOverview.labelStats}
          relTypeStats={graphOverview.relTypeStats}
          onHighlightLabel={highlightLabel}
          onHighlightRelationshipType={highlightRelationshipType}
        />
      ) : null}

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
