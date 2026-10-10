
import streamlit as st
import sqlite3
from openai import OpenAI

st.set_page_config(
    page_title="Nexus AI",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 Nexus AI")
st.caption("Seu assistente pessoal inteligente")

# Configuração da API
api_key = st.secrets.get("OPENAI_API_KEY", "")

if not api_key:
    st.warning(
        "Configure sua chave OPENAI_API_KEY "
        "nas configurações Secrets do Streamlit Cloud."
    )
    st.stop()

client = OpenAI(api_key=api_key)

# Banco de dados
conn = sqlite3.connect("nexus.db", check_same_thread=False)
conn.execute("""
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL
)
""")
conn.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    done INTEGER DEFAULT 0
)
""")
conn.commit()

def get_memories():
    return conn.execute(
        "SELECT id, content FROM memories ORDER BY id DESC"
    ).fetchall()

def get_tasks():
    return conn.execute(
        "SELECT id, content, done FROM tasks ORDER BY id DESC"
    ).fetchall()

# Menu
page = st.sidebar.radio(
    "Menu",
    ["Conversar", "Memória", "Tarefas"]
)

if page == "Conversar":
    st.subheader("Converse com o Nexus")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Como posso ajudar?")

    if prompt:
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        memories = get_memories()
        memory_text = "\n".join(
            item[1] for item in memories
        ) or "Nenhuma memória salva."

        try:
            with st.chat_message("assistant"):
                with st.spinner("Pensando..."):
                    response = client.chat.completions.create(
                        model="gpt-4.1-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "Você é o Nexus AI, um assistente "
                                    "pessoal útil, honesto e organizado. "
                                    "Responda em português brasileiro. "
                                    "Memórias do usuário:\n" + memory_text
                                )
                            },
                            *st.session_state.messages
                        ]
                    )

                    answer = response.choices[0].message.content
                    st.markdown(answer)

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

        except Exception as e:
            st.error(f"Erro na API: {e}")

elif page == "Memória":
    st.subheader("🧠 Memória do Nexus")

    new_memory = st.text_input(
        "O que você quer que o Nexus lembre?"
    )

    if st.button("Salvar memória"):
        if new_memory.strip():
            conn.execute(
                "INSERT INTO memories (content) VALUES (?)",
                (new_memory.strip(),)
            )
            conn.commit()
            st.success("Memória salva!")

    for memory_id, content in get_memories():
        col1, col2 = st.columns([4, 1])
        col1.write(content)

        if col2.button("Apagar", key=f"memory_{memory_id}"):
            conn.execute(
                "DELETE FROM memories WHERE id = ?",
                (memory_id,)
            )
            conn.commit()
            st.rerun()

elif page == "Tarefas":
    st.subheader("📋 Minhas tarefas")

    new_task = st.text_input("Nova tarefa")

    if st.button("Adicionar tarefa"):
        if new_task.strip():
            conn.execute(
                "INSERT INTO tasks (content) VALUES (?)",
                (new_task.strip(),)
            )
            conn.commit()
            st.rerun()

    for task_id, content, done in get_tasks():
        col1, col2 = st.columns([4, 1])

        col1.write(("✅ " if done else "⬜ ") + content)

        if not done:
            if col2.button("Concluir", key=f"task_{task_id}"):
                conn.execute(
                    "UPDATE tasks SET done = 1 WHERE id = ?",
                    (task_id,)
                )
                conn.commit()
                st.rerun()
