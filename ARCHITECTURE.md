# claiw Technical Architecture

*A CLI for Agentic Workflows That Feels Like a Video Game*

---

## 1. Look and Feel

### Design Philosophy

The terminal is a canvas, not a constraint. claiw treats every character as intentional. The aesthetic draws from three sources:

1. **Retro gaming** - The satisfaction of a save point, the clarity of a health bar, the joy of a level-up screen
2. **Japanese minimalism** - Negative space is information. Silence is a feature.
3. **dbt's developer empathy** - Compile once, run anywhere. Make the happy path obvious.

### Color Palette

```
┌─────────────────────────────────────────────────────────────────┐
│  CLAIW COLOR SYSTEM                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PRIMARY                                                        │
│  ━━━━━━━                                                        │
│  ██ Claw Purple (#8B5CF6)  - Brand, success states              │
│  ██ Bone White  (#F5F5F4)  - Primary text                       │
│  ██ Shadow Gray (#27272A)  - Backgrounds, muted                 │
│                                                                 │
│  SEMANTIC                                                       │
│  ━━━━━━━━                                                       │
│  ██ Ember (#F59E0B)        - Warnings, in-progress              │
│  ██ Crimson (#EF4444)      - Errors, failures                   │
│  ██ Jade (#10B981)         - Success, checkpoints               │
│  ██ Frost (#06B6D4)        - Info, links, hints                 │
│                                                                 │
│  GRAYSCALE (for ASCII art depth)                                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                  │
│  ░ Light   ▒ Medium   ▓ Heavy   █ Solid                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Typography in Terminal

```
HIERARCHY:
━━━━━━━━━━

  ╔══════════════════════════════════════╗
  ║  WORKFLOW: data-pipeline-v2          ║  <- Box drawing for major headers
  ╚══════════════════════════════════════╝

  ── Step 3 of 7 ──────────────────────────  <- Light rules for sections

  • Fetching source data                     <- Bullets for items
    └─ Connected to postgres://...           <- Tree chars for hierarchy

  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄  <- Dotted for subtle breaks
```

### The Claw Mascot

```
Standard (idle):           Thinking:                  Success:

    ╭──╮                      ╭──╮                      ╭──╮
   ╱    ╲                    ╱ ·· ╲                    ╱ ◠◠ ╲
  │ ·  · │                  │ ·  · │                  │ ◡  ◡ │
  │  ──  │                  │  ~~  │                  │  ◡◡  │
   ╲    ╱                    ╲    ╱                    ╲    ╱
    ╰┬┬╯                      ╰┬┬╯                      ╰┬┬╯
    ╱  ╲                      ╱||╲                      ╱  ╲
   ╱    ╲                    ╱    ╲                    ╱ ✧  ╲

Error:                     Working:

    ╭──╮                      ╭──╮
   ╱ ×× ╲                    ╱    ╲
  │ ·  · │                  │ ◉  ◉ │
  │  ▽▽  │                  │  --  │
   ╲    ╱                    ╲    ╱
    ╰┬┬╯                      ╰┬┬╯
    ╱  ╲                     ⟨╱  ╲⟩
   ╱    ╲                    ╱    ╲
```

### Workflow Graph Visualization

```
$ claiw preview data-analyst

╭─────────────────────────────────────────────────────────────────────╮
│  data-analyst v2.3.1                                                │
│  "Analyzes datasets and generates insights with citations"          │
╰─────────────────────────────────────────────────────────────────────╯

                          ┌─────────────┐
                          │   START     │
                          │  ◇ ingest   │
                          └──────┬──────┘
                                 │
                                 ▼
                          ┌─────────────┐
                          │  validate   │
                          │  ◈ schema   │
                          └──────┬──────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
             ┌─────────────┐           ┌─────────────┐
             │   analyze   │           │   profile   │
             │  ◈ pandas   │           │  ◈ stats    │
             └──────┬──────┘           └──────┬──────┘
                    │                         │
                    └────────────┬────────────┘
                                 │
                                 ▼
                          ┌─────────────┐
                          │  synthesize │
                          │  ◈ llm      │
                          └──────┬──────┘
                                 │
                                 ▼
                          ┌─────────────┐
                          │    END      │
                          │  ◆ report   │
                          └─────────────┘

Legend: ◇ Input  ◈ Transform  ◆ Output  ● Checkpoint

Steps: 6  │  Avg Runtime: 2m 34s  │  Success Rate: 94.2%
```

### Progress Display During Execution

```
$ claiw run data-analyst --input sales.csv

╔═══════════════════════════════════════════════════════════════════════╗
║  claiw • data-analyst v2.3.1                                          ║
╚═══════════════════════════════════════════════════════════════════════╝

  ╭──╮
 ╱ ◉◉ ╲   Working...
│ ·  · │
│  --  │   ── Step 3 of 6: analyze ─────────────────────────────────────
 ╲    ╱
  ╰┬┬╯     ████████████████████░░░░░░░░░░░░░░░░░░░░  47%
 ⟨╱  ╲⟩
 ╱    ╲    • Loaded 47,293 rows from sales.csv
           • Schema validated: 12 columns, 3 nullable
           • Running pandas analysis...
             └─ Detected 3 anomalies in Q3 data
             └─ Correlation matrix: 89% complete

  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

  Timeline:
  ┌─────┬─────┬─────┬─────┬─────┬─────┐
  │  ✓  │  ✓  │  ◉  │  ○  │  ○  │  ○  │
  └─────┴─────┴─────┴─────┴─────┴─────┘
  ingest validate analyze profile synth report

  Elapsed: 1m 12s  │  Est. Remaining: 1m 22s  │  Tokens: 12,847

  [s]kip  [p]ause  [d]etail  [q]uit
```

### Error Display

```
$ claiw run data-analyst --input corrupted.csv

╔═══════════════════════════════════════════════════════════════════════╗
║  claiw • data-analyst v2.3.1                                          ║
╚═══════════════════════════════════════════════════════════════════════╝

    ╭──╮
   ╱ ×× ╲    Step 2 Failed
  │ ·  · │
  │  ▽▽  │   ── validate ──────────────────────────────────────────────
   ╲    ╱
    ╰┬┬╯     Schema validation failed at row 1,247
   ╱  ╲
  ╱    ╲

  ┌─────────────────────────────────────────────────────────────────────┐
  │  ERROR: Column 'revenue' expected float, got string "N/A"          │
  │                                                                     │
  │  Context:                                                           │
  │    Row 1247: {"date": "2024-03-15", "revenue": "N/A", ...}         │
  │                                                                     │
  │  Suggestion:                                                        │
  │    Add null handling in validate step config:                       │
  │                                                                     │
  │    steps:                                                           │
  │      validate:                                                      │
  │        null_values: ["N/A", "null", ""]  # <- add this             │
  │                                                                     │
  └─────────────────────────────────────────────────────────────────────┘

  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

  Checkpoint saved: run_abc123_step1

  [r]etry  [e]dit config  [f]ix & continue  [i]nspect state  [q]uit
