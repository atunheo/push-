import streamlit as st
import pandas as pd
import requests
import re

st.title("🚀 GitLab ")

# Nhập thông tin GitLab
gitlab_username = st.text_input("👤 GitLab Username", "")
gitlab_token = st.text_input("🔑 GitLab Token", type="password")

# Upload file Excel
uploaded_file = st.file_uploader("📂 Upload Excel file", type=["xlsx"])

def normalize_repo_name(value):
    """Chuẩn hóa path repo (GitLab path: thường là tên thư mục)"""
    try:
        numeric = float(value)
        if numeric.is_integer():
            return str(int(numeric))
    except Exception:
        pass
    text = str(value).strip()
    if text.endswith(".0"):
        return text[:-2]
    return text

def sanitize_name(name: str) -> str:
    """
    Làm sạch tên repo để hợp lệ với GitLab:
    - Chỉ giữ lại chữ, số, dấu cách, ., +, -, _
    - Thay ký tự lạ bằng '-'
    - Nếu bắt đầu không hợp lệ thì thêm 'repo-' vào đầu
    """
    name = str(name).strip()
    name = re.sub(r"[^A-Za-z0-9 .+\-_]", "-", name)
    if not name or not re.match(r"^[A-Za-z0-9]", name):
        name = "repo-" + name
    return name

# Nút bắt đầu
if st.button("▶️ Bắt đầu chạy"):
    if not gitlab_username or not gitlab_token:
        st.error("❌ Vui lòng nhập Username và Token GitLab trước khi chạy.")
    elif uploaded_file is None:
        st.error("❌ Vui lòng upload file Excel trước khi chạy.")
    else:
        df = pd.read_excel(uploaded_file)

        required_columns = ["Tên repo", "Tiêu đề", "Nội dung"]
        if not all(col in df.columns for col in required_columns):
            st.error(f"❌ File Excel phải có các cột: {required_columns}")
        else:
            st.write("📋 Preview dữ liệu:", df.head())

            success, errors = 0, 0
            for _, row in df.iterrows():
                repo = normalize_repo_name(row["Tên repo"])
                title = str(row["Tiêu đề"]).strip()

                clean_title = sanitize_name(title)

                payload = {"name": clean_title, "path": repo, "visibility": "public"}
                response = requests.post(
                    "https://gitlab.com/api/v4/projects",
                    headers={
                        "PRIVATE-TOKEN": gitlab_token,
                        "Content-Type": "application/json"
                    },
                    json=payload
                )

                if response.status_code == 201:
                    st.success(f"✅ Đã tạo repo: {clean_title}")
                    success += 1
                else:
                    st.error(f"❌ Lỗi tạo repo {title}: {response.json()}")
                    errors += 1

            st.info(f"📊 Kết quả: {success} thành công, {errors} lỗi")
