from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..kg.graph_metadata_service import graph_metadata_service
from ..kg.graph_service import graph_service
from ..schemas.graph import GraphQueryRequest, GraphQueryResponse
from ..schemas.graph_workbench import (
    GraphWorkbenchLabelMetaListResponse,
    GraphWorkbenchMetaSummary,
    GraphWorkbenchPropertyKeyMetaListResponse,
    GraphWorkbenchRelationshipTypeMetaListResponse,
    GraphWorkbenchSchemaResponse,
)

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/meta/summary", response_model=GraphWorkbenchMetaSummary)
async def get_graph_meta_summary():
    """返回数据库级图谱元信息总览。"""
    return await graph_metadata_service.get_summary()


@router.get("/meta/labels", response_model=GraphWorkbenchLabelMetaListResponse)
async def get_graph_meta_labels(
    q: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """返回 label 元数据列表。"""
    return await graph_metadata_service.list_labels(q=q, limit=limit, offset=offset)


@router.get(
    "/meta/relationship-types",
    response_model=GraphWorkbenchRelationshipTypeMetaListResponse,
)
async def get_graph_meta_relationship_types(
    q: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """返回 relationship type 元数据列表。"""
    return await graph_metadata_service.list_relationship_types(
        q=q,
        limit=limit,
        offset=offset,
    )


@router.get("/meta/property-keys", response_model=GraphWorkbenchPropertyKeyMetaListResponse)
async def get_graph_meta_property_keys(
    q: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """返回 property key 元数据列表。"""
    return await graph_metadata_service.list_property_keys(q=q, limit=limit, offset=offset)


@router.get("/meta/schema", response_model=GraphWorkbenchSchemaResponse)
async def get_graph_meta_schema():
    """返回数据库 schema 信息。"""
    return await graph_metadata_service.get_schema()


@router.post("/query", response_model=GraphQueryResponse)
async def query_graph(payload: GraphQueryRequest):
    """按过滤条件执行图谱高级查询。"""
    return await graph_service.query_graph(payload)


@router.get("/herb/{name}")
async def get_herb_graph(
    name: str,
    depth: int = Query(1, ge=1, le=3)
):
    """获取以药材为中心的图谱"""
    result = await graph_service.get_herb_graph(name, depth=depth)
    if not result["center"]:
        raise HTTPException(status_code=404, detail=f"Herb '{name}' not found")
    return result


@router.get("/search")
async def search_nodes(
    q: str = Query(..., min_length=1),
    label: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """搜索节点"""
    results = await graph_service.search_nodes(q, label=label, limit=limit)
    return {"items": results, "total": len(results)}


@router.get("/node/{node_id}")
async def get_node(node_id: str):
    """根据 ID 获取节点"""
    node = await graph_service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.get("/node/{node_id}/expand")
async def expand_node_graph(
    node_id: str,
    depth: int = Query(1, ge=1, le=1),
    limit: int = Query(20, ge=1, le=50),
):
    """按节点 ID 扩展一跳邻居子图。"""
    graph = await graph_service.expand_node_graph(node_id, depth=depth, limit=limit)
    if not graph["center"]:
        raise HTTPException(status_code=404, detail="Node not found")
    return graph


@router.get("/node/{node_id}/relationships")
async def get_node_relationships(
    node_id: str,
    status: Optional[str] = Query(None)
):
    """获取节点的所有关系"""
    relationships = await graph_service.get_relationships(node_id, status=status)
    return {"items": relationships}


@router.get("/path")
async def find_path(
    from_name: str = Query(...),
    to_name: str = Query(...),
    max_depth: int = Query(4, ge=1, le=6)
):
    """查找两个节点之间的路径"""
    paths = await graph_service.find_path(from_name, to_name, max_depth=max_depth)
    return {"paths": paths}


@router.get("/pending")
async def get_pending(
    type: str = Query(..., pattern="^(nodes|relationships)$"),
    limit: int = Query(50, ge=1, le=100)
):
    """获取待验证的节点或关系"""
    if type == "nodes":
        items = await graph_service.get_pending_nodes(limit=limit)
    else:
        items = await graph_service.get_pending_relationships(limit=limit)
    return {"items": items, "type": type}
