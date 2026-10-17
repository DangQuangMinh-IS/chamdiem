# Task: Online Peer Evaluation System (Chấm Điểm Chéo Online)

- **Status:** Completed
- **Driver:** User Request (Implement online peer evaluation system with Default Imputation 100% and Streamlit deployment)
- **Date:** 2026-10-17

## Goal & Scope
- **Goal:** Build an end-to-end online peer review and grade calculation system ready for deployment on Streamlit Community Cloud (no custom domain needed).
- **In Scope:**
  - High-precision calculation engine (`core/calculator.py`) using `Decimal`, `ROUND_HALF_UP`, 100% default imputation, penalty on missing evaluators, 10.0 cap and 0.0 floor redistribution.
  - Data storage layer (`core/storage.py`) using SQLite database with support for token generation, group management, and submission tracking.
  - Streamlit UI (`app.py`):
    - Student Interface: Activated via `?token=<secret_token>`. Mobile-friendly, 100% default sliders, total budget indicator, submit locking.
    - Admin/Teacher Interface: Create groups & members, view/export magic links, monitor submission progress in real-time, close evaluation, calculate final scores, export CSV.
  - Automated test suite (`tests/test_calculator.py`, `tests/test_storage.py`) covering all mathematical invariants and edge cases.
- **Out of Scope (Non-goals):**
  - Complex LDAP/Active Directory university integration.
  - Multi-tenant billing.

## Impacted Files & Architecture
- New files:
  - `requirements.txt`
  - `core/__init__.py`
  - `core/calculator.py`
  - `core/storage.py`
  - `app.py`
  - `tests/__init__.py`
  - `tests/test_calculator.py`
  - `tests/test_storage.py`
  - `CHANGELOG.md`
- Modified files:
  - `PROJECT.md`
  - `README.md`
  - `.gitignore`
- Schemas / Migrations:
  - SQLite tables: `groups`, `members`, `evaluations`

## Execution Checklist
- [x] 1. Preparation & Inspection (branch created, venv ready)
- [x] 2. Implementation:
  - [x] 2.1 Dependencies manifest (`requirements.txt`)
  - [x] 2.2 Core calculation engine (`core/calculator.py`) with `Decimal` and invariants
  - [x] 2.3 Storage and Token Manager (`core/storage.py`)
  - [x] 2.4 Streamlit UI (`app.py`) with Student (Magic Link) & Admin views
- [x] 3. Validation & Testing:
  - [x] Automated tests (`pytest`: 8/8 passed in 0.08s)
  - [x] Edge cases (all missing, 1 missing, cap overflow, zero budget, 9-member team)
- [x] 4. Documentation & Cleanup:
  - [x] Update `PROJECT.md`, `README.md`, `CHANGELOG.md`
  - [x] Clean debug logs & unused code
  - [x] Archive task file
