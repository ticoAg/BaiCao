import {
  type Simulation,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
} from "d3-force"

import {
  DEFAULT_ALPHA,
  DEFAULT_ALPHA_MIN,
  EXTRA_TICKS_PER_RENDER,
  FORCE_CENTER_X,
  FORCE_CENTER_Y,
  FORCE_CHARGE,
  LINK_DISTANCE,
  MAX_PRECOMPUTED_TICKS,
  VELOCITY_DECAY,
} from "./constants"
import type { VizGraph } from "./models/VizGraph"
import type { VizNode } from "./models/VizNode"
import type { VizRelationship } from "./models/VizRelationship"

function circularLayout(nodes: VizNode[]): void {
  const r = (nodes.length * LINK_DISTANCE) / (Math.PI * 2)
  for (let i = 0; i < nodes.length; i++) {
    const node = nodes[i]
    if (node.x === 0 && node.y === 0 && !node.fx && !node.fy) {
      node.x = r * Math.sin((2 * Math.PI * i) / nodes.length)
      node.y = r * Math.cos((2 * Math.PI * i) / nodes.length)
    }
  }
}

// 取每对节点间的第一条关系用于 forceLink
function onePerPair(graph: VizGraph): VizRelationship[] {
  return graph.groupedRelationships().map((p) => p.relationships[0])
}

export class ForceSimulation {
  simulation: Simulation<VizNode, VizRelationship>

  constructor(render: () => void) {
    this.simulation = forceSimulation<VizNode, VizRelationship>()
      .velocityDecay(VELOCITY_DECAY)
      .force("charge", forceManyBody().strength(FORCE_CHARGE))
      .force("centerX", forceX(0).strength(FORCE_CENTER_X))
      .force("centerY", forceY(0).strength(FORCE_CENTER_Y))
      .alphaMin(DEFAULT_ALPHA_MIN)
      .on("tick", () => {
        this.simulation.tick(EXTRA_TICKS_PER_RENDER)
        render()
      })
      .stop()
  }

  updateNodes(graph: VizGraph): void {
    const nodes = graph.nodes()
    circularLayout(nodes)
    this.simulation
      .nodes(nodes)
      .force(
        "collide",
        forceCollide<VizNode>().radius((n) => n.radius + 25)
      )
  }

  updateRelationships(graph: VizGraph): void {
    const rels = onePerPair(graph)
    this.simulation.force(
      "link",
      forceLink<VizNode, VizRelationship>(rels)
        .id((n) => n.id)
        .distance(
          (r) => r.source.radius + r.target.radius + LINK_DISTANCE * 2
        )
    )
  }

  precomputeAndStart(onEnd?: () => void): void {
    this.simulation.stop()
    let ticks = 0
    const start = performance.now()
    while (
      performance.now() - start < 250 &&
      ticks < MAX_PRECOMPUTED_TICKS
    ) {
      this.simulation.tick(1)
      ticks++
      if (this.simulation.alpha() <= this.simulation.alphaMin()) break
    }

    this.simulation.restart().on("end", () => {
      onEnd?.()
      this.simulation.on("end", null)
    })
  }

  restart(): void {
    this.simulation.alpha(DEFAULT_ALPHA).restart()
  }
}
