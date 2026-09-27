import { memo, useEffect, useRef } from "react"
import cytoscape, { type Core, type ElementDefinition } from "cytoscape"
import { Button, Typography } from "../ui/index"
import { PlusOutlined } from "../ui/icons"
import type { GraphData, GraphEdge, GraphNode } from "../../types/graph"
import { relTypeLabels } from "../../types/graph"
import GraphToolbar from "./GraphToolbar"

const { Text } = Typography

interface GraphCanvasWorkspaceProps {
  graphData: GraphData | null
  highlightedLabel: string | null
  highlightedRelationshipType: string | null
  onNodeSelect: (node: GraphNode) => void
  onEdgeSelect: (edge: GraphEdge) => void
  onCanvasClick: () => void
  onNodeDoubleClick: (node: GraphNode) => void
  onOpenQuery: () => void
}

const nodeId = (node: GraphNode) => node.id || node.name
const edgeId = (edge: GraphEdge, index: number) =>
  `edge:${edge.id || `${edge.source?.id || edge.source?.name}:${edge.rel_type}:${edge.target?.id || edge.target?.name}:${index}`}`

const nodeColor = (label?: string) => {
  if (label === "药材" || label === "Herb") return "#2f7654"
  if (label === "功效" || label === "Efficacy") return "#1c8b91"
  if (label === "来源" || label === "Source") return "#b76b48"
  return "#4b6fa8"
}

function graphElements(graph: GraphData) {
  const nodes = new Map(graph.nodes.map((node) => [nodeId(node), node]))
  const edges = new Map<string, GraphEdge>()
  const elements: ElementDefinition[] = graph.nodes.map((node) => ({
    data: {
      id: nodeId(node),
      label: node.name,
      color: nodeColor(node.labels?.[0]),
      nodeType: node.labels?.[0] || "",
    },
  }))

  graph.edges.forEach((edge, index) => {
    const source = edge.source?.id || edge.source?.name
    const target = edge.target?.id || edge.target?.name
    if (!source || !target || !nodes.has(source) || !nodes.has(target)) return
    const id = edgeId(edge, index)
    edges.set(id, edge)
    elements.push({
      data: {
        id,
        source,
        target,
        label: relTypeLabels[edge.rel_type || ""] || edge.rel_type || "",
        relType: edge.rel_type || "",
      },
    })
  })

  return { elements, nodes, edges }
}

