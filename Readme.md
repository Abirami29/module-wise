# Module-Wise: Your Terraform Modules Intelligence Platform

## What is Module-Wise?

**Module-Wise** is a RAG-powered chat platform that enables platform and infrastructure engineers to quickly understand their shared Terraform modules ecosystem. Whether you're asking about module usage patterns, identifying stale modules, spotting duplication, or assessing blast radius impacts, Module-Wise delivers confident answers backed by your actual module repository.

### Key Capabilities
- **Module Usage Analysis** - Understand how modules are consumed across your service repos
- **Staleness Detection** - Identify unused or outdated modules
- **Duplication Discovery** - Spot redundant modules that could be consolidated
- **Blast Radius Assessment** - Evaluate the impact of changes across dependent services
- **Fallback Intelligence** - Clearly indicates when no existing module covers a use case, guiding new module creation

### Available Interfaces
Access Module-Wise via CLI or interactive Streamlit chat—your choice, same intelligence.

---

## Architecture & Implementation

| Field | Details |
|-------|---------|
| **Use Case** | Platform engineers ask: "is module X still used anywhere," "what's the blast radius if I change/deprecate module X," "is there an existing module for Y before I build something new," "which repos are behind on module versions." Surface: Streamlit chat (CLI as fallback). |
| **Corpus** | 1 shared infra-modules repo (8 Terraform modules, READMEs, git history) + 3 consumer repos (service-webshop, service-billing, service-analytics) that reference modules via versioned git source URLs. Format: .tf HCL + Markdown. Synthetic but structurally realistic data, self-owned. |
| **Ingestion & Cleaning** | git clone (or already-local) each repo → python-hcl2 parses .tf files into structured module/resource/variable data → GitPython pulls commit messages/dates per file → strip nothing meaningful needed (already clean synthetic HCL, no boilerplate to drop). |
| **Ingestion & Freshness** | One-time batch build for this project; in production this would re-run on a webhook/schedule when any repo pushes to main — noted as a "future work" item, not built. |
| **Chunking & Embedding** | **Graph side**: no chunking — structured nodes/edges from parsed HCL, entity/relationship extraction via LLMGraphTransformer (Nebius as LLM). **Vector side** (baseline): module README/description chunked at doc level (one chunk per module, ~150-300 tokens each — small enough not to split), embedded via Nebius embeddings into Chroma. |
| **Retrieval** | **Graph**: Neo4j via Neo4jGraph + GraphCypherQAChain, NL→Cypher, top match by direct traversal (not top-k — graph queries return exact matches). **Vector**: Chroma, dense similarity, top-k=3. A LangGraph router decides which path to use per question, with fallback if one path returns low-confidence/empty. |

---

## Production Architecture (Target Design)

```
┌──────────────────────────────────────────────────────────────┐
│  PRODUCTION ARCHITECTURE (target design, not fully built)    │
└──────────────────────────────────────────────────────────────┘

  [GitHub: infra-modules repo]     [GitHub: service-* repos]
         │  push to main                  │  push to main
         ▼                                 ▼
   ┌───────────────────────────────────────────────┐
   │  GitHub webhook (on push) → triggers ingestion│
   └───────────────────────────────────────────────┘
                        │
                        ▼
   ┌────────────────────────────────────────────────┐
   │  Ingestion job (e.g. GitHub Action, Lambda,    │
   │  or Airflow DAG)                               │
   │  1. git pull affected repo                     │
   │  2. python-hcl2 parse → structured facts       │
   │  3. LLMGraphTransformer → relationship extract │
   │  4. write nodes/edges into Neo4j AuraDB        │
   │  5. re-embed changed READMEs into vector store │
   └────────────────────────────────────────────────┘
                        │
                        ▼
   ┌────────────────────────────────────────────────┐
   │  Neo4j AuraDB (graph)  +  Vector store         │
   │  — always reflects latest repo state           │
   └────────────────────────────────────────────────┘
                        │
                        ▼
   ┌────────────────────────────────────────────────┐
   │  Serving layer: Streamlit / API / Slack bot    │
   │  — only ever reads, never rebuilds inline      │
   └────────────────────────────────────────────────┘
```

**Key principle**: On-demand indexing decouples ingestion from serving. New code deploys don't rebuild the graph—repo changes trigger ingestion webhooks instead. Serving layer remains lightweight and responsive.
