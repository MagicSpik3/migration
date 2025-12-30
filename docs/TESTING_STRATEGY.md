# Documentation Generator Testing Strategy

This module (`tests/test_doc_generator_complex.py`) ensures the `DocumentationEngine` correctly translates SPSS logic into technical documentation without relying on a live LLM connection during testing.

## Test Scenarios

### 1. Complex Branching Diagram (`test_complex_branching_diagram`)
* **Goal:** Verify that the engine can parse complex, multi-step logic flows returned by the LLM.
* **Input:** Mocked LLM response containing conditional logic nodes (e.g., "CheckRegion", "NorthBranch", "SouthBranch").
* **Verification:** Checks that:
    * The Mermaid graph syntax (`graph TD;`) is generated.
    * Specific nodes from the branching logic appear in the output.
    * CSS classes (`class logic`, `class data`) are applied correctly based on the node type.

### 2. Markdown Formatting (`test_markdown_formatting_dedent`)
* **Goal:** Prevent the "Whitespace Trap" where Python's `textwrap.dedent` fails to remove indentation if injected variables have no indentation.
* **Verification:** Reads the generated `.md` file line-by-line to ensure headers (`# Documentation`) and code blocks (` ```mermaid `) start at column 0 (no leading spaces).

### 3. Error Resilience (`test_malformed_llm_response`)
* **Goal:** Ensure the pipeline does not crash if the LLM times out or returns `None`.
* **Input:** `None` returned for the diagram generation step.
* **Verification:** Checks that a valid Markdown file is still produced, containing a placeholder Mermaid node labeled **"LLM Generation Timed Out"** instead of crashing or leaving the file empty.