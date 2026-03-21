# Task: IMPL-004 Provenance Module TDD - New Implementation with Evidence-Source Lineage

## Implementation Summary

### Files Modified
- `packages/api/app/溯源/__init__.py`: Refactored ProvenanceService with extracted lineage query patterns, type aliases, and enhanced docstrings

### Files Verified (pre-existing, not created this session)
- `packages/api/tests/unit/provenance/test_provenance.py`: 8 test cases covering all ProvenanceService behaviors

### TDD Phases

**RED Phase**: 8 test cases were already written covering:
- `test_create_evidence` - evidence node creation with required fields
- `test_get_evidence` - evidence retrieval by ID
- `test_get_evidence_not_found` - None return for missing evidence
- `test_link_evidence_to_source` - DERIVED_FROM relationship creation
- `test_query_entity_lineage` - Entity -> Evidence -> Source chain query
- `test_query_source_derivations` - reverse lineage: Source -> all derived entities
- `test_collect_evidence_for_entity` - evidence aggregation per entity
- `test_lineage_chain_completeness` - chain integrity verification

**GREEN Phase**: All 8 tests pass against the existing ProvenanceService implementation.

**REFACTOR Phase**: Applied 3 refactorings:
1. **Extract lineage query pattern**: Extracted `_LINEAGE_PATH` constant for the common `(entity)-[:has_evidence]->(evidence:Evidence)-[:derived_from]->(source:Source)` Cypher pattern, used by `QUERY_ENTITY_LINEAGE` and `QUERY_SOURCE_DERIVATIONS`
2. **Add type aliases and hints**: Created `NodeDict`, `LineageChain`, `EvidenceRecord` type aliases; added comprehensive docstrings with Args/Returns to all public methods
3. **Lineage chain builder**: `_build_lineage_chain` helper already existed; enhanced class-level docstring documenting all public API capabilities

### Content Added
- **`_LINEAGE_PATH`** (`packages/api/app/溯源/__init__.py`): Extracted Cypher path pattern constant
- **`NodeDict`** (`packages/api/app/溯源/__init__.py`): Type alias for `Dict[str, Any]` node dictionaries
- **`LineageChain`** (`packages/api/app/溯源/__init__.py`): Type alias for lineage chain response
- **`EvidenceRecord`** (`packages/api/app/溯源/__init__.py`): Type alias for evidence collection records

## Test Results

```
8 passed in 0.52s
Coverage: 89% (target: >= 80%)
Missing lines: connect/close lifecycle, None guard branches, None-return edge cases
```

## Outputs for Dependent Tasks

### Available Components
```python
from app.溯源 import ProvenanceService, provenance_service
```

### Integration Points
- **ProvenanceService**: Singleton at `provenance_service` - manages Evidence -> Source lineage in Neo4j
- **create_evidence()**: Creates Evidence nodes with `content`, `source_name`, `page_reference`, `status`
- **get_evidence()**: Retrieves Evidence by ID, returns None if not found
- **link_evidence_to_source()**: Creates `(Evidence)-[:DERIVED_FROM]->(Source)` relationship
- **query_entity_lineage()**: Traverses Entity -> Evidence -> Source chain
- **query_source_derivations()**: Finds all entities derived from a given source
- **collect_evidence_for_entity()**: Aggregates all evidence+source pairs for an entity
- **lineage_chain_completeness()**: Checks `has_evidence`, `has_source`, `chain_complete` flags

### Usage Examples
```python
# Create evidence and link to source
evidence = await provenance_service.create_evidence(
    content="本草纲目记载人参主补五脏",
    source_name="Bencao Gangmu",
    page_reference="卷十二"
)
await provenance_service.link_evidence_to_source(
    evidence_id=evidence["id"],
    source_id="source-uuid"
)

# Query lineage
lineage = await provenance_service.query_entity_lineage(entity_id="herb-uuid")
# Returns: {"entity": {...}, "evidence": {...}, "source": {...}}

# Check completeness
check = await provenance_service.lineage_chain_completeness(entity_id="herb-uuid")
assert check["chain_complete"] is True
```

## Status: Complete
