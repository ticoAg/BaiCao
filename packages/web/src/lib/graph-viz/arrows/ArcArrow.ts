import type { RelationshipCaptionLayout } from "../models/VizRelationship"

type Point = { x: number; y: number }
const sq = (l: number) => l * l
const coord = (p: Point) => `${p.x},${p.y}`

function intersectCircle(
  fixedPt: Point,
  radius: number,
  xCenter: number,
  polarity: number,
  hc: number
): Point {
  const g = fixedPt.y / (fixedPt.x - hc)
  const c = fixedPt.y - g * fixedPt.x
  const A = 1 + sq(g)
  const B = 2 * (g * c - xCenter)
  const C = sq(c) + sq(xCenter) - sq(radius)
  const x = (-B + polarity * Math.sqrt(sq(B) - 4 * A * C)) / (2 * A)
  return { x, y: (x - hc) * g }
}

export class ArcArrow {
  deflection: number
  midShaftPoint: Point
  outline: (shortCaptionLength: number) => string
  overlay: (minWidth: number) => string
  shaftLength: number

  constructor(
    startRadius: number,
    endRadius: number,
    endCentre: number,
    deflection: number,
    arrowWidth: number,
    headWidth: number,
    headLength: number,
    captionLayout: RelationshipCaptionLayout
  ) {
    this.deflection = deflection
    const dRad = (deflection * Math.PI) / 180
    const startAttach = {
      x: Math.cos(dRad) * startRadius,
      y: Math.sin(dRad) * startRadius,
    }

    const ratio = startRadius / (endRadius + headLength)
    const homotheticCenter = (-endCentre * ratio) / (1 - ratio)
    const endAttach = intersectCircle(
      startAttach,
      endRadius + headLength,
      endCentre,
      -1,
      homotheticCenter
    )

    const g1 = -startAttach.x / startAttach.y
    const c1 = startAttach.y + sq(startAttach.x) / startAttach.y
    const g2 = -(endAttach.x - endCentre) / endAttach.y
    const c2 =
      endAttach.y + ((endAttach.x - endCentre) * endAttach.x) / endAttach.y

    const cx = (c1 - c2) / (g2 - g1)
    const cy = g1 * cx + c1
    const arcRadius = Math.sqrt(
      sq(cx - startAttach.x) + sq(cy - startAttach.y)
    )
    const startAngle = Math.atan2(startAttach.x - cx, cy - startAttach.y)
    const endAngle = Math.atan2(endAttach.x - cx, cy - endAttach.y)
    let sweepAngle = endAngle - startAngle
    if (deflection > 0) sweepAngle = 2 * Math.PI - sweepAngle

    this.shaftLength = sweepAngle * arcRadius
    if (startAngle > endAngle) this.shaftLength = 0

    let midShaftAngle = (startAngle + endAngle) / 2
    if (deflection > 0) midShaftAngle += Math.PI
    this.midShaftPoint = {
      x: cx + arcRadius * Math.sin(midShaftAngle),
      y: cy - arcRadius * Math.cos(midShaftAngle),
    }

    const startTangent = (dr: number) => {
      const dx =
        (dr < 0 ? 1 : -1) * Math.sqrt(sq(dr) / (1 + sq(g1)))
      return { x: startAttach.x + dx, y: startAttach.y + g1 * dx }
    }

    const endTangent = (dr: number) => {
      const dx =
        (dr < 0 ? -1 : 1) * Math.sqrt(sq(dr) / (1 + sq(g2)))
      return { x: endAttach.x + dx, y: endAttach.y + g2 * dx }
    }

    const angleTangent = (angle: number, dr: number) => ({
      x: cx + (arcRadius + dr) * Math.sin(angle),
      y: cy - (arcRadius + dr) * Math.cos(angle),
    })

    const endNormal = (dc: number) => {
      const dx =
        (dc < 0 ? -1 : 1) * Math.sqrt(sq(dc) / (1 + sq(1 / g2)))
      return { x: endAttach.x + dx, y: endAttach.y - dx / g2 }
    }

    const endOverlayCorner = (dr: number, dc: number) => {
      const shoulder = endTangent(dr)
      const tip = endNormal(dc)
      return {
        x: shoulder.x + tip.x - endAttach.x,
        y: shoulder.y + tip.y - endAttach.y,
      }
    }

    const shaftRadius = arrowWidth / 2
    const headRadius = headWidth / 2
    const posSweep = startAttach.y > 0 ? 0 : 1
    const negSweep = startAttach.y < 0 ? 0 : 1

    this.outline = (shortCaptionLength: number) => {
      if (startAngle > endAngle) {
        return [
          "M", coord(endTangent(-headRadius)),
          "L", coord(endNormal(headLength)),
          "L", coord(endTangent(headRadius)),
          "Z",
        ].join(" ")
      }

      if (captionLayout === "external") {
        let captionSweep = shortCaptionLength / arcRadius
        if (deflection > 0) captionSweep *= -1
        const sb = midShaftAngle - captionSweep / 2
        const eb = midShaftAngle + captionSweep / 2

        return [
          "M", coord(startTangent(shaftRadius)),
          "L", coord(startTangent(-shaftRadius)),
          "A", arcRadius - shaftRadius, arcRadius - shaftRadius, 0, 0, posSweep, coord(angleTangent(sb, -shaftRadius)),
          "L", coord(angleTangent(sb, shaftRadius)),
          "A", arcRadius + shaftRadius, arcRadius + shaftRadius, 0, 0, negSweep, coord(startTangent(shaftRadius)),
          "Z",
          "M", coord(angleTangent(eb, shaftRadius)),
          "L", coord(angleTangent(eb, -shaftRadius)),
          "A", arcRadius - shaftRadius, arcRadius - shaftRadius, 0, 0, posSweep, coord(endTangent(-shaftRadius)),
          "L", coord(endTangent(-headRadius)),
          "L", coord(endNormal(headLength)),
          "L", coord(endTangent(headRadius)),
          "L", coord(endTangent(shaftRadius)),
          "A", arcRadius + shaftRadius, arcRadius + shaftRadius, 0, 0, negSweep, coord(angleTangent(eb, shaftRadius)),
        ].join(" ")
      }

      return [
        "M", coord(startTangent(shaftRadius)),
        "L", coord(startTangent(-shaftRadius)),
        "A", arcRadius - shaftRadius, arcRadius - shaftRadius, 0, 0, posSweep, coord(endTangent(-shaftRadius)),
        "L", coord(endTangent(-headRadius)),
        "L", coord(endNormal(headLength)),
        "L", coord(endTangent(headRadius)),
        "L", coord(endTangent(shaftRadius)),
        "A", arcRadius + shaftRadius, arcRadius + shaftRadius, 0, 0, negSweep, coord(startTangent(shaftRadius)),
      ].join(" ")
    }

    this.overlay = (minWidth: number) => {
      const r = Math.max(minWidth / 2, shaftRadius)
      return [
        "M", coord(startTangent(r)),
        "L", coord(startTangent(-r)),
        "A", arcRadius - r, arcRadius - r, 0, 0, posSweep, coord(endTangent(-r)),
        "L", coord(endOverlayCorner(-r, headLength)),
        "L", coord(endOverlayCorner(r, headLength)),
        "L", coord(endTangent(r)),
        "A", arcRadius + r, arcRadius + r, 0, 0, negSweep, coord(startTangent(r)),
      ].join(" ")
    }
  }
}
