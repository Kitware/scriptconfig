### AGENT Context

#### 1) Setup

* Python ≥ 3.8 (see `pyproject.toml`).
* Developer install:

  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -e .[all]
  ```

#### 2) Project Layout (top-level)

* `scriptconfig/`: library implementation
* `tests/`: pytest suite
* `docs/`: Sphinx docs (`docs/source`)
* `examples/`: usage samples
* `dev/`: developer utilities / scripts
* Root scripts: `run_tests.py`, `run_linter.sh`, `run_doctests.sh`.

#### 3) Core APIs / Concepts

* **Preferred API: `DataConfig` / `dataconf`** (`scriptconfig/dataconfig.py`)

  * Declarative config classes via class attrs; supports `.cli`, loading, normalization hooks, inheritance.
* **Legacy API: `Config`** (`scriptconfig/config.py`)

  * Dict-backed config with `__default__`, `load`, `cli`, YAML/JSON persistence.
* **Value wrappers** (`scriptconfig/value.py`)

  * `Value`, `Path`, `PathList`, `Flag` provide metadata (help, type, required, aliases, choices, positional behavior).
* **Casting** (`scriptconfig/smartcast.py`)

  * Converts CLI strings → Python types; set explicit `Value(type=...)` for complex/list inputs to avoid heuristic miscasts.
* **CLI**: `argparse_ext.py` + packaged CLI under `scriptconfig/_cli/`.

#### 4) Tests / Lint / Docs

* Run full test suite (pytest + coverage + xdoctest):

  ```bash
  python run_tests.py
  ```
* Tests should always be run for changes.

* Lint:

  ```bash
  ./run_linter.sh
  ```

* Docs:

  ```bash
  pip install sphinx
  cd docs && make html
  ```

#### 5) Contribution Rules / Invariants

* Prefer **`DataConfig`** for new features; maintain backwards compatibility for `Config` when touching shared logic.
* Preserve existing CLI behaviors (aliases, positional handling, counter flags); update/add tests when changing parsing/casting.
* Optional deps (e.g., rich argparse / argcomplete / numpy / omegaconf) must remain optional and imports should be guarded.
* Retain `PYTHON_ARGCOMPLETE_OK` marker if modifying entrypoints.
* Agents should add changelog entries for relevant changes when one is not already present.
