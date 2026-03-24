import type { BaseType, Selection } from "d3-selection"
import type { VizNode, NodeCaptionLine } from "../models/VizNode"
import type { VizRelationship } from "../models/VizRelationship"
import { CAPTION_FONT_SIZE } from "../constants"

const noop = () => undefined
const RING_STROKE = 8

export interface NodeRenderer {
  onGraphChange: (
    sel: Selection<SVGGElement, VizNode, BaseType, unknown>
  ) => void
  onTick: (
    sel: Selection<SVGGElement, VizNode, BaseType, unknown>
  ) => void
}

export interface RelRenderer {
  onGraphChange: (
    sel: Selection<SVGGElement, VizRelationship, BaseType, unknown>
  ) => void
  onTick: (
    sel: Selection<SVGGElement, VizRelationship, BaseType, unknown>
  ) => void
}

export const nodeOutline: NodeRenderer = {
  onGraphChange(sel) {
    sel
      .selectAll("circle.b-outline")
      .data((n) => [n])
      .join("circle")
      .classed("b-outline", true)
      .attr("cx", 0)
      .attr("cy", 0)
      .attr("r", (n: VizNode) => n.radius)
      .attr("fill", (n: VizNode) => n.fill)
      .attr("stroke", (n: VizNode) => n.stroke)
      .attr("stroke-width", 2)
  },
  onTick: noop,
}

export const nodeCaption: NodeRenderer = {
  onGraphChange(sel) {
    sel
      .selectAll("text.caption")
      .data((n: VizNode) => n.caption)
      .join("text")
      .classed("caption", true)
      .attr("text-anchor", "middle")
      .attr("pointer-events", "none")
      .attr("x", 0)
      .attr("y", (line: NodeCaptionLine) => line.baseline)
      .attr("font-size", CAPTION_FONT_SIZE)
      .attr("fill", (line: NodeCaptionLine) => line.node.textColor)
      .text((line: NodeCaptionLine) => line.text)
  },
  onTick: noop,
}

export const nodeRing: NodeRenderer = {
  onGraphChange(sel) {
    sel
      .selectAll("circle.ring")
      .data((n: VizNode) => [n])
      .join(
        (enter) =>
          enter
            .insert("circle", ".b-outline")
            .classed("ring", true)
            .attr("cx", 0)
            .attr("cy", 0)
            .attr("stroke-width", `${RING_STROKE}px`)
            .attr("r", (n) => n.radius + 4)
            .attr("fill", "none")
            .attr("stroke", (n) => n.stroke)
            .attr("opacity", 0)
            .attr("pointer-events", "none"),
        (update) =>
          update
            .attr("r", (n) => n.radius + 4)
            .attr("stroke", (n) => n.stroke)
            .attr("opacity", (n) => (n.selected ? 0.6 : 0)),
        (exit) => exit.remove()
      )
  },
  onTick: noop,
}

export const arrowPath: RelRenderer = {
  onGraphChange(sel) {
    sel
      .selectAll("path.b-outline")
      .data((r) => [r])
      .join("path")
      .classed("b-outline", true)
      .attr("fill", "#8DCC93")
      .attr("stroke", "none")
  },
  onTick(sel) {
    sel
      .selectAll<BaseType, VizRelationship>("path.b-outline")
      .attr("d", (d) => d.arrow?.outline(d.shortCaptionLength ?? 0) ?? "")
  },
}

export const relationshipType: RelRenderer = {
  onGraphChange(sel) {
    sel
      .selectAll("text")
      .data((r) => [r])
      .join("text")
      .attr("text-anchor", "middle")
      .attr("pointer-events", "none")
      .attr("font-size", CAPTION_FONT_SIZE)
      .attr("fill", "#555")
  },
  onTick(sel) {
    sel
      .selectAll<BaseType, VizRelationship>("text")
      .attr("x", (r) => r.arrow?.midShaftPoint?.x ?? 0)
      .attr(
        "y",
        (r) => (r.arrow?.midShaftPoint?.y ?? 0) + CAPTION_FONT_SIZE / 2 - 1
      )
      .attr("transform", (r) => {
        if (r.naturalAngle < 90 || r.naturalAngle > 270) {
          return `rotate(180 ${r.arrow?.midShaftPoint?.x ?? 0} ${r.arrow?.midShaftPoint?.y ?? 0})`
        }
        return null as unknown as string
      })
      .text((r) => r.shortCaption ?? "")
  },
}

export const relationshipOverlay: RelRenderer = {
  onGraphChange(sel) {
    sel
      .selectAll("path.overlay")
      .data((r) => [r])
      .join("path")
      .classed("overlay", true)
      .attr("fill", "transparent")
      .attr("stroke", "none")
  },
  onTick(sel) {
    const band = 16
    sel
      .selectAll<BaseType, VizRelationship>("path.overlay")
      .attr("d", (d) => d.arrow?.overlay(band) ?? "")
  },
}

export const nodeRenderers: NodeRenderer[] = [nodeOutline, nodeCaption, nodeRing]
export const relationshipRenderers: RelRenderer[] = [
  arrowPath,
  relationshipType,
  relationshipOverlay,
]
