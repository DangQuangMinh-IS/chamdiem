# PROJECT.md

Per-project facts. Fill this in once per project; update it when stack, commands, or structure change.

## Overview
- Name: Hệ Thống Đánh Giá Chéo & Chấm Điểm Nhóm Trực Tuyến
- One-line purpose: Đánh giá chéo đóng góp nhóm sinh viên qua Magic Link độc bản, tự động bù khuyết 100% (Default Imputation) và tính điểm Decimal chuẩn xác.
- Target user: Giảng viên, Trợ giảng và Sinh viên làm bài tập lớn/đồ án nhóm
- Stage: prototype / in use

## Tech Stack & Dependencies
- Language(s) / runtime: Python 3.10+
- Framework(s): Streamlit, pytest, pandas
- Database / storage: SQLite (Local) / Cloud-ready (Streamlit secrets / Supabase)
- Hosting / deploy: Streamlit Community Cloud (`*.streamlit.app`)
- Dependency manifest(s): `requirements.txt`

## Commands (exact, from repo root)
- Install: `pip install -r requirements.txt`
- Dev server: `streamlit run app.py`
- Format: none
- Lint: none
- Typecheck: none
- Test (all): `pytest`
- Test (single file): `pytest tests/test_calculator.py`
- Build: none
- DB migrate / seed: none (auto-initialized on startup)

## Structure (annotated tree)
```text
/
├── core/
│   ├── __init__.py        # Public API export
│   ├── calculator.py      # Decimal math engine, 100% imputation, penalty, cap 10.0
│   └── storage.py         # SQLite storage, Magic Link tokens, and evaluation matrix
├── data/                  # SQLite database location (chamdiem.db)
├── tests/
│   ├── __init__.py
│   ├── test_calculator.py # Unit tests verifying invariants and mathematical precision
│   └── test_storage.py    # Unit tests for storage operations
├── app.py                 # Streamlit UI (Student View via Magic Link + Admin Dashboard)
├── requirements.txt       # Dependencies
├── AGENTS.md              # Workflow rules and constitution
├── PROJECT.md             # Project facts & conventions
└── README.md              # User and deployment documentation
```

## Key files
| File | Purpose |
|---|---|
| `core/calculator.py` | Decimal calculation engine, 100% default imputation, penalty, 10.0 cap, Largest Remainder adjustment |
| `core/storage.py` | SQLite database manager, magic link tokens, peer evaluation recording, and closing |
| `app.py` | Streamlit web UI supporting both Student View (`?token=...`) and Admin View |
| `tests/test_calculator.py` | Test suite covering 8 scenarios (equality, imputation, penalties, overflow, edge cases) |

## Conventions
- Math precision: Standard library `decimal.Decimal` with `ROUND_HALF_UP` and Largest Remainder Method; avoid float inaccuracies.
- Security: Unique one-time magic tokens (`uuid4`) per student, no password friction, anonymous evaluation among teammates.
- UI: Streamlit responsive sliders with 100% default state, total budget validation gauge, and submission locking.

## Constraints and gotchas
- Streamlit query parameters: `st.query_params.get("token")` routes directly to the student's evaluation form.
- Multi-user concurrency: SQLite connections are managed using context managers with immediate commit/close to prevent Windows file-lock issues.
