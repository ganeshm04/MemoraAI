# MemoraAI - Memory System Technical Design Document

This document outlines the design, architecture, lifecycle, failure mitigations, and engineering tradeoffs of the cognitive memory layer in MemoraAI.

---

## 🎯 Goals

- **Long-term Personalization:** Enable AI assistants to capture, persist, and adapt to user-specific traits, preferences, roles, and instructions across distinct conversation sessions.
- **Immediate Context Continuity:** Retain raw dialog history for pronoun resolution and follow-up contextual understanding within active conversations.
- **Episodic Compression:** Summarize long chat sessions into high-level event summaries, tracking sentiments and key topics without bloating database schemas or prompt context windows.
- **Low-latency Execution:** Ensure LTM extraction and updates do not block real-time request-response cycles.

---

## 🛑 Non-Goals

- **General-purpose Knowledge Base:** The memory layer is *not* a substitute for the general document ingestion RAG system (which handles PDFs, URLs, and external texts). It does not store factual knowledge (e.g. *"how gravity works"*), but rather user-centric facts (e.g. *"user is studying gravity"*).
- **Multi-user Real-time Collaborative State:** The system is optimized for isolated, user-specific sessions and does not support real-time sync or memory sharing across different users.
- **Deterministic Action Orchestration:** Memory does not act as an agentic planning tool or state machine for tool execution; it acts solely as a semantic context injector.

---

## 🏛️ Architecture

MemoraAI models human cognitive structures using a three-tier memory architecture stored in separate PostgreSQL tables:

```
                  ┌───────────────────────┐
                  │      User Input       │
                  └──────────┬────────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │    Adaptive Router    │
                 └──────────┬────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Short-Term  │     │  Long-Term   │     │  Episodic    │
│    Memory    │     │    Memory    │     │   Memory     │
├──────────────┤     ├──────────────┤     ├──────────────┤
│ Working logs │     │ extracted    │     │ Historical   │
│ of active    │     │ user facts   │     │ session      │
│ conversation │     │ & preferences│     │ summaries    │
└──────────────┘     └──────────────┘     └──────────────┘
```

### 1. Database Schema Specifications

#### A. `short_term_memory`
Stores chronological raw messages within an active session.
```sql
CREATE TABLE short_term_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    token_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_stm_session ON short_term_memory(session_id, created_at DESC);
```

#### B. `long_term_memory`
Stores extracted, user-specific factual records.
```sql
CREATE TABLE long_term_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    fact_key VARCHAR(255) NOT NULL,    -- e.g., 'occupation', 'preferred_languages'
    fact_value TEXT NOT NULL,           -- e.g., 'Software Engineer', 'Python, TypeScript'
    category VARCHAR(100) DEFAULT 'general',
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_ltm_user_fact ON long_term_memory(user_id, fact_key);
```

#### C. `episodic_memory`
Stores high-level chronological summaries of complete chat sessions.
```sql
CREATE TABLE episodic_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL,
    topics JSONB DEFAULT '[]'::jsonb,
    sentiment VARCHAR(50) DEFAULT 'neutral',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_em_user ON episodic_memory(user_id, created_at DESC);
```

---

## 🔄 Memory Lifecycle

```
[Ingestion / Dialog] ─► [STM Ingress] ─► [Background LTM Extraction] ──► [LTM Store]
         │                                                                   │
         │                                                                   ▼
[Episodic Summarize] ◄── [Session End / Clear] ◄── [Response Gen] ◄── [Inject Prompt]
```

1. **Write Path (Ingestion & Extraction):**
   - Every input and response is appended to the `short_term_memory` table.
   - A background hook evaluates the session message count. When the count is a multiple of 5, an asynchronous worker extracts LTM facts.
   - The worker sends the recent 5 messages to the LLM with instructions to output structured JSON:
     ```json
     {
       "facts": [
         {"key": "occupation", "value": "AI Developer", "category": "professional"}
       ]
     }
     ```
   - These facts areupserted (`INSERT ... ON CONFLICT (user_id, fact_key) DO UPDATE`) into the `long_term_memory` table.
2. **Read Path (Retrieval & Ingestion):**
   - When a user submits a query, the **Adaptive Router** classifies the intent. If it requires user context, the system pulls:
     - The last 5 messages from `short_term_memory` for immediate continuity.
     - The user's accumulated profile from `long_term_memory`.
     - Recent session summaries from `episodic_memory`.
   - The system formats these components into the LLM system prompt context:
     ```text
     [User Facts & Preferences]:
     - occupation: AI Developer
     - preferred_languages: Python, TypeScript
     ```
