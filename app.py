"""Streamlit Web Application for Online Peer Evaluation System."""

import io
from decimal import Decimal
import pandas as pd
import streamlit as st

from core.storage import Storage

# Set page config
st.set_page_config(
    page_title="Hệ Thống Đánh Giá Chéo & Chấm Điểm Nhóm",
    page_icon="🎓",
    layout="wide",
)

storage = Storage()

def get_current_base_url() -> str:
    """Tự động nhận diện URL máy chủ hiện tại (Streamlit Cloud hoặc Localhost)."""
    try:
        if hasattr(st, "context"):
            if getattr(st.context, "url", None):
                import urllib.parse
                parsed = urllib.parse.urlparse(st.context.url)
                if parsed.scheme and parsed.netloc:
                    return f"{parsed.scheme}://{parsed.netloc}"
            if getattr(st.context, "headers", None):
                host = st.context.headers.get("host") or st.context.headers.get("Host")
                if host:
                    proto = "http" if ("localhost" in host or "127.0.0.1" in host) else "https"
                    return f"{proto}://{host}"
    except Exception:
        pass
    return "http://localhost:8501"


# Read token from query params
query_params = st.query_params
raw_token = query_params.get("token", None)
if isinstance(raw_token, list):
    token = raw_token[0] if raw_token else None
else:
    token = raw_token
if token:
    token = str(token).strip()