```

### Animation Principles

1. **Spinners are semantic** - Different spinners for different operations:
   ```
   ◐◓◑◒  Network/API calls
   ⠋⠙⠹⠸  File I/O
   ▁▂▃▄▅▆▇█  Progress with known duration
   ⣾⣽⣻⢿⡿⣟⣯⣷  LLM thinking
   ```

2. **Transitions are instant** - No fade-ins. State changes are immediate.

3. **Updates are batched** - Redraw at most 10fps. Terminal is not a video game.

4. **Scrollback is sacred** - Never clear the terminal. Append, don't replace.

---

## 2. Core Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER LAYER                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   $ claiw <command>                                                     │
│                                                                         │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│   │   run        │  │   history    │  │   registry   │                 │
│   │   preview    │  │   inspect    │  │   evolve     │                 │
│   │   resume     │  │   compare    │  │   share      │                 │
│   └──────────────┘  └──────────────┘  └──────────────┘                 │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                              CORE LAYER                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌───────────────────────────────────────────────────────────────┐    │
│   │                      Workflow Engine                           │    │
│   │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │    │
│   │  │   Parser    │ │  Executor   │ │ Checkpointer│              │    │
│   │  │   (YAML)    │ │  (DAG)      │ │ (DBOS)      │              │    │
│   │  └─────────────┘ └─────────────┘ └─────────────┘              │    │
│   └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│   ┌─────────────────────┐  ┌─────────────────────┐                     │
│   │   LLM Abstraction   │  │    State Manager    │                     │
│   │  ┌───────────────┐  │  │  ┌───────────────┐  │                     │
│   │  │ pydantic-ai   │  │  │  │    SQLite     │  │                     │
│   │  │   unified     │  │  │  │    DuckDB     │  │                     │
│   │  │   interface   │  │  │  │    (hybrid)   │  │                     │
│   │  └───────────────┘  │  │  └───────────────┘  │                     │
│   └─────────────────────┘  └─────────────────────┘                     │
│                                                                         │
│   ┌─────────────────────┐  ┌─────────────────────┐                     │
│   │     Renderer        │  │    Registry Client  │                     │
│   │  ┌───────────────┐  │  │  ┌───────────────┐  │                     │
│   │  │   Rich/Click  │  │  │  │   PyPI-style  │  │                     │
│   │  │   hybrid      │  │  │  │   workflow    │  │                     │
│   │  │   output      │  │  │  │   packages    │  │                     │
│   │  └───────────────┘  │  │  └───────────────┘  │                     │
│   └─────────────────────┘  └─────────────────────┘                     │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                           STORAGE LAYER                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ~/.claiw/                                                             │
│   ├── config.yaml           # Global configuration                      │
│   ├── secrets.yaml.enc      # Encrypted secrets (age)                   │
│   ├── claiw.db              # SQLite: workflows, runs, metadata         │
│   ├── analytics.duckdb      # DuckDB: metrics, evals, aggregates        │
│   ├── cache/                # Workflow package cache                    │
│   │   └── data-analyst/                                                │
│   │       ├── v2.3.1/                                                  │
│   │       └── v2.3.0/                                                  │
│   └── runs/                 # Run artifacts                             │
│       └── abc123/                                                       │
│           ├── state.json                                               │
│           ├── logs/                                                    │
│           └── outputs/                                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Module Structure

```
claiw/
├── __init__.py
├── __main__.py                    # Entry point: python -m claiw
├── cli/
│   ├── __init__.py
│   ├── main.py                    # Click group root
│   ├── run.py                     # claiw run
│   ├── preview.py                 # claiw preview
│   ├── history.py                 # claiw history
│   ├── registry.py                # claiw registry
│   ├── evolve.py                  # claiw evolve
│   └── config.py                  # claiw config
│
├── engine/
│   ├── __init__.py
│   ├── workflow.py                # Workflow class
│   ├── step.py                    # Step abstraction
│   ├── executor.py                # DAG execution
│   ├── checkpoint.py              # DBOS integration
│   └── resume.py                  # Resume logic
│
├── llm/
│   ├── __init__.py
│   ├── provider.py                # Provider abstraction
│   ├── anthropic.py               # Claude implementation
│   ├── openai.py                  # GPT implementation
│   ├── local.py                   # Ollama/local models
│   └── router.py                  # Model routing logic
│
├── state/
│   ├── __init__.py
│   ├── sqlite.py                  # SQLite operations
│   ├── duckdb.py                  # DuckDB analytics
│   ├── encryption.py              # State encryption
│   └── export.py                  # Share/export logic
│
├── registry/
│   ├── __init__.py
│   ├── client.py                  # Registry API client
│   ├── package.py                 # Workflow package format
│   ├── resolver.py                # Version resolution
│   └── evolution.py               # Training/evolution logic
│
├── render/
│   ├── __init__.py
│   ├── console.py                 # Rich console wrapper
│   ├── graph.py                   # ASCII graph rendering
│   ├── progress.py                # Progress displays
│   ├── mascot.py                  # Claw mascot states
│   └── themes.py                  # Color themes
│
├── testing/
│   ├── __init__.py
│   ├── runner.py                  # Test execution
│   ├── fixtures.py                # Test fixtures
│   ├── mocks.py                   # LLM mocking
│   └── evals.py                   # Eval framework
│
└── models/
    ├── __init__.py
    ├── workflow.py                # Pydantic workflow models
    ├── step.py                    # Step models
    ├── run.py                     # Run models
    └── config.py                  # Config models
```

### Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           REQUEST FLOW                                    │
└──────────────────────────────────────────────────────────────────────────┘

  $ claiw run data-analyst --input sales.csv

         │
         ▼
  ┌──────────────┐
  │  CLI Parser  │  Parse args, validate, load config
  │   (Click)    │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │   Registry   │  Resolve "data-analyst" -> cached package or fetch
  │   Resolver   │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │   Workflow   │  Parse YAML, validate schema, build DAG
  │   Parser     │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │   Executor   │  ◀──────────────────────────────────────┐
  │    (DAG)     │                                         │
  └──────┬───────┘                                         │
         │                                                 │
         │ For each step:                                  │
         │                                                 │
         ▼                                                 │
  ┌──────────────┐      ┌──────────────┐                  │
  │    Step      │─────▶│   LLM Call   │  (if needed)     │
  │   Handler    │      │  (pydantic-  │                  │
  │              │◀─────│    ai)       │                  │
  └──────┬───────┘      └──────────────┘                  │
         │                                                 │
         ▼                                                 │
  ┌──────────────┐                                         │
  │ Checkpointer │  Save state to SQLite (DBOS pattern)   │
  │   (DBOS)     │                                         │
  └──────┬───────┘                                         │
         │                                                 │
         ▼                                                 │
  ┌──────────────┐                                         │
  │   Renderer   │  Update terminal display               │
  │   (Rich)     │                                         │
  └──────┬───────┘                                         │
         │                                                 │
         │ next step ─────────────────────────────────────┘
         │
         ▼
  ┌──────────────┐
  │   Complete   │  Final output, analytics write
  └──────────────┘
```

---

## 3. Workflow Engine Design

### Workflow Definition Format

Workflows are defined in YAML with a clear, declarative structure. The philosophy: **workflows should read like documentation**.

