import streamlit as st
import pandas as pd
from datetime import datetime, date, time
import numpy as np
from sqlalchemy import create_engine, text
import socket
import time as tempo
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Atendimento Viana - Psicologia", 
    page_icon="🧠",
    layout="wide"
)

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

# --- FUNÇÃO PARA TESTAR CONEXÃO COM INTERNET ---
def testar_conexao_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

# --- FUNÇÃO PARA VERIFICAR SECRETS ---
def verificar_secrets():
    if "DB_URL" in st.secrets:
        db_url = st.secrets["DB_URL"]
        
        if "[YOUR-PASSWORD]" in db_url:
            st.error("❌ **ERRO: Substitua [YOUR-PASSWORD] pela senha real!**")
            st.stop()
        
        return db_url
    else:
        return None

# --- CONEXÃO COM O BANCO DE DADOS ---
@st.cache_resource
def conectar_banco():
    if not testar_conexao_internet():
        st.error("⚠️ **Sem conexão com a internet!**")
        st.stop()
    
    db_url = verificar_secrets()
    
    if db_url is None:
        st.error("⚠️ **Erro: DB_URL não encontrada!**")
        st.info("""
        Crie o arquivo `.streamlit/secrets.toml` com:
        DB_URL = "postgresql://postgres.opuyirrrrzibpxzkrikk:SUA_SENHA@aws-1-eu-west-2.pooler.supabase.com:5432/postgres"
        """)
        st.stop()
    
    try:
        engine = create_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            connect_args={'connect_timeout': 15}
        )
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return engine
        
    except Exception as e:
        erro_str = str(e)
        
        if "could not translate host name" in erro_str:
            st.error("❌ **Erro: Host não encontrado! Use o Session Pooler**")
        elif "password authentication" in erro_str.lower():
            st.error("❌ **Erro: Senha incorreta!**")
        else:
            st.error(f"❌ **Erro:** {e}")
        
        st.stop()

