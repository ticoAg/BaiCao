import type { GraphData } from "../../../types/graph"
import { VizNode } from "./VizNode"
import { VizRelationship } from "./VizRelationship"

export interface NodePair {
  nodeA: VizNode
  nodeB: VizNode
  relationships: VizRelationship[]
  isLoop(): boolean
}

export class VizGraph {
  private _nodes: VizNode[] = []
  private _relationships: VizRelationship[] = []
  private nodeMap: Map<string, VizNode> = new Map()
  private expandedNodeMap: Map<string, Set<string>> = new Map()

  nodes(): VizNode[] {
    return this._nodes
  }

  relationships(): VizRelationship[] {
    return this._relationships
  }

  findNode(id: string): VizNode | undefined {
    return this.nodeMap.get(id)
  }

  addNodes(nodes: VizNode[]): void {
    for (const node of nodes) {
      if (!this.nodeMap.has(node.id)) {
        this._nodes.push(node)
        this.nodeMap.set(node.id, node)
      }
    }
  }

  addRelationships(rels: VizRelationship[]): void {
    const existingIds = new Set(this._relationships.map((r) => r.id))
    for (const rel of rels) {
      if (!existingIds.has(rel.id)) {
        this._relationships.push(rel)
        existingIds.add(rel.id)
      }
    }
  }

  addExpandedNodes(sourceNode: VizNode, nodes: VizNode[]): void {
    const ids = new Set(nodes.map((n) => n.id))
    this.expandedNodeMap.set(sourceNode.id, ids)
    this.addNodes(nodes)
  }

  removeNode(node: VizNode): void {
    this._nodes = this._nodes.filter((n) => n !== node)
    this.nodeMap.delete(node.id)
  }

  removeConnectedRelationships(node: VizNode): void {
    this._relationships = this._relationships.filter(
      (r) => r.source !== node && r.target !== node
    )
  }

  collapseNode(node: VizNode): void {
    const expandedIds = this.expandedNodeMap.get(node.id)
    if (!expandedIds) return

    // 递归收起子节点
    for (const id of expandedIds) {
      const child = this.nodeMap.get(id)
      if (child) {
        this.collapseNode(child)
        this.removeConnectedRelationships(child)
        this.removeNode(child)
      }
    }
    this.expandedNodeMap.delete(node.id)
  }

  findNodeNeighbourIds(nodeId: string): string[] {
    const ids = new Set<string>()
    for (const rel of this._relationships) {
      if (rel.source.id === nodeId) ids.add(rel.target.id)
      if (rel.target.id === nodeId) ids.add(rel.source.id)
    }
    return Array.from(ids)
  }

  groupedRelationships(): NodePair[] {
    const pairMap = new Map<string, NodePair>()

    for (const rel of this._relationships) {
      const [a, b] =
        rel.source.id < rel.target.id
          ? [rel.source, rel.target]
          : [rel.target, rel.source]
      const key = `${a.id}:${b.id}`

      let pair = pairMap.get(key)
      if (!pair) {
        pair = {
          nodeA: a,
          nodeB: b,
          relationships: [],
          isLoop: () => a === b,
        }
        pairMap.set(key, pair)
      }
      pair.relationships.push(rel)
    }

    return Array.from(pairMap.values())
  }

  static fromGraphData(data: GraphData): VizGraph {
    const graph = new VizGraph()

    const nodes = data.nodes.map((n) => new VizNode(n))
    graph.addNodes(nodes)

    const rels = data.edges.map((edge, index) => {
      const sourceId = edge.source?.id || edge.source?.name || ""
      const targetId = edge.target?.id || edge.target?.name || ""
      const source = graph.findNode(sourceId)
      const target = graph.findNode(targetId)
      if (!source || !target) {
        throw new Error(
          `Relationship references missing node: ${sourceId} -> ${targetId}`
        )
      }
      return new VizRelationship(
        source,
        target,
        edge,
        edge.id || `edge-${index}`
      )
    })
    graph.addRelationships(rels)

    return graph
  }
}
