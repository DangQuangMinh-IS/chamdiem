"""Unit tests for SQLite storage layer."""

import tempfile
from pathlib import Path
from core.storage import Storage


def test_storage_lifecycle():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test.db"
        storage = Storage(db_path)

        # 1. Create group
        group_id = storage.create_group(
            name="Nhóm Thử Nghiệm",
            code="TEST-01",
            group_score_x=8.0,
            penalty_ratio=0.1,
        )
        assert group_id > 0

        # 2. Add members
        t1 = storage.add_member(group_id, "SV01", "Học viên 1", "hv1@test.com")
        t2 = storage.add_member(group_id, "SV02", "Học viên 2", "hv2@test.com")
        t3 = storage.add_member(group_id, "SV03", "Học viên 3", "hv3@test.com")
        assert len(t1) == 16

        # 3. Retrieve member by token
        m1 = storage.get_member_by_token(t1)
        assert m1 is not None
        assert m1["full_name"] == "Học viên 1"
        assert len(m1["peers"]) == 2  # SV02 and SV03

        # 4. Submit evaluations from SV01
        m2_id = [p["id"] for p in m1["peers"] if p["student_id"] == "SV02"][0]
        m3_id = [p["id"] for p in m1["peers"] if p["student_id"] == "SV03"][0]

        ok = storage.submit_evaluation(
            group_id=group_id,
            evaluator_id=m1["id"],
            ratings={m2_id: 110.0, m3_id: 90.0},
        )
        assert ok is True

        # Check member status
        m1_updated = storage.get_member_by_token(t1)
        assert m1_updated["is_submitted"] == 1

        # 5. Close and calculate
        res = storage.close_and_calculate_group(group_id)
        assert res.group_average > 0

        # Verify group is closed
        grp = storage.get_group(group_id)
        assert grp["is_closed"] == 1


def test_pre_evaluation_and_apply_score_later():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_pre.db"
        storage = Storage(db_path)

        # 1. Create group WITHOUT score X (group_score_x = 0.0)
        group_id = storage.create_group(
            name="Nhóm Đồ Án Chưa Có Điểm",
            code="DA-PRE",
            group_score_x=0.0,
            penalty_ratio=0.0,
        )

        t1 = storage.add_member(group_id, "A", "Sinh viên A")
        t2 = storage.add_member(group_id, "B", "Sinh viên B")
        t3 = storage.add_member(group_id, "C", "Sinh viên C")

        m1 = storage.get_member_by_token(t1)
        m2 = storage.get_member_by_token(t2)
        m3 = storage.get_member_by_token(t3)

        # A gives B 110%, C 90%
        storage.submit_evaluation(group_id, m1["id"], {m2["id"]: 110.0, m3["id"]: 90.0})
        # B gives A 100%, C 100%
        storage.submit_evaluation(group_id, m2["id"], {m1["id"]: 100.0, m3["id"]: 100.0})
        # C gives A 100%, B 100%
        storage.submit_evaluation(group_id, m3["id"], {m1["id"]: 100.0, m2["id"]: 100.0})

        # 2. Close and lock percentages before having group score
        res = storage.close_and_calculate_group(group_id)
        members = storage.get_group_members(group_id)
        # Verify scores are None, but percentages exist
        for m in members:
            assert m["final_score"] is None
            assert m["final_pct"] is not None

        # B received 105% (110% from A, 100% from C -> avg = 105%)
        m2_db = [m for m in members if m["student_id"] == "B"][0]
        assert m2_db["final_pct"] == 105.0

        # 3. Later: Instructor enters group score X = 8.0
        res_after = storage.update_group_score(group_id, 8.0)
        members_after = storage.get_group_members(group_id)

        m2_after = [m for m in members_after if m["student_id"] == "B"][0]
        assert m2_after["final_score"] is not None
        # 8.0 * 1.05 = 8.40
        assert m2_after["final_score"] == 8.40


def test_delete_member_and_group():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_del.db"
        storage = Storage(db_path)

        g_id = storage.create_group("Nhóm Cần Xóa", "DEL-01", 8.0)
        t1 = storage.add_member(g_id, "SV01", "Member 1")
        t2 = storage.add_member(g_id, "SV02", "Member 2")

        members = storage.get_group_members(g_id)
        assert len(members) == 2

        # 1. Delete single member
        m1_id = members[0]["id"]
        storage.delete_member(m1_id)
        members_remaining = storage.get_group_members(g_id)
        assert len(members_remaining) == 1
        assert members_remaining[0]["student_id"] == "SV02"

        # 2. Delete whole group
        storage.delete_group(g_id)
        assert storage.get_group(g_id) is None
        assert len(storage.get_group_members(g_id)) == 0


def test_update_group_and_member():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_update.db"
        storage = Storage(db_path)

        g_id = storage.create_group("Tên Cũ", "OLD-01", 7.0, 0.05, "2026-10-20")
        t1 = storage.add_member(g_id, "SV01", "Tên Cũ 1", "old@test.com")
        m1 = storage.get_member_by_token(t1)

        # 1. Update group
        ok_g = storage.update_group(
            group_id=g_id,
            name="Tên Mới",
            code="NEW-01",
            group_score_x=8.5,
            penalty_ratio=0.1,
            deadline="2026-11-01",
        )
        assert ok_g is True
        grp = storage.get_group(g_id)
        assert grp["name"] == "Tên Mới"
        assert grp["code"] == "NEW-01"
        assert grp["group_score_x"] == 8.5
        assert grp["penalty_ratio"] == 0.1
        assert grp["deadline"] == "2026-11-01"

        # 2. Update member
        ok_m = storage.update_member(
            member_id=m1["id"],
            student_id="SV99",
            full_name="Tên Mới 1",
            email="new@test.com",
        )
        assert ok_m is True
        m1_updated = storage.get_member_by_token(t1)
        assert m1_updated["student_id"] == "SV99"
        assert m1_updated["full_name"] == "Tên Mới 1"
        assert m1_updated["email"] == "new@test.com"


