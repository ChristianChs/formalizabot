# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

FormalizaBot MYPE — a Spanish-language conversational agent that advises on
formalizing micro/small businesses (MYPE) in Tacna, Perú. All normative
(legal/regulatory) content in a response must be grounded in official
documents retrieved via RAG and cited by source; the agent must never
answer normative questions from the LLM's parametric knowledge alone (see
`Bitacora.md`, Hallazgo 1 — an ungrounded LLM invented a fake legal
requirement).

`README.md` and `SPEC.md` are authoritative and detailed — read `SPEC.md`
before making architectural changes, since it documents *why* each design
decision was made (temperature=0 for grounding, separate LLM instance for
tool routing, etc.) and tracks which requirements (RF1–RF8) are done vs.
pending.

## Commands

```
# venv + deps (Windows/Git Bash)
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt

# (re)build the vector index — REQUIRED after any change under data/normativa/
python -m app.rag.build_index

# CLI: single question, no memory
python -m app.main

# Gradio chat UI: session memory, multi-turn — this is how the user manually tests changes
python -m app.ui

# Regression set (domain guardrail + prompt-injection resistance) — the project's test suite
python -m app.eval.regression
```

There is no pytest/unit-test suite — `app/eval/regression.py` (via `chain.batch()`) is the correctness check for this project. It runs with `max_concurrency=1` because Groq's free tier caps at 6000 tokens/minute; running it back-to-back can trip a `RateLimitError` — wait a minute and retry rather than treating it as a real failure.

**Critical gotcha**: the Chroma index in `data/chroma_db/` is *not* rebuilt automatically. Any edit/add/delete under `data/normativa/` requires re-running `python -m app.rag.build_index`, or the bot silently answers from the stale corpus (looks like "no tengo esa información" even when the doc has the answer).

## Working with the user

The user tests interactively in the Gradio UI (`python -m app.ui`) themselves rather than via scripted API calls — don't build one-off scripts to drive the chatbot programmatically as a substitute for that.

## Architecture

Everything lives under `app/`. The core idea: one RAG "response chain" is built once (`build_respuesta_components()` in `app/rag/chain.py`) and reused by both the memoryless single-question path and the stateful chatbot — there is no duplicate construction of retriever/LLM/prompt.

- **`app/config.py`** — loads `.env` (Groq API key, model, base URL). Raises at import time if `GROQ_API_KEY` is missing.
- **`app/llm.py`** — `get_llm(temperature)`: Groq via `ChatOpenAI` (LangChain interop, not a raw client — intentional per SPEC.md Bloque 1).
- **`app/schemas.py`** — `RespuestaMYPE` Pydantic schema (`respuesta`, `fuera_de_dominio`, `fundamentado_en_contexto`) parsed via `JsonOutputParser`; the LLM is prompted to emit raw JSON only.
- **`app/prompts/system_prompt.py`** — persona, domain guardrail, and the anti-prompt-injection rules (context/question are always treated as *data*, never instructions).
- **`app/rag/`**:
  - `loader.py` / `splitter.py` — load `.md`/`.pdf` from `data/normativa/`, chunk them.
  - `embeddings.py` — local HuggingFace embeddings.
  - `vectorstore.py` — build/load Chroma, cached via `lru_cache` (one embedding load per process).
  - `build_index.py` — the (re)indexing entry point (see gotcha above).
  - `chain.py` — the core LCEL assembly:
    - `RETRIEVAL_K = 4`, `LLM_TEMPERATURE = 0` are the single source of truth, reused everywhere.
    - `build_respuesta_components()` → `(retriever, respuesta_chain)`, the reusable pair.
    - `build_condensador()` — a separate small chain that rewrites a follow-up question ("¿y para ese régimen?") into a self-contained one, used only to query the retriever/generation, never shown to the user as their literal question.
    - `_finalize()` — merges LLM structured output with source citations; sources are *derived from retrieved-chunk metadata*, never asked of the LLM (avoids invented citations). Sources are only attached when `fundamentado_en_contexto=True` and not `fuera_de_dominio`.
    - `build_rag_chain()` / `answer_question()` — memoryless single-question path (`app/main.py`).
- **`app/chatbot.py`** — `Chatbot` class: per-`session_id` memory via `InMemoryChatMessageHistory`, built once in `__init__`, not per turn. `stream()` order per turn: (1) try `resolver_tool_call` (deterministic tool short-circuit), (2) condense the question against history if there's prior history, (3) retrieve docs with the condensed question, (4) stream the grounded response chain, (5) update history with the *original* (uncondensed) question and final answer.
- **`app/tools/`** — deterministic tool-calling (SPEC.md Bloque 9), kept separate from the grounding chain's LLM/temperature:
  - `nrus.py` — `calcular_categoria_nrus` (NRUS tax category from a fixed table — math is never delegated to the LLM, RF8).
  - `router.py` — `resolver_tool_call()`: a *separate* LLM (same temperature=0, but conceptually distinct from grounding) decides whether to call a tool; `_llamada_valida()` then cross-checks any numeric argument the LLM produced actually appears in the user's literal text before executing — this guards against the 8B model inventing a plausible-looking argument (e.g. an income figure) that the user never stated. Also swallows `openai.BadRequestError` from malformed tool-call payloads by treating it as "no tool call" rather than crashing the turn.
- **`app/ui.py`** — Gradio `ChatInterface` over `Chatbot.stream()` (the primary way the user manually verifies behavior).
- **`app/eval/regression.py`** — batch regression set covering domain guardrail + injection resistance; the closest thing to a test suite in this repo.

## Design invariants to preserve when changing this code

- Normative content must stay grounded — never let a code change make it easier for the LLM to answer from parametric knowledge without a citable source.
- Keep `RETRIEVAL_K`/`LLM_TEMPERATURE` in `app/rag/chain.py` as the single definition; don't reintroduce per-caller retrieval/temperature constants.
- Sources (`fuentes`) must continue to come from retrieved-chunk metadata, never from the LLM's own output.
- The tool-routing LLM/temperature is intentionally separate from the grounding chain's — don't merge them.
- Don't add a second construction path for the retriever/prompt/LLM triplet; extend `build_respuesta_components()` instead.
