import type { GraphEdge } from "../../../types/graph"
import { relTypeLabels } from "../../../types/graph"
import type { VizNode } from "./VizNode"
import type { ArcArrow } from "../arrows/ArcArrow"
import type { StraightArrow } from "../arrows/StraightArrow"
import type { LoopArrow } from "../arrows/LoopArrow"
import { CAPTION_FONT_SIZE } from "../constants"

export type RelationshipCaptionLayout = "internal" | "external"

export class VizRelationship {
  id: string
  source: VizNode
  target: VizNode
  type: string
  data: GraphEdge

  // 几何缓存
  naturalAngle: number = 0
  centreDistance: number = 0
  arrow?: ArcArrow | StraightArrow | LoopArrow

  // 标签
  caption: string
  captionLength: number = 0
  captionHeight: number = CAPTION_FONT_SIZE
  captionLayout: RelationshipCaptionLayout = "external"
  shortCaption?: string
  shortCaptionLength?: number

  // 状态
  selected: boolean = false
  internal: boolean = true

  constructor(source: VizNode, target: VizNode, data: GraphEdge, id: string) {
    this.id = id
    this.source = source
    this.target = target
    this.type = data.rel_type || ""
    this.data = data
    this.caption = relTypeLabels[this.type] || this.type
  }

  isLoop(): boolean {
    return this.source === this.target
  }

  get isNode(): boolean {
    return false
  }

  get isRelationship(): boolean {
    return true
  }
}
