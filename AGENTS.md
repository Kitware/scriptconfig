# AGENT Instructions

## 1. Development Environment Setup
- **Language/Runtime**: Python ≥ 3.8 (see `pyproject.toml` for minimum version).
- **Core tools**: `python`, `pip`, and `virtualenv`/`venv`. Optional but recommended locally: `flake8`, `pytest`, `xdoctest`, `coverage`, and `sphinx-build` (for docs).
- **Dependencies**: Install from `requirements.txt`, which chains runtime, test, and optional extras (e.g., `numpy`, `omegaconf`, `rich_argparse`, `argcomplete`). Runtime deps include `ubelt` and `PyYAML`.
- **Quick setup** (mirrors `run_developer_setup.sh`):
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  pip install -e .        # editable install for development
  ```
  Running `./run_developer_setup.sh` performs the same steps.
- **Environment variables**: None required for basic development/testing. CLI autocomplete hooks already declare `PYTHON_ARGCOMPLETE_OK`; no extra env is needed.
- **Docs build prerequisites**: `sphinx-build` is not pinned in `requirements/`; install `sphinx` (and optionally `furo`/themes) manually if you need to build docs.

## 2. Repository Structure Overview
- **`scriptconfig/`**: Main package.
  - `config.py` – legacy `Config` implementation and metaclass logic.
  - `dataconfig.py` – modern `DataConfig`/`dataconf` declarative API (preferred).
  - `value.py` – `Value`, `Path`, `PathList`, `Flag` metadata wrappers.
  - `smartcast.py` – “smart” CLI/string → Python type casting helpers.
  - `argparse_ext.py` – argparse extensions and utilities.
  - `dict_like.py`, `file_like.py` – helpers for dict/file abstractions.
  - `_cli/` – packaged CLI (`scriptconfig` entry point) with modal subcommands.
  - `util/` – small utilities (e.g., `class_or_instancemethod`).
  - `.pyi` stub files and `py.typed` indicate partial type hints that should track implementations.
- **`tests/`**: Pytest suite covering CLI behaviors, inheritance, casting, pickling, path handling, etc.
- **`docs/`**: Sphinx docs (`docs/source`) with manual pages; build via `make html` inside `docs` (requires `sphinx-build` installed).
- **`examples/`**: Sample configs/usage.
- **`dev/`**: Developer utilities (benchmarks, stub generation, secret setup scripts).
- **Root scripts**:  
  - `run_tests.py` – pytest + coverage + xdoctest runner.  
  - `run_doctests.sh` – xdoctest runner.  
  - `run_linter.sh` – basic `flake8` checks.  
  - `publish.sh`, `publish` related scripts for releases.

## 3. Important Components
- **DataConfig / dataconf** (`dataconfig.py`): Declarative config classes defined via class attributes. Handles CLI parsing (`.cli`), loading from kwargs/files, normalization hooks, and inheritance. Metaclass (`MetaDataConfig`) auto-collects defaults.
- **Config** (`config.py`): Legacy dictionary-backed config with `__default__` mapping and `load`/`cli` helpers. Supports smart casting, CLI overrides, file loading, and YAML/JSON persistence.
- **Value/Path/PathList/Flag** (`value.py`): Wrap defaults with metadata: type, help, positionals, required, aliases, choices, etc. `Path*` helpers normalize filesystem inputs; `Flag` supports boolean/counter-like switches.
- **Smartcast** (`smartcast.py`): Heuristically converts strings/CLI tokens to Python types (numbers, lists, bools); can be forced/overridden via `Value(type=...)`.
- **CLI infrastructure**:
  - `argparse_ext.py` adds richer parser behaviors.
  - `_cli/main.py` exposes modal CLI for helper commands (entry point `scriptconfig`).
- **Utilities**: `util/util_class.py` provides decorators for class-or-instance methods; `_ubelt_repr_extension` integrates with `ubelt` repr improvements.
- **Diagnostics**: `diagnostics.py` toggles debug flags for meta-class operations.

## 4. Testing Guide
- **Primary command**: `python run_tests.py` (runs pytest with coverage and xdoctest across package and tests). Equivalent to:
  ```bash
  pytest --cov=scriptconfig --cov-config=pyproject.toml \
         --cov-report=html --cov-report=term \
         --xdoctest scriptconfig tests
  ```
- **Doctests only**: `./run_doctests.sh` (xdoctest with Google style).  
- **Lint (fast sanity)**: `./run_linter.sh` (flake8 E9/F6x/F7x/F82 on src and tests).  
- **Pytest config**: `pytest.ini`/`pyproject.toml` ignore `dev`, `docs`, `setup.py`; warnings filtered. Tests rely on standard tmp paths and built-in fixtures—no external services.
- **Adding tests**: Place new files under `tests/` with `test_*.py`; prefer small, focused cases mirroring existing patterns. For docstring examples, ensure they run under xdoctest Google style.

## 5. Extending or Modifying the System
- Prefer **`DataConfig`** for new features; keep `Config` compatible when touching shared logic. Maintain parity between implementation and `.pyi` stubs when altering public signatures.
- Use **`Value`/`Path`/`Flag`** to add metadata (type enforcement, help, position, aliases). For list/complex parsing, explicitly set `type` to avoid overly aggressive `smartcast`.
- Respect metaclass expectations: `__default__` mirrors `default`; `normalize`/`__post_init__` hooks may be invoked during load/cli.
- Keep backward compatibility with CLI behaviors (aliases, positional handling, counter flags). Update relevant tests or add new ones when modifying parsing or casting.
- File/Path handling: prefer `Path`/`PathList` wrappers; rely on `FileLike`/`DictLike` helpers for duck-typed behavior.
- When adding CLI commands, extend `_cli/main.py` modal CLI and ensure new subcommands are imported similarly to `TemplateCLI`.
- Documentation: add/revise Sphinx sources under `docs/source`; ensure code examples are valid doctests.

## 6. Documentation Overview
- **Top-level**: `README.rst` summarizing goals, quick examples, and project links.  
- **Sphinx** (`docs/source`):
  - `manual/getting_started.rst` – DataConfig basics, smartcast behavior, CLI usage.
  - `auto/` – (autogenerated API stubs if populated).
  - Build with `make html` from `docs/` or `sphinx-build -M html source build`.
- **Changelog**: `CHANGELOG.md` tracks release history.  
- **Packaging metadata**: `pyproject.toml`, `setup.py`, `MANIFEST.in`, `LICENSE`.

## 7. Task-Specific Knowledge
- Package is partially typed; update `.pyi` files and keep `py.typed` intact when changing signatures.
- Tests cover nuanced behaviors: alias resolution, counter flags, inheritance/override rules, pickle compatibility (`test_pickle_dataconf.py`), smartcast edge cases (`test_smartcast_issues.py`), and modal CLI features. Consult relevant tests before altering logic.
- CLI entry point (`scriptconfig.__main__` → `_cli/main.py`) expects `PYTHON_ARGCOMPLETE_OK` marker—retain it if touching entrypoints.
- Optional extras (`requirements/optional.txt`) broaden CLI ergonomics (rich argparse, argcomplete) and casting support (numpy/omegaconf); keep imports optional/guarded.
- Coverage config omits `scriptconfig/__main__.py` and setup scripts; branch coverage enabled.
- Repository is mirrored across GitLab/GitHub; keep licensing (Apache 2) and metadata consistent when modifying distribution files.
