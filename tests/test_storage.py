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
