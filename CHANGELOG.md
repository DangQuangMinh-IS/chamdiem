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
- Pre-evaluation workflow: Allows groups to self-evaluate and lock contribution percentages ($R_i \times 100\%$, e.g. A 110%, B 100%, C 95%...) before receiving a group grade, with a one-click conversion tool to apply group score $X$ later.
- Management actions: Member deletion and full group deletion with cascade cleanup and safety popover confirmation.
- Re-evaluation workflow: Allows students to edit and resubmit their ratings while the evaluation window is open (prefilling previous ratings), with instructor capability to unlock individual submissions or reopen closed groups.
- Entity editing: In-place editing for group metadata (name, code, group score, penalty, deadline) and student details (MSSV, name, email).
- Detailed evaluation matrix viewer: Full evaluator-to-target cross-evaluation grid displaying distributed percentages, submission statuses, and CSV export.
- Group cloning: Deep duplication of an entire group including metadata, members (with new independent magic tokens), and the complete evaluation matrix.
- Automated test suite (`tests/test_calculator.py`, `tests/test_storage.py`) covering mathematical invariants, imputation, penalties, overflow, and storage operations.
- Project documentation in `PROJECT.md` and `README.md`.

