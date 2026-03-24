import { PairwiseArcsRelationshipRouting } from "./routing/PairwiseArcsRelationshipRouting"
import type { VizGraph } from "./models/VizGraph"
import type { VizNode, NodeCaptionLine } from "./models/VizNode"
import { NODE_RADIUS } from "./constants"

function measureText(
  text: string,
  fontSize: number,
  ctx: CanvasRenderingContext2D
): number {
  ctx.font = `${fontSize}px sans-serif`
  return ctx.measureText(text).width
}

export class GraphGeometryModel {
  routing: PairwiseArcsRelationshipRouting
  private canvas: HTMLCanvasElement
  private ctx: CanvasRenderingContext2D

  constructor() {
    this.routing = new PairwiseArcsRelationshipRouting()
    this.canvas = document.createElement("canvas")
    this.ctx = this.canvas.getContext("2d")!
  }

  formatNodeCaptions(nodes: VizNode[]): void {
    for (const node of nodes) {
      node.caption = fitCaptionIntoCircle(node, this.ctx)
    }
  }

  onGraphChange(graph: VizGraph): void {
    this.formatNodeCaptions(graph.nodes())
    this.routing.measureRelationshipCaptions(graph.relationships())
  }

  onTick(graph: VizGraph): void {
    this.routing.layoutRelationships(graph)
  }
}

const CAPTION_FONT_SIZE = 11

function fitCaptionIntoCircle(
  node: VizNode,
  ctx: CanvasRenderingContext2D
): NodeCaptionLine[] {
  const fontSize = CAPTION_FONT_SIZE
  const radius = node.radius
  const text = node.name
  const maxLen = Math.floor(
    (Math.pow(radius, 2) * Math.PI) / Math.pow(fontSize, 2)
  )
  const captionText = text.length > maxLen ? text.substring(0, maxLen) : text
  const measure = (t: string) => measureText(t, fontSize, ctx)
  const spaceW = measure(" ")
  const words = captionText.split(" ")

  const emptyLine = (lineCount: number, lineIndex: number): NodeCaptionLine => {
    const baseline = (1 + lineIndex - lineCount / 2) * fontSize
    const chordDist =
      lineIndex < lineCount / 2 ? baseline - fontSize / 2 : baseline + fontSize / 2
    const maxW = Math.sqrt(Math.pow(radius, 2) - Math.pow(chordDist, 2)) * 2
    return { node, text: "", baseline, remainingWidth: isNaN(maxW) ? 0 : maxW }
  }

  const addShortened = (line: NodeCaptionLine, word: string): string => {
    while (word.length > 2) {
      const nw = `${word.substring(0, word.length - 2)}\u2026`
      if (measure(nw) < line.remainingWidth) {
        return `${line.text.split(" ").slice(0, -1).join(" ")} ${nw}`
      }
      word = word.substring(0, word.length - 1)
    }
    return `${word}\u2026`
  }

  const fitLines = (lineCount: number): [NodeCaptionLine[], number] => {
    const lines: NodeCaptionLine[] = []
    const wordWidths = words.map((w) => measure(w))
    let wi = 0
    for (let li = 0; li < lineCount; li++) {
      const line = emptyLine(lineCount, li)
      while (wi < words.length && wordWidths[wi] < line.remainingWidth - spaceW) {
        line.text = `${line.text} ${words[wi]}`
        line.remainingWidth -= wordWidths[wi] + spaceW
        wi++
      }
      lines.push(line)
    }
    if (wi < words.length) {
      lines[lineCount - 1].text = addShortened(lines[lineCount - 1], words[wi])
    }
    return [lines, wi]
  }

  let consumed = 0
  const maxLines = (radius * 2) / fontSize
  let result = [emptyLine(1, 0)]

  for (let lc = 1; lc <= maxLines; lc++) {
    const [candidateLines, candidateWords] = fitLines(lc)
    if (!candidateLines.some((l) => !l.text)) {
      result = candidateLines
      consumed = candidateWords
    }
    if (consumed >= words.length) return result
  }
  return result
}
