# Implementation Plan: Architecture 3.0 (Advanced Autonomous Agent)

## Overview
This plan details the implementation of five major capabilities that will transition the application from a raw "Code Generating Sandbox" (Architecture 2.0) into a highly resilient, state-of-the-art "Autonomous Data Scientist" (Architecture 3.0).

---

## Step-by-Step Implementation

### Feature #1: Self-Correcting Data Validation (Data Contracts)
**Goal:** Ensure the ETL script written by the Transformer Agent actually outputs valid data for the Modeler Agent.
1. **Define the Contract:** Create a new Python module (e.g., `backend/contracts.py`). Define a hardcoded schema validation function using `pandas`.
    - Example check: *Are there nulls in `qty_sold`? Does `store_id` exist? Are all `discount_pct` numeric?*
2. **Hook into Orchestrator:** In `backend/orchestrator.py`, after the Transformer Agent completes its script and saves `features.parquet`, call the validation function.
3. **The Self-Correction Loop:** If the validation throws a custom `DataContractError`, catch it. Instead of moving to Phase 3 (Modeler), append the error message to the Transformer Agent's chat history and prompt it to fix its script: *"Your ETL script failed the data contract: Column 'discount_pct' contains strings instead of floats. Please rewrite your script."*

### Feature #2: Memory & Context Persistence Between Runs
**Goal:** Give the Explorer and Transformer agents a permanent "memory" of past runs so they stop making the same mistakes or discoveries twice.
1. **DuckDB Update:** In `backend/storage.py`, create a new table: `CREATE TABLE IF NOT EXISTS knowledge_base (topic VARCHAR, insight VARCHAR, timestamp TIMESTAMP)`.
2. **Synthesizer Update:** Modify Phase 4 (Synthesizer Agent) in `backend/orchestrator.py`. Give it a new tool called `save_insight(topic, insight)`. Instruct the agent: *"If you learned something specific about the data schema during this run, save it."*
3. **Prompt Injection:** Update the system instructions for the Explorer and Transformer agents. Query the `knowledge_base` table and inject all past insights directly into their system prompts: *"Past learnings: 1. The Markdown column is a string percentage..."*

### Feature #3: Hyperparameter Tuning & Cross-Validation
**Goal:** Optimize model accuracy during Phase 3 (AutoML) instead of using default configurations.
1. **Requirements Update:** Add `optuna` and `scikit-learn` (specifically `TimeSeriesSplit`) to `requirements.txt`.
2. **Prompt Update:** In `backend/orchestrator.py`, rewrite the `model_prompt` (Phase 3). 
    - Instruct the Modeler Agent: *"You MUST use `TimeSeriesSplit(n_splits=3)` to validate your models. Do not use a single cutoff date."*
    - Instruct the Modeler Agent: *"You MUST use `optuna` to tune the `max_depth` and `learning_rate` of your LightGBM/XGBoost models for 10 trials before generating final predictions."*

### Feature #5: Human-in-the-Loop Override
**Goal:** Allow the user to review the ETL plan before the agent starts executing irreversible data manipulations or training expensive models.
1. **API Update:** Break `/api/forecast/run` into two steps. Let it run up to Phase 2 (ETL script generation).
2. **Frontend Update:** When Phase 2 generates the script, pause the execution and send a specific UI event (`action: "REQUEST_APPROVAL"`). Render the proposed Python script in the Chat UI with "Approve" and "Reject/Modify" buttons.
3. **User Interaction:**
    - If "Approve": The backend continues to Phase 3.
    - If "Reject" + User feedback ("Don't fill NaNs with zero, use median"): Send the feedback back to the Transformer Agent so it rewrites the script, and loop back to the approval state.

### Feature #6: Semantic Error Parsing (The "Stack Trace Explainer")
**Goal:** Prevent the agent from getting confused by massive 5,000-token Python stack traces.
1. **Sandbox Update:** Modify `backend/sandbox.py`. When a script fails, intercept the raw standard error string.
2. **LLM Pre-Processing:** Make a synchronous, low-temperature call to `gemini-3.1-flash-lite-preview`. 
    - **Prompt:** *"Read this Python stack trace. Summarize exactly what failed in 2 sentences. E.g., 'A KeyError occurred on line 12 because the dataframe does not have a column named store_code'."*
3. **Return Format:** Return *only* this concise explanation back to the generating agent (Explorer/Transformer/Modeler) instead of the raw stack trace. This saves context tokens and dramatically improves the agent's ability to self-correct its code.