# --- INICIALIZAÇÃO DO BANCO ---
def inicializar_banco():
    engine = conectar_banco()
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pacientes (
                id SERIAL PRIMARY KEY,
                nome_completo VARCHAR(100) NOT NULL,
                telefone VARCHAR(20) NOT NULL,
                email VARCHAR(100),
                data_nascimento DATE,
                profissao VARCHAR(50),
                como_chegou VARCHAR(50),
                queixa_principal TEXT NOT NULL,
                medicacoes_atuais TEXT,
                observacoes_iniciais TEXT,
                ativo BOOLEAN DEFAULT TRUE,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS consultas (
                id SERIAL PRIMARY KEY,
                paciente_id INTEGER REFERENCES pacientes(id),
                data_consulta TIMESTAMP NOT NULL,
                primeira_consulta BOOLEAN DEFAULT TRUE,
                valor_consulta DECIMAL(10,2) DEFAULT 0,
                status VARCHAR(20) DEFAULT 'agendada',
                observacoes_tecnicas TEXT,
                pagamento_realizado BOOLEAN DEFAULT FALSE,
                forma_pagamento VARCHAR(50),
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()
    return engine

# --- INICIALIZAÇÃO ---
engine = inicializar_banco()
st.sidebar.success("✅ Banco conectado")

# --- INTERFACE ---
st.markdown("<h1 style='text-align: center; color: #1f77b4;'>🧠 ATENDIMENTO VIANA</h1>", unsafe_allow_html=True)
st.markdown("---")

st.sidebar.markdown("## 🧭 Navegação")
menu = st.sidebar.selectbox("Selecione:", [
    "➕ Cadastrar Paciente", 
    "📅 Marcar Consulta",
    "👥 Ver Pacientes", 
    "🗓️ Agenda",
    "✅ Registrar Consulta",
    "📊 Estatísticas"
])

# 1. CADASTRAR PACIENTE
if menu == "➕ Cadastrar Paciente":
    st.header("👤 Cadastrar Paciente")
    with st.form("form_paciente"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo*")
            telefone = st.text_input("Telefone*")
            email = st.text_input("Email")
            data_nascimento = st.date_input("Nascimento", max_value=date.today())
        with col2:
            profissao = st.text_input("Profissão")
            como_chegou = st.selectbox("Como chegou", ["Indicação", "Internet", "Redes Sociais", "Outro"])
            queixa_principal = st.text_area("Queixa Principal*", height=100)
        medicacoes = st.text_input("Medicações")
        observacoes = st.text_area("Observações", height=80)
        
        if st.form_submit_button("💾 Salvar"):
            if nome and telefone and queixa_principal:
                try:
                    with engine.connect() as conn:
                        conn.execute(text("""
                            INSERT INTO pacientes 
                            (nome_completo, telefone, email, data_nascimento, profissao, 
                             como_chegou, queixa_principal, medicacoes_atuais, observacoes_iniciais) 
                            VALUES (:n, :t, :e, :d, :p, :c, :q, :m, :o)
                        """), {
                            "n":nome, "t":telefone, "e":email, "d":data_nascimento, 
                            "p":profissao, "c":como_chegou, "q":queixa_principal, 
                            "m":medicacoes, "o":observacoes
                        })
                        conn.commit()
                    st.success("✅ Cadastrado!")
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                st.error("❌ Campos obrigatórios")

# 2. MARCAR CONSULTA
elif menu == "📅 Marcar Consulta":
    st.header("📅 Marcar Consulta")
    try:
        pacientes_df = pd.read_sql("SELECT id, nome_completo FROM pacientes WHERE ativo = TRUE", engine)
        
        if pacientes_df.empty:
            st.warning("⚠️ Cadastre pacientes primeiro!")
        else:
            with st.form("form_consulta"):
                col1, col2 = st.columns(2)
                with col1:
                    paciente = st.selectbox("Paciente*", pacientes_df['nome_completo'])
                    data_c = st.date_input("Data*", min_value=date.today())
                    hora_c = st.time_input("Horário*", value=time(14, 0))
                with col2:
                    primeira = st.checkbox("Primeira Consulta", value=True)
                    valor = st.number_input("Valor", value=2500.0 if primeira else 2000.0)
                    forma = st.selectbox("Pagamento", ["Dinheiro", "Transferência", "MB Way"])
                
                if st.form_submit_button("📅 Agendar"):
                    paciente_id = int(pacientes_df[pacientes_df['nome_completo'] == paciente].iloc[0]['id'])
                    data_hora = datetime.combine(data_c, hora_c)
                    with engine.connect() as conn:
                        conn.execute(text("""
                            INSERT INTO consultas 
                            (paciente_id, data_consulta, primeira_consulta, valor_consulta, forma_pagamento) 
                            VALUES (:id, :dt, :pr, :vl, :fm)
                        """), {
                            "id":paciente_id, "dt":data_hora, "pr":primeira, 
                            "vl":valor, "fm":forma
                        })
                        conn.commit()
                    st.success("✅ Agendado!")
    except Exception as e:
        st.error(f"Erro: {e}")

# 3. VER PACIENTES
elif menu == "👥 Ver Pacientes":
    st.header("👥 Pacientes")
    try:
        df = pd.read_sql("SELECT id, nome_completo, telefone, profissao, data_cadastro FROM pacientes WHERE ativo = TRUE", engine)
        st.dataframe(df)
    except Exception as e:
        st.error(f"Erro: {e}")

# 4. AGENDA
elif menu == "🗓️ Agenda":
    st.header("🗓️ Agenda")
    try:
        agenda_df = pd.read_sql("""
            SELECT p.nome_completo, c.data_consulta, c.status, c.valor_consulta
            FROM consultas c JOIN pacientes p ON c.paciente_id = p.id
            ORDER BY c.data_consulta
        """, engine)
        st.dataframe(agenda_df)
    except Exception as e:
        st.error(f"Erro: {e}")

# 5. REGISTRAR CONSULTA
elif menu == "✅ Registrar Consulta":
    st.header("✅ Registrar Consulta")
    try:
        consultas_df = pd.read_sql("""
            SELECT c.id, p.nome_completo, c.data_consulta 
            FROM consultas c JOIN pacientes p ON c.paciente_id = p.id 
            WHERE c.status = 'agendada'
        """, engine)
        
        if not consultas_df.empty:
            consultas_df['display'] = consultas_df['nome_completo'] + " - " + consultas_df['data_consulta'].astype(str)
            selecao = st.selectbox("Escolha a consulta:", consultas_df['display'])
            
            if st.button("Marcar como Realizada"):
                idx = consultas_df[consultas_df['display'] == selecao].index[0]
                c_id = int(consultas_df.loc[idx, 'id'])
                with engine.connect() as conn:
                    conn.execute(text("UPDATE consultas SET status = 'realizada' WHERE id = :id"), {"id":c_id})
                    conn.commit()
                st.success("✅ Registrada!")
                st.rerun()
        else:
            st.info("Sem consultas agendadas")
    except Exception as e:
        st.error(f"Erro: {e}")

# 6. ESTATÍSTICAS
elif menu == "📊 Estatísticas":
    st.header("📊 Estatísticas")
    try:
        total = pd.read_sql("SELECT COUNT(*) as total FROM pacientes WHERE ativo = TRUE", engine).iloc[0]['total']
        st.metric("Total de Pacientes", int(total))
        
        status_df = pd.read_sql("SELECT status, COUNT(*) as quantidade FROM consultas GROUP BY status", engine)
        if not status_df.empty:
            st.bar_chart(status_df.set_index('status'))
    except Exception as e:
        st.error(f"Erro: {e}")

# RODAPÉ
st.markdown("---")
st.markdown("<div style='text-align: center;'>www.atendimentoviana.cv</div>", unsafe_allow_html=True)