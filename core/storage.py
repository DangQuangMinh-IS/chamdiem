"""SQLite storage layer for peer evaluation system."""

import os
import sqlite3
import uuid
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

from core.calculator import (
    calculate_final_scores,
    CalculationResult,
    to_decimal,
)

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "chamdiem.db"


class Storage:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    code TEXT UNIQUE NOT NULL,
                    group_score_x REAL NOT NULL,
                    penalty_ratio REAL DEFAULT 0.0,
                    deadline TEXT,
                    is_closed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    student_id TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    email TEXT,
                    token TEXT UNIQUE NOT NULL,
                    is_submitted INTEGER DEFAULT 0,
                    submitted_at TIMESTAMP,
                    final_score REAL,
                    final_r REAL,
                    final_pct REAL,
                    is_locked INTEGER DEFAULT 0,
                    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    evaluator_id INTEGER NOT NULL,
                    target_id INTEGER NOT NULL,
                    score_pct REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(group_id, evaluator_id, target_id),
                    CHECK(evaluator_id <> target_id),
                    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                    FOREIGN KEY (evaluator_id) REFERENCES members(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_id) REFERENCES members(id) ON DELETE CASCADE
                );
                """
            )

            # Migration: Ensure is_locked column exists in existing DBs
            cols = [r["name"] for r in conn.execute("PRAGMA table_info(members)").fetchall()]
            if "is_locked" not in cols:
                conn.execute("ALTER TABLE members ADD COLUMN is_locked INTEGER DEFAULT 0")

    def create_group(
        self,
        name: str,
        code: str,
        group_score_x: float,
        penalty_ratio: float = 0.0,
        deadline: Optional[str] = None,
    ) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO groups (name, code, group_score_x, penalty_ratio, deadline)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, code, group_score_x, penalty_ratio, deadline),
            )
            return int(cursor.lastrowid)

    def add_member(
        self,
        group_id: int,
        student_id: str,
        full_name: str,
        email: Optional[str] = None,
    ) -> str:
        token = uuid.uuid4().hex[:16]
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO members (group_id, student_id, full_name, email, token)
                VALUES (?, ?, ?, ?, ?)
                """,
                (group_id, student_id, full_name, email, token),
            )
            return token

    def get_member_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT m.*, g.name AS group_name, g.code AS group_code,
                       g.group_score_x, g.penalty_ratio, g.deadline, g.is_closed
                FROM members m
                JOIN groups g ON m.group_id = g.id
                WHERE m.token = ?
                """,
                (token,),
            ).fetchone()
            if not row:
                return None

            member = dict(row)
            peers = conn.execute(
                """
                SELECT id, student_id, full_name
                FROM members
                WHERE group_id = ? AND id <> ?
                ORDER BY student_id ASC
                """,
                (member["group_id"], member["id"]),
            ).fetchall()
            member["peers"] = [dict(p) for p in peers]
            return member

    def get_group(self, group_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM groups WHERE id = ?", (group_id,)
            ).fetchone()
            return dict(row) if row else None

    def list_groups(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT g.*, 
                       COUNT(m.id) as total_members,
                       SUM(CASE WHEN m.is_submitted = 1 THEN 1 ELSE 0 END) as submitted_count
                FROM groups g
                LEFT JOIN members m ON g.id = m.group_id
                GROUP BY g.id
                ORDER BY g.id DESC
                """
            ).fetchall()
            return [dict(r) for r in rows]

    def get_group_members(self, group_id: int) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM members 
                WHERE group_id = ? 
                ORDER BY student_id ASC
                """,
                (group_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def delete_member(self, member_id: int) -> bool:
        """Xóa thành viên khỏi nhóm (tự động xóa đánh giá liên quan)."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM members WHERE id = ?", (member_id,))
            return True

    def delete_group(self, group_id: int) -> bool:
        """Xóa nhóm hoàn toàn (tự động xóa toàn bộ thành viên và đánh giá)."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM groups WHERE id = ?", (group_id,))
            return True

    def update_group(
        self,
        group_id: int,
        name: str,
        code: str,
        group_score_x: float = 0.0,
        penalty_ratio: float = 0.0,
        deadline: Optional[str] = None,
    ) -> bool:
        """Cập nhật thông tin nhóm (Tên nhóm, mã nhóm, điểm X, tỷ lệ phạt, hạn chót)."""
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE groups
                SET name = ?, code = ?, group_score_x = ?, penalty_ratio = ?, deadline = ?
                WHERE id = ?
                """,
                (name, code, float(group_score_x), float(penalty_ratio), deadline, group_id),
            )
            return True

    def update_member(
        self,
        member_id: int,
        student_id: str,
        full_name: str,
        email: Optional[str] = None,
    ) -> bool:
        """Cập nhật thông tin thành viên (MSSV, Họ tên, Email)."""
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE members
                SET student_id = ?, full_name = ?, email = ?
                WHERE id = ?
                """,
                (student_id, full_name, email, member_id),
            )
            return True

    def unlock_member_submission(self, member_id: int) -> bool:
        """Mở khóa để thành viên có thể vào chấm lại (reset trạng thái nộp và mở khóa)."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE members SET is_submitted = 0, submitted_at = NULL, is_locked = 0 WHERE id = ?",
                (member_id,),
            )
            return True

    def set_member_lock(self, member_id: int, is_locked: bool) -> bool:
        """Khóa hoặc mở khóa phiếu của một thành viên."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE members SET is_locked = ? WHERE id = ?",
                (1 if is_locked else 0, member_id),
            )
            return True

    def set_group_lock(
        self, group_id: int, is_locked: bool, only_submitted: bool = True
    ) -> int:
        """Khóa hoặc mở khóa toàn bộ phiếu trong nhóm."""
        with self._get_connection() as conn:
            if only_submitted and is_locked:
                cursor = conn.execute(
                    "UPDATE members SET is_locked = 1 WHERE group_id = ? AND is_submitted = 1",
                    (group_id,),
                )
            else:
                cursor = conn.execute(
                    "UPDATE members SET is_locked = ? WHERE group_id = ?",
                    (1 if is_locked else 0, group_id),
                )
            return cursor.rowcount

    def reopen_group(self, group_id: int) -> bool:
        """Mở lại đợt đánh giá cho nhóm sau khi đã chốt điểm."""
        with self._get_connection() as conn:
            conn.execute("UPDATE groups SET is_closed = 0 WHERE id = ?", (group_id,))
            return True

    def get_evaluations_by_evaluator(
        self, group_id: int, evaluator_id: int
    ) -> Dict[int, float]:
        """Lấy danh sách các điểm mà thành viên đã chấm trước đó."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT target_id, score_pct
                FROM evaluations
                WHERE group_id = ? AND evaluator_id = ?
                """,
                (group_id, evaluator_id),
            ).fetchall()
            return {int(r["target_id"]): float(r["score_pct"]) for r in rows}

    def clone_group(
        self,
        group_id: int,
        new_code: Optional[str] = None,
        new_name: Optional[str] = None,
    ) -> int:
        """Sao chép toàn bộ nhóm gồm tất cả thành viên, điểm số và ma trận đánh giá."""
        group = self.get_group(group_id)
        if not group:
            raise ValueError(f"Không tìm thấy nhóm ID {group_id}")

        target_name = new_name or f"{group['name']} (Bản sao)"
        base_code = new_code or f"{group['code']}-COPY"
        target_code = base_code

        with self._get_connection() as conn:
            # Tránh trùng mã nhóm
            count = 1
            while conn.execute("SELECT id FROM groups WHERE code = ?", (target_code,)).fetchone():
                target_code = f"{base_code}-{count}"
                count += 1

            # 1. Tạo nhóm mới
            cursor = conn.execute(
                """
                INSERT INTO groups (name, code, group_score_x, penalty_ratio, deadline, is_closed)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    target_name,
                    target_code,
                    group["group_score_x"],
                    group["penalty_ratio"],
                    group["deadline"],
                    group["is_closed"],
                ),
            )
            new_group_id = int(cursor.lastrowid)

            # 2. Sao chép thành viên
            old_members = conn.execute(
                "SELECT * FROM members WHERE group_id = ?", (group_id,)
            ).fetchall()

            id_mapping = {}  # old_id -> new_id
            for m in old_members:
                new_token = uuid.uuid4().hex[:16]
                is_locked_val = m["is_locked"] if "is_locked" in m.keys() else 0
                cur_m = conn.execute(
                    """
                    INSERT INTO members (group_id, student_id, full_name, email, token, is_submitted, submitted_at, final_score, final_r, final_pct, is_locked)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_group_id,
                        m["student_id"],
                        m["full_name"],
                        m["email"],
                        new_token,
                        m["is_submitted"],
                        m["submitted_at"],
                        m["final_score"],
                        m["final_r"],
                        m["final_pct"],
                        is_locked_val,
                    ),
                )
                id_mapping[m["id"]] = cur_m.lastrowid

            # 3. Sao chép các đánh giá chéo
            old_evals = conn.execute(
                "SELECT * FROM evaluations WHERE group_id = ?", (group_id,)
            ).fetchall()

            for ev in old_evals:
                old_ev_id = ev["evaluator_id"]
                old_tg_id = ev["target_id"]
                if old_ev_id in id_mapping and old_tg_id in id_mapping:
                    conn.execute(
                        """
                        INSERT INTO evaluations (group_id, evaluator_id, target_id, score_pct)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            new_group_id,
                            id_mapping[old_ev_id],
                            id_mapping[old_tg_id],
                            ev["score_pct"],
                        ),
                    )

            return new_group_id

    def submit_evaluation(
        self,
        group_id: int,
        evaluator_id: int,
        ratings: Dict[int, float],
    ) -> bool:
        with self._get_connection() as conn:
            group = conn.execute(
                "SELECT is_closed FROM groups WHERE id = ?", (group_id,)
            ).fetchone()
            if not group or group["is_closed"] == 1:
                return False

            member = conn.execute(
                "SELECT is_locked FROM members WHERE id = ?", (evaluator_id,)
            ).fetchone()
            if member and member["is_locked"] == 1:
                return False

            for target_id, score_pct in ratings.items():
                if target_id == evaluator_id:
                    continue
                conn.execute(
                    """
                    INSERT INTO evaluations (group_id, evaluator_id, target_id, score_pct)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(group_id, evaluator_id, target_id)
                    DO UPDATE SET score_pct = excluded.score_pct, created_at = CURRENT_TIMESTAMP
                    """,
                    (group_id, evaluator_id, target_id, float(score_pct)),
                )

            conn.execute(
                """
                UPDATE members
                SET is_submitted = 1, submitted_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (evaluator_id,),
            )
            return True

    def get_evaluations_matrix(self, group_id: int) -> Dict[int, Dict[int, float]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT evaluator_id, target_id, score_pct
                FROM evaluations
                WHERE group_id = ?
                """,
                (group_id,),
            ).fetchall()

            evals: Dict[int, Dict[int, float]] = {}
            for r in rows:
                ev_id = r["evaluator_id"]
                t_id = r["target_id"]
                if ev_id not in evals:
                    evals[ev_id] = {}
                evals[ev_id][t_id] = float(r["score_pct"])
            return evals

    def close_and_calculate_group(
        self, group_id: int, group_score_x: Optional[float] = None
    ) -> CalculationResult:
        group = self.get_group(group_id)
        if not group:
            raise ValueError(f"Không tìm thấy nhóm {group_id}")

        if group_score_x is not None:
            score_x = float(group_score_x)
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE groups SET group_score_x = ? WHERE id = ?",
                    (score_x, group_id),
                )
        else:
            score_x = float(group["group_score_x"])

        members = self.get_group_members(group_id)
        member_ids = [m["id"] for m in members]

        evaluations = self.get_evaluations_matrix(group_id)

        result = calculate_final_scores(
            group_score_x=score_x,
            evaluations=evaluations,
            member_ids=member_ids,
            penalty_ratio=group["penalty_ratio"],
        )

        with self._get_connection() as conn:
            for uid, sc in result.member_scores.items():
                f_score = float(sc.final_score) if score_x > 0 else None
                conn.execute(
                    """
                    UPDATE members
                    SET final_score = ?, final_r = ?, final_pct = ?
                    WHERE id = ?
                    """,
                    (
                        f_score,
                        float(sc.final_r),
                        float(sc.contribution_pct),
                        uid,
                    ),
                )
            conn.execute(
                "UPDATE groups SET is_closed = 1 WHERE id = ?", (group_id,)
            )

        return result

    def update_group_score(
        self, group_id: int, new_group_score_x: float
    ) -> CalculationResult:
        """Cập nhật điểm nhóm X và tự động quy đổi ra điểm số chính thức cho từng thành viên."""
        return self.close_and_calculate_group(group_id, group_score_x=new_group_score_x)

    def seed_sample_data(self) -> int:
        with self._get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM groups WHERE code = 'NHOM-DEMO'"
            ).fetchone()
            if existing:
                return existing["id"]

        g_id = self.create_group(
            name="Nhóm 01 - Đồ án Công nghệ Phần mềm",
            code="NHOM-DEMO",
            group_score_x=8.5,
            penalty_ratio=0.1,
            deadline="2026-10-30 23:59:00",
        )

        students = [
            ("SV01", "Nguyễn Văn An", "an.nv@student.edu.vn"),
            ("SV02", "Trần Thị Bình", "binh.tt@student.edu.vn"),
            ("SV03", "Lê Hoàng Cường", "cuong.lh@student.edu.vn"),
            ("SV04", "Phạm Minh Dũng", "dung.pm@student.edu.vn"),
            ("SV05", "Hoàng Ngọc Em", "em.hn@student.edu.vn"),
        ]

        for s_id, name, email in students:
            self.add_member(g_id, s_id, name, email)

        return g_id
