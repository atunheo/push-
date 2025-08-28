import streamlit as st
import pandas as pd
import requests
import urllib.parse

st.title("🚀 GitLab ")

gitlab_username = st.text_input("👤 GitLab Username", "")
gitlab_token = st.text_input("🔑 GitLab Token", type="password")
uploaded_file = st.file_uploader("📂 Upload Excel file", type=["xlsx"])

def normalize_repo_name(value):
    """Chuẩn hóa path repo từ Excel"""
    try:
        numeric = float(value)
        if numeric.is_integer():
            return str(int(numeric))
    except Exception:
        pass
    return str(value).strip()

def create_repo(repo, title, content):
    """Tạo repo + thêm README.md"""
    payload = {"name": title, "path": repo, "visibility": "public"}
    response = requests.post(
        "https://gitlab.com/api/v4/projects",
        headers={"PRIVATE-TOKEN": gitlab_token, "Content-Type": "application/json"},
        json=payload
    )
    if response.status_code != 201:
        return None, response.json()

    project = response.json()
    project_id = project["id"]

    # Commit README.md
    file_payload = {
        "branch": "main",
        "content": f"# {title}\n\n{content}",
        "commit_message": "Add README.md"
    }
    file_url = f"https://gitlab.com/api/v4/projects/{project_id}/repository/files/README.md"
    file_resp = requests.post(
        file_url,
        headers={"PRIVATE-TOKEN": gitlab_token, "Content-Type": "application/json"},
        json=file_payload
    )

    return project_id, file_resp.json() if file_resp.status_code not in (200,201) else None

def rename_repo(project_id, new_name):
    """Đổi tên repo sang tên cuối cùng"""
    url = f"https://gitlab.com/api/v4/projects/{project_id}"
    payload = {"name": new_name}
    resp = requests.put(
        url,
        headers={"PRIVATE-TOKEN": gitlab_token, "Content-Type": "application/json"},
        json=payload
    )
    return resp.status_code, resp.json()

# Nút bắt đầu
if st.button("▶️ Bắt đầu chạy"):
    if not gitlab_username or not gitlab_token:
        st.error("❌ Vui lòng nhập Username và Token GitLab.")
    elif uploaded_file is None:
        st.error("❌ Vui lòng upload file Excel.")
    else:
        df = pd.read_excel(uploaded_file)
        required_columns = ["Tên repo", "Tiêu đề", "Nội dung", "Tên repo cuối cùng"]
        if not all(col in df.columns for col in required_columns):
            st.error(f"❌ Excel cần có các cột: {required_columns}")
        else:
            st.write("📋 Preview:", df.head())
            success, errors = 0, 0

            for _, row in df.iterrows():
                repo = normalize_repo_name(row["Tên repo"])
                title = str(row["Tiêu đề"]).strip()
                content = str(row["Nội dung"]).strip()
                final_name = str(row["Tên repo cuối cùng"]).strip()

                st.write(f"➡️ Đang xử lý repo: {repo} ...")

                # Step 1: Create repo + add README.md
                project_id, err = create_repo(repo, title, content)
                if not project_id:
                    st.error(f"❌ Lỗi tạo repo {title}: {err}")
                    errors += 1
                    continue
                st.success(f"✅ Đã tạo repo: {title}")

                # Step 2: Rename repo
                status, resp = rename_repo(project_id, final_name)
                if status == 200:
                    st.success(f"🔄 Đã đổi tên repo thành: {final_name}")
                    success += 1
                else:
                    st.error(f"❌ Lỗi đổi tên repo {title}: {resp}")
                    errors += 1

            st.info(f"📊 Kết quả: {success} thành công, {errors} lỗi")
