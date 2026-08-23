Build Plan — Agile, LangChain + LangGraph, 1.5 Days (~12 hrs)

Structured as small increments. Each one ships something runnable and has a concrete test/acceptance check before you move to the next — no increment depends on polish from a later one, so if you run out of time anywhere, everything before that point still demos cleanly.

Epic 1: Synthetic Data (Day 1, Hour 0–1.5)

Story 1.1 — Build synthetic repos

Create 1 terraform-modules repo (6-8 generic modules: vpc-base, s3-bucket-standard, rds-postgres, security-group-web, ecs-service, lambda-function, etc.)
Create 2-3 "domain" repos consuming some modules via source = "git::...//module?ref=..."
Bake in intentional inconsistencies: one repo on a stale module version, one module with zero consumers (orphan), two near-duplicate resource blocks across different modules
Each module gets a short README (purpose, inputs/outputs)
✅ Definition of done / test: git log on each repo shows real commits; manually eyeball that inconsistencies exist and are identifiable by reading the files yourself (this is your ground truth — write it down in a notes file, you'll grade your own system against it later)
Epic 2: Parsing Layer (Day 1, Hour 1.5–3.5)

Story 2.1 — HCL parser

python-hcl2 script: walk each repo, extract module blocks (source, ref), resource blocks, variables
Output as a clean Python data structure (list of dicts) — this is framework-agnostic, doesn't touch LangChain yet
✅ Test: unit test / print statement asserting parsed output matches your ground-truth notes from 1.1 (e.g., "module count == 8", "domain-repo-2 references vpc-base at v1.0.0")

Story 2.2 — Git metadata extraction

GitPython: pull commit history/messages per file
✅ Test: spot-check 2-3 files, confirm commit messages/dates match what you expect from git log

Shippable checkpoint: a parsed_data.json (or similar) file — structural ground truth, no LLM involved yet. This alone is a demoable artifact ("here's what I extracted from raw Terraform").

Epic 3: Deterministic Graph Facts (Day 1, Hour 3.5–5)

Story 3.1 — Load into Neo4j

Push parsed nodes/edges (Repo, ModuleDef, ModuleCall, Resource) into Neo4j AuraDB via langchain_community.graphs.Neo4jGraph
✅ Test: run a raw Cypher query in Neo4j browser, confirm node/edge counts match parsed data

Story 3.2 — Hard-coded Cypher queries (no LLM)

Write direct Cypher for: unused modules, version drift across repos
✅ Test: output matches your ground-truth notes exactly (these should be 100% correct, deterministic — no LLM guessing allowed here)

Shippable checkpoint: you can already answer "what's unused" and "what's out of version sync" correctly, without any LLM call. This is a real, working feature on its own.

Epic 4: LLM-Enriched Graph Layer (Day 1, Hour 5–7)

Story 4.1 — Duplicate-capability detection

LLMGraphTransformer (or a direct LLM call) reads module READMEs/resource blocks, flags duplicates_capability edges between similar modules
Nebius as the LLM
✅ Test: does it correctly flag the duplicate pair you planted in 1.1? (precision check against your known ground truth)

Story 4.2 — Natural-language graph query chain

GraphCypherQAChain: NL question → Cypher → answer
✅ Test: run 3-4 questions ("what's the blast radius if I change vpc-base?"), manually verify Cypher generated is sane and answer is grounded

Shippable checkpoint: you can ask a graph question in plain English and get a correct, grounded answer. This is your core GraphRAG feature — fully working end to end.

Epic 5: Vector RAG Baseline (Day 2, Hour 0–1.5)

Story 5.1 — Embed + store

Chroma + Nebius embeddings over module READMEs/descriptions
✅ Test: query "is there a module for X", confirm top-k results are sensible

Story 5.2 — Vector QA chain

Standard LangChain retrieval chain
✅ Test: same 3-4 questions from 4.2 run through vector mode — confirm it gives worse or non-answers for relational questions (this is expected and is your comparison finding, not a bug)

Shippable checkpoint: two independent, working query paths — graph and vector — both demoable separately.

Epic 6: LangGraph Router (Day 2, Hour 1.5–3)

Story 6.1 — Stateful router

LangGraph state machine: classify question type → route to graph chain or vector chain → fallback if low-confidence → synthesize answer with source-path label
✅ Test: run your fixed 10-question eval set through the router, log which path each one took, confirm routing decisions make sense manually

Shippable checkpoint: one unified entrypoint that intelligently routes — this is your "actual product," not just two disconnected demos.

Epic 7: Comparison Report (Day 2, Hour 3–4)

Story 7.1 — Run the eval

Same 10 questions through graph-only, vector-only, and router
Log answers + which was more correct/faithful against your ground truth
✅ Test: report is internally consistent — every claim traceable to a logged run, not just written from memory

Shippable checkpoint: your actual required deliverable (per the handout) is done at this point, independent of the UI.

Epic 8: UI + Deploy (Day 2, Hour 4–5.5)

Story 8.1 — Streamlit chat UI

Wraps the LangGraph router, shows which path was used per answer
✅ Test: click through the UI yourself, ask the 10 eval questions live, confirm no crashes

Story 8.2 — Deploy

Push to Streamlit Community Cloud or HF Spaces, secrets configured (Nebius/OpenAI keys, Neo4j creds)
✅ Test: open the deployed link in an incognito window, run 2-3 questions live
Epic 9: Ship (Day 2, Hour 5.5–6)
Record 5-min demo video
Write project doc (framework table + comparison findings + future-work paragraph)
Submit via the Google Form