# Custom styling for mobile and clean look
st.markdown(
    """
    <style>
    /* 1. Ẩn hoàn toàn Header, Menu 3 chấm, Watermark và liên kết GitHub */
    #MainMenu {visibility: hidden !important; display: none !important;}
    header {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    [data-testid="stHeader"] {visibility: hidden !important; display: none !important;}
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    [data-testid="stDecoration"] {visibility: hidden !important; display: none !important;}
    [data-testid="stStatusWidget"] {visibility: hidden !important; display: none !important;}
    .stDeployButton {display: none !important;}
    [data-testid="manage-app-button"] {display: none !important;}
    a[href*="github.com"] {display: none !important;}

    /* 2. Căn chỉnh lề trên gọn gàng sau khi ẩn header */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }

    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 4px solid #4CAF50;
    }
    .stSlider > div {
        padding-top: 4px;
        padding-bottom: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_student_view(member_token: str):
    """Student interface accessed via unique magic token."""
    member_data = storage.get_member_by_token(member_token)

    if not member_data:
        st.error("❌ Không tìm thấy thông tin đánh giá cho mã liên kết này.")
        st.warning(
            "💡 **Lưu ý:** Nếu bạn vừa tạo nhóm trên máy chủ Cloud (Streamlit Cloud), "
            "dữ liệu nằm trên Cloud. Hãy mở đường link mang tên miền Cloud của bạn "
            "(dạng `https://ten-app.streamlit.app/?token=...`) thay vì `http://localhost:8501`."
        )
        st.info("Nếu chạy tại máy cá nhân, hãy đảm bảo bạn lấy đúng Magic Link từ Tab 2 của phiên bản đang chạy.")
        return

    group_name = member_data["group_name"]
    group_code = member_data["group_code"]
    group_score_x = member_data["group_score_x"]
    is_closed = member_data["is_closed"] == 1
    is_submitted = member_data["is_submitted"] == 1
    peers = member_data.get("peers", [])

    st.title("🎓 Phiếu Đánh Giá Chéo Thành Viên")
    st.caption(f"Dự án: **{group_name}** ({group_code})")

    # Member information header
    col1, col2, col3 = st.columns([1.5, 1, 1])
    with col1:
        st.markdown(f"**Học viên:** {member_data['full_name']} (`{member_data['student_id']}`)")
    with col2:
        if group_score_x > 0:
            st.markdown(f"**Điểm nhóm (X):** `{group_score_x:.2f}`")
        else:
            st.markdown("**Điểm nhóm (X):** *Chưa có (Đánh giá tỷ lệ %)*")
    with col3:
        if is_closed:
            st.warning("🔒 Đợt đánh giá đã đóng")
        elif is_submitted:
            st.success("✅ Đã nộp phiếu")
        else:
            st.info("⏳ Đang chờ nộp")

    st.divider()

    # Case 1: Group is closed
    if is_closed:
        st.info("📢 Đợt đánh giá của nhóm đã kết thúc và được chốt kết quả.")
        if member_data.get("final_pct") is not None:
            st.markdown("### 🏆 Kết quả chính thức của bạn")
            if group_score_x > 0 and member_data.get("final_score") is not None:
                c1, c2, c3 = st.columns(3)
                c1.metric("Điểm chính thức", f"{member_data['final_score']:.2f} đ")
                c2.metric("Tỷ lệ % nhận được", f"{member_data['final_pct']:.2f}%")
                c3.metric("Hệ số R nhận được", f"{member_data['final_r']:.4f}")
            else:
                c1, c2 = st.columns(2)
                c1.metric("Tỷ lệ % nhận được", f"{member_data['final_pct']:.2f}%")
                c2.info("⏳ Đang chờ Giảng viên chấm điểm nhóm X để quy đổi ra điểm số chính thức.")
        return

    # Case 2: Already submitted (can edit if group is still open)
    edit_flag_key = f"editing_{member_data['id']}"
    is_editing = st.session_state.get(edit_flag_key, False)

    if is_submitted and not is_editing:
        st.success(f"🎉 Bạn đã nộp phiếu đánh giá thành công vào lúc: **{member_data['submitted_at']}**")
        st.markdown(
            """
            > **Bảo mật:** Phiếu đánh giá của bạn đã được ghi nhận an toàn.
            > Nếu bạn cần điều chỉnh điểm số trước khi hết hạn đánh giá, bạn có thể bấm nút **Chỉnh Sửa Lại Phiếu Chấm** bên dưới.
            """
        )
        c_re_col1, c_re_col2 = st.columns([1.5, 2])
        with c_re_col1:
            if st.button("✏️ Chỉnh Sửa Lại Phiếu Chấm", type="primary", use_container_width=True):
                prev_evals = storage.get_evaluations_by_evaluator(member_data["group_id"], member_data["id"])
                form_key = f"ratings_{member_data['id']}"
                if form_key not in st.session_state:
                    st.session_state[form_key] = {}
                for p in peers:
                    p_id = p["id"]
                    val = float(prev_evals.get(p_id, 100.0))
                    st.session_state[form_key][p_id] = val
                    st.session_state[f"peer_slider_{p_id}"] = val
                st.session_state[edit_flag_key] = True
                st.rerun()
        return

    # Case 3: Fill evaluation form (initial or re-evaluating)
    if not peers:
        st.warning("Nhóm của bạn chỉ có 1 thành viên. Không cần thực hiện đánh giá chéo.")
        return

    if is_editing:
        st.warning("⚠️ **Bạn đang ở chế độ chỉnh sửa lại phiếu đánh giá.** Sau khi hoàn tất điều chỉnh, vui lòng bấm **'Cập Nhật & Nộp Lại Phiếu'** ở cuối trang.")
        if st.button("❌ Hủy bỏ chỉnh sửa (Giữ nguyên phiếu đã nộp)"):
            st.session_state[edit_flag_key] = False
            st.rerun()

    n_peers = len(peers)
    expected_total = n_peers * 100.0

    guide_col_info = (
        f"**Cột Điểm quy đổi:** Hiển thị điểm số tương ứng trên thang 10 (theo Điểm nhóm **X = {group_score_x:.2f}**) làm mốc đối chiếu để bạn không chấm quá tay."
        if group_score_x > 0
        else "**Cột Tỷ lệ đối chiếu:** Hiển thị tỷ lệ nhận được của bạn so với mức chuẩn 100% (ví dụ: 110%, 100%, 95%). Sau khi Giảng viên chấm điểm nhóm X, điểm của từng bạn sẽ được tính tự động."
    )

    st.markdown(
        f"""
        > 💡 **Hướng dẫn:** 
        > - Mặc định tất cả thành viên là **100%** (đóng góp đều nhau).
        > - Độ chia nhỏ nhất là **1%**. Bạn có thể kéo trượt linh hoạt hoặc bấm vào thanh trượt để chỉnh.
        > - {guide_col_info}
        > - **Ràng buộc:** Tổng điểm chia cho các bạn phải khớp đúng **100% × {n_peers} = {expected_total:.0f}%**.
        """
    )

    # Session state for quick reset
    form_key = f"ratings_{member_data['id']}"
    if form_key not in st.session_state:
        prev_evals = storage.get_evaluations_by_evaluator(member_data["group_id"], member_data["id"])
        st.session_state[form_key] = {
            p["id"]: float(prev_evals.get(p["id"], 100.0)) for p in peers
        }

    if st.button("🔄 Đặt lại tất cả 100% (Cào bằng / Đều nhau)"):
        for p in peers:
            p_id = p["id"]
            st.session_state[form_key][p_id] = 100.0
            st.session_state[f"peer_slider_{p_id}"] = 100.0
        st.rerun()

    st.markdown("---")
    current_ratings = {}

    for peer in peers:
        p_id = peer["id"]
        current_val = float(st.session_state[form_key].get(p_id, 100.0))

        c_name, c_slider, c_score = st.columns([1.3, 2.2, 1.1])
        with c_name:
            st.markdown(f"**{peer['full_name']}**")
            st.caption(f"MSSV: `{peer['student_id']}`")
        with c_slider:
            new_val = st.slider(
                label=f"Điểm cho {peer['full_name']}",
                min_value=50.0,
                max_value=150.0,
                value=current_val,
                step=1.0,
                format="%.0f%%",
                key=f"peer_slider_{p_id}",
                label_visibility="collapsed",
            )
            st.session_state[form_key][p_id] = new_val
            current_ratings[p_id] = new_val
        with c_score:
            diff_from_base = new_val - 100.0
            delta_label = f"{diff_from_base:+.0f}%" if diff_from_base != 0 else "Chuẩn 100%"

            if group_score_x > 0:
                equiv_score = group_score_x * (new_val / 100.0)
                # Cảnh báo nếu điểm quy đổi vượt trần 10.0
                if equiv_score > 10.0:
                    st.metric(
                        label="Điểm tạm tính",
                        value=f"{equiv_score:.2f} đ",
                        delta="⚠️ Kịch trần 10.0",
                        delta_color="inverse",
                    )
                else:
                    st.metric(
                        label="Điểm tạm tính",
                        value=f"{equiv_score:.2f} đ",
                        delta=delta_label,
                        delta_color="normal" if diff_from_base >= 0 else "inverse",
                    )
            else:
                st.metric(
                    label="Tỷ lệ nhận được",
                    value=f"{new_val:.0f}%",
                    delta=delta_label,
                    delta_color="normal" if diff_from_base >= 0 else "inverse",
                )

    # Total check
    actual_total = sum(current_ratings.values())
    diff = actual_total - expected_total

    st.markdown("---")
    status_col, submit_col = st.columns([2, 1])

    with status_col:
        if abs(diff) < 0.001:
            st.success(f"✅ **Tổng điểm đã chia:** `{actual_total:.0f}%` / `{expected_total:.0f}%` (Hợp lệ)")
        elif diff > 0:
            st.error(f"⚠️ **Tổng điểm đã chia:** `{actual_total:.0f}%` / `{expected_total:.0f}%` (Thừa `{diff:.0f}%` - Cần giảm bớt)")
        else:
            st.warning(f"⚠️ **Tổng điểm đã chia:** `{actual_total:.0f}%` / `{expected_total:.0f}%` (Thiếu `{abs(diff):.0f}%` - Cần tăng thêm)")

    with submit_col:
        is_valid = abs(diff) < 0.001
        btn_label = "🚀 Cập Nhật & Nộp Lại Phiếu" if is_editing else "🚀 Xác Nhận & Nộp Phiếu"
        if st.button(btn_label, type="primary", disabled=not is_valid, use_container_width=True):
            success = storage.submit_evaluation(
                group_id=member_data["group_id"],
                evaluator_id=member_data["id"],
                ratings=current_ratings,
            )
            if success:
                st.session_state[edit_flag_key] = False
                st.balloons()
                st.success("Nộp phiếu thành công!")
                st.rerun()
            else:
                st.error("Không thể nộp phiếu. Có thể đợt đánh giá đã đóng.")


def render_admin_view():
    """Instructor / Administrator management interface."""
    st.title("⚙️ Quản Trị Hệ Thống Đánh Giá Chéo")
    st.caption("Quản lý danh sách nhóm, tạo Magic Link cho sinh viên và chốt điểm tự động.")

    tab1, tab2, tab3 = st.tabs([
        "📋 Danh Sách Nhóm & Đợt Chấm",
        "🔗 Cấp Phát Magic Link",
        "📊 Chốt Sổ & Tính Điểm",
    ])

    # ---------------- TAB 1: Danh sách nhóm ----------------
    with tab1:
        st.subheader("Tạo Nhóm Mới")
        has_score = st.checkbox(
            "Đã có điểm nhóm chính thức (X)",
            value=False,
            help="Bỏ chọn nếu nhóm muốn tự đánh giá chéo lấy danh sách % đóng góp trước (A 110%, B 100%, C 95%...), nhập điểm sau.",
            key="create_group_has_score",
        )
        with st.form("create_group_form"):
            col1, col2 = st.columns(2)
            with col1:
                g_name = st.text_input("Tên nhóm / Đề tài", placeholder="VD: Nhóm 01 - Hệ Thống AI")
            with col2:
                g_code = st.text_input("Mã nhóm (duy nhất)", placeholder="VD: NHOM-01")

            if has_score:
                g_score = st.number_input("Điểm nhóm (X)", min_value=0.1, max_value=10.0, value=8.5, step=0.1)
            else:
                g_score = 0.0
                st.caption("ℹ️ **Chế độ đánh giá tỷ lệ %:** Thành viên tự đánh giá chéo nhau trước để chốt tỷ lệ hưởng (ví dụ: A 110%, B 100%, C 95%...). Sau khi có điểm nhóm X, Giảng viên chỉ cần nhập điểm để tự động quy đổi ra điểm số cho từng người.")

            col4, col5 = st.columns(2)
            with col4:
                g_penalty = st.slider("Tỷ lệ phạt người không nộp (%)", min_value=0, max_value=50, value=10, step=5) / 100.0
            with col5:
                g_deadline = st.date_input("Hạn chót đánh giá")

            submitted = st.form_submit_button("➕ Thêm Nhóm Mới", type="primary")
            if submitted:
                if not g_name or not g_code:
                    st.error("Vui lòng nhập đầy đủ Tên nhóm và Mã nhóm.")
                else:
                    try:
                        new_id = storage.create_group(
                            name=g_name.strip(),
                            code=g_code.strip(),
                            group_score_x=g_score,
                            penalty_ratio=g_penalty,
                            deadline=str(g_deadline),
                        )
                        st.success(f"Đã tạo nhóm thành công! ID: {new_id}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

        # Seed sample data button
        if st.button("🧪 Tạo Nhóm Mẫu Dữ Liệu Thử Nghiệm (Demo Group)"):
            demo_id = storage.seed_sample_data()
            st.success(f"Đã tạo/kiểm tra nhóm mẫu demo (ID: {demo_id})!")
            st.rerun()

        st.divider()
        st.subheader("Danh Sách Các Nhóm Hiện Có")
        groups = storage.list_groups()
        if not groups:
            st.info("Chưa có nhóm nào trong hệ thống. Hãy tạo nhóm mới ở trên.")
        else:
            for g in groups:
                score_disp = f"Điểm nhóm: {g['group_score_x']:.2f}" if g['group_score_x'] > 0 else "Chưa có điểm (Đánh giá %)"
                with st.expander(f"📁 {g['name']} ({g['code']}) - {score_disp}"):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.markdown(f"**Số thành viên:** {g['total_members']}")
                    c2.markdown(f"**Đã nộp:** {g['submitted_count']}/{g['total_members']}")
                    c3.markdown(f"**Mức phạt:** {g['penalty_ratio']*100:.0f}%")
                    c4.markdown(f"**Trạng thái:** {'🔒 Đã chốt điểm' if g['is_closed'] == 1 else '🟢 Đang mở'}")

                    # Group Actions: Sửa thông tin, Copy nhóm, Xóa nhóm
                    st.write("")
                    c_act1, c_act2, c_act3 = st.columns(3)
                    with c_act1:
                        with st.popover("✏️ Sửa Thông Tin Nhóm", use_container_width=True):
                            st.markdown(f"**Chỉnh sửa nhóm: `{g['code']}`**")
                            edit_g_name = st.text_input("Tên nhóm / Đề tài", value=g["name"], key=f"edit_gname_{g['id']}")
                            edit_g_code = st.text_input("Mã nhóm (duy nhất)", value=g["code"], key=f"edit_gcode_{g['id']}")
                            edit_g_score = st.number_input("Điểm nhóm (X)", min_value=0.0, max_value=10.0, value=float(g["group_score_x"]), step=0.1, key=f"edit_gscore_{g['id']}")
                            edit_g_penalty = st.slider("Tỷ lệ phạt (%)", min_value=0, max_value=50, value=int(g["penalty_ratio"] * 100), step=5, key=f"edit_gpen_{g['id']}") / 100.0
                            edit_g_dl = st.text_input("Hạn chót đánh giá", value=g["deadline"] or "", key=f"edit_gdl_{g['id']}")
                            if st.button("💾 Lưu Thay Đổi", type="primary", key=f"save_g_{g['id']}", use_container_width=True):
                                if not edit_g_name.strip() or not edit_g_code.strip():
                                    st.error("Tên nhóm và Mã nhóm không được để trống.")
                                else:
                                    try:
                                        storage.update_group(
                                            group_id=g['id'],
                                            name=edit_g_name.strip(),
                                            code=edit_g_code.strip(),
                                            group_score_x=edit_g_score,
                                            penalty_ratio=edit_g_penalty,
                                            deadline=edit_g_dl.strip() or None,
                                        )
                                        st.success("Đã cập nhật thông tin nhóm!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Lỗi: {e}")

                    with c_act2:
                        with st.popover("📋 Sao Chép Nhóm (Copy)", use_container_width=True):
                            st.markdown(f"**Sao chép toàn bộ dữ liệu nhóm: `{g['code']}`**")
                            st.caption("Tạo bản sao mới bao gồm toàn bộ thành viên (với Magic Link mới độc lập) và toàn bộ ma trận đánh giá chéo đã chấm.")
                            clone_name = st.text_input("Tên nhóm mới", value=f"{g['name']} (Bản sao)", key=f"clone_name_{g['id']}")
                            clone_code = st.text_input("Mã nhóm mới", value=f"{g['code']}-COPY", key=f"clone_code_{g['id']}")
                            if st.button("🚀 Xác Nhận Tạo Bản Sao", type="primary", key=f"btn_clone_{g['id']}", use_container_width=True):
                                try:
                                    new_gid = storage.clone_group(g['id'], new_code=clone_code.strip(), new_name=clone_name.strip())
                                    st.success(f"Đã sao chép thành công nhóm mới (ID: {new_gid})!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Lỗi khi sao chép: {e}")

                    with c_act3:
                        with st.popover("🗑️ Xóa Nhóm", use_container_width=True):
                            st.warning(f"Bạn có chắc muốn xóa nhóm **{g['name']}**?")
                            st.caption("Lưu ý: Mọi thành viên và dữ liệu đánh giá của nhóm này sẽ bị xóa vĩnh viễn.")
                            if st.button("Xác nhận xóa vĩnh viễn", type="primary", key=f"confirm_del_grp_{g['id']}", use_container_width=True):
                                storage.delete_group(g['id'])
                                st.success(f"Đã xóa nhóm {g['name']} thành công!")
                                st.rerun()

                    # Current members list with edit, unlock re-evaluation, and delete actions
                    members = storage.get_group_members(g['id'])
                    if members:
                        st.markdown("#### Danh sách thành viên hiện tại:")
                        for idx, m in enumerate(members):
                            col_m_info, col_m_edit, col_m_unlock, col_m_del = st.columns([2.8, 0.9, 1.3, 0.8])
                            with col_m_info:
                                sub_badge = "✅ Đã nộp" if m["is_submitted"] == 1 else "⏳ Chưa nộp"
                                st.write(f"**{idx+1}. {m['full_name']}** (`{m['student_id']}`) — *{sub_badge}*")
                            with col_m_edit:
                                with st.popover("✏️ Sửa", key=f"pop_edit_m_{m['id']}"):
                                    st.markdown(f"**Sửa thông tin SV `{m['student_id']}`**")
                                    new_mssv = st.text_input("MSSV", value=m["student_id"], key=f"m_mssv_{m['id']}")
                                    new_name = st.text_input("Họ và Tên", value=m["full_name"], key=f"m_name_{m['id']}")
                                    new_email = st.text_input("Email", value=m["email"] or "", key=f"m_email_{m['id']}")
                                    if st.button("Lưu", key=f"save_m_{m['id']}", type="primary", use_container_width=True):
                                        if new_mssv.strip() and new_name.strip():
                                            storage.update_member(m['id'], new_mssv.strip(), new_name.strip(), new_email.strip() or None)
                                            st.success("Đã cập nhật!")
                                            st.rerun()
                                        else:
                                            st.error("MSSV và Họ Tên không được để trống.")
                            with col_m_unlock:
                                if m["is_submitted"] == 1:
                                    if st.button("🔄 Cho nộp lại", key=f"unlock_m_{m['id']}", help="Mở khóa để sinh viên này có thể vào chấm và gửi lại phiếu"):
                                        storage.unlock_member_submission(m['id'])
                                        st.success(f"Đã mở khóa cho {m['full_name']}!")
                                        st.rerun()
                            with col_m_del:
                                if st.button("🗑️ Xóa", key=f"del_mem_{m['id']}", help=f"Xóa thành viên {m['full_name']}"):
                                    storage.delete_member(m['id'])
                                    st.success(f"Đã xóa {m['full_name']}!")
                                    st.rerun()
                    else:
                        st.info("Nhóm này chưa có thành viên nào.")

                    # Member addition
                    st.markdown("#### Thêm thành viên vào nhóm:")
                    with st.form(f"add_member_{g['id']}"):
                        m_c1, m_c2, m_c3, m_c4 = st.columns([1, 1.5, 1.5, 1])
                        with m_c1:
                            m_mssv = st.text_input("MSSV", key=f"mssv_{g['id']}")
                        with m_c2:
                            m_name = st.text_input("Họ và Tên", key=f"name_{g['id']}")
                        with m_c3:
                            m_email = st.text_input("Email", key=f"email_{g['id']}")
                        with m_c4:
                            st.write("")
                            st.write("")
                            add_btn = st.form_submit_button("Thêm SV")

                        if add_btn:
                            if m_mssv and m_name:
                                storage.add_member(g["id"], m_mssv.strip(), m_name.strip(), m_email.strip() if m_email else None)
                                st.success(f"Đã thêm {m_name} vào nhóm!")
                                st.rerun()
                            else:
                                st.error("Vui lòng điền MSSV và Họ Tên.")

    # ---------------- TAB 2: Cấp phát Magic Link ----------------
    with tab2:
        st.subheader("🔗 Danh Sách Magic Link Của Thành Viên")
        st.markdown("Mỗi sinh viên sử dụng đường link độc bản này để truy cập thẳng vào trang đánh giá mà không cần mật khẩu.")

        groups = storage.list_groups()
        if not groups:
            st.info("Chưa có nhóm nào.")
        else:
            group_options = {f"{g['name']} ({g['code']})": g["id"] for g in groups}
            selected_group_name = st.selectbox("Chọn nhóm để xem link:", list(group_options.keys()))
            selected_g_id = group_options[selected_group_name]

            # Base URL input for link formatting (auto-detected)
            default_base = get_current_base_url()
            base_url = st.text_input(
                "Đường dẫn máy chủ (Base URL):",
                value=default_base,
                help="Hệ thống tự động nhận diện tên miền máy chủ hiện tại (Cloud hoặc Local).",
            )

            members = storage.get_group_members(selected_g_id)
            if not members:
                st.warning("Nhóm này chưa có thành viên nào.")
            else:
                link_data = []
                for m in members:
                    magic_link = f"{base_url.rstrip('/')}/?token={m['token']}"
                    link_data.append({
                        "MSSV": m["student_id"],
                        "Họ và Tên": m["full_name"],
                        "Email": m["email"] or "",
                        "Trạng thái": "✅ Đã nộp" if m["is_submitted"] == 1 else "⏳ Chưa nộp",
                        "Thời gian nộp": m["submitted_at"] or "",
                        "Magic Link": magic_link,
                    })

                df_links = pd.DataFrame(link_data)
                st.dataframe(df_links, use_container_width=True)

                # Export CSV button
                csv_buffer = io.StringIO()
                df_links.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
                st.download_button(
                    label="📥 Tải Danh Sách Link Gửi Sinh Viên (CSV)",
                    data=csv_buffer.getvalue(),
                    file_name=f"magic_links_{selected_group_name}.csv",
                    mime="text/csv",
                )

    # ---------------- TAB 3: Chốt điểm & Tính toán ----------------
    with tab3:
        st.subheader("📊 Chốt Sổ & Tính Điểm Tự Động")
        st.caption("Thuật toán tự động điền khuyết 100% cho người quên nộp, trừ phạt (nếu có), cắt trần 10.0 và bảo toàn quỹ điểm.")

        groups = storage.list_groups()
        if not groups:
            st.info("Chưa có nhóm nào.")
        else:
            group_options = {f"{g['name']} ({g['code']})": g["id"] for g in groups}
            selected_calc_group = st.selectbox("Chọn nhóm cần chốt điểm:", list(group_options.keys()), key="calc_group_select")
            calc_g_id = group_options[selected_calc_group]
            group_info = storage.get_group(calc_g_id)

            score_x = float(group_info['group_score_x'])
            is_closed = group_info['is_closed'] == 1

            col1, col2, col3 = st.columns(3)
            with col1:
                if score_x > 0:
                    st.metric("Điểm nhóm (X)", f"{score_x:.2f}")
                else:
                    st.metric("Điểm nhóm (X)", "Chưa nhập (Đánh giá %)")
            with col2:
                st.metric("Mức phạt vắng mặt", f"{group_info['penalty_ratio']*100:.0f}%")
            with col3:
                st.metric("Trạng thái", "🔒 Đã chốt" if is_closed else "🟢 Đang mở")

            st.markdown("---")

            # Nút chốt điểm hoặc mở lại đợt đánh giá
            c_action1, c_action2 = st.columns([2, 1])
            with c_action1:
                if not is_closed:
                    action_text = "🔒 Chốt Tỷ Lệ Đóng Góp (%) Của Nhóm" if score_x == 0 else "🚀 Tiến Hành Chốt Điểm Nhóm Này"
                    if st.button(action_text, type="primary"):
                        try:
                            result = storage.close_and_calculate_group(calc_g_id)
                            st.success("✅ Đã chốt thành công!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi tính toán: {e}")
                else:
                    st.info("Nhóm đã được chốt sổ và khóa phiếu.")

            with c_action2:
                if is_closed:
                    if st.button("🔓 Mở Lại Đợt Đánh Giá", type="secondary", use_container_width=True):
                        storage.reopen_group(calc_g_id)
                        st.success("Đã mở lại đợt đánh giá cho nhóm!")
                        st.rerun()

            # Ma trận đánh giá chéo chi tiết (Xem đánh giá)
            with st.expander("🔎 Xem Ma Trận Đánh Giá Chéo Chi Tiết", expanded=False):
                members = storage.get_group_members(calc_g_id)
                matrix = storage.get_evaluations_matrix(calc_g_id)
                if not members:
                    st.info("Nhóm này chưa có thành viên.")
                else:
                    st.markdown("#### Chi tiết điểm số từng thành viên đã chấm cho nhau:")
                    st.caption("Hàng ngang: Thành viên chấm | Cột dọc: Thành viên được chấm | Giá trị: Tỷ lệ % đã cho")

                    matrix_rows = []
                    for ev in members:
                        ev_id = ev["id"]
                        row_data = {
                            "MSSV": ev["student_id"],
                            "Người chấm": ev["full_name"],
                            "Trạng thái": "✅ Đã nộp" if ev["is_submitted"] == 1 else "⏳ Chưa nộp (Khuyết)",
                        }
                        ev_ratings = matrix.get(ev_id, {})
                        total_given = 0.0
                        for tg in members:
                            tg_id = tg["id"]
                            col_name = f"{tg['full_name']} ({tg['student_id']})"
                            if tg_id == ev_id:
                                row_data[col_name] = "— (Tự chấm)"
                            else:
                                if tg_id in ev_ratings:
                                    val = ev_ratings[tg_id]
                                    total_given += val
                                    row_data[col_name] = f"{val:.0f}%"
                                else:
                                    if ev["is_submitted"] == 0:
                                        row_data[col_name] = "100% (Khuyết)"
                                        total_given += 100.0
                                    else:
                                        row_data[col_name] = "0%"

                        row_data["Tổng % đã chia"] = f"{total_given:.0f}%"
                        matrix_rows.append(row_data)

                    df_matrix = pd.DataFrame(matrix_rows)
                    st.dataframe(df_matrix, use_container_width=True)

                    csv_matrix = io.StringIO()
                    df_matrix.to_csv(csv_matrix, index=False, encoding="utf-8-sig")
                    st.download_button(
                        label="📥 Xuất Ma Trận Đánh Giá Chéo (CSV)",
                        data=csv_matrix.getvalue(),
                        file_name=f"ma_tran_danh_gia_{group_info['code']}.csv",
                        mime="text/csv",
                        key=f"dl_matrix_{calc_g_id}",
                    )

            # Hiển thị kết quả sau khi đã chốt
            updated_group = storage.get_group(calc_g_id)
            if updated_group and updated_group["is_closed"] == 1:
                curr_score_x = float(updated_group["group_score_x"])
                members = storage.get_group_members(calc_g_id)

                if curr_score_x == 0:
                    st.markdown("### 📋 Bảng Tỷ Lệ Đóng Góp Đã Chốt (Chờ Điểm Nhóm X)")
                    st.caption("Các thành viên đã hoàn thành đánh giá chéo. Dưới đây là tỷ lệ % nhận được và mô phỏng điểm số theo các mức điểm nhóm dự kiến.")

                    res_data = []
                    for m in members:
                        pct = m['final_pct'] or 100.0
                        res_data.append({
                            "MSSV": m["student_id"],
                            "Họ và Tên": m["full_name"],
                            "Tỷ lệ % nhận được": f"{pct:.2f}%",
                            "Tương ứng nếu X = 8.0": f"{min(10.0, 8.0 * (pct / 100.0)):.2f}",
                            "Tương ứng nếu X = 8.5": f"{min(10.0, 8.5 * (pct / 100.0)):.2f}",
                            "Tương ứng nếu X = 9.0": f"{min(10.0, 9.0 * (pct / 100.0)):.2f}",
                            "Trạng thái nộp": "Đúng hạn" if m["is_submitted"] == 1 else "Vắng mặt (Bị phạt)",
                        })

                    df_res = pd.DataFrame(res_data)
                    st.dataframe(df_res, use_container_width=True)

                    # Form nhập điểm nhóm X để quy đổi
                    st.markdown("---")
                    st.markdown("#### 🎯 Nhập Điểm Nhóm (X) Để Quy Đổi Ra Điểm Số Chính Thức:")
                    c_in_x, c_btn_apply = st.columns([2, 1])
                    with c_in_x:
                        apply_x = st.number_input("Điểm nhóm X do Giảng viên chấm:", min_value=0.1, max_value=10.0, value=8.5, step=0.1, key=f"apply_x_{calc_g_id}")
                    with c_btn_apply:
                        st.write("")
                        st.write("")
                        if st.button("⚡ Áp Điểm & Quy Đổi Điểm Số", type="primary", use_container_width=True):
                            storage.update_group_score(calc_g_id, apply_x)
                            st.balloons()
                            st.success(f"Đã quy đổi điểm thành công theo điểm nhóm X = {apply_x:.2f}!")
                            st.rerun()

                    csv_res = io.StringIO()
                    df_res.to_csv(csv_res, index=False, encoding="utf-8-sig")
                    st.download_button(
                        label="📥 Xuất Bảng Tỷ Lệ Đóng Góp (CSV)",
                        data=csv_res.getvalue(),
                        file_name=f"ty_le_dong_gop_{updated_group['code']}.csv",
                        mime="text/csv",
                    )

                else:
                    st.markdown("### 🏆 Bảng Điểm Kết Quả Chính Thức")
                    res_data = []
                    for m in members:
                        pct = m['final_pct'] or 100.0
                        res_data.append({
                            "MSSV": m["student_id"],
                            "Họ và Tên": m["full_name"],
                            "Điểm chính thức": f"{m['final_score']:.2f}" if m['final_score'] is not None else "",
                            "Tỷ lệ nhận được (%)": f"{pct:.2f}%",
                            "Hệ số R": f"{m['final_r']:.4f}" if m['final_r'] is not None else "",
                            "Trạng thái nộp": "Đúng hạn" if m["is_submitted"] == 1 else "Vắng mặt (Bị phạt)",
                        })

                    df_res = pd.DataFrame(res_data)
                    st.dataframe(df_res, use_container_width=True)

                    # Tùy chọn cập nhật lại điểm nhóm X nếu cần
                    with st.expander("✏️ Cập nhật lại Điểm nhóm (X)"):
                        c_re_x, c_re_btn = st.columns([2, 1])
                        with c_re_x:
                            re_x = st.number_input("Nhập điểm nhóm mới:", min_value=0.1, max_value=10.0, value=curr_score_x, step=0.1, key=f"re_x_{calc_g_id}")
                        with c_re_btn:
                            st.write("")
                            st.write("")
                            if st.button("Cập nhật lại điểm"):
                                storage.update_group_score(calc_g_id, re_x)
                                st.success("Đã cập nhật lại điểm thành công!")
                                st.rerun()

                    csv_res = io.StringIO()
                    df_res.to_csv(csv_res, index=False, encoding="utf-8-sig")
                    st.download_button(
                        label="📥 Xuất Bảng Điểm Chính Thức (CSV)",
                        data=csv_res.getvalue(),
                        file_name=f"bang_diem_{updated_group['code']}.csv",
                        mime="text/csv",
                    )


# Router: Student View if ?token=... is present, else Admin View
if token:
    render_student_view(token)
else:
    render_admin_view()
