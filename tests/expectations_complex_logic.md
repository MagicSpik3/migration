# Test Contract: Debugging Complex Logic Optimization

**Test Script:** `tests/debug_complex_logic.py`
**Goal:** Verify that pipeline state is preserved across steps using the "Primary Key Heuristic".

---

## Phase 1: The Setup (`calc_delays`)

### 1. Input Data
* **Source:** `input_data.csv` (Raw)
* **Columns:** `id`, `dor` (string), `dod` (string), `region`, `age`, `sex`, `status`
* **Row Count:** 6 (Original raw data)

### 2. Execution
* **Function:** `calc_delays(df)`
* **Logic:**
    1.  Parse `dor` to Date.
    2.  Calculate `delay_days`.
    3.  **FILTER:** Keep only `delay_days >= 0`. (Drops 1 row: ID 103)

### 3. Expected Output
* **Rows:** 5 (Row 103 removed)
* **Columns:** Adds `delay_days`, `date_reg`, `date_death`.
* **Critical Check:** Does the output contain the `id` column? **YES.**

### 4. Optimizer Decision (The Fix)
* **Old Logic:** Row count dropped (6 -> 5). **SKIP SAVE.** (FAIL)
* **New Logic:** `id` column present. **UPDATE STATE.** (PASS)
* **Console Output:** `💾 Pipeline State Updated (calc_delays preserved 'id')`

---

## Phase 2: The Target (`complex_logic`)

### 1. Input Data
* **Source:** `temp_pipeline_state.csv` (The file saved by Phase 1)
* **Crucial Requirement:** Must contain column `delay_days`.

### 2. Execution
* **Function:** `complex_logic(df)`
* **Logic:**
    1.  `filter(!is.na(delay_days))`
    2.  `summarise(avg_delay = mean(delay_days))`

### 3. Validation
* **Old Result:** `Error: object 'delay_days' not found`.
* **Expected Result:** **PASS**. The function runs without error.

### 4. Optimizer Outcome
* **Console Output:** `✅ Optimization SUCCESS.`