def test_unlock_reopen_and_get_evaluations():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_unlock.db"
        storage = Storage(db_path)

        g_id = storage.create_group("Nhóm Unlock", "UL-01", 8.0)
        t1 = storage.add_member(g_id, "A", "Sinh viên A")
        t2 = storage.add_member(g_id, "B", "Sinh viên B")

        m1 = storage.get_member_by_token(t1)
        m2 = storage.get_member_by_token(t2)

        storage.submit_evaluation(g_id, m1["id"], {m2["id"]: 100.0})
        m1_sub = storage.get_member_by_token(t1)
        assert m1_sub["is_submitted"] == 1

        # Check get_evaluations_by_evaluator
        evals = storage.get_evaluations_by_evaluator(g_id, m1["id"])
        assert evals == {m2["id"]: 100.0}

        # Unlock submission
        storage.unlock_member_submission(m1["id"])
        m1_unlocked = storage.get_member_by_token(t1)
        assert m1_unlocked["is_submitted"] == 0

        # Close and Reopen group
        storage.close_and_calculate_group(g_id)
        assert storage.get_group(g_id)["is_closed"] == 1

        storage.reopen_group(g_id)
        assert storage.get_group(g_id)["is_closed"] == 0


def test_clone_group_full_data():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_clone.db"
        storage = Storage(db_path)

        g_id = storage.create_group("Nhóm Gốc", "ORIGINAL-01", 9.0, 0.1)
        t1 = storage.add_member(g_id, "A", "Sinh viên A")
        t2 = storage.add_member(g_id, "B", "Sinh viên B")

        m1 = storage.get_member_by_token(t1)
        m2 = storage.get_member_by_token(t2)

        storage.submit_evaluation(g_id, m1["id"], {m2["id"]: 105.0})
        storage.submit_evaluation(g_id, m2["id"], {m1["id"]: 95.0})
        storage.close_and_calculate_group(g_id)

        # Clone group
        cloned_id = storage.clone_group(g_id, new_code="CLONE-01", new_name="Nhóm Bản Sao")
        assert cloned_id != g_id

        cloned_grp = storage.get_group(cloned_id)
        assert cloned_grp["name"] == "Nhóm Bản Sao"
        assert cloned_grp["code"] == "CLONE-01"
        assert cloned_grp["group_score_x"] == 9.0
        assert cloned_grp["penalty_ratio"] == 0.1
        assert cloned_grp["is_closed"] == 1

        cloned_members = storage.get_group_members(cloned_id)
        assert len(cloned_members) == 2

        # Verify new tokens are generated and distinct from original
        cloned_tokens = [m["token"] for m in cloned_members]
        assert t1 not in cloned_tokens
        assert t2 not in cloned_tokens
        assert len(set(cloned_tokens)) == 2

        # Verify cloned evaluations matrix
        cloned_matrix = storage.get_evaluations_matrix(cloned_id)
        cm1 = [m for m in cloned_members if m["student_id"] == "A"][0]
        cm2 = [m for m in cloned_members if m["student_id"] == "B"][0]

        assert cloned_matrix[cm1["id"]][cm2["id"]] == 105.0
        assert cloned_matrix[cm2["id"]][cm1["id"]] == 95.0


def test_lock_and_unlock_functionality():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_lock.db"
        storage = Storage(db_path)

        g_id = storage.create_group("Nhóm Bảo Mật", "SEC-01", 8.0)
        t1 = storage.add_member(g_id, "SV01", "Member 1")
        t2 = storage.add_member(g_id, "SV02", "Member 2")

        m1 = storage.get_member_by_token(t1)
        m2 = storage.get_member_by_token(t2)

        # Default: not locked
        assert m1["is_locked"] == 0

        # Submit evaluation from SV01
        ok = storage.submit_evaluation(g_id, m1["id"], {m2["id"]: 100.0})
        assert ok is True

        # Admin locks SV01
        storage.set_member_lock(m1["id"], is_locked=True)
        m1_locked = storage.get_member_by_token(t1)
        assert m1_locked["is_locked"] == 1

        # Attempting to submit while locked should fail
        ok_locked = storage.submit_evaluation(g_id, m1["id"], {m2["id"]: 110.0})
        assert ok_locked is False

        # Admin unlocks SV01
        storage.set_member_lock(m1["id"], is_locked=False)
        m1_unlocked = storage.get_member_by_token(t1)
        assert m1_unlocked["is_locked"] == 0

        # Group-level lock for submitted members
        storage.set_group_lock(g_id, is_locked=True, only_submitted=True)
        m1_chk = storage.get_member_by_token(t1)
        m2_chk = storage.get_member_by_token(t2)
        assert m1_chk["is_locked"] == 1
        assert m2_chk["is_locked"] == 0  # SV02 not submitted yet, so not locked

        # Group-level unlock for all
        storage.set_group_lock(g_id, is_locked=False, only_submitted=False)
        assert storage.get_member_by_token(t1)["is_locked"] == 0
        assert storage.get_member_by_token(t2)["is_locked"] == 0