```yaml
# ~/.claiw/workflows/data-analyst.yaml
# OR fetched from registry: claiw://data-analyst@2.3.1

meta:
  name: data-analyst
  version: 2.3.1
  description: "Analyzes datasets and generates insights with citations"
  author: claiw-core
  license: Apache-2.0

  # Evolution metadata (the Pokemon system)
  lineage:
    parent: data-analyst@2.2.0
    mutations:
      - "Added correlation analysis"
      - "Improved null handling"
    training_runs: 47
    success_rate: 0.942

  # Resource hints
  resources:
    memory: 2GB
    timeout: 10m

  # Tags for discovery
  tags:
    - data
    - analysis
    - pandas

# Environment and secrets
env:
  required:
    - ANTHROPIC_API_KEY
  optional:
    - OPENAI_API_KEY
    - DATABASE_URL

# LLM configuration
llm:
  default: claude-sonnet
  fallback: gpt-4o-mini

  # Per-step overrides allowed
  routing:
    synthesize: claude-opus  # Complex reasoning needs best model
    validate: local          # Simple validation can use local

# Input schema (validated at runtime)
input:
  type: object
  required:
    - source
  properties:
    source:
      type: string
      description: "Path to CSV/Parquet file or database connection"
    columns:
      type: array
      items: string
      description: "Specific columns to analyze (optional)"

# Output schema
output:
  type: object
  properties:
    report:
      type: string
      format: markdown
    insights:
      type: array
      items:
        type: object
        properties:
          finding: string
          confidence: number
          citations: array

# The workflow graph
steps:
  ingest:
    type: input
    description: "Load and parse the source data"
    handler: claiw.builtins.ingest
    config:
      formats:
        - csv
        - parquet
        - json
    outputs:
      - dataframe

  validate:
    type: transform
    depends_on: [ingest]
    description: "Validate schema and data quality"
    handler: claiw.builtins.validate
    config:
      null_values: ["N/A", "null", ""]
      strict: false
    outputs:
      - validation_report
      - clean_dataframe

  analyze:
    type: transform
    depends_on: [validate]
    description: "Run statistical analysis"
    handler: claiw.builtins.pandas_analyze
    config:
      operations:
        - describe
        - correlations
        - anomalies
    outputs:
      - analysis_results

  profile:
    type: transform
    depends_on: [validate]
    parallel_with: [analyze]  # Can run in parallel
    description: "Generate data profile"
    handler: claiw.builtins.profile
    outputs:
      - profile_report

  synthesize:
    type: llm
    depends_on: [analyze, profile]
    description: "Generate insights using LLM"
    handler: claiw.builtins.llm_synthesize
    config:
      model: ${llm.routing.synthesize}
      temperature: 0.3
      system_prompt: |
        You are a data analyst. Given statistical analysis and profiling
        results, generate actionable insights. Always cite specific
        statistics from the data.
      user_prompt: |
        Analyze this data:

        Analysis Results:
        ${analyze.output}

        Profile:
        ${profile.output}

        Generate 3-5 key insights with confidence scores.
    outputs:
      - insights

  report:
    type: output
    depends_on: [synthesize]
    description: "Generate final report"
    handler: claiw.builtins.report_generator
    config:
      format: markdown
      include:
        - executive_summary
        - detailed_findings
        - methodology
        - data_quality_notes
    outputs:
      - report

# Checkpoint configuration
checkpoints:
  strategy: after_each_step  # or: on_failure, explicit
  retention: 7d

# Error handling
on_error:
  validate:
    retry: 2
    fallback: continue_with_warnings
  synthesize:
    retry: 3
    fallback: fail

# Tests (run with: claiw test data-analyst)
tests:
  unit:
    - name: "Handles empty dataset"
      input:
        source: "fixtures/empty.csv"
      expect:
        status: failure
        error_contains: "empty dataset"

    - name: "Processes standard CSV"
      input:
        source: "fixtures/sample.csv"
      expect:
        status: success
        output:
          report: { type: string, min_length: 100 }

  evals:
    - name: "Insight quality"
      input:
        source: "fixtures/sales_q3.csv"
      judge:
        model: claude-opus
        criteria:
          - "Insights are specific and actionable"
          - "Statistics are cited correctly"
          - "Confidence scores are reasonable"
      threshold: 0.8
```

### Step Handler Interface

```python
# claiw/engine/step.py

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel

class StepContext(BaseModel):
    """Context passed to every step handler."""
    run_id: str
    step_name: str
    workflow_name: str
    workflow_version: str

    # Previous step outputs (dependency injection)
    inputs: Dict[str, Any]

    # Step configuration from YAML
    config: Dict[str, Any]

    # LLM client (if needed)
    llm: Optional["LLMClient"]

    # State manager for checkpointing
    state: "StateManager"

    # Progress callback for UI updates
    progress: "ProgressCallback"


class StepResult(BaseModel):
    """Result from step execution."""
    status: Literal["success", "failure", "skipped"]
    outputs: Dict[str, Any]
    duration_ms: int
    tokens_used: Optional[int] = None
    metadata: Dict[str, Any] = {}


class StepHandler(ABC):
    """Base class for all step handlers."""

    @abstractmethod
    async def execute(self, ctx: StepContext) -> StepResult:
        """Execute the step logic."""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate step configuration at parse time."""
        pass

    def can_resume(self, ctx: StepContext) -> bool:
        """Check if step supports resume from checkpoint."""
        return True
```

### Executor Implementation

```python
# claiw/engine/executor.py

import asyncio
from dataclasses import dataclass
from typing import Dict, List, Set
from collections import defaultdict

@dataclass
class ExecutionPlan:
    """Represents the DAG execution order."""
    levels: List[List[str]]  # Steps that can run in parallel at each level
    dependencies: Dict[str, Set[str]]

    @classmethod
    def from_workflow(cls, workflow: Workflow) -> "ExecutionPlan":
        """Build execution plan from workflow definition."""
        # Topological sort with parallel detection
        in_degree = defaultdict(int)
        dependents = defaultdict(list)

        for step in workflow.steps.values():
            for dep in step.depends_on:
                in_degree[step.name] += 1
                dependents[dep].append(step.name)

        levels = []
        ready = [s for s in workflow.steps if in_degree[s] == 0]

        while ready:
            levels.append(ready)
            next_ready = []
            for step in ready:
                for dependent in dependents[step]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        next_ready.append(dependent)
            ready = next_ready

        return cls(
            levels=levels,
            dependencies={s: set(workflow.steps[s].depends_on)
                         for s in workflow.steps}
        )


class WorkflowExecutor:
    """Executes workflows with checkpointing and resume support."""

    def __init__(
        self,
        checkpoint_manager: CheckpointManager,
        llm_provider: LLMProvider,
        renderer: Renderer,
    ):
        self.checkpointer = checkpoint_manager
        self.llm = llm_provider
        self.renderer = renderer

    async def execute(
        self,
        workflow: Workflow,
        inputs: Dict[str, Any],
        *,
        run_id: Optional[str] = None,
        resume_from: Optional[str] = None,
    ) -> WorkflowResult:
        """Execute a workflow, optionally resuming from checkpoint."""

        # Initialize or resume run
        if resume_from:
            run = await self.checkpointer.load_run(resume_from)
            completed_steps = run.completed_steps
        else:
            run_id = run_id or generate_run_id()
            run = Run(id=run_id, workflow=workflow, inputs=inputs)
            completed_steps = set()
            await self.checkpointer.save_run(run)

        plan = ExecutionPlan.from_workflow(workflow)
        outputs: Dict[str, Any] = {}

        # Load outputs from completed steps
        for step_name in completed_steps:
            checkpoint = await self.checkpointer.load_step(run.id, step_name)
            outputs[step_name] = checkpoint.outputs

        # Execute remaining steps level by level
        for level in plan.levels:
            # Filter out completed steps
            pending = [s for s in level if s not in completed_steps]

            if not pending:
                continue

            # Execute steps in parallel within level
            tasks = []
            for step_name in pending:
                step = workflow.steps[step_name]

                # Gather inputs from dependencies
                step_inputs = {
                    dep: outputs[dep]
                    for dep in step.depends_on
                }

                ctx = StepContext(
                    run_id=run.id,
                    step_name=step_name,
                    workflow_name=workflow.meta.name,
                    workflow_version=workflow.meta.version,
                    inputs=step_inputs,
                    config=step.config,
                    llm=self.llm.get_client(step.config.get("model")),
                    state=self.checkpointer,
                    progress=self.renderer.get_progress(step_name),
                )

                task = self._execute_step(step, ctx)
                tasks.append((step_name, task))

            # Wait for all parallel steps
            results = await asyncio.gather(
                *[t[1] for t in tasks],
                return_exceptions=True
            )

            # Process results
            for (step_name, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    return WorkflowResult(
                        status="failure",
                        failed_step=step_name,
                        error=str(result),
                        outputs=outputs,
                    )

                outputs[step_name] = result.outputs

                # Checkpoint after each step
                await self.checkpointer.save_step(
                    run.id, step_name, result
                )

        return WorkflowResult(
            status="success",
            outputs=outputs,
        )

    async def _execute_step(
        self,
        step: Step,
        ctx: StepContext
    ) -> StepResult:
        """Execute a single step with error handling."""
        handler = self._load_handler(step.handler)

        self.renderer.step_started(ctx.step_name)

        try:
            result = await handler.execute(ctx)
            self.renderer.step_completed(ctx.step_name, result)
            return result

        except Exception as e:
            # Check retry policy
            retries = step.on_error.get("retry", 0)

            for attempt in range(retries):
                self.renderer.step_retry(ctx.step_name, attempt + 1)
                try:
                    result = await handler.execute(ctx)
                    self.renderer.step_completed(ctx.step_name, result)
                    return result
                except Exception:
                    continue

            # Check fallback
            fallback = step.on_error.get("fallback")
            if fallback == "continue_with_warnings":
                self.renderer.step_warning(ctx.step_name, str(e))
                return StepResult(
                    status="skipped",
                    outputs={},
                    duration_ms=0,
                    metadata={"warning": str(e)}
                )

            raise
```

