import { memo, useRef, useEffect, useCallback, useImperativeHandle, forwardRef } from "react"
import { Empty, Button, Space, Typography } from "antd"
import type { GraphData } from "../../types/graph"
import { Visualization, VizGraph, GraphEventHandler } from "../../lib/graph-viz"
import type { GraphEventCallbacks } from "../../lib/graph-viz"
import GraphToolbar from "./GraphToolbar"

const { Text } = Typography

export interface GraphCanvasWorkspaceHandle {
  zoomIn: () => void
  zoomOut: () => void
  zoomToFit: () => void
  getVisualization: () => Visualization | null
  getGraph: () => VizGraph | null
  getEventHandler: () => GraphEventHandler | null
}

interface GraphCanvasWorkspaceProps {
  graphData: GraphData | null
  eventCallbacks: GraphEventCallbacks
  onOpenQuery: () => void
}

const GraphCanvasWorkspace = forwardRef<
  GraphCanvasWorkspaceHandle,
  GraphCanvasWorkspaceProps
>(({ graphData, eventCallbacks, onOpenQuery }, ref) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const vizRef = useRef<Visualization | null>(null)
  const graphModelRef = useRef<VizGraph | null>(null)
  const eventHandlerRef = useRef<GraphEventHandler | null>(null)
  const callbacksRef = useRef(eventCallbacks)
  callbacksRef.current = eventCallbacks

  useImperativeHandle(
    ref,
    () => ({
      zoomIn: () => vizRef.current?.zoomIn(),
      zoomOut: () => vizRef.current?.zoomOut(),
      zoomToFit: () => vizRef.current?.zoomToFit(),
      getVisualization: () => vizRef.current,
      getGraph: () => graphModelRef.current,
      getEventHandler: () => eventHandlerRef.current,
    }),
    []
  )

  useEffect(() => {
    if (!svgRef.current || !graphData) return

    // 清理旧实例
    if (vizRef.current) {
      vizRef.current.destroy()
      vizRef.current = null
      graphModelRef.current = null
      eventHandlerRef.current = null
    }

    const svg = svgRef.current
    const graph = VizGraph.fromGraphData(graphData)
    graphModelRef.current = graph

    const measureSize = () => ({
      width: svg.clientWidth || 800,
      height: svg.clientHeight || 600,
    })

    const viz = new Visualization(svg, measureSize, graph)
    vizRef.current = viz

    const handler = new GraphEventHandler(graph, viz, callbacksRef.current)
    eventHandlerRef.current = handler
    handler.bindEventHandlers()

    viz.init()
    viz.precomputeAndStart()

    return () => {
      viz.destroy()
    }
  }, [graphData])

  // 响应尺寸变化
  useEffect(() => {
    if (!containerRef.current) return
    const observer = new ResizeObserver(() => {
      vizRef.current?.resize()
    })
    observer.observe(containerRef.current)
    return () => observer.disconnect()
  }, [])

  const handleZoomIn = useCallback(() => vizRef.current?.zoomIn(), [])
  const handleZoomOut = useCallback(() => vizRef.current?.zoomOut(), [])
  const handleZoomToFit = useCallback(() => vizRef.current?.zoomToFit(), [])

  return (
    <div
      ref={containerRef}
      data-testid="graph-canvas-workspace"
      style={{
        position: "relative",
        height: "100%",
        minHeight: "100%",
        borderRadius: 22,
        overflow: "hidden",
        background:
          "radial-gradient(circle at 24% 18%, rgba(228, 240, 233, 0.96) 0%, rgba(247, 250, 248, 0.94) 34%, rgba(239, 245, 241, 0.92) 100%)",
        boxShadow: "inset 0 0 0 1px rgba(183, 201, 188, 0.38)",
      }}
    >
      {graphData ? (
        <>
          <svg
            ref={svgRef}
            style={{ width: "100%", height: "100%", cursor: "grab" }}
          />
          <GraphToolbar
            onZoomIn={handleZoomIn}
            onZoomOut={handleZoomOut}
            onZoomToFit={handleZoomToFit}
          />
        </>
      ) : (
        <div style={{ height: "100%", display: "grid", placeItems: "center" }}>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <Space direction="vertical" size={8}>
                <Text strong style={{ color: "#203127", fontSize: 16 }}>
                  等待一张新图谱进入工作区
                </Text>
                <Button type="primary" onClick={onOpenQuery}>
                  立即开始查询
                </Button>
              </Space>
            }
          />
        </div>
      )}
    </div>
  )
})

GraphCanvasWorkspace.displayName = "GraphCanvasWorkspace"

export default memo(GraphCanvasWorkspace)
