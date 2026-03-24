import type { VizGraph, NodePair } from "../models/VizGraph"
import { VizRelationship } from "../models/VizRelationship"
import { ArcArrow } from "../arrows/ArcArrow"
import { StraightArrow } from "../arrows/StraightArrow"
import { LoopArrow } from "../arrows/LoopArrow"
import {
  SHAFT_WIDTH,
  HEAD_WIDTH,
  HEAD_HEIGHT,
  DEFAULT_DEFLECTION_STEP,
  MAXIMUM_TOTAL_DEFLECTION,
  LOOP_STRAIGHT_LENGTH,
  LOOP_SPREAD_DEGREES,
} from "../constants"

const sq = (d: number) => d * d

function measureText(text: string, fontSize: number, ctx: CanvasRenderingContext2D): number {
  ctx.font = `${fontSize}px sans-serif`
  return ctx.measureText(text).width
}

export class PairwiseArcsRelationshipRouting {
  private canvas: HTMLCanvasElement
  private ctx: CanvasRenderingContext2D

  constructor() {
    this.canvas = document.createElement("canvas")
    this.ctx = this.canvas.getContext("2d")!
  }

  measureRelationshipCaption(rel: VizRelationship): number {
    const padding = 8
    return measureText(rel.caption, rel.captionHeight, this.ctx) + padding * 2
  }

  measureRelationshipCaptions(rels: VizRelationship[]): void {
    for (const rel of rels) {
      rel.captionLength = this.measureRelationshipCaption(rel)
      rel.captionLayout =
        SHAFT_WIDTH > rel.captionHeight && !rel.isLoop()
          ? "internal"
          : "external"
    }
  }

  shortenCaption(
    rel: VizRelationship,
    caption: string,
    targetWidth: number
  ): [string, number] {
    let short = caption || ""
    while (short.length > 2) {
      short = `${short.substring(0, short.length - 2)}\u2026`
      const w = measureText(short, rel.captionHeight, this.ctx) + 16
      if (w < targetWidth) return [short, w]
    }
    return ["", 0]
  }

  computeGeometryForNonLoopArrows(pairs: NodePair[]): void {
    for (const pair of pairs) {
      if (pair.isLoop()) continue
      const dx = pair.nodeA.x - pair.nodeB.x
      const dy = pair.nodeA.y - pair.nodeB.y
      const angle = ((Math.atan2(dy, dx) / Math.PI) * 180 + 360) % 360
      const dist = Math.sqrt(sq(dx) + sq(dy))
      for (const rel of pair.relationships) {
        rel.naturalAngle =
          rel.target === pair.nodeA ? (angle + 180) % 360 : angle
        rel.centreDistance = dist
      }
    }
  }

  distributeAnglesForLoopArrows(
    pairs: NodePair[],
    allRels: VizRelationship[]
  ): void {
    for (const pair of pairs) {
      if (!pair.isLoop()) continue
      const node = pair.nodeA
      let angles: number[] = []
      for (const rel of allRels) {
        if (rel.isLoop()) continue
        if (rel.source === node) angles.push(rel.naturalAngle)
        if (rel.target === node) angles.push(rel.naturalAngle + 180)
      }
      angles = angles.map((a) => (a + 360) % 360).sort((a, b) => a - b)

      if (angles.length > 0) {
        const gap = { start: 0, end: 0 }
        for (let i = 0; i < angles.length; i++) {
          const s = angles[i]
          const e = i === angles.length - 1 ? angles[0] + 360 : angles[i + 1]
          if (e - s > gap.end - gap.start) {
            gap.start = s
            gap.end = e
          }
        }
        const sep = (gap.end - gap.start) / (pair.relationships.length + 1)
        pair.relationships.forEach((rel, i) => {
          rel.naturalAngle = (gap.start + (i + 1) * sep - 90) % 360
        })
      } else {
        const sep = 360 / pair.relationships.length
        pair.relationships.forEach((rel, i) => {
          rel.naturalAngle = i * sep
        })
      }
    }
  }

  layoutRelationships(graph: VizGraph): void {
    const pairs = graph.groupedRelationships()
    this.computeGeometryForNonLoopArrows(pairs)
    this.distributeAnglesForLoopArrows(pairs, graph.relationships())

    for (const pair of pairs) {
      for (const rel of pair.relationships) {
        delete rel.arrow
      }

      const midIdx = (pair.relationships.length - 1) / 2
      const numSteps = pair.relationships.length - 1
      const total = DEFAULT_DEFLECTION_STEP * numSteps
      const step =
        total > MAXIMUM_TOTAL_DEFLECTION
          ? MAXIMUM_TOTAL_DEFLECTION / numSteps
          : DEFAULT_DEFLECTION_STEP

      for (let i = 0; i < pair.relationships.length; i++) {
        const rel = pair.relationships[i]
        const sw = SHAFT_WIDTH
        const hw = HEAD_WIDTH
        const hh = HEAD_HEIGHT

        if (pair.isLoop()) {
          rel.arrow = new LoopArrow(
            rel.source.radius,
            LOOP_STRAIGHT_LENGTH,
            LOOP_SPREAD_DEGREES,
            sw, hw, hh,
            rel.captionHeight
          )
        } else if (i === midIdx) {
          rel.arrow = new StraightArrow(
            rel.source.radius,
            rel.target.radius,
            rel.centreDistance,
            sw, hw, hh,
            rel.captionLayout
          )
        } else {
          let deflection = step * (i - midIdx)
          if (pair.nodeA !== rel.source) deflection *= -1
          rel.arrow = new ArcArrow(
            rel.source.radius,
            rel.target.radius,
            rel.centreDistance,
            deflection,
            sw, hw, hh,
            rel.captionLayout
          )
        }

        if (rel.arrow.shaftLength > rel.captionLength) {
          rel.shortCaption = rel.caption
          rel.shortCaptionLength = rel.captionLength
        } else {
          ;[rel.shortCaption, rel.shortCaptionLength] = this.shortenCaption(
            rel,
            rel.caption,
            rel.arrow.shaftLength
          )
        }
      }
    }
  }
}
