import { type BaseType, type Selection, select as d3Select } from "d3-selection"
import {
  type D3ZoomEvent,
  type ZoomBehavior,
  zoom as d3Zoom,
  zoomIdentity,
} from "d3-zoom"

import {
  ZOOM_FIT_PADDING_PERCENT,
  ZOOM_MAX_SCALE,
  ZOOM_MIN_SCALE,
} from "./constants"
import type { VizGraph } from "./models/VizGraph"
import type { VizNode } from "./models/VizNode"
import type { VizRelationship } from "./models/VizRelationship"
import { GraphGeometryModel } from "./GraphGeometryModel"
import { ForceSimulation } from "./ForceSimulation"
import { nodeEventHandlers, relationshipEventHandlers } from "./mouseEventHandlers"
import {
  nodeRenderers,
  relationshipRenderers,
} from "./renderers/nodeRenderer"
import { menuRenderers } from "./renderers/menuRenderer"

export class Visualization {
  private root: Selection<SVGElement, unknown, BaseType, unknown>
  private baseGroup: Selection<SVGGElement, unknown, BaseType, unknown>
  private rect: Selection<SVGRectElement, unknown, BaseType, unknown>
  private container: Selection<SVGGElement, unknown, BaseType, unknown>
  private geometry: GraphGeometryModel
  private zoomBehavior: ZoomBehavior<SVGElement, unknown>
  private zoomMinScale: number = ZOOM_MIN_SCALE
  private callbacks: Record<string, Array<(...args: any[]) => void>> = {}
  private draw = false

  forceSimulation: ForceSimulation
  graph: VizGraph

  constructor(
    element: SVGElement,
    private measureSize: () => { width: number; height: number },
    graph: VizGraph
  ) {
    this.graph = graph
    this.root = d3Select(element)
    this.root.selectAll("g").remove()
    this.baseGroup = this.root.append("g").attr("transform", "translate(0,0)")

    const size = measureSize()
    this.rect = this.baseGroup
      .append("rect")
      .style("fill", "none")
      .style("pointer-events", "all")
      .attr("x", -Math.floor(size.width / 2))
      .attr("y", -Math.floor(size.height / 2))
      .attr("width", "100%")
      .attr("height", "100%")
      .attr("transform", "scale(1)")
      .on("click", () => {
        if (!this.draw) this.trigger("canvasClicked")
      })

    this.container = this.baseGroup.append("g")
    this.geometry = new GraphGeometryModel()

    this.zoomBehavior = d3Zoom<SVGElement, unknown>()
      .scaleExtent([this.zoomMinScale, ZOOM_MAX_SCALE])
      .on("zoom", (e: D3ZoomEvent<SVGElement, unknown>) => {
        this.draw = true
        this.container.attr("transform", String(e.transform))
      })
      .wheelDelta(
        (e) => -e.deltaY * (e.deltaMode === 1 ? 0.05 : e.deltaMode ? 1 : 0.002)
      )

    this.root
      .call(this.zoomBehavior)
      .on("click.zoom", () => (this.draw = false))
      .on("dblclick.zoom", null)

    this.forceSimulation = new ForceSimulation(this.render.bind(this))
  }

  private render() {
    this.geometry.onTick(this.graph)

    this.container
      .selectAll<SVGGElement, VizNode>("g.node")
      .attr("transform", (d) => `translate(${d.x},${d.y})`)

    const nodeGroups = this.container.selectAll<SVGGElement, VizNode>("g.node")
    nodeRenderers.forEach((r) => nodeGroups.call(r.onTick))

    this.container
      .selectAll<SVGGElement, VizRelationship>("g.relationship")
      .attr(
        "transform",
        (d) =>
          `translate(${d.source.x} ${d.source.y}) rotate(${d.naturalAngle + 180})`
      )

    const relGroups = this.container.selectAll<SVGGElement, VizRelationship>(
      "g.relationship"
    )
    relationshipRenderers.forEach((r) => relGroups.call(r.onTick))
  }

  private updateNodes() {
    const nodes = this.graph.nodes()
    this.geometry.onGraphChange(this.graph)

    const nodeGroups = this.container
      .select("g.layer.nodes")
      .selectAll<SVGGElement, VizNode>("g.node")
      .data(nodes, (d) => d.id)
      .join("g")
      .attr("class", "node")
      .attr("aria-label", (d) => `graph-node${d.id}`)
      .call(
        nodeEventHandlers,
        this.trigger.bind(this),
        this.forceSimulation.simulation
      )
      .classed("selected", (n) => n.selected)

    nodeRenderers.forEach((r) => nodeGroups.call(r.onGraphChange))
    menuRenderers.forEach((r) =>
      nodeGroups.call(r.onGraphChange, this.trigger.bind(this))
    )

    this.forceSimulation.updateNodes(this.graph)
    this.forceSimulation.updateRelationships(this.graph)
  }

