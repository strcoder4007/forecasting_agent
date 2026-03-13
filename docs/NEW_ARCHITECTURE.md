# The Autonomous Forecasting Agent: Architecture 2.0

## The Core Philosophy
The current system is a static Machine Learning pipeline with an LLM bolted onto the end for data analysis. If the schema of the CSV file changes (e.g., a column is named `Store_Code` instead of `LOC_ID`), the static pipeline breaks. 

**Architecture 2.0** shifts the paradigm: The LLM is no longer just a consumer of the forecast; the LLM *is* the orchestrator of the entire data science lifecycle. It dynamically discovers data, writes its own ETL pipelines, trains models, and generates forecasts on the fly using a secure code-execution sandbox.

---

## 1. The Execution Sandbox (The Core Enabler)
To operate autonomously, the agent needs to write and execute code. 
- **Tool:** `execute_python(code: str, timeout: int = 60)`
- **Mechanism:** The backend saves the generated code to a temporary `.py` file and executes it via Python's `subprocess.run()`. It captures `stdout` and `stderr`.
- **Self-Correction:** If the code fails (e.g., a `KeyError` because the agent hallucinated a column name), the stack trace is returned to the agent. The agent reads the error, rewrites the code, and tries again until it succeeds.

---

## 2. The Multi-Agent Workflow
The process of forecasting is too complex for a single prompt. We will divide the work among specialized sub-agents, orchestrated by a Master Agent.

### Phase 1: The Data Explorer Agent
**Goal:** Understand the raw data without human intervention.
- **Input:** A directory path containing raw files (CSV, Excel, Parquet).
- **Process:** 
  - The agent writes Python scripts to list the directory.
  - It writes pandas code to load `df.head()`, `df.dtypes`, and `df.isnull().sum()`.
  - It looks for joining keys (e.g., "Both Sales and SOH have a `Store_Code` column").
- **Output:** An internal Markdown report detailing the schema, data quality issues (e.g., "Sales contains negative quantities", "Discounts are formatted as strings with '%' signs"), and the recommended target variable for forecasting.

### Phase 2: The ETL / Transformer Agent
**Goal:** Clean the data and build a feature matrix.
- **Input:** The raw data paths and the Explorer Agent's Markdown report.
- **Process:**
  - Writes data cleaning scripts (e.g., using regex to strip currency symbols, converting dates to `datetime64`).
  - Writes aggregation logic (e.g., grouping daily transactional data into weekly buckets).
  - Writes feature engineering code (e.g., calculating 4-week rolling averages, creating `is_promotional` flags).
- **Output:** A clean, unified feature matrix saved to a temporary Parquet file or DuckDB table.

### Phase 3: The Modeler Agent (AutoML)
**Goal:** Find the best mathematical representation of the demand.
- **Input:** The clean feature matrix.
- **Process:**
  - Writes code to perform a time-series cross-validation split (preventing data leakage).
  - Instantiates multiple models using `scikit-learn`, `lightgbm`, or `xgboost` (e.g., Ridge, Poisson LightGBM).
  - Evaluates the models using WMAPE and MAPE.
  - Identifies the winning model and runs the final inference on the future horizon.
- **Output:** The final predictions and accuracy metrics saved to the database.

### Phase 4: The Synthesizer (User Interface)
**Goal:** Communicate the results to the user.
- **Input:** The final predictions and the execution logs from the previous agents.
- **Process:** Reads the results and explains the methodology to the user in natural language.
  - *"I discovered your data, cleaned the pricing strings, and engineered rolling demand features. I tested LightGBM and Ridge regression; LightGBM won with a WMAPE of 38%. Here are the expected high-risk stockouts for next week..."*

---

## 3. Transition Strategy
To migrate the current codebase to Architecture 2.0 without losing the UI we just built:

1. **Retain the UI:** The split-screen UI is perfect. The left panel remains the chat. The right panel (Agent Trace Logs) will now become an incredible visualizer, showing the actual Python code being written and executed by the agents in real-time.
2. **Deprecate the Static Pipeline:** We will remove `data_loader.py` and `forecast_pipeline.py`. The system will no longer rely on hardcoded pandas transformations.
3. **Implement `execute_python`:** We will add the code-execution tool to `chat_service.py` to act as the foundation for the new agents.
4. **Agent Orchestration:** We will update `chat_service.py` to use a state machine or prompt chaining to guide the LLM through the Explorer -> ETL -> Modeler workflow.

## 4. Advantages of Architecture 2.0
- **Zero Configuration:** A user can drop a completely unknown dataset into the folder and simply say "Forecast this." The agent figures out the rest.
- **Resilience:** Static pipelines crash when data formats change slightly. A code-generating agent can catch the error, rewrite its parsing logic, and continue.
- **Transparency:** The user can literally see the exact Python code the agent used to clean the data and train the model in the Trace Panel.