### Checkpoint System (DBOS-Inspired)

```python
# claiw/engine/checkpoint.py

from datetime import datetime
from typing import Any, Dict, Optional
import sqlite3
import json

class CheckpointManager:
    """
    DBOS-inspired checkpoint system.

    Philosophy: Every step is a transaction. State is durably stored
    after each step completes, enabling exact resume on failure.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    workflow_name TEXT NOT NULL,
                    workflow_version TEXT NOT NULL,
                    status TEXT NOT NULL,
                    inputs TEXT NOT NULL,  -- JSON
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    outputs TEXT  -- JSON
                );

                CREATE TABLE IF NOT EXISTS step_checkpoints (
                    run_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    outputs TEXT NOT NULL,  -- JSON
                    started_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    tokens_used INTEGER,
                    metadata TEXT,  -- JSON
                    PRIMARY KEY (run_id, step_name),
                    FOREIGN KEY (run_id) REFERENCES runs(id)
                );

                CREATE INDEX IF NOT EXISTS idx_runs_workflow
                    ON runs(workflow_name, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_runs_status
                    ON runs(status);
            """)

    async def save_run(self, run: Run) -> None:
        """Save or update run metadata."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO runs
                (id, workflow_name, workflow_version, status, inputs,
                 created_at, updated_at, completed_at, outputs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run.id,
                run.workflow.meta.name,
                run.workflow.meta.version,
                run.status,
                json.dumps(run.inputs),
                run.created_at.isoformat(),
                datetime.utcnow().isoformat(),
                run.completed_at.isoformat() if run.completed_at else None,
                json.dumps(run.outputs) if run.outputs else None,
            ))

    async def save_step(
        self,
        run_id: str,
        step_name: str,
        result: StepResult
    ) -> None:
        """Durably save step checkpoint. This is the core DBOS pattern."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO step_checkpoints
                (run_id, step_name, status, outputs, started_at,
                 completed_at, duration_ms, tokens_used, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                step_name,
                result.status,
                json.dumps(result.outputs),
                result.started_at.isoformat(),
                result.completed_at.isoformat(),
                result.duration_ms,
                result.tokens_used,
                json.dumps(result.metadata),
            ))

            # Update run's updated_at
            conn.execute("""
                UPDATE runs SET updated_at = ? WHERE id = ?
            """, (datetime.utcnow().isoformat(), run_id))

    async def load_run(self, run_id: str) -> Run:
        """Load run with all checkpoint data for resume."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            run_row = conn.execute(
                "SELECT * FROM runs WHERE id = ?", (run_id,)
            ).fetchone()

            if not run_row:
                raise RunNotFoundError(run_id)

            checkpoints = conn.execute("""
                SELECT * FROM step_checkpoints
                WHERE run_id = ? ORDER BY completed_at
            """, (run_id,)).fetchall()

            return Run.from_db(run_row, checkpoints)

    async def get_completed_steps(self, run_id: str) -> Set[str]:
        """Get set of successfully completed steps."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT step_name FROM step_checkpoints
                WHERE run_id = ? AND status = 'success'
            """, (run_id,)).fetchall()

            return {row[0] for row in rows}
```

---

## 4. Registry System

### Design Philosophy

The registry is modeled after PyPI meets Pokemon. Workflows are:
1. **Versioned** - Semantic versioning with clear upgrade paths
2. **Discoverable** - Rich metadata and search
3. **Evolvable** - Training runs improve agents over time
4. **Tradeable** - Share trained agents with encrypted state

### Registry Protocol

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         REGISTRY ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────┘

  Local Cache                        Registry API                   Storage
  ───────────                        ────────────                   ───────

  ~/.claiw/cache/                    api.claiw.dev                  S3/R2
  ├── data-analyst/
  │   ├── v2.3.1/     ◀──────────   GET /workflows/                 ┌─────┐
  │   │   ├── workflow.yaml          data-analyst/                  │ CDN │
  │   │   ├── handlers/              2.3.1                          └──┬──┘
  │   │   └── tests/                                                   │
  │   └── metadata.json              POST /workflows/      ─────────▶  │
  │                                  (publish)                         │
  └── index.json                                                       │
      (local registry                GET /search?q=data   ◀────────────┘
       index)

```

### Workflow Package Format

```
data-analyst-2.3.1.claiw
├── manifest.json              # Package metadata
├── workflow.yaml              # Main workflow definition
├── handlers/                  # Custom step handlers
│   ├── __init__.py
│   └── custom_analyzer.py
├── fixtures/                  # Test fixtures
│   ├── sample.csv
│   └── edge_cases.csv
├── tests/                     # Test definitions
│   ├── unit.yaml
│   └── evals.yaml
├── evolution/                 # Training history
│   ├── lineage.json          # Parent versions, mutations
│   └── training_runs.jsonl   # Historical training data
└── SIGNATURE                  # Package signature for integrity
```

### Evolution System (The Pokemon Metaphor)

The key insight: agents improve through use. Every successful run is training data.

```python
# claiw/registry/evolution.py

from dataclasses import dataclass
from typing import List, Optional
import json

@dataclass
class EvolutionRecord:
    """Records a single training run for evolution."""
    run_id: str
    workflow_version: str
    input_hash: str
    output_quality: float  # 0.0 - 1.0, from eval or user feedback
    tokens_used: int
    duration_ms: int
    user_corrections: Optional[List[str]] = None
    timestamp: str


