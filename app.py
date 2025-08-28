import streamlit as st
import pandas as pd
import requests
import urllib.parse

st.title("🚀 GitLab")

# Lấy token từ secrets (bảo mật hơn hardcode)
gitlab_token = st.secrets["GITLAB_TOKEN"]

# Nhập username GitLab
gitlab_username = st.text_input("🔑 GitLab Username", "")

# Upload file Excel
uploaded_file = st.file_uploader("📂 Upload Excel file", type=["xlsx"])

def normalize_repo_name(value):
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

if uploaded_file is not None and gitlab_username:
    df = pd.read_excel(uploaded_file)

    required_columns = ["Tên repo", "Tiêu đề", "Nội dung"]
    if not all(col in df.columns for col in required_columns):
        st.error(f"❌ File Excel phải có các cột: {required_columns}")
    else:
        st.write("📋 Preview dữ liệu:", df.head())

        if st.button("🚀 Tạo Repo trên GitLab"):
            success, errors = 0, 0
            for _, row in df.iterrows():
                repo = normalize_repo_name(row["Tên repo"])
                title = str(row["Tiêu đề"]).strip()

                payload = {"name": title, "path": repo, "visibility": "public"}
                response = requests.post(
                    "https://gitlab.com/api/v4/projects",
                    headers={
                        "PRIVATE-TOKEN": gitlab_token,
                        "Content-Type": "application/json"
                    },
                    json=payload
                )

                if response.status_code == 201:
                    st.success(f"✅ Đã tạo repo: {title}")
                    success += 1
                else:
                    st.error(f"❌ Lỗi tạo repo {title}: {response.json()}")
                    errors += 1

            st.info(f"📊 Kết quả: {success} thành công, {errors} lỗi")
