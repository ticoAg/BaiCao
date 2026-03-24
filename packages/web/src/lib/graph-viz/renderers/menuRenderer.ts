import { arc as d3Arc } from "d3-shape"
import type { BaseType, Selection } from "d3-selection"
import type { VizNode } from "../models/VizNode"
import { CONTEXT_MENU_ITEM_COUNT, CONTEXT_MENU_WIDTH, CONTEXT_MENU_PAD_ANGLE } from "../constants"

export interface MenuRenderer {
  onGraphChange: (
    sel: Selection<SVGGElement, VizNode, BaseType, unknown>,
    trigger: (event: string, node: VizNode) => void
  ) => void
}

function drawArc(radius: number, itemNumber: number, width = CONTEXT_MENU_WIDTH) {
  const startAngle =
    ((2 * Math.PI) / CONTEXT_MENU_ITEM_COUNT) * (itemNumber - 1)
  const endAngle = startAngle + (2 * Math.PI) / CONTEXT_MENU_ITEM_COUNT
  const innerRadius = Math.max(radius + 8, 20)
  return d3Arc<VizNode>()
    .innerRadius(innerRadius)
    .outerRadius(innerRadius + width)
    .startAngle(startAngle)
    .endAngle(endAngle)
    .padAngle(CONTEXT_MENU_PAD_ANGLE)
}

const selectedNodes = (node: VizNode) => (node.selected ? [node] : [])

// SVG 图标（简单 unicode 符号）
const ICON_EXPAND = "\u2B1C" // ⬜ 展开
const ICON_REMOVE = "\u2716" // ✖ 移除
const ICON_UNLOCK = "\u{1F513}" // 🔓 解锁

function createMenuItem(
  selection: Selection<SVGGElement, VizNode, BaseType, unknown>,
  trigger: (event: string, node: VizNode) => void,
  eventType: string,
  itemIndex: number,
  className: string,
  label: string
) {
  // 弧形背景
  const tab = selection
    .selectAll(`path.${className}`)
    .data(selectedNodes)
    .join("path")
    .classed(className, true)
    .classed("context-menu-item", true)
    .attr("fill", "rgba(0,0,0,0.6)")
    .attr("cursor", "pointer")
    .attr("d", (node) => drawArc(node.radius, itemIndex)(node as any) ?? "")

  // 图标文字
  const icon = selection
    .selectAll(`text.icon-${className}`)
    .data(selectedNodes)
    .join("text")
    .classed(`icon-${className}`, true)
    .classed("context-menu-item", true)
    .attr("text-anchor", "middle")
    .attr("dominant-baseline", "central")
    .attr("font-size", 12)
    .attr("fill", "#fff")
    .attr("pointer-events", "none")
    .attr("x", (node) => {
      const c = drawArc(node.radius, itemIndex).centroid(node as any)
      return c ? c[0] : 0
    })
    .attr("y", (node) => {
      const c = drawArc(node.radius, itemIndex).centroid(node as any)
      return c ? c[1] : 0
    })
    .text(label)

  // 事件绑定
  tab
    .on("mousedown.drag", (event: Event) => {
      event.stopPropagation()
    })
    .on("mouseup", (_event: Event, node: VizNode) => {
      trigger(eventType, node)
    })
    .on("mouseover", (_event: Event, node: VizNode) => {
      node.contextMenu = {
        menuSelection: eventType,
        menuContent: label,
        label,
      }
      trigger("menuMouseOver", node)
    })
    .on("mouseout", (_event: Event, node: VizNode) => {
      node.contextMenu = null
      trigger("menuMouseOut", node)
    })

  return { tab, icon }
}

export const expandMenuItem: MenuRenderer = {
  onGraphChange(sel, trigger) {
    createMenuItem(sel, trigger, "nodeDblClicked", 1, "expand-node", "展开")
  },
}

export const removeMenuItem: MenuRenderer = {
  onGraphChange(sel, trigger) {
    createMenuItem(sel, trigger, "nodeClose", 2, "remove-node", "移除")
  },
}

export const unlockMenuItem: MenuRenderer = {
  onGraphChange(sel, trigger) {
    createMenuItem(sel, trigger, "nodeUnlock", 3, "unlock-node", "解锁")
  },
}

export const menuRenderers: MenuRenderer[] = [
  expandMenuItem,
  removeMenuItem,
  unlockMenuItem,
]