const GraphCanvasWorkspace = ({
  graphData,
  highlightedLabel,
  highlightedRelationshipType,
  onNodeSelect,
  onEdgeSelect,
  onCanvasClick,
  onNodeDoubleClick,
  onOpenQuery,
}: GraphCanvasWorkspaceProps) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<Core | null>(null)
  const callbacksRef = useRef({ onNodeSelect, onEdgeSelect, onCanvasClick, onNodeDoubleClick })
  callbacksRef.current = { onNodeSelect, onEdgeSelect, onCanvasClick, onNodeDoubleClick }

  useEffect(() => {
    if (!containerRef.current || !graphData?.edges.length) return
    const { elements, nodes, edges } = graphElements(graphData)
    const cy = cytoscape({
      container: containerRef.current,
      elements,
      layout: graphData.nodes.length <= 8
        ? { name: "circle", animate: false, fit: true, padding: 40, nodeDimensionsIncludeLabels: true, avoidOverlap: true, radius: graphData.nodes.length <= 4 ? 90 : 150 }
        : { name: "cose", animate: false, fit: true, padding: 48, nodeDimensionsIncludeLabels: true, componentSpacing: 80, idealEdgeLength: 100 },
      minZoom: 0.25,
      maxZoom: 1.25,
      style: [
        { selector: "node", style: { "background-color": "data(color)", label: "data(label)", color: "#203127", "font-size": 14, "font-weight": "bold", "text-valign": "bottom", "text-halign": "center", "text-margin-y": 8, "text-wrap": "ellipsis", "text-max-width": "92px", "text-background-color": "#fbfdfb", "text-background-opacity": 0.95, "text-background-padding": "2px", width: 36, height: 36, "border-width": 2, "border-color": "#fff" } },
        { selector: "edge", style: { width: 2, "line-color": "#91a69a", "target-arrow-color": "#91a69a", "target-arrow-shape": "triangle", "curve-style": "bezier", label: "data(label)", color: "#52645b", "font-size": 11, "text-background-color": "#fbfdfb", "text-background-opacity": 1, "text-background-padding": "3px" } },
        { selector: ":selected", style: { "border-color": "#d18a3c", "border-width": 4 } },
        { selector: ".muted", style: { opacity: 0.18 } },
      ],
    })
    cyRef.current = cy
    cy.on("tap", "node", (event) => {
      const node = nodes.get(event.target.id())
      if (node) callbacksRef.current.onNodeSelect(node)
    })
    cy.on("tap", "edge", (event) => {
      const edge = edges.get(event.target.id())
      if (edge) callbacksRef.current.onEdgeSelect(edge)
    })
    cy.on("tap", (event) => {
      if (event.target === cy) callbacksRef.current.onCanvasClick()
    })
    cy.on("dbltap", "node", (event) => {
      const node = nodes.get(event.target.id())
      if (node) callbacksRef.current.onNodeDoubleClick(node)
    })
    cy.on("mouseover", "node", (event) => {
      containerRef.current?.setAttribute("title", nodes.get(event.target.id())?.name || "")
    })
    cy.on("mouseout", "node", () => containerRef.current?.removeAttribute("title"))

    const observer = new ResizeObserver(() => {
      cy.resize()
      cy.fit(undefined, 48)
    })
    observer.observe(containerRef.current)
    return () => {
      observer.disconnect()
      cy.destroy()
      cyRef.current = null
    }
  }, [graphData])

  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.elements().removeClass("muted")
    if (highlightedLabel) {
      cy.nodes().forEach((node) => {
        if (node.data("nodeType") !== highlightedLabel) node.addClass("muted")
      })
    }
    if (highlightedRelationshipType) {
      cy.edges().forEach((edge) => {
        if (edge.data("relType") !== highlightedRelationshipType) edge.addClass("muted")
      })
    }
  }, [graphData, highlightedLabel, highlightedRelationshipType])

  return (
    <div data-testid="graph-canvas-workspace" style={{ position: "relative", height: "100%", overflow: "hidden", background: "#fbfdfb" }}>
      {graphData?.edges.length ? (
        <>
          <div ref={containerRef} aria-label="图谱可视化" style={{ width: "100%", height: "100%" }} />
          <GraphToolbar
            onZoomIn={() => cyRef.current?.zoom(cyRef.current.zoom() * 1.25)}
            onZoomOut={() => cyRef.current?.zoom(cyRef.current.zoom() / 1.25)}
            onZoomToFit={() => cyRef.current?.fit(undefined, 48)}
          />
        </>
      ) : graphData?.nodes.length ? (
        <div className="graph-node-list" aria-label="匹配节点">
          {graphData.nodes.map((node) => (
            <div
              key={nodeId(node)}
              className="graph-node-list-item"
              style={{ opacity: highlightedLabel && node.labels?.[0] !== highlightedLabel ? 0.3 : 1 }}
            >
              <button type="button" className="graph-node-list-select" onClick={() => onNodeSelect(node)}>
                <span className="graph-node-list-dot" style={{ background: nodeColor(node.labels?.[0]) }} />
                <span className="graph-node-list-text">
                  <strong>{node.name}</strong>
                  <small>{node.labels?.[0] || "节点"}</small>
                </span>
              </button>
              <Button size="small" title="展开节点" aria-label={`展开 ${node.name}`} icon={<PlusOutlined />} onClick={() => onNodeDoubleClick(node)} />
            </div>
          ))}
        </div>
      ) : (
        <div style={{ height: "100%", display: "grid", placeItems: "center", textAlign: "center" }}>
          <div>
            <Text strong style={{ display: "block", color: "#203127", fontSize: 16 }}>暂无图谱结果</Text>
            <Button type="primary" onClick={onOpenQuery} style={{ marginTop: 16 }}>打开查询器</Button>
          </div>
        </div>
      )}
    </div>
  )
}

export default memo(GraphCanvasWorkspace)
