import streamlit as st
import pandas as pd
from datetime import datetime, date, time
import numpy as np
from sqlalchemy import create_engine, text

# --- FUNÇÃO DE CONVERSÃO DE TIPOS ---
def converter_numpy_para_python(valor):
    if isinstance(valor, (np.integer, np.int64)):
        return int(valor)
    elif isinstance(valor, (np.floating, np.float64)):
        return float(valor)
    elif isinstance(valor, np.bool_):
        return bool(valor)
    else:
        return valor

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Atendimento Viana - Psicologia", 
    page_icon="🧠",
    layout="wide"
)

# --- CONEXÃO SEGURA (BUSCA APENAS NOS SECRETS) ---
def conectar_banco():
    """Busca a URL de conexão apenas nos Secrets do Streamlit Cloud"""
    if "DB_URL" in st.secrets:
        db_url = st.secrets["DB_URL"]
        return create_engine(db_url)
    else:
        # Exibe aviso caso você esqueça de configurar o Secret
        st.error("⚠️ Configuração ausente: 'DB_URL' não encontrada nos Secrets.")
        st.info("Acesse Settings > Secrets no Streamlit Cloud para configurar a conexão.")
        st.stop()

# --- INICIALIZAÇÃO DO BANCO ---
def inicializar_banco():
    engine = conectar_banco()
    with engine.connect() as conn:
        # Tabela pacientes
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pacientes (
                id SERIAL PRIMARY KEY,
                nome_completo VARCHAR(100) NOT NULL,
                telefone VARCHAR(20) NOT NULL,
                email VARCHAR(100),
                data_nascimento DATE,
                profissao VARCHAR(50),
                queixa_principal TEXT NOT NULL,
                ativo BOOLEAN DEFAULT TRUE,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        # Tabela consultas
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS consultas (
                id SERIAL PRIMARY KEY,
                paciente_id INTEGER REFERENCES pacientes(id),
                data_consulta TIMESTAMP NOT NULL,
                valor_consulta DECIMAL(10,2) DEFAULT 0,
                status VARCHAR(20) DEFAULT 'agendada',
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()

# Execução inicial
try:
    inicializar_banco()
except Exception as e:
    st.error(f"Erro ao conectar com o banco de dados: {e}")

# --- INTERFACE ---
st.markdown("<h1 style='text-align: center; color: #1f77b4;'>🧠 ATENDIMENTO VIANA</h1>", unsafe_allow_html=True)
st.markdown("---")

menu = st.sidebar.selectbox("Navegação", ["➕ Cadastrar Paciente", "👥 Ver Pacientes", "📊 Estatísticas"])

if menu == "➕ Cadastrar Paciente":
    st.header("👤 Novo Cadastro")
    with st.form("form_paciente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo*")
            tel = st.text_input("Telefone*")
        with col2:
            queixa = st.text_area("Queixa Principal*")
        
        if st.form_submit_button("💾 Salvar"):
            if nome and tel and queixa:
                try:
                    engine = conectar_banco()
                    with engine.connect() as conn:
                        conn.execute(text("INSERT INTO pacientes (nome_completo, telefone, queixa_principal) VALUES (:n, :t, :q)"),
                                     {"n":nome, "t":tel, "q":queixa})
                        conn.commit()
                    st.success("✅ Paciente cadastrado!")
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                st.error("Preencha os campos obrigatórios.")

elif menu == "👥 Ver Pacientes":
    st.header("👥 Lista de Pacientes")
    try:
        engine = conectar_banco()
        df = pd.read_sql("SELECT * FROM pacientes WHERE ativo = TRUE", engine)
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")

elif menu == "📊 Estatísticas":
    st.header("📊 Resumo")
    try:
        engine = conectar_banco()
        resumo = pd.read_sql("SELECT COUNT(*) as total FROM pacientes", engine)
        st.metric("Total de Pacientes", int(resumo['total'][0]))
    except:
        st.info("Sem dados.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>www.atendimentoviana.cv</div>", unsafe_allow_html=True)