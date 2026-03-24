import type { SimulationNodeDatum } from "d3-force"
import type { GraphNode } from "../../../types/graph"
import { nodeStyleMap, defaultNodeStyle } from "../../../types/graph"
import { NODE_RADIUS } from "../constants"

export interface NodeCaptionLine {
  node: VizNode
  text: string
  baseline: number
  remainingWidth: number
}

export interface ContextMenuItem {
  menuSelection: string
  menuContent: string
  label: string
}

export class VizNode implements SimulationNodeDatum {
  id: string
  labels: string[]
  name: string
  data: GraphNode

  // d3-force 位置
  x: number = 0
  y: number = 0
  vx?: number
  vy?: number
  fx: number | null = null
  fy: number | null = null
  index?: number

  // 可视化状态
  radius: number = NODE_RADIUS
  selected: boolean = false
  expanded: boolean = false
  hoverFixed: boolean = false
  contextMenu: ContextMenuItem | null = null

  // 渲染缓存
  caption: NodeCaptionLine[] = []

  // 样式
  fill: string
  stroke: string
  textColor: string

  constructor(data: GraphNode) {
    this.id = data.id || data.name
    this.labels = data.labels || []
    this.name = data.name
    this.data = data

    const primaryLabel = this.labels[0] || "Unknown"
    const style = nodeStyleMap[primaryLabel] || defaultNodeStyle
    this.fill = style.fill
    this.stroke = style.stroke
    this.textColor = style.textColor
  }

  get isNode(): boolean {
    return true
  }

  get isRelationship(): boolean {
    return false
  }
}