class EvolutionEngine:
    """
    Manages workflow evolution through training.

    Philosophy: Agents should get better over time. Each run is an
    opportunity to learn. Users can "level up" their agents through
    curated training sets.
    """

    def __init__(self, state_manager: StateManager):
        self.state = state_manager

    async def record_run(
        self,
        run: Run,
        quality_score: float,
        user_corrections: Optional[List[str]] = None,
    ) -> EvolutionRecord:
        """Record a run for potential evolution."""
        record = EvolutionRecord(
            run_id=run.id,
            workflow_version=run.workflow.meta.version,
            input_hash=hash_inputs(run.inputs),
            output_quality=quality_score,
            tokens_used=run.total_tokens,
            duration_ms=run.total_duration_ms,
            user_corrections=user_corrections,
            timestamp=datetime.utcnow().isoformat(),
        )

        await self.state.append_evolution_record(
            run.workflow.meta.name,
            record
        )

        return record

    async def propose_evolution(
        self,
        workflow_name: str,
        min_training_runs: int = 50,
        quality_threshold: float = 0.9,
    ) -> Optional[EvolutionProposal]:
        """
        Analyze training data and propose prompt/config improvements.

        This is the "leveling up" process.
        """
        records = await self.state.get_evolution_records(workflow_name)

        if len(records) < min_training_runs:
            return None

        # Analyze patterns in high-quality runs
        high_quality = [r for r in records if r.output_quality >= quality_threshold]
        low_quality = [r for r in records if r.output_quality < 0.7]

        # Extract user corrections for prompt improvement
        all_corrections = []
        for record in records:
            if record.user_corrections:
                all_corrections.extend(record.user_corrections)

        if not all_corrections:
            return None

        # Use LLM to synthesize improvements
        proposal = await self._generate_evolution_proposal(
            workflow_name,
            high_quality_patterns=self._extract_patterns(high_quality),
            low_quality_patterns=self._extract_patterns(low_quality),
            user_corrections=all_corrections,
        )

        return proposal

    async def apply_evolution(
        self,
        workflow_name: str,
        proposal: EvolutionProposal,
    ) -> str:
        """
        Apply evolution proposal, creating new version.

        Returns new version string.
        """
        current = await self.state.get_workflow(workflow_name)

        new_version = bump_version(
            current.meta.version,
            "minor" if proposal.is_breaking else "patch"
        )

        evolved = Workflow(
            meta=WorkflowMeta(
                **current.meta.dict(),
                version=new_version,
                lineage=Lineage(
                    parent=f"{workflow_name}@{current.meta.version}",
                    mutations=proposal.changes,
                    training_runs=len(await self.state.get_evolution_records(workflow_name)),
                    success_rate=proposal.projected_success_rate,
                ),
            ),
            steps=apply_mutations(current.steps, proposal.step_changes),
            llm=apply_mutations(current.llm, proposal.llm_changes),
        )

        await self.state.save_workflow(evolved)

        return new_version
```

### Sharing Trained Agents

```python
# claiw/registry/export.py

from cryptography.fernet import Fernet
import json
import tarfile
from pathlib import Path

class AgentExporter:
    """
    Export trained agents with encrypted state.

    The "selling a beefed up WoW account" feature.
    """

    async def export_agent(
        self,
        workflow_name: str,
        *,
        include_training_data: bool = True,
        include_state: bool = True,
        encryption_key: Optional[str] = None,
    ) -> Path:
        """
        Export agent to shareable package.

        Args:
            workflow_name: Name of workflow to export
            include_training_data: Include evolution records
            include_state: Include run history and checkpoints
            encryption_key: If provided, encrypt sensitive data
        """
        workflow = await self.state.get_workflow(workflow_name)

        export_dir = Path(tempfile.mkdtemp())
        package_name = f"{workflow_name}-{workflow.meta.version}.claiw"

        # Export workflow definition
        (export_dir / "workflow.yaml").write_text(
            workflow.to_yaml()
        )

        # Export manifest
        manifest = {
            "name": workflow_name,
            "version": workflow.meta.version,
            "exported_at": datetime.utcnow().isoformat(),
            "includes_training": include_training_data,
            "includes_state": include_state,
            "encrypted": encryption_key is not None,
        }
        (export_dir / "manifest.json").write_text(json.dumps(manifest))

        # Export evolution data
        if include_training_data:
            records = await self.state.get_evolution_records(workflow_name)
            evolution_data = [r.dict() for r in records]

            if encryption_key:
                fernet = Fernet(encryption_key.encode())
                encrypted = fernet.encrypt(json.dumps(evolution_data).encode())
                (export_dir / "evolution" / "records.enc").write_bytes(encrypted)
            else:
                (export_dir / "evolution" / "records.jsonl").write_text(
                    "\n".join(json.dumps(r) for r in evolution_data)
                )

        # Export state
        if include_state:
            runs = await self.state.get_runs(workflow_name, limit=100)
            state_data = {
                "runs": [r.dict() for r in runs],
                "checkpoints": await self._export_checkpoints(runs),
            }

            if encryption_key:
                fernet = Fernet(encryption_key.encode())
                encrypted = fernet.encrypt(json.dumps(state_data).encode())
                (export_dir / "state.enc").write_bytes(encrypted)
            else:
                (export_dir / "state.json").write_text(json.dumps(state_data))

        # Create tarball
        output_path = export_dir.parent / package_name
        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(export_dir, arcname=workflow_name)

        return output_path
```

---

## 5. State Management

### Dual Database Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         STATE ARCHITECTURE                               │
└─────────────────────────────────────────────────────────────────────────┘

  SQLite (claiw.db)                    DuckDB (analytics.duckdb)
  ─────────────────                    ────────────────────────

  OLTP workload                        OLAP workload
  - Workflow definitions               - Run aggregates
  - Run metadata                       - Token usage analytics
  - Step checkpoints                   - Performance trends
  - Secrets (encrypted)                - Eval results

  Optimized for:                       Optimized for:
  - Single-row lookups                 - Analytical queries
  - Transactional writes               - Time-series analysis
  - Resume operations                  - Cost tracking

  ┌────────────────────┐              ┌────────────────────┐
  │  runs              │              │  run_metrics       │
  │  step_checkpoints  │    sync     │  daily_usage       │
  │  workflows         │  ────────▶  │  eval_results      │
  │  secrets           │   (async)   │  provider_costs    │
  └────────────────────┘              └────────────────────┘

```

### SQLite Schema

```sql
-- Core operational tables

CREATE TABLE workflows (
    name TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    definition TEXT NOT NULL,  -- YAML
    cached_at TEXT NOT NULL,
    source TEXT NOT NULL,  -- 'local', 'registry', 'file'
    source_url TEXT
);

CREATE TABLE runs (
    id TEXT PRIMARY KEY,
    workflow_name TEXT NOT NULL,
    workflow_version TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'success', 'failure', 'cancelled')),
    inputs TEXT NOT NULL,
    outputs TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT,

    FOREIGN KEY (workflow_name) REFERENCES workflows(name)
);

CREATE TABLE step_checkpoints (
    run_id TEXT NOT NULL,
    step_name TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    status TEXT NOT NULL,
    inputs TEXT NOT NULL,
    outputs TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    tokens_used INTEGER,
    cost_usd REAL,
    llm_provider TEXT,
    llm_model TEXT,
    metadata TEXT,

    PRIMARY KEY (run_id, step_name),
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE TABLE secrets (
    key TEXT PRIMARY KEY,
    value_encrypted BLOB NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE evolution_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_name TEXT NOT NULL,
    run_id TEXT NOT NULL,
    output_quality REAL NOT NULL,
    user_corrections TEXT,  -- JSON array
    created_at TEXT NOT NULL,

    FOREIGN KEY (workflow_name) REFERENCES workflows(name),
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

-- Indexes
CREATE INDEX idx_runs_workflow_created ON runs(workflow_name, created_at DESC);
CREATE INDEX idx_runs_status ON runs(status);
CREATE INDEX idx_checkpoints_run ON step_checkpoints(run_id, sequence);
CREATE INDEX idx_evolution_workflow ON evolution_records(workflow_name, created_at DESC);
```

### DuckDB Analytics Schema

