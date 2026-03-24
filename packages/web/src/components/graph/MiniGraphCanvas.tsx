import { useRef, useEffect, useCallback } from "react"
import type { GraphData } from "../../types/graph"
import { Visualization, VizGraph, VizNode, VizRelationship, GraphEventHandler } from "../../lib/graph-viz"

interface MiniGraphCanvasProps {
  graphData: GraphData
  onNodeClick?: (node: VizNode) => void
  onEdgeClick?: (rel: VizRelationship) => void
  onNodeHover?: (node: VizNode | null) => void
  onEdgeHover?: (rel: VizRelationship | null) => void
  onCanvasClick?: () => void
}

export default function MiniGraphCanvas({
  graphData,
  onNodeClick,
  onEdgeClick,
  onNodeHover,
  onEdgeHover,
  onCanvasClick,
}: MiniGraphCanvasProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const vizRef = useRef<Visualization | null>(null)

  useEffect(() => {
    if (!svgRef.current) return

    vizRef.current?.destroy()
    const svg = svgRef.current
    const graph = VizGraph.fromGraphData(graphData)

    const measureSize = () => ({
      width: svg.clientWidth || 600,
      height: svg.clientHeight || 320,
    })

    const viz = new Visualization(svg, measureSize, graph)
    vizRef.current = viz

    const handler = new GraphEventHandler(graph, viz, {
      onNodeSelected: (n) => onNodeClick?.(n),
      onRelationshipSelected: (r) => onEdgeClick?.(r),
      onCanvasClicked: () => onCanvasClick?.(),
      onNodeHover: (n) => onNodeHover?.(n),
      onRelationshipHover: (r) => onEdgeHover?.(r),
      onNodeDblClicked: () => {},
    })
    handler.bindEventHandlers()

    viz.init()
    viz.precomputeAndStart()

    return () => {
      viz.destroy()
      vizRef.current = null
    }
  }, [graphData])

  const handleZoomToFit = useCallback(() => vizRef.current?.zoomToFit(), [])

  return (
    <svg
      ref={svgRef}
      style={{ width: "100%", height: "100%", cursor: "grab" }}
    />
  )
}
