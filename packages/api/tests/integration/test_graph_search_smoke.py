import pytest


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_graph_search_returns_seeded_demo_herb(client, demo_seed_data):
    response = await client.get(
        "/api/v1/graph/search",
        params={"q": "人参", "label": "Herb", "limit": 5},
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] >= 1

    matched = next(
        (
            item
            for item in payload["items"]
            if item["node"]["id"] == demo_seed_data["herb_ids"]["人参"]
        ),
        None,
    )
    assert matched is not None
    assert matched["node"]["name"] == "人参"
    assert matched["node"]["status"] == "verified"
    assert matched["node"]["dataset"] == demo_seed_data["dataset_tag"]
    assert "Herb" in matched["labels"]


@pytest.mark.asyncio
async def test_herb_graph_returns_seeded_neighbors(client, demo_seed_data):
    response = await client.get("/api/v1/graph/herb/人参", params={"depth": 1})

    assert response.status_code == 200

    payload = response.json()
    center = payload["center"]

    assert center["id"] == demo_seed_data["herb_ids"]["人参"]
    assert center["name"] == "人参"
    assert center["status"] == "verified"

    node_names = {node["name"] for node in payload["nodes"]}
    assert "人参皂苷Rb1" in node_names
    assert "大补元气" in node_names
    assert "脾经" in node_names

    edge_types = {edge["rel_type"] for edge in payload["edges"]}
    assert "包含成分" in edge_types
    assert "具有功效" in edge_types
    assert "具有性味" in edge_types
    assert "归于经脉" in edge_types
