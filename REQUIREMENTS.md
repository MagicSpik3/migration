# Migration Engine: System Requirements Specification (SRS)
**Version:** 1.0.0
**Status:** Active Development

---

## 1. Project Overview
The Migration Engine is an automated system designed to convert legacy SPSS syntax files (`.sps`) into modern, production-ready R code (`tidyverse`). Unlike simple transpilers, this system uses a multi-agent architecture to analyze intent, architect robust pipelines, and rigorously test logic using both probabilistic (LLM) and deterministic (AST/Unit Test) methods.

### 1.1 Core Philosophy
1.  **Safety First:** No hallucinated variables. No dropped columns.
2.  **Hybrid Intelligence:** Use LLMs for *Drafting* (creativity) and ASTs for *Refactoring* (syntax/math safety).
3.  **Test-Driven:** No code is accepted without passing a generated `testthat` suite.
4.  **Pipeline Continuity:** Every function must accept a dataframe and return a dataframe (unless it is a pure endpoint reporter).

---

## 2. System Architecture
The system operates as a linear pipeline with feedback loops.

### 2.1 The Pipeline Steps
1.  **Map:** Scans dependencies and builds the execution graph.
2.  **Analyze:** Converts SPSS syntax into natural language specifications.
3.  **Architect:** Drafts R code using Schema Injection and Style Guides.
4.  **Validate:** Statically checks for critical pipeline breaks (e.g., `NULL` returns).
5.  **Optimize:** * *Deterministic:* Fixes common syntax errors via AST Refactoring.
    * *Probabilistic:* Uses an Agentic Retry Loop to fix logic errors.
6.  **QA:** Generates and runs comprehensive Unit Tests.
7.  **Assemble:** Generates the master `main.R` controller.

---

## 3. Functional Requirements

### 3.1 Component: Manifest Manager (`Map`)
* **REQ-MAP-01:** Must scan a target directory for `.sps` files.
* **REQ-MAP-02:** Must detect dependencies via `INSERT FILE` or `INCLUDE` commands.
* **REQ-MAP-03:** Must classify files as `logic` (transformations) or `controller` (orchestrators).
* **REQ-MAP-04:** Must output a JSON Manifest (`migration_manifest.json`) defining the execution order.

### 3.2 Component: Spec Analyst (`Analyze`)
* **REQ-ANA-01:** Must ingest raw SPSS syntax and generate a Markdown Specification (`.md`).
* **REQ-ANA-02:** Must identify **Business Rules** (e.g., "Age > 65 is Senior").
* **REQ-ANA-03:** Must identify **Data Transformations** (Recodes, Filters, Aggregations).
* **REQ-ANA-04:** Must NOT simply translate code line-by-line; it must capture *intent*.

### 3.3 Component: R Architect (`Draft`)
* **REQ-ARC-01:** Must ingest the `.md` Spec and the **Data Schema** (from `input_data.csv`).
* **REQ-ARC-02:** **Schema Injection:** Must strictly use *only* columns present in the provided schema or created within the function.
* **REQ-ARC-03:** **Knowledge Base:** Must utilize the `glossary.csv` to map SPSS commands to correct `dplyr` equivalents (e.g., `SELECT IF` -> `filter`).
* **REQ-ARC-04:** Must follow the "Golden Pattern":
    * Use `tidyverse` verbs.
    * Use `snake_case` variable names.
    * Ensure explicit `return(df)` at the end of transformation functions.

### 3.4 Component: Code Validator (`Gatekeeper`)
* **REQ-VAL-01:** Must perform static analysis on the Draft R code *before* optimization.
* **REQ-VAL-02:** Must reject code that:
    * Returns `NULL`.
    * Uses `transmute()` (dropping data safety).
    * Fails to return a dataframe.
* **REQ-VAL-03:** Must provide a "PASS/FAIL" signal to the orchestrator.

### 3.5 Component: Code Optimizer (`Refine`)
* **REQ-OPT-01:** **AST Refactoring:** Must run an R script (`refactor.R`) to deterministically fix known issues:
    * Invalid Date Math (`as.numeric(d1-d2)` -> `difftime`).
    * Unsafe Type Casting (`cut(age)` -> `cut(as.numeric(age))`).
* **REQ-OPT-02:** **Agentic Retry Loop:** Must run a feedback loop (max 3 retries) where compile errors are fed back to the LLM for correction.
* **REQ-OPT-03:** Must use `styler` to enforce PEP-8 equivalent formatting for R.

### 3.6 Component: QA Engineer (`Test`)
* **REQ-QA-01:** Must generate a `testthat` suite (`tests/test_func.R`) for every logic function.
* **REQ-QA-02:** Must verify:
    * **Happy Path:** Standard data inputs.
    * **Edge Cases:** Boundary values (e.g., 0, negative numbers, missing values).
* **REQ-QA-03:** Must execute the tests via `Rscript`.
* **REQ-QA-04:** Must flag the migration step as "Unstable" if tests fail, but not halt the entire batch execution (allow manual review).

### 3.7 Component: Pipeline Controller (`Assemble`)
* **REQ-CON-01:** Must generate a `main.R` script.
* **REQ-CON-02:** Must source all migrated function files.
* **REQ-CON-03:** Must execute functions in the order defined by the Manifest.
* **REQ-CON-04:** Must handle data loading and global error reporting.

---

## 4. Non-Functional Requirements

### 4.1 Reliability & Stability
* **NFR-REL-01:** The system must be resilient to LLM hallucinations. The Schema Injection and Validator steps are critical mitigations.
* **NFR-REL-02:** The system must self-recover from transient compilation errors during the Optimization phase.

### 4.2 Maintainability
* **NFR-MNT-01:** All generated R code must score 0 on `lintr` (or be auto-corrected by `styler`).
* **NFR-MNT-02:** The system must include a Self-Test Framework (`run_framework_tests.py`) to verify the migration engine itself.

### 4.3 Extensibility
* **NFR-EXT-01:** The Knowledge Base (`glossary.csv`) must be editable by users to add custom mappings without changing Python code.

---

## 5. Data Requirements
* **REQ-DAT-01:** Input data must be provided as CSV for Schema Injection.
* **REQ-DAT-02:** The system assumes all inputs are initially `character` type (legacy CSV behavior) and must explicitly cast types in R.

---

## 6. Glossary & Standards
* **Dates:** Always use `lubridate::ymd()` or `dmy()`.
* **Math:** Always wrap subtractions in `as.numeric()`.
* **Logic:** Always use `case_when()` instead of nested `if_else`.