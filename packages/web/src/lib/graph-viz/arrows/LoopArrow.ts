class Pt {
  constructor(public x: number, public y: number) {}
  toString() {
    return `${this.x} ${this.y}`
  }
}

export class LoopArrow {
  midShaftPoint: Pt
  outline: () => string
  overlay: (minWidth: number) => string
  shaftLength: number

  constructor(
    nodeRadius: number,
    straightLength: number,
    spreadDegrees: number,
    shaftWidth: number,
    headWidth: number,
    headLength: number,
    captionHeight: number
  ) {
    const spread = (spreadDegrees * Math.PI) / 180
    const r1 = nodeRadius
    const r2 = nodeRadius + headLength
    const r3 = nodeRadius + straightLength
    const loopR = r3 * Math.tan(spread / 2)
    const shaftR = shaftWidth / 2
    this.shaftLength = loopR * 3 + shaftWidth

    const normalPoint = (sweep: number, radius: number, disp: number) => {
      const lr = radius * Math.tan(spread / 2)
      const cy = radius / Math.cos(spread / 2)
      return new Pt(
        (lr + disp) * Math.sin(sweep),
        cy + (lr + disp) * Math.cos(sweep)
      )
    }

    this.midShaftPoint = normalPoint(0, r3, shaftR + captionHeight / 2 + 2)

    const startPt = (radius: number, disp: number) =>
      normalPoint((Math.PI + spread) / 2, radius, disp)
    const endPt = (radius: number, disp: number) =>
      normalPoint(-(Math.PI + spread) / 2, radius, disp)

    this.outline = () => {
      const inner = loopR - shaftR
      const outer = loopR + shaftR
      return [
        "M", startPt(r1, shaftR),
        "L", startPt(r3, shaftR),
        "A", outer, outer, 0, 1, 1, endPt(r3, shaftR),
        "L", endPt(r2, shaftR),
        "L", endPt(r2, -headWidth / 2),
        "L", endPt(r1, 0),
        "L", endPt(r2, headWidth / 2),
        "L", endPt(r2, -shaftR),
        "L", endPt(r3, -shaftR),
        "A", inner, inner, 0, 1, 0, startPt(r3, -shaftR),
        "L", startPt(r1, -shaftR),
        "Z",
      ].join(" ")
    }

    this.overlay = (minWidth: number) => {
      const d = Math.max(minWidth / 2, shaftR)
      const inner = loopR - d
      const outer = loopR + d
      return [
        "M", startPt(r1, d),
        "L", startPt(r3, d),
        "A", outer, outer, 0, 1, 1, endPt(r3, d),
        "L", endPt(r2, d),
        "L", endPt(r2, -d),
        "L", endPt(r3, -d),
        "A", inner, inner, 0, 1, 0, startPt(r3, -d),
        "L", startPt(r1, -d),
        "Z",
      ].join(" ")
    }
  }
}
