# Test-suite navigation

Run the complete suite from the project root with:

```text
.venv\Scripts\python.exe -m pytest -q
```

## Suite groups

| Directory | Purpose |
|---|---|
| `unit/detectors/` | AST and source-analysis detector behaviour |
| `unit/services/` | Ingestion, functional validation, eligibility, prevalence, and metric logic |
| `integration/` | End-to-end research and generation workflow behaviour |
| `ui/` | Streamlit application behaviour |

The detector tests are intentionally separate from functional-validation
tests. Functional validation decides which authentic submissions enter the
analysis dataset; detector tests decide whether a source pattern satisfies a
defect definition.
