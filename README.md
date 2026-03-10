# AI-Driven Adaptive Diagnostic Engine

A **1D Adaptive Testing System** that uses **Item Response Theory (IRT 3PL)** to estimate student ability in real time and generate **AI-powered personalized study plans**. Built with FastAPI, MongoDB, and OpenAI.

---

## Table of Contents
- [How to Run the Project](#how-to-run-the-project)
- [Adaptive Algorithm Logic](#adaptive-algorithm-logic)
- [API Documentation](#api-documentation)
- [AI Log](#ai-log)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)

---

## How to Run the Project

### Prerequisites
- **Python 3.11+**
- **MongoDB** — [MongoDB Atlas Free Tier](https://www.mongodb.com/atlas) (recommended) or local install
- **OpenAI API Key** — [Get one here](https://platform.openai.com/api-keys) (for study plan generation)

### Step-by-Step Setup

```bash
# 1. Navigate to the project directory
cd AI-Driven-Adaptive-Diagnostic-Engine

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
copy .env.example .env
# Open .env and replace with your MongoDB Atlas URI and OpenAI API key
```

**`.env` file — what to fill in:**
```
MONGODB_URI=mongodb+srv://<your-username>:<your-password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
OPENAI_API_KEY=sk-your-actual-api-key-here
```

```bash
# 5. Seed the question database (inserts 21 GRE-style questions into MongoDB)
python -m scripts.seed_questions

# 6. Start the development server
uvicorn app.main:app --reload
```

**Server output you should see:**
```
✅ Connected to MongoDB: adaptive_diagnostic_engine
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Verify It Works
- **Swagger UI**: Open http://localhost:8000/docs — interactive API explorer
- **Health Check**: Visit http://localhost:8000/health — confirms MongoDB connection

### Running Tests
```bash
pytest tests/ -v          # Run all 32 tests
pytest tests/test_irt.py -v        # IRT math tests only
pytest tests/test_adaptive.py -v   # Adaptive engine tests only
pytest tests/test_api.py -v        # API integration tests only
```

---

## Adaptive Algorithm Logic

### The Problem with Traditional Testing
Traditional tests give you a raw score like "7/10 correct" — but that doesn't account for *how hard* the questions were. A student who gets 7 hard questions right is clearly stronger than someone who gets 7 easy questions right.

### Our Solution: Item Response Theory (IRT 3PL)
We use the **3-Parameter Logistic Model**, the same mathematical framework powering the GRE and GMAT:

```
P(correct | θ) = c + (1 - c) × [1 / (1 + e^(-a(θ - b)))]
```

| Parameter | What It Means | Range |
|-----------|---------------|-------|
| **θ (theta)** | Student's estimated ability | -3.0 to +3.0 |
| **a** | How well the question separates strong/weak students | 0.5 to 3.0 |
| **b** | The difficulty level of the question | -3.0 to +3.0 |
| **c** | Probability of guessing correctly (floor) | 0.0 to 0.35 |

### How It Works — Step by Step

1. **Start**: Student begins at θ = 0.0 (average), target difficulty = 0.5
2. **Question Selection**: System queries MongoDB for a question near the target difficulty (±0.1 band, with fallback widening to ±0.2, then ±0.3 if no match found)
3. **Student Answers**: Correctness checked against stored `correct_answer`
4. **Ability Update**: Theta is updated using an MLE-inspired step:
   ```
   Δθ = learning_rate × a × (response - P(θ)) × guessing_weight
   ```
   - Correct on hard question → **big increase** in θ
   - Incorrect on easy question → **big decrease** in θ
   - Correct but likely guessed → **small increase** (discounted)
5. **Next Difficulty**: Updated θ is mapped from [-3, +3] to difficulty [0.1, 1.0] via linear normalization
6. **Stopping**: Test ends after **10 questions** OR when Standard Error of Measurement (SEM) drops below 0.3
7. **Result**: Final θ, accuracy, topic breakdown, and difficulty trajectory are recorded

### Why IRT Instead of Simple Rules?

| Approach | Problem |
|----------|---------|
| Simple +0.1/-0.1 | No statistical basis; same score means different things on different tests |
| Elo Rating | No item discrimination; treats every question the same |
| **IRT 3PL** ✅ | Accounts for guessing, item discrimination, and difficulty — produces a **comparable ability score** across all test sessions |

---

## API Documentation

### Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/session/start` | Start a new adaptive test session |
| `GET` | `/question/next` | Get the next question (adapted to student level) |
| `POST` | `/answer/submit` | Submit an answer, receive updated ability score |
| `GET` | `/results/{session_id}` | Get final test results after completion |
| `POST` | `/plan/generate` | Generate a personalized AI study plan |
| `GET` | `/health` | System health check |

---

### `POST /session/start`
**Create a new test session.** Idempotent — returns existing active session if one exists.

```bash
curl -X POST http://localhost:8000/session/start \
  -H "Content-Type: application/json" \
  -d '{"student_id": "student_001"}'
```
```json
{
  "session_id": "65f2a1b3c4d5e6f7a8b9c0d1",
  "current_theta": 0.0,
  "status": "active",
  "message": "Session initialized"
}
```

---

### `GET /question/next`
**Retrieve the next adaptive question.** Difficulty adjusts based on current ability. Never exposes the correct answer.

```bash
curl "http://localhost:8000/question/next?session_id=65f2a1b3c4d5e6f7a8b9c0d1"
```
```json
{
  "question_id": "65f1a2b3c4d5e6f7a8b9c0d2",
  "question_text": "If 3x + 7 = 22, what is the value of x?",
  "options": ["3", "5", "7", "15"],
  "topic": "Algebra",
  "difficulty_band": "Medium"
}
```

---

### `POST /answer/submit`
**Submit an answer and get ability update.** Returns 409 on duplicate submission.

```bash
curl -X POST http://localhost:8000/answer/submit \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "65f2a1b3c4d5e6f7a8b9c0d1",
    "question_id": "65f1a2b3c4d5e6f7a8b9c0d2",
    "selected_answer": "B",
    "time_taken_seconds": 45
  }'
```
```json
{
  "correct": true,
  "updated_theta": 0.1523,
  "questions_remaining": 9,
  "session_status": "active"
}
```

---

### `GET /results/{session_id}`
**Get final results.** Returns 400 if session still active, 404 if not found.

```bash
curl "http://localhost:8000/results/65f2a1b3c4d5e6f7a8b9c0d1"
```
```json
{
  "session_id": "65f2a1b3c4d5e6f7a8b9c0d1",
  "student_id": "student_001",
  "final_theta": 1.234,
  "accuracy_rate": 0.8,
  "total_questions": 10,
  "correct_count": 8,
  "topics_attempted": ["Algebra", "Vocabulary", "Reading Comprehension"],
  "topics_missed": ["Vocabulary"],
  "difficulty_trajectory": [0.5, 0.55, 0.6, 0.65, 0.7, 0.6, 0.65, 0.7, 0.75, 0.8],
  "percentile_estimate": "Above Average"
}
```

---

### `POST /plan/generate`
**Generate an AI-powered study plan.** Idempotent — returns cached plan if already generated.

```bash
curl -X POST http://localhost:8000/plan/generate \
  -H "Content-Type: application/json" \
  -d '{"session_id": "65f2a1b3c4d5e6f7a8b9c0d1"}'
```
```json
{
  "plan": {
    "step_1": {
      "focus": "Vocabulary in Context",
      "action": "Study 50 high-frequency GRE words using spaced repetition",
      "resource_type": "Flashcard Deck"
    },
    "step_2": {
      "focus": "Quadratic Equations",
      "action": "Review factoring methods with 15 practice problems at difficulty 0.4-0.6",
      "resource_type": "Practice Set"
    },
    "step_3": {
      "focus": "Mixed Review",
      "action": "Take one timed 20-question mixed-topic diagnostic focusing on difficulty 0.6+",
      "resource_type": "Timed Mock Test"
    }
  },
  "generated_at": "2026-03-10T12:00:00Z"
}
```

---

### `GET /health`
**System health check.** Pings MongoDB to verify connectivity.

```bash
curl http://localhost:8000/health
```
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-03-10T12:00:00Z"
}
```

---

### Error Responses

| Scenario | Code | Detail |
|----------|------|--------|
| Session not found | 404 | `"Session not found"` |
| Session still active (on results) | 400 | `"Session is still active..."` |
| Duplicate answer for same question | 409 | `"Answer already submitted for this question"` |
| Invalid answer (not A-D) | 422 | Pydantic validation error |
| LLM API failure | 503 | `"Study plan generation failed..."` + `Retry-After` header |

---

## AI Log

### Tools Used During Development
| Tool | How It Was Used |
|------|-----------------|
| **Cursor AI (Claude/Gemini)** | Full-stack code generation — architecture scaffolding, IRT implementation, FastAPI endpoints, MongoDB integration, tests, and documentation |
| **OpenAI GPT-4o-mini** | Used at runtime within the application to generate personalized study plans via API |

### What AI Accelerated
- **Architecture scaffolding**: Generated the 5-layer project structure (config → database → engine → API → AI) from the design spec in minutes
- **IRT 3PL implementation**: Translated the mathematical formula into working Python with overflow protection and proper bounds
- **Question bank creation**: Generated 21 GRE-style questions with realistic IRT parameters (discrimination, difficulty, guessing)
- **Test suite**: Created 32 unit + integration tests with mock repositories for testing without a live database
- **Boilerplate reduction**: Pydantic models, FastAPI routers, MongoDB repository patterns — all generated quickly

### Challenges AI Couldn't Solve
1. **IRT Parameter Calibration**: AI generated plausible-looking `a`, `b`, `c` values, but couldn't validate whether the parameters would produce sensible theta trajectories without running actual simulations. Required manual review of psychometric literature to verify discrimination and guessing ranges.

2. **MLE Learning Rate Tuning**: The theta update step size (set to 0.4) needed manual experimentation. AI initially suggested 1.0, which caused theta to oscillate wildly. Too low (0.1) made theta barely change. The correct value was found by running simulated test sequences.

3. **MongoDB TTL Index Behavior**: AI assumed TTL indexes behave identically across local MongoDB and Atlas — they don't. Atlas TTL backgrounds run every 60 seconds; local can be slower. This required manual testing on both environments.

4. **Prompt Engineering Iteration**: The first AI-generated LLM prompt for study plans returned inconsistent formats (sometimes prose, sometimes partial JSON). Required 3 iterations of manual prompt refinement to achieve consistent structured JSON output, including adding `response_format: {"type": "json_object"}`.

5. **Edge Case Discovery**: AI didn't initially account for the scenario where the question pool is exhausted before 10 questions (if difficulty bands are too narrow). The fallback widening logic (±0.1 → ±0.2 → ±0.3 → any remaining question) was designed after manual testing revealed gaps.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                            │
│         Browser / Postman / Mobile App                      │
│         (Stateless — all state on server)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/JSON
┌────────────────────────▼────────────────────────────────────┐
│                    API LAYER (FastAPI)                       │
│                                                             │
│  POST /session/start    │  GET /question/next               │
│  POST /answer/submit    │  GET /results/{session_id}        │
│  POST /plan/generate    │  GET /health                      │
│                                                             │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────────────┐  │
│  │   Pydantic   │ │   Routers    │ │  Error Handling      │  │
│  │   Schemas    │ │              │ │  Middleware           │  │
│  └─────────────┘ └──────────────┘ └──────────────────────┘  │
└──────┬───────────────────┬──────────────────┬───────────────┘
       │                   │                  │
┌──────▼──────┐   ┌───────▼────────┐  ┌──────▼──────────────┐
│  ADAPTIVE   │   │   DATABASE     │  │   AI INSIGHTS       │
│  ALGORITHM  │   │   LAYER        │  │   MODULE            │
│  ENGINE     │   │   (MongoDB)    │  │   (OpenAI)          │
│             │   │                │  │                     │
│  IRT 3PL    │   │  Questions     │  │  Prompt Builder     │
│  Theta MLE  │   │  UserSessions  │  │  LLM Client         │
│  SEM Check  │   │  TestResults   │  │  Plan Generator     │
│  Question   │   │                │  │  Retry Logic        │
│  Selection  │   │  Motor (async) │  │                     │
└─────────────┘   └────────────────┘  └─────────────────────┘
```

### MongoDB Collections

| Collection | Purpose | Indexes |
|------------|---------|---------|
| `questions` | 21 GRE items with IRT params | `{difficulty, topic}`, `{tags}` |
| `user_sessions` | Live test state, updated per answer | `{student_id, status}`, TTL on `updated_at` |
| `test_results` | Immutable completion records | `{session_id}` (unique), `{student_id}` |

---

## Project Structure

```
AI-Driven-Adaptive-Diagnostic-Engine/
├── app/
│   ├── main.py               # FastAPI app entry point
│   ├── config.py              # Pydantic Settings, env var loader
│   ├── database.py            # Motor async MongoDB + index creation
│   ├── ai/
│   │   ├── llm_client.py      # OpenAI client, retry logic, JSON parsing
│   │   ├── plan_generator.py  # Orchestrates study plan generation
│   │   └── prompt_builder.py  # System + user prompt templates
│   ├── engine/
│   │   ├── irt.py             # IRT 3PL core math (pure functions)
│   │   └── adaptive.py        # Question selection, scoring, stopping
│   ├── models/
│   │   ├── question.py        # Question document model
│   │   ├── session.py         # Session document model
│   │   └── results.py         # TestResult document model
│   ├── repositories/
│   │   ├── question_repo.py   # Difficulty-band queries + fallback widening
│   │   ├── session_repo.py    # Session CRUD + atomic updates
│   │   └── results_repo.py    # Immutable result storage + plan updates
│   ├── routers/
│   │   ├── session_router.py  # POST /session/start
│   │   ├── question_router.py # GET /question/next
│   │   ├── answer_router.py   # POST /answer/submit
│   │   └── results_router.py  # GET /results, POST /plan/generate
│   └── schemas/
│       └── schemas.py         # API request/response contracts
├── scripts/
│   └── seed_questions.py      # Seeds 21 GRE questions into MongoDB
├── tests/
│   ├── test_irt.py            # 18 IRT math unit tests
│   ├── test_adaptive.py       # 8 adaptive engine tests
│   └── test_api.py            # 6 API integration tests
├── .env.example               # Environment variable template
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```
