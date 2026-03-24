import { type D3DragEvent, drag as d3Drag } from "d3-drag"
import type { Simulation } from "d3-force"
import type { BaseType, Selection } from "d3-selection"

import {
  DEFAULT_ALPHA_TARGET,
  DRAG_THRESHOLD,
  DRAGGING_ALPHA,
  DRAGGING_ALPHA_TARGET,
} from "./constants"
import type { VizNode } from "./models/VizNode"
import type { VizRelationship } from "./models/VizRelationship"

export function nodeEventHandlers(
  selection: Selection<SVGGElement, VizNode, BaseType, unknown>,
  trigger: (event: string, node: VizNode) => void,
  simulation: Simulation<VizNode, VizRelationship>
) {
  let initialPos: [number, number]
  let restarted = false

  const onNodeClick = (_event: Event, node: VizNode) => {
    trigger("nodeClicked", node)
  }

  const onNodeDblClick = (_event: Event, node: VizNode) => {
    trigger("nodeDblClicked", node)
  }

  const onNodeMouseOver = (_event: Event, node: VizNode) => {
    if (!node.fx && !node.fy) {
      node.hoverFixed = true
      node.fx = node.x
      node.fy = node.y
    }
    trigger("nodeMouseOver", node)
  }

  const onNodeMouseOut = (_event: Event, node: VizNode) => {
    if (node.hoverFixed) {
      node.hoverFixed = false
      node.fx = null
      node.fy = null
    }
    trigger("nodeMouseOut", node)
  }

  const dragstarted = (event: D3DragEvent<SVGGElement, VizNode, unknown>) => {
    initialPos = [event.x, event.y]
    restarted = false
  }

  const dragged = (
    event: D3DragEvent<SVGGElement, VizNode, unknown>,
    node: VizNode
  ) => {
    const dist =
      Math.pow(initialPos[0] - event.x, 2) +
      Math.pow(initialPos[1] - event.y, 2)

    if (dist > DRAG_THRESHOLD && !restarted) {
      simulation
        .alphaTarget(DRAGGING_ALPHA_TARGET)
        .alpha(DRAGGING_ALPHA)
        .restart()
      restarted = true
    }

    node.hoverFixed = false
    node.fx = event.x
    node.fy = event.y
  }

  const dragended = () => {
    if (restarted) {
      simulation.alphaTarget(DEFAULT_ALPHA_TARGET)
    }
  }

  return selection
    .call(
      d3Drag<SVGGElement, VizNode>()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended)
    )
    .on("mouseover", onNodeMouseOver)
    .on("mouseout", onNodeMouseOut)
    .on("click", onNodeClick)
    .on("dblclick", onNodeDblClick)
}

export function relationshipEventHandlers(
  selection: Selection<SVGGElement, VizRelationship, BaseType, unknown>,
  trigger: (event: string, rel: VizRelationship) => void
) {
  return selection
    .on("mousedown", (event: Event, rel: VizRelationship) => {
      event.stopPropagation()
      trigger("relationshipClicked", rel)
    })
    .on("mouseover", (_event: Event, rel: VizRelationship) => {
      trigger("relMouseOver", rel)
    })
    .on("mouseout", (_event: Event, rel: VizRelationship) => {
      trigger("relMouseOut", rel)
    })
}
