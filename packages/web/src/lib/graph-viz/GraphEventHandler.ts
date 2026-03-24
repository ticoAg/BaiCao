import type { VizGraph } from "./models/VizGraph"
import type { VizNode } from "./models/VizNode"
import type { VizRelationship } from "./models/VizRelationship"
import type { Visualization } from "./Visualization"

export type GraphInteraction = "NODE_EXPAND" | "NODE_UNPINNED" | "NODE_DISMISSED"

export interface GraphEventCallbacks {
  onNodeSelected: (node: VizNode) => void
  onRelationshipSelected: (rel: VizRelationship) => void
  onCanvasClicked: () => void
  onNodeHover: (node: VizNode | null) => void
  onRelationshipHover: (rel: VizRelationship | null) => void
  onNodeDblClicked: (node: VizNode) => void
  onGraphInteraction?: (event: GraphInteraction) => void
}

export class GraphEventHandler {
  graph: VizGraph
  visualization: Visualization
  callbacks: GraphEventCallbacks
  selectedItem: VizNode | VizRelationship | null = null

  constructor(
    graph: VizGraph,
    visualization: Visualization,
    callbacks: GraphEventCallbacks
  ) {
    this.graph = graph
    this.visualization = visualization
    this.callbacks = callbacks
  }

  selectItem(item: VizNode | VizRelationship): void {
    if (this.selectedItem) {
      this.selectedItem.selected = false
    }
    this.selectedItem = item
    item.selected = true
    this.visualization.update({
      updateNodes: item.isNode,
      updateRelationships: item.isRelationship,
      restartSimulation: false,
    })
  }

  deselectItem(): void {
    if (this.selectedItem) {
      this.selectedItem.selected = false
      this.visualization.update({
        updateNodes: this.selectedItem.isNode,
        updateRelationships: this.selectedItem.isRelationship,
        restartSimulation: false,
      })
      this.selectedItem = null
    }
    this.callbacks.onCanvasClicked()
  }

  nodeClicked(node: VizNode): void {
    if (!node) return
    node.hoverFixed = false
    node.fx = node.x
    node.fy = node.y
    if (!node.selected) {
      this.selectItem(node)
      this.callbacks.onNodeSelected(node)
    } else {
      this.deselectItem()
    }
  }

  nodeUnlock(node: VizNode): void {
    if (!node) return
    node.fx = null
    node.fy = null
    this.deselectItem()
    this.callbacks.onGraphInteraction?.("NODE_UNPINNED")
  }

  nodeDblClicked(node: VizNode): void {
    this.callbacks.onNodeDblClicked(node)
  }

  nodeClose(node: VizNode): void {
    this.graph.removeConnectedRelationships(node)
    this.graph.removeNode(node)
    this.deselectItem()
    this.visualization.update({
      updateNodes: true,
      updateRelationships: true,
      restartSimulation: true,
    })
    this.callbacks.onGraphInteraction?.("NODE_DISMISSED")
  }

  onNodeMouseOver(node: VizNode): void {
    if (!node.contextMenu) {
      this.callbacks.onNodeHover(node)
    }
  }

  onRelationshipMouseOver(rel: VizRelationship): void {
    this.callbacks.onRelationshipHover(rel)
  }

  onRelationshipClicked(rel: VizRelationship): void {
    if (!rel.selected) {
      this.selectItem(rel)
      this.callbacks.onRelationshipSelected(rel)
    } else {
      this.deselectItem()
    }
  }

  onCanvasClicked(): void {
    this.deselectItem()
  }

  onItemMouseOut(): void {
    this.callbacks.onNodeHover(null)
  }

  bindEventHandlers(): void {
    this.visualization
      .on("nodeMouseOver", this.onNodeMouseOver.bind(this))
      .on("nodeMouseOut", this.onItemMouseOut.bind(this))
      .on("relMouseOver", this.onRelationshipMouseOver.bind(this))
      .on("relMouseOut", this.onItemMouseOut.bind(this))
      .on("relationshipClicked", this.onRelationshipClicked.bind(this))
      .on("canvasClicked", this.onCanvasClicked.bind(this))
      .on("nodeClose", this.nodeClose.bind(this))
      .on("nodeClicked", this.nodeClicked.bind(this))
      .on("nodeDblClicked", this.nodeDblClicked.bind(this))
      .on("nodeUnlock", this.nodeUnlock.bind(this))
  }
}
