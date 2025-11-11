import streamlit as st
import pandas as pd
import requests
import time
import re

st.title("🚀 GitLab 🐷")

# Nhập thông tin GitLab
gitlab_username = st.text_input("🐷 GitLab Username", "")
gitlab_token = st.text_input("🐽 GitLab Token", type="password")

# Upload Excel
uploaded_file = st.file_uploader("📂 Upload Excel file", type=["xlsx"])

# Nhập số giây delay
push_delay = st.number_input("⏳ Delay giữa các repo (giây)", min_value=0, max_value=60, value=3)

def normalize_repo_name(value):
    """Chuẩn hóa path repo (dùng làm project path ban đầu)"""
    try:
        numeric = float(value)
        if numeric.is_integer():
            return str(int(numeric))
    except Exception:
        pass
    return str(value).strip()

def clean_title(title: str) -> str:
    """Bỏ dấu # ở đầu tiêu đề nếu có"""
    title = str(title).strip()
    title = re.sub(r"^#+\s*", "", title)  # bỏ hết # ở đầu
    return title

def create_repo(repo):
    """Tạo repo trống"""
    payload = {"name": repo, "path": repo, "visibility": "public"}
    resp = requests.post(
        "https://gitlab.com/api/v4/projects",
        headers={"PRIVATE-TOKEN": gitlab_token, "Content-Type": "application/json"},
        json=payload
    )
    if resp.status_code == 201:
        return resp.json()["id"], None
    return None, resp.json()

def push_readme(project_id, title, content):
    """Push README.md vào repo qua API"""
    file_url = f"https://gitlab.com/api/v4/projects/{project_id}/repository/files/README.md"
    file_payload = {
        "branch": "main",
        "content": content,  # Không thêm tiêu đề nữa
        "commit_message": "Add README.md"
    }
    resp = requests.post(
        file_url,
        headers={"PRIVATE-TOKEN": gitlab_token, "Content-Type": "application/json"},
        json=file_payload
    )
    return resp.status_code, resp.json()

def rename_repo(project_id, new_name):
    """Đổi tên repo sau khi đã push"""
    url = f"https://gitlab.com/api/v4/projects/{project_id}"
    payload = {"name": new_name}
    resp = requests.put(
        url,
        headers={"PRIVATE-TOKEN": gitlab_token, "Content-Type": "application/json"},
        json=payload
    )
    return resp.status_code, resp.json()

# Nút chạy
if st.button("🐖 Bắt đầu chạy"):
    if not gitlab_username or not gitlab_token:
        st.error("❌ Vui lòng nhập Username + Token GitLab.")
    elif uploaded_file is None:
        st.error("❌ Vui lòng upload file Excel.")
    else:
        df = pd.read_excel(uploaded_file)
        required_columns = ["Tên repo", "Tiêu đề", "Nội dung", "Tên repo cuối cùng"]
        if not all(col in df.columns for col in required_columns):
            st.error(f"❌ Excel cần có cột: {required_columns}")
        else:
            st.write("📋 Preview:", df.head())
            success, errors = 0, 0

            for idx, row in df.iterrows():
                repo = normalize_repo_name(row["Tên repo"])
                title = str(row["Tiêu đề"]).strip()
                content = str(row["Nội dung"]).strip()
                final_name = str(row["Tên repo cuối cùng"]).strip()

                st.write(f"➡️ Đang xử lý repo: {repo} ...")

                # Step 1: Create repo
                project_id, err = create_repo(repo)
                if not project_id:
                    st.error(f"❌ Lỗi tạo repo {repo}: {err}")
                    errors += 1
                    continue
                st.success(f"✅ Đã tạo repo: {repo}")

                # Step 2: Push README.md
                status, resp = push_readme(project_id, title, content)
                if status in (200, 201):
                    st.success("📤 Đã push README.md")
                else:
                    st.error(f"❌ Lỗi push README.md: {resp}")
                    errors += 1
                    continue

                # Step 3: Rename repo
                status, resp = rename_repo(project_id, final_name)
                if status == 200:
                    st.success(f"🔄 Đã đổi tên repo thành: {final_name}")
                    success += 1
                else:
                    st.error(f"❌ Lỗi đổi tên repo {repo}: {resp}")
                    errors += 1

                # Delay giữa các repo
                if idx < len(df) - 1 and push_delay > 0:
                    st.info(f"⏳ Đợi {push_delay} giây trước repo tiếp theo...")
                    time.sleep(push_delay)

            st.info(f"📊 Kết quả: {success} thành công, {errors} lỗi")