  private updateRelationships() {
    const rels = this.graph.relationships()
    this.geometry.onGraphChange(this.graph)

    const relGroups = this.container
      .select("g.layer.relationships")
      .selectAll<SVGGElement, VizRelationship>("g.relationship")
      .data(rels, (d) => d.id)
      .join("g")
      .attr("class", "relationship")
      .call(relationshipEventHandlers, this.trigger.bind(this))
      .classed("selected", (r) => r.selected)

    relationshipRenderers.forEach((r) => relGroups.call(r.onGraphChange))
    this.forceSimulation.updateRelationships(this.graph)
    this.render()
  }

  // 公共 API

  on(event: string, callback: (...args: any[]) => void): this {
    if (!this.callbacks[event]) this.callbacks[event] = []
    this.callbacks[event].push(callback)
    return this
  }

  trigger = (event: string, ...args: any[]): void => {
    const cbs = this.callbacks[event] ?? []
    cbs.forEach((cb) => cb.apply(null, args))
  }

  init(): void {
    this.container
      .selectAll("g.layer")
      .data(["relationships", "nodes"])
      .join("g")
      .attr("class", (d) => `layer ${d}`)

    this.updateNodes()
    this.updateRelationships()
    this.adjustZoomToFitGraph()
    this.setInitialZoom()
  }

  setInitialZoom(): void {
    const count = this.graph.nodes().length
    const scale =
      -0.02364554 + 1.913 / (1 + Math.pow(count / 12.7211, 0.8156444))
    this.zoomBehavior.scaleBy(this.root, Math.max(0.1, scale))
  }

  precomputeAndStart(): void {
    this.forceSimulation.precomputeAndStart(() => this.zoomToFit())
  }

  update(options: {
    updateNodes: boolean
    updateRelationships: boolean
    restartSimulation?: boolean
  }): void {
    if (options.updateNodes) this.updateNodes()
    if (options.updateRelationships) this.updateRelationships()
    if (options.restartSimulation ?? true) this.forceSimulation.restart()
    this.trigger("updated")
  }

  zoomIn(): void {
    this.draw = true
    this.zoomBehavior.scaleBy(this.root, 1.3)
  }

  zoomOut(): void {
    this.draw = true
    this.zoomBehavior.scaleBy(this.root, 0.7)
  }

  zoomToFit(): void {
    const factor = this.getZoomToFitFactor()
    if (factor) {
      this.zoomBehavior.transform(
        this.root,
        zoomIdentity
          .scale(Math.min(factor.scale, ZOOM_MAX_SCALE))
          .translate(factor.offset.x, factor.offset.y)
      )
    }
    this.adjustZoomToFitGraph()
  }

  private getZoomToFitFactor():
    | { scale: number; offset: { x: number; y: number } }
    | undefined {
    const bbox = this.container.node()?.getBBox()
    const svgNode = this.root.node()
    const w = svgNode?.clientWidth
    const h = svgNode?.clientHeight
    if (!bbox || !w || !h || bbox.width === 0 || bbox.height === 0) return

    const scale =
      (1 - ZOOM_FIT_PADDING_PERCENT) /
      Math.max(bbox.width / w, bbox.height / h)
    return {
      scale,
      offset: {
        x: -(bbox.x + bbox.width / 2),
        y: -(bbox.y + bbox.height / 2),
      },
    }
  }

  private adjustZoomToFitGraph(): void {
    const factor = this.getZoomToFitFactor()
    const minScale = factor ? factor.scale * 0.75 : this.zoomMinScale
    if (minScale <= this.zoomMinScale) {
      this.zoomMinScale = minScale
      this.zoomBehavior.scaleExtent([minScale, ZOOM_MAX_SCALE])
    }
  }

  resize(): void {
    const size = this.measureSize()
    this.rect
      .attr("x", -Math.floor(size.width / 2))
      .attr("y", -Math.floor(size.height / 2))
    this.root.attr(
      "viewBox",
      [
        -Math.floor(size.width / 2),
        -Math.floor(size.height / 2),
        size.width,
        size.height,
      ].join(" ")
    )
  }

  destroy(): void {
    this.forceSimulation.simulation.stop()
    this.root.selectAll("*").remove()
  }
}
