# Hệ Thống Đánh Giá Chéo & Chấm Điểm Nhóm Trực Tuyến 🎓

Ứng dụng web đánh giá chéo thành viên trong nhóm đồ án/bài tập lớn, áp dụng giải thuật **Bù Khuyết Mặc Định 100% (Default Imputation)**, tính toán với độ chính xác cao bằng `decimal.Decimal`, triệt tiêu sai số làm tròn và triển khai online **hoàn toàn miễn phí, không cần mua tên miền**.

---

## 🚀 Các Tính Năng Nổi Bật

1. **Truy Cập Nhanh Qua Magic Link (Không Cần Mật Khẩu):**
   - Mỗi sinh viên được cấp một đường dẫn bí mật độc bản (ví dụ: `https://ten-app.streamlit.app/?token=abc123xyz`).
   - Mở trực tiếp trên điện thoại (Zalo, Messenger, Safari, Chrome), tự động nhận diện đúng nhóm và danh sách các bạn cùng nhóm.
   - Phiếu đánh giá **hoàn toàn ẩn danh** giữa các thành viên.

2. **Giải Thuật Toán Học Chặt Chẽ:**
   - **Bù khuyết 100% (Default Imputation):** Người quên nộp tự động được giả định chấm đồng đội 100%, bảo toàn tổng hệ số $\sum R_i = N$.
   - **Tùy chọn phạt (Penalty):** Hỗ trợ trừ điểm người quên nộp và tái phân phối lượng phạt cho thành viên nộp đầy đủ.
   - **Cắt trần 10.0 & Cắt sàn 0.0:** Tự động tái phân phối lượng điểm dôi dư theo tỷ lệ đóng góp.
   - **Triệt tiêu sai số 0.01 (Largest Remainder Method):** Đảm bảo tổng điểm sau làm tròn khớp chính xác 100% với quỹ điểm $N \times X$.

3. **Giao Diện Thân Thiện (Mobile-First):**
   - Mặc định khởi tạo $100\%$ cho tất cả thành viên (cho phép nộp ngay nếu nhóm đồng thuận cào bằng).
   - Thanh trạng thái kiểm tra tổng điểm trực quan (`800% / 800%`).
   - Tự động khóa phiếu sau khi bấm nộp để chống sửa đổi tùy tiện.

4. **Bảng Điều Khiển Cho Giảng Viên (Admin View):**
   - Tạo đợt chấm, thêm danh sách sinh viên.
   - Xuất danh sách Magic Link ra file CSV để gửi cho lớp.
   - Theo dõi tiến độ nộp phiếu thời gian thực.
   - Bấm 1 nút để chốt sổ, tự động tính điểm và xuất bảng điểm Excel/CSV.

---

## 🛠️ Hướng Dẫn Chạy Cục Bộ (Local)

### 1. Yêu cầu môi trường
- Python 3.10 trở lên.

### 2. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 3. Khởi chạy ứng dụng
```bash
streamlit run app.py
```
Trình duyệt sẽ tự động mở tại địa chỉ: `http://localhost:8501`.

### 4. Chạy kiểm thử tự động (Unit Tests)
```bash
pytest
```

---

## 🌐 Hướng Dẫn Triển Khai Lên Web (Không Cần Domain)

Bạn có thể đưa hệ thống lên mạng internet chỉ với 3 bước miễn phí:

### Bước 1: Đẩy mã nguồn lên GitHub
```bash
git add .
git commit -m "feat: complete peer evaluation system"
git push origin feat/peer-eval-online
```

### Bước 2: Đăng nhập Streamlit Community Cloud
1. Truy cập [share.streamlit.io](https://share.streamlit.io) và chọn **Continue with GitHub**.
2. Bấm nút **Create app** (hoặc **New app**).

### Bước 3: Điền thông tin và Deploy
- **Repository:** Chọn repository `DangQuangMinh-IS/chamdiem`
- **Branch:** `main` (hoặc nhánh bạn merge vào)
- **Main file path:** `app.py`
- **App URL:** Đặt tên đường dẫn tùy ý (ví dụ: `chamdiem-nhom.streamlit.app`).

Bấm **Deploy!** — Chỉ sau 1-2 phút, ứng dụng của bạn sẽ hoạt động online với kết nối bảo mật HTTPS có sẵn!