```sql
-- Materialized analytics tables (synced from SQLite)

CREATE TABLE run_metrics AS
SELECT
    r.id as run_id,
    r.workflow_name,
    r.workflow_version,
    r.status,
    r.created_at::TIMESTAMP as created_at,
    r.completed_at::TIMESTAMP as completed_at,
    EPOCH_MS(r.completed_at::TIMESTAMP - r.created_at::TIMESTAMP) as duration_ms,
    SUM(s.tokens_used) as total_tokens,
    SUM(s.cost_usd) as total_cost_usd,
    COUNT(s.step_name) as step_count
FROM sqlite_scan('claiw.db', 'runs') r
LEFT JOIN sqlite_scan('claiw.db', 'step_checkpoints') s ON r.id = s.run_id
GROUP BY r.id, r.workflow_name, r.workflow_version, r.status, r.created_at, r.completed_at;

-- Daily aggregates for dashboard
CREATE TABLE daily_usage AS
SELECT
    DATE_TRUNC('day', created_at) as date,
    workflow_name,
    COUNT(*) as run_count,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
    AVG(duration_ms) as avg_duration_ms,
    SUM(total_tokens) as total_tokens,
    SUM(total_cost_usd) as total_cost_usd
FROM run_metrics
GROUP BY DATE_TRUNC('day', created_at), workflow_name;

-- Provider cost tracking
CREATE TABLE provider_costs AS
SELECT
    DATE_TRUNC('day', s.completed_at::TIMESTAMP) as date,
    s.llm_provider,
    s.llm_model,
    COUNT(*) as call_count,
    SUM(s.tokens_used) as total_tokens,
    SUM(s.cost_usd) as total_cost_usd
FROM sqlite_scan('claiw.db', 'step_checkpoints') s
WHERE s.llm_provider IS NOT NULL
GROUP BY DATE_TRUNC('day', s.completed_at::TIMESTAMP), s.llm_provider, s.llm_model;

-- Eval trends
CREATE TABLE eval_trends AS
SELECT
    DATE_TRUNC('day', e.created_at::TIMESTAMP) as date,
    e.workflow_name,
    AVG(e.output_quality) as avg_quality,
    COUNT(*) as eval_count
FROM sqlite_scan('claiw.db', 'evolution_records') e
GROUP BY DATE_TRUNC('day', e.created_at::TIMESTAMP), e.workflow_name;
```

### Encryption Strategy

```python
# claiw/state/encryption.py

from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64

class SecretsManager:
    """
    Manages encrypted secrets storage.

    Uses age-compatible encryption (scrypt + AES-GCM).
    Master key derived from user passphrase.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._master_key: Optional[bytes] = None

    def unlock(self, passphrase: str) -> None:
        """Derive master key from passphrase."""
        # Load salt from secrets file or generate
        salt = self._get_or_create_salt()

        kdf = Scrypt(
            salt=salt,
            length=32,
            n=2**14,
            r=8,
            p=1,
        )
        self._master_key = kdf.derive(passphrase.encode())

    def store_secret(self, key: str, value: str) -> None:
        """Encrypt and store a secret."""
        if not self._master_key:
            raise SecretsLockedError()

        nonce = os.urandom(12)
        aesgcm = AESGCM(self._master_key)
        ciphertext = aesgcm.encrypt(nonce, value.encode(), key.encode())

        encrypted = base64.b64encode(nonce + ciphertext)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO secrets (key, value_encrypted, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (key, encrypted, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))

    def get_secret(self, key: str) -> Optional[str]:
        """Decrypt and retrieve a secret."""
        if not self._master_key:
            raise SecretsLockedError()

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value_encrypted FROM secrets WHERE key = ?", (key,)
            ).fetchone()

        if not row:
            return None

        encrypted = base64.b64decode(row[0])
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]

        aesgcm = AESGCM(self._master_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, key.encode())

        return plaintext.decode()
```

---

## 6. LLM Provider Abstraction

### Design Goals

1. **Seamless switching** - Change providers with a config edit, not code changes
2. **Unified interface** - Same API regardless of provider
3. **Smart routing** - Route different steps to optimal models
4. **Cost tracking** - Know exactly what you're spending

### Provider Interface

```python
# claiw/llm/provider.py

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, List
from pydantic import BaseModel

class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class LLMResponse(BaseModel):
    content: str
    model: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    latency_ms: int
    finish_reason: str

class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
    ) -> LLMResponse:
        """Generate a completion."""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Stream a completion."""
        pass

    @abstractmethod
    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Estimate cost in USD."""
        pass

    @property
    @abstractmethod
    def available_models(self) -> List[str]:
        """List available models."""
        pass


class ProviderRouter:
    """
    Routes LLM calls to appropriate providers based on config.

    Implements the model routing from workflow YAML.
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self.providers: Dict[str, LLMProvider] = {}
        self._init_providers()

    def _init_providers(self):
        """Initialize configured providers."""
        # Map model prefixes to providers
        self.model_prefixes = {
            "claude": "anthropic",
            "gpt": "openai",
            "o1": "openai",
            "local": "ollama",
            "gemini": "google",
        }

        for provider_name in self._get_required_providers():
            self.providers[provider_name] = self._create_provider(provider_name)

    def get_client(self, model: str) -> LLMClient:
        """Get appropriate client for model."""
        provider_name = self._resolve_provider(model)
        provider = self.providers[provider_name]

        return LLMClient(
            provider=provider,
            model=model,
            default_temperature=self.config.temperature,
        )

    def _resolve_provider(self, model: str) -> str:
        """Resolve model string to provider name."""
        # Handle aliases
        model = self.config.aliases.get(model, model)

        # Resolve by prefix
        for prefix, provider in self.model_prefixes.items():
            if model.startswith(prefix):
                return provider

        # Fallback to default
        return self.config.default_provider


class LLMClient:
    """High-level client for LLM operations in steps."""

    def __init__(
        self,
        provider: LLMProvider,
        model: str,
        default_temperature: float = 0.7,
    ):
        self.provider = provider
        self.model = model
        self.default_temperature = default_temperature
        self._call_count = 0
        self._total_tokens = 0
        self._total_cost = 0.0

    async def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Simple completion interface."""
        messages = []
        if system:
            messages.append(Message(role="system", content=system))
        messages.append(Message(role="user", content=prompt))

        response = await self.provider.complete(
            messages,
            model=self.model,
            temperature=temperature or self.default_temperature,
            max_tokens=max_tokens,
        )

        self._call_count += 1
        self._total_tokens += response.tokens_input + response.tokens_output
        self._total_cost += response.cost_usd

        return response.content

    async def structured(
        self,
        prompt: str,
        output_schema: Type[BaseModel],
        *,
        system: Optional[str] = None,
        retries: int = 2,
    ) -> BaseModel:
        """
        Structured output with pydantic validation.

        Uses pydantic-ai patterns under the hood.
        """
        for attempt in range(retries + 1):
            response = await self.complete(
                prompt=f"{prompt}\n\nRespond with JSON matching this schema:\n{output_schema.schema_json()}",
                system=system,
                temperature=0.3,  # Lower temp for structured output
            )

            try:
                # Try to parse response as JSON
                data = json.loads(self._extract_json(response))
                return output_schema.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as e:
                if attempt == retries:
                    raise StructuredOutputError(f"Failed to parse response: {e}")
                continue

    @property
    def stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "calls": self._call_count,
            "tokens": self._total_tokens,
            "cost_usd": self._total_cost,
        }
```

### Provider Implementations

