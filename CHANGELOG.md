# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- High-precision calculation engine (`core/calculator.py`) using `Decimal` arithmetic, 100% default imputation, penalty ratio for missing evaluators, 10.0 cap with excess redistribution, and Largest Remainder Method rounding.
- SQLite persistence layer (`core/storage.py`) supporting groups, students, one-time magic tokens, and peer evaluation recording.
- Dual-mode Streamlit UI (`app.py`):
  - Student View activated via `?token=<magic_token>` with 100% default sliders, total budget validation, and submission locking.
  - Admin/Teacher Dashboard for group creation, Magic Link generation/CSV export, real-time submission tracking, and final grade calculation.
- Automated test suite (`tests/test_calculator.py`, `tests/test_storage.py`) covering mathematical invariants, imputation, penalties, overflow, and storage operations.
- Project documentation in `PROJECT.md` and `README.md`.