3. **Archive Path (Session Archival & Summarization):**
   - Clicking "New Session" or "Clear Chat" triggers a summarization call (`POST /api/v1/memory/episodic/summarize`).
   - The worker fetches all messages in the `short_term_memory` table for that session, compiles a high-level summary, extracts topics and sentiment scores, and writes them to the `episodic_memory` table.
   - The session's `short_term_memory` records are then deleted to purge active chat state.

---

## ❌ Failure Cases & Mitigations

### 1. Wrong Memory Extracted
* **The Failure:** The model misinterprets a hypothetical statement (e.g. *"I wish I worked in Python"* or *"Imagine if I lived in Tokyo"*) as a fact, saving `preferred_language = Python` or `location = Tokyo`.
* **Mitigation:**
  - **Prompt Restriction:** The extraction system prompt strictly forbids extracting hypothetical, sarcastic, or transient statements. Only extract concrete, explicitly stated preferences or statements of fact.
  - **Confidence Rating:** The extraction output requires the LLM to provide a confidence score (0.0 to 1.0) for each fact. Facts with a confidence score under `0.7` are discarded.

### 2. Duplicate Memory
* **The Failure:** The extraction pipeline extracts the same fact (e.g. `occupation = Engineer`) repeatedly on different message intervals, bloat-writing duplicates in the database.
* **Mitigation:**
  - **Database Constraints:** A unique index constraint is defined on `(user_id, fact_key)`.
  - **Upsert Merging:** The LTM write path uses `ON CONFLICT (user_id, fact_key) DO UPDATE` to overwrite old values, keeping a single, clean state per fact key.
  - **LTM Deduplication Prompting:** The fact extractor is provided with existing LTM facts during runs, instructing it to only output *new* or *changed* facts, completely skipping unchanged data.

### 3. Contradicting Memory
* **The Failure:** The user's preferences change over time. (e.g., in session 1: *"I am learning Python"*, but in session 4: *"I stopped coding in Python, I write TypeScript now"*), leading to conflicting facts: `preferred_language = Python` and `preferred_language = TypeScript`.
* **Mitigation:**
  - **Recency Overwrite:** Since upserts overwrite existing `fact_key` values, newer assertions automatically replace older ones.
  - **Conflict Resolution Prompting:** When a newly extracted fact conflicts with an existing fact, the extractor compares them. The instruction states: *"If the user makes a statement contradicting an existing fact, assume the new statement represents an update and replace the existing value."*

### 4. Context Overflow
* **The Failure:** Over months of use, LTM accumulates hundreds of facts, and episodic memory contains dozens of session summaries. Injecting all of them into the LLM system prompt exhausts context windows and degrades performance.
* **Mitigation:**
  - **K-nearest Fact Retrieval:** Instead of dumping the entire LTM database into the prompt, LTM values are vectorized or indexed. We run a lightweight text search matching the user's current query against LTM `fact_key` and `fact_value` fields, retrieving only the top `5` semantically relevant facts.
  - **Episodic Decay:** Only the last `3` episodic summaries are loaded for active chat sessions, limiting historical context bloat.

---

## ⚖️ Tradeoffs

- **Asynchronous background extraction vs. Inline execution:** 
  Running fact extraction asynchronously after a message threshold (every 5 messages) prevents latency penalties on standard chat routes. The tradeoff is that the system's "learning" is delayed by a few messages; however, this is a minor tradeoff compared to adding 1.5 seconds of latency to every chat response.
- **Relational SQL vs. Document DB:**
  Storing memory in structured PostgreSQL tables allows strict data validation, constraint checking, and transactional security, but makes schema updates (like adding new memory categories) more rigid compared to NoSQL databases. We chose PostgreSQL to leverage the existing database connection pool and maintain transactional reliability.
- **Stateless API Gateway vs. Session Caching:**
  The NestJS Gateway does not cache memory in local memory stores, relying instead on fetching database states on every request. This ensures horizontal scaling capabilities for the gateway but increases overall database read operations.

---

## 🔮 Future Improvements

1. **Memory Decay & Forgetting Curve:** Implement a mathematical decay score ($S = S_0 \cdot e^{-\lambda t}$) on LTM facts. Facts that are rarely recalled or haven't been updated in months will have their scores reduced, eventually moving to an archived "forgotten" state to keep active profiles dense and clean.
2. **Interactive Memory Settings Dashboard:** Provide a frontend settings panel where users can view, edit, or delete facts that MemoraAI has learned about them, giving the user transparency and control over their agent's memory.
3. **Memory Graph Connections:** Establish semantic relationships between memories (e.g., linking the fact `job = Data Scientist` to `skill = PyTorch`) to allow the model to query associative clusters of memories.