```python
# claiw/llm/anthropic.py

import anthropic
from .provider import LLMProvider, LLMResponse, Message

class AnthropicProvider(LLMProvider):
    """Anthropic/Claude provider."""

    PRICING = {
        "claude-3-opus": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet": {"input": 3.0, "output": 15.0},
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
        "claude-sonnet": {"input": 3.0, "output": 15.0},  # alias
        "claude-opus": {"input": 15.0, "output": 75.0},   # alias
    }

    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def complete(
        self,
        messages: List[Message],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        model = self._resolve_model(model or "claude-sonnet")

        # Convert to Anthropic format
        system = None
        anthropic_messages = []
        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        start = time.monotonic()
        response = await self.client.messages.create(
            model=model,
            messages=anthropic_messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
        )
        latency_ms = int((time.monotonic() - start) * 1000)

        return LLMResponse(
            content=response.content[0].text,
            model=model,
            tokens_input=response.usage.input_tokens,
            tokens_output=response.usage.output_tokens,
            cost_usd=self.estimate_cost(
                model,
                response.usage.input_tokens,
                response.usage.output_tokens
            ),
            latency_ms=latency_ms,
            finish_reason=response.stop_reason,
        )

    async def stream(
        self,
        messages: List[Message],
        **kwargs,
    ) -> AsyncIterator[str]:
        model = self._resolve_model(kwargs.get("model", "claude-sonnet"))

        system = None
        anthropic_messages = []
        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        async with self.client.messages.stream(
            model=model,
            messages=anthropic_messages,
            system=system,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4096),
        ) as stream:
            async for text in stream.text_stream:
                yield text

    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        pricing = self.PRICING.get(model, self.PRICING["claude-sonnet"])
        return (
            (input_tokens / 1_000_000) * pricing["input"] +
            (output_tokens / 1_000_000) * pricing["output"]
        )

    @property
    def available_models(self) -> List[str]:
        return list(self.PRICING.keys())

    def _resolve_model(self, model: str) -> str:
        aliases = {
            "claude-sonnet": "claude-3-5-sonnet-20241022",
            "claude-opus": "claude-3-opus-20240229",
            "claude-haiku": "claude-3-haiku-20240307",
        }
        return aliases.get(model, model)
```

---

## 7. Testing Strategy

### Testing Pyramid

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          TESTING PYRAMID                                 │
└─────────────────────────────────────────────────────────────────────────┘

                              ╱╲
                             ╱  ╲
                            ╱    ╲
                           ╱ Evals╲         Manual judgment, expensive
                          ╱        ╲        Run before major releases
                         ╱──────────╲
                        ╱            ╲
                       ╱ Integration  ╲     Full workflow runs with mocks
                      ╱                ╲    Run on PR, daily
                     ╱──────────────────╲
                    ╱                    ╲
                   ╱     Unit Tests       ╲  Fast, focused, deterministic
                  ╱                        ╲ Run on every commit
                 ╱──────────────────────────╲

```

### Unit Testing

```python
# tests/engine/test_executor.py

import pytest
from claiw.engine import WorkflowExecutor, Workflow, Step
from claiw.testing import MockLLMProvider, MemoryCheckpointManager

@pytest.fixture
def mock_llm():
    """Mock LLM that returns canned responses."""
    return MockLLMProvider({
        "analyze": "Analysis complete: 3 patterns detected.",
        "synthesize": '{"insights": [{"finding": "test", "confidence": 0.9}]}',
    })

@pytest.fixture
def memory_checkpoint():
    """In-memory checkpoint manager for testing."""
    return MemoryCheckpointManager()

class TestExecutor:
    async def test_simple_workflow_executes(self, mock_llm, memory_checkpoint):
        """Test basic workflow execution."""
        workflow = Workflow.from_yaml("""
            meta:
              name: test
              version: 1.0.0
            steps:
              start:
                type: input
                handler: claiw.builtins.echo
              end:
                type: output
                depends_on: [start]
                handler: claiw.builtins.echo
        """)

        executor = WorkflowExecutor(
            checkpoint_manager=memory_checkpoint,
            llm_provider=mock_llm,
            renderer=NullRenderer(),
        )

        result = await executor.execute(workflow, {"input": "test"})

        assert result.status == "success"
        assert memory_checkpoint.runs_count == 1

    async def test_resume_from_checkpoint(self, mock_llm, memory_checkpoint):
        """Test resuming a failed workflow."""
        workflow = Workflow.from_yaml("""
            meta:
              name: test
              version: 1.0.0
            steps:
              step1:
                type: transform
                handler: claiw.builtins.echo
              step2:
                type: transform
                depends_on: [step1]
                handler: claiw.builtins.failing
              step3:
                type: output
                depends_on: [step2]
                handler: claiw.builtins.echo
        """)

        executor = WorkflowExecutor(
            checkpoint_manager=memory_checkpoint,
            llm_provider=mock_llm,
            renderer=NullRenderer(),
        )

        # First run fails at step2
        result = await executor.execute(workflow, {"input": "test"})
        assert result.status == "failure"
        assert result.failed_step == "step2"

        run_id = result.run_id

        # Fix the handler
        workflow.steps["step2"].handler = "claiw.builtins.echo"

        # Resume from checkpoint
        result = await executor.execute(
            workflow,
            {"input": "test"},
            resume_from=run_id
        )

        assert result.status == "success"

        # step1 should not have been re-executed
        assert memory_checkpoint.get_step_execution_count(run_id, "step1") == 1
```

### Integration Testing

```python
# tests/integration/test_workflows.py

import pytest
from pathlib import Path
from claiw.testing import WorkflowTestRunner, MockRegistry

FIXTURES_DIR = Path(__file__).parent / "fixtures"

class TestDataAnalystWorkflow:
    """Integration tests for the data-analyst workflow."""

    @pytest.fixture
    def runner(self, tmp_path):
        return WorkflowTestRunner(
            config_dir=tmp_path,
            registry=MockRegistry(),
            llm_responses_file=FIXTURES_DIR / "llm_responses.json",
        )

    async def test_full_workflow_with_csv(self, runner):
        """Test complete workflow with sample CSV."""
        result = await runner.run(
            "data-analyst",
            inputs={"source": str(FIXTURES_DIR / "sample.csv")},
        )

        assert result.status == "success"
        assert "report" in result.outputs
        assert len(result.outputs["insights"]) >= 1

        # Check checkpoint was created for each step
        assert result.checkpoints_created == 6

    async def test_handles_empty_csv(self, runner):
        """Test error handling for empty datasets."""
        result = await runner.run(
            "data-analyst",
            inputs={"source": str(FIXTURES_DIR / "empty.csv")},
        )

        assert result.status == "failure"
        assert "empty dataset" in result.error.lower()

    async def test_handles_malformed_csv(self, runner):
        """Test graceful handling of malformed data."""
        result = await runner.run(
            "data-analyst",
            inputs={"source": str(FIXTURES_DIR / "malformed.csv")},
        )

        # Should fail at validate step with clear error
        assert result.status == "failure"
        assert result.failed_step == "validate"
```

### Eval Framework

```python
# claiw/testing/evals.py

from dataclasses import dataclass
from typing import List, Optional
from pydantic import BaseModel

class EvalCriteria(BaseModel):
    """Single evaluation criterion."""
    name: str
    description: str
    weight: float = 1.0

class EvalResult(BaseModel):
    """Result of a single eval."""
    workflow_name: str
    eval_name: str
    passed: bool
    score: float  # 0.0 - 1.0
    criteria_scores: Dict[str, float]
    judge_reasoning: str
    run_id: str
    duration_ms: int

