import type { RelationshipCaptionLayout } from "../models/VizRelationship"

export class StraightArrow {
  length: number
  midShaftPoint: { x: number; y: number }
  outline: (shortCaptionLength: number) => string
  overlay: (minWidth: number) => string
  shaftLength: number
  deflection = 0

  constructor(
    startRadius: number,
    endRadius: number,
    centreDistance: number,
    shaftWidth: number,
    headWidth: number,
    headHeight: number,
    captionLayout: RelationshipCaptionLayout
  ) {
    this.length = centreDistance - (startRadius + endRadius)
    this.shaftLength = this.length - headHeight
    const startArrow = startRadius
    const endShaft = startArrow + this.shaftLength
    const endArrow = startArrow + this.length
    const shaftR = shaftWidth / 2
    const headR = headWidth / 2

    this.midShaftPoint = { x: startArrow + this.shaftLength / 2, y: 0 }

    this.outline = (shortCaptionLength: number) => {
      if (captionLayout === "external") {
        const sb = startArrow + (this.shaftLength - shortCaptionLength) / 2
        const eb = endShaft - (this.shaftLength - shortCaptionLength) / 2
        return [
          "M", startArrow, shaftR,
          "L", sb, shaftR, "L", sb, -shaftR,
          "L", startArrow, -shaftR, "Z",
          "M", eb, shaftR,
          "L", endShaft, shaftR, "L", endShaft, headR,
          "L", endArrow, 0,
          "L", endShaft, -headR, "L", endShaft, -shaftR,
          "L", eb, -shaftR, "Z",
        ].join(" ")
      }
      return [
        "M", startArrow, shaftR,
        "L", endShaft, shaftR, "L", endShaft, headR,
        "L", endArrow, 0,
        "L", endShaft, -headR, "L", endShaft, -shaftR,
        "L", startArrow, -shaftR, "Z",
      ].join(" ")
    }

    this.overlay = (minWidth: number) => {
      const r = Math.max(minWidth / 2, shaftR)
      return [
        "M", startArrow, r,
        "L", endArrow, r,
        "L", endArrow, -r,
        "L", startArrow, -r, "Z",
      ].join(" ")
    }
  }
}
