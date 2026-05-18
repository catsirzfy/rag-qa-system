"""Streamlit 前端 — 登录 → 用户问答 / 管理后台。"""
import json, requests, streamlit as st

API = "http://localhost:8000/api/v1"
st.set_page_config(page_title="RAG 知识库", page_icon="📚", layout="wide")

# ================================================================
# 状态初始化
# ================================================================
if "token" not in st.session_state: st.session_state.token = None
if "user" not in st.session_state: st.session_state.user = None
if "messages" not in st.session_state: st.session_state.messages = []

def headers():
    return {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}

# ================================================================
# 登录页
# ================================================================
def login_page():
    st.title("📚 RAG 知识库问答系统")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("登录")
        username = st.text_input("用户名", key="login_user")
        password = st.text_input("密码", type="password", key="login_pass")
        if st.button("登录", use_container_width=True):
            r = requests.post(f"{API}/auth/login", json={"username": username, "password": password})
            if r.status_code == 200:
                d = r.json()["data"]
                st.session_state.token = d["access_token"]
                st.session_state.user = d["user"]
                st.rerun()
            else:
                st.error(r.json().get("detail", "登录失败"))
    with col2:
        st.subheader("注册")
        reg_user = st.text_input("用户名", key="reg_user")
        reg_email = st.text_input("邮箱", key="reg_email")
        reg_pass = st.text_input("密码", type="password", key="reg_pass")
        if st.button("注册", use_container_width=True):
            r = requests.post(f"{API}/auth/register", json={"username": reg_user, "email": reg_email, "password": reg_pass})
            if r.status_code == 200:
                st.success("注册成功，请登录")
            else:
                st.error(r.json().get("detail", "注册失败"))

# ================================================================
# 用户端
# ================================================================
def user_page():
    with st.sidebar:
        st.write(f"👤 {st.session_state.user['username']} ({st.session_state.user['role']})")
        st.divider()

        # 文档管理
        st.subheader("📄 上传文档")
        uploaded = st.file_uploader("选择文件", type=["md","txt","pdf"], accept_multiple_files=True, label_visibility="collapsed")
        if uploaded:
            files = [("files", (f.name, f.getvalue())) for f in uploaded]
            r = requests.post(f"{API}/chat/upload", files=files, headers=headers())
            if r.status_code == 200: st.success(r.json()["message"]); st.rerun()
            else: st.error(r.json().get("detail","失败"))

        st.subheader("📋 知识库")
        try:
            r = requests.get(f"{API}/chat/documents")
            d = r.json()["data"]
            st.metric("文本块", d["chunks"])
            for f in d["files"]: st.write(f"📄 {f}")
        except: st.info("暂无文档")

        if st.button("🚪 退出登录", use_container_width=True):
            st.session_state.token = None; st.session_state.user = None; st.rerun()

    # 主区域
    st.header(f"💬 知识库问答")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if q := st.chat_input("输入问题..."):
        st.session_state.messages.append({"role": "user", "content": q})
        with st.chat_message("user"): st.write(q)
        with st.chat_message("assistant"):
            placeholder = st.empty(); full = ""
            try:
                r = requests.post(f"{API}/chat/ask/stream", json={"question": q}, stream=True, headers=headers())
                for line in r.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data: "): continue
                    try: data = json.loads(line[6:])
                    except: continue
                    if data.get("done"): break
                    if "text" in data: full += data["text"]; placeholder.markdown(full + "▌")
                placeholder.markdown(full)
                st.session_state.messages.append({"role": "assistant", "content": full})
            except Exception as e: placeholder.error(str(e))

# ================================================================
# 管理端
# ================================================================
def admin_page():
    tabs = st.tabs(["📊 概览", "👥 用户管理", "💬 问答"])
    with tabs[0]:
        st.header("知识库概览")
        try:
            r = requests.get(f"{API}/admin/stats", headers=headers())
            d = r.json()["data"]
            st.metric("文本块总数", d["chunks"])
            st.subheader("已索引文档")
            for f in d["files"]: st.write(f"📄 {f}")
        except Exception as e: st.error(str(e))

    with tabs[1]:
        st.header("用户管理")
        try:
            r = requests.get(f"{API}/admin/users", headers=headers())
            users = r.json()["data"]
            for u in users:
                badge = "🛡" if u["role"] == "admin" else "👤"
                st.write(f"{badge} **{u['username']}** — {u['email']} — `{u['role']}` {'✅' if u['is_active'] else '❌'}")
            st.metric("用户总数", len(users))
        except Exception as e: st.error(str(e))

    with tabs[2]:
        user_page()  # 管理员也能问答

    with st.sidebar:
        st.write(f"🛡 {st.session_state.user['username']} (管理员)")
        if st.button("🚪 退出", use_container_width=True):
            st.session_state.token = None; st.session_state.user = None; st.rerun()

# ================================================================
# 入口
# ================================================================
if st.session_state.token and st.session_state.user:
    if st.session_state.user["role"] == "admin":
        admin_page()
    else:
        user_page()
else:
    login_page()