class EvalRunner:
    """
    Runs evals against workflows using LLM-as-judge.

    Philosophy: Evals are not pass/fail tests. They're quality scores
    that help track improvement over time.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        judge_model: str = "claude-opus",
    ):
        self.llm = llm_provider
        self.judge_model = judge_model

    async def run_eval(
        self,
        workflow: Workflow,
        eval_config: EvalConfig,
        inputs: Dict[str, Any],
    ) -> EvalResult:
        """Run a single eval against a workflow."""

        # Execute workflow
        executor = WorkflowExecutor(...)
        result = await executor.execute(workflow, inputs)

        if result.status != "success":
            return EvalResult(
                workflow_name=workflow.meta.name,
                eval_name=eval_config.name,
                passed=False,
                score=0.0,
                criteria_scores={},
                judge_reasoning=f"Workflow failed: {result.error}",
                run_id=result.run_id,
                duration_ms=result.duration_ms,
            )

        # Judge the output
        judge_prompt = self._build_judge_prompt(
            eval_config.criteria,
            inputs,
            result.outputs,
        )

        judgment = await self.llm.structured(
            prompt=judge_prompt,
            output_schema=JudgmentSchema,
            model=self.judge_model,
            temperature=0.0,  # Deterministic judging
        )

        overall_score = sum(
            judgment.scores[c.name] * c.weight
            for c in eval_config.criteria
        ) / sum(c.weight for c in eval_config.criteria)

        return EvalResult(
            workflow_name=workflow.meta.name,
            eval_name=eval_config.name,
            passed=overall_score >= eval_config.threshold,
            score=overall_score,
            criteria_scores=judgment.scores,
            judge_reasoning=judgment.reasoning,
            run_id=result.run_id,
            duration_ms=result.duration_ms,
        )

    def _build_judge_prompt(
        self,
        criteria: List[EvalCriteria],
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
    ) -> str:
        return f"""
You are evaluating an AI workflow's output. Score each criterion from 0.0 to 1.0.

INPUT:
{json.dumps(inputs, indent=2)}

OUTPUT:
{json.dumps(outputs, indent=2)}

CRITERIA TO EVALUATE:
{chr(10).join(f"- {c.name}: {c.description}" for c in criteria)}

For each criterion, provide a score and explain your reasoning.
"""


class EvalSuite:
    """Run and track eval suites over time."""

    async def run_suite(
        self,
        workflow_name: str,
        version: str,
    ) -> EvalSuiteResult:
        """Run all evals for a workflow version."""
        workflow = await self.registry.get(workflow_name, version)
        evals = workflow.tests.get("evals", [])

        results = []
        for eval_config in evals:
            result = await self.runner.run_eval(
                workflow,
                eval_config,
                eval_config.input,
            )
            results.append(result)

            # Store in DuckDB for trend analysis
            await self.analytics.record_eval(result)

        return EvalSuiteResult(
            workflow_name=workflow_name,
            version=version,
            results=results,
            overall_score=sum(r.score for r in results) / len(results),
            passed=all(r.passed for r in results),
        )
```

### CLI Test Commands

```
$ claiw test data-analyst

╔═══════════════════════════════════════════════════════════════════════╗
║  claiw test • data-analyst v2.3.1                                     ║
╚═══════════════════════════════════════════════════════════════════════╝

  Running tests...

  UNIT TESTS
  ──────────
  ✓ Handles empty dataset                                     12ms
  ✓ Processes standard CSV                                    45ms
  ✓ Validates column types                                    23ms
  ✓ Handles null values with config                           18ms

  4/4 passed                                                  98ms

  INTEGRATION TESTS
  ─────────────────
  ✓ Full workflow with sample data                           2.3s
  ✓ Resume from validate checkpoint                          1.1s
  ✓ Parallel step execution                                  1.8s

  3/3 passed                                                 5.2s

  EVALS
  ─────
  ⠸ Running Insight quality eval...

  Insight quality                                            Score: 0.87
    ├─ Specific and actionable: 0.9
    ├─ Statistics cited: 0.85
    └─ Confidence reasonable: 0.85

  Judge reasoning: "Insights correctly identified seasonal
  patterns and cited specific percentages. Minor deduction
  for one insight lacking confidence interval."

  1/1 passed (threshold: 0.8)                                8.4s

  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

  SUMMARY
  ═══════
  Total: 8 tests
  Passed: 8
  Failed: 0
  Duration: 13.7s

  ✓ All tests passed
```

---

## 8. Key Tradeoffs

### What claiw Accepts

| Decision | Rationale |
|----------|-----------|
| **YAML over Python for workflow definitions** | Workflows should be readable by non-engineers. YAML is familiar, auditable, and can be validated statically. Python can be used for custom handlers. |
| **SQLite + DuckDB over Postgres** | Zero setup. Works offline. Single file backup. Postgres is overkill for local CLI tool. Registry could use Postgres. |
| **Click over Typer** | Click's context system is more flexible. Better control over output. More mature ecosystem. |
| **pydantic-ai for structured output** | Proven patterns. Good validation. Provider-agnostic design. |
| **DBOS patterns over custom state** | Battle-tested checkpoint/resume semantics. Clear transaction boundaries. |
| **Registry is optional** | Local-first. You can use claiw without ever touching the registry. |
| **Encryption at rest** | Secrets and shareable state must be secure by default. |

### What claiw Rejects

| Decision | Rationale |
|----------|-----------|
| **TUI interfaces** | This is not a browser. Scrollback is sacred. Output should be grepable. |
| **GraphQL API** | REST is sufficient. GraphQL adds complexity without benefit for this use case. |
| **Kubernetes orchestration** | claiw is a CLI tool, not an orchestration platform. Use Temporal/Dagster for that. |
| **Real-time collaboration** | Single-user tool. Collaboration happens through shared workflows, not live sessions. |
| **Plugin system at v1** | Plugins add complexity. Start with good built-in handlers. Add plugins in v2. |
| **Web UI** | The terminal is the interface. Web dashboards can come later as a separate project. |
| **Multi-tenancy** | This is not a SaaS. Registry might be multi-tenant, but CLI is single-user. |

### Performance Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Cold start | < 500ms | CLI tools must be fast. uvx adds ~200ms. |
| Workflow parse | < 100ms | YAML parsing should be imperceptible. |
| Checkpoint write | < 50ms | SQLite is fast enough. |
| UI refresh rate | 10 fps max | Terminal is not a video game. |
| Memory overhead | < 100MB | CLI should be lightweight. |

### Security Boundaries

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SECURITY BOUNDARIES                              │
└─────────────────────────────────────────────────────────────────────────┘

  TRUSTED                              UNTRUSTED
  ───────                              ─────────

  ~/.claiw/config.yaml                 Registry packages (verified)
  ~/.claiw/secrets.yaml.enc            Downloaded handlers (sandboxed)
  Local workflow files                 LLM responses (validated)

                    ┌───────────────┐
                    │   Boundary    │
                    │               │
   User Input ──────│► Validation  ─│──────► Execution
                    │   Sanitize    │
                    └───────────────┘

  ASSUMPTIONS:
  - Local files are trusted (user's machine)
  - Registry packages are signed and verified
  - Custom handlers run with limited permissions
  - LLM output is never executed directly
  - Secrets never leave the machine unencrypted

```

---

## Summary

claiw is built on these principles:

1. **Local-first, registry-optional** - Works beautifully offline
2. **Stateful by default** - Every run is resumable
3. **Testing is not optional** - Unit, integration, evals baked in
4. **The terminal is enough** - No TUI, no web UI, just great output
5. **Evolution over configuration** - Agents improve through use

The architecture prioritizes developer experience over infrastructure complexity. A single developer should be able to run `uvx claiw run data-analyst` and feel like they're using a polished video game, not wrestling with a distributed system.
