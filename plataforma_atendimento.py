import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime, date, time
import os
import numpy as np
from sqlalchemy import create_engine, text

# --- FUNÇÃO DE CONVERSÃO DE TIPOS ---
def converter_numpy_para_python(valor):
    """Converte tipos numpy para tipos Python nativos"""
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

# --- CONEXÃO COM O BANCO DE DADOS (PROTEGIDA) ---
def conectar_banco():
    """Conecta ao banco usando Secrets para proteger a senha"""
    # No Streamlit Cloud, configuramos a DB_URL em Settings > Secrets
    if "DB_URL" in st.secrets:
        db_url = st.secrets["DB_URL"]
    else:
        # Caso queira rodar localmente no futuro, ele usará esta linha
        # IMPORTANTE: Nunca coloque a senha do Supabase aqui se for enviar ao GitHub
        db_url = "postgresql://postgres:SENHA_LOCAL@localhost:5432/postgres"
    
    engine = create_engine(db_url)
    return engine

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
                como_chegou VARCHAR(50),
                queixa_principal TEXT NOT NULL,
                medicacoes_atuais TEXT,
                observacoes_iniciais TEXT,
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
                primeira_consulta BOOLEAN DEFAULT TRUE,
                valor_consulta DECIMAL(10,2) DEFAULT 0,
                status VARCHAR(20) DEFAULT 'agendada' CHECK (status IN ('agendada', 'realizada', 'cancelada', 'falta')),
                observacoes_tecnicas TEXT,
                pagamento_realizado BOOLEAN DEFAULT FALSE,
                forma_pagamento VARCHAR(50),
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()

# Rodar inicialização ao abrir o app
try:
    inicializar_banco()
except Exception as e:
    st.error("Erro de conexão com o banco de dados.")
    st.info("Certifique-se de configurar a DB_URL nos Secrets do Streamlit Cloud.")

# --- INTERFACE ---
st.markdown("<h1 style='text-align: center; color: #1f77b4;'>🧠 ATENDIMENTO VIANA - CONSULTÓRIO DE PSICOLOGIA</h1>", unsafe_allow_html=True)
st.markdown("---")

st.sidebar.markdown("## 🧭 Navegação")
menu = st.sidebar.selectbox("Selecione uma opção:", [
    "➕ Cadastrar Paciente", 
    "📅 Marcar Consulta",
    "👥 Ver Pacientes", 
    "🗓️ Agenda da Semana",
    "✅ Registrar Consulta Realizada",
    "📊 Estatísticas"
])

# 1. CADASTRAR PACIENTE
if menu == "➕ Cadastrar Paciente":
    st.header("👤 Cadastrar Novo Paciente")
    with st.form("form_paciente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo*", placeholder="Nome completo do paciente")
            telefone = st.text_input("Telefone*", placeholder="+238 XXX XX XX") 
            email = st.text_input("Email", placeholder="paciente@email.cv")
            data_nascimento = st.date_input("Data de Nascimento", max_value=date.today())
        with col2:
            profissao = st.text_input("Profissão", placeholder="Profissão atual")
            como_chegou = st.selectbox("Como chegou até nós", ["Indicação", "Internet", "Redes Sociais", "Outro"])
            queixa_principal = st.text_area("Queixa Principal*", height=100)
        medicacoes = st.text_input("Medicações Atuais")
        observacoes = st.text_area("Observações Iniciais", height=80)
        
        if st.form_submit_button("💾 Salvar Paciente"):
            if nome and telefone and queixa_principal:
                try:
                    engine = conectar_banco()
                    with engine.connect() as conn:
                        query = text("""INSERT INTO pacientes 
                            (nome_completo, telefone, email, data_nascimento, profissao, como_chegou, queixa_principal, medicacoes_atuais, observacoes_iniciais) 
                            VALUES (:n, :t, :e, :d, :p, :c, :q, :m, :o)""")
                        conn.execute(query, {"n":nome, "t":telefone, "e":email, "d":data_nascimento, "p":profissao, "c":como_chegou, "q":queixa_principal, "m":medicacoes, "o":observacoes})
                        conn.commit()
                    st.success("✅ Paciente cadastrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.error("❌ Preencha os campos obrigatórios (*)")

# 2. MARCAR CONSULTA  
elif menu == "📅 Marcar Consulta":
    st.header("📅 Marcar Nova Consulta")
    try:
        engine = conectar_banco()
        pacientes_df = pd.read_sql("SELECT id, nome_completo FROM pacientes WHERE ativo = TRUE", engine)
        
        if pacientes_df.empty:
            st.warning("⚠️ Cadastre pacientes primeiro!")
        else:
            with st.form("form_consulta"):
                col1, col2 = st.columns(2)
                with col1:
                    paciente_nome = st.selectbox("Paciente*", pacientes_df['nome_completo'])
                    data_c = st.date_input("Data*", min_value=date.today())
                    hora_c = st.time_input("Horário*", value=time(14, 0))
                with col2:
                    primeira = st.checkbox("Primeira Consulta", value=True)
                    valor = st.number_input("Valor (CVE)", value=2500.0 if primeira else 2000.0)
                    forma = st.selectbox("Pagamento", ["Dinheiro", "Transferência", "MB Way", "Outro"])
                
                if st.form_submit_button("📅 Agendar"):
                    paciente_id = int(pacientes_df[pacientes_df['nome_completo'] == paciente_nome].iloc[0]['id'])
                    data_hora = datetime.combine(data_c, hora_c)
                    with engine.connect() as conn:
                        conn.execute(text("""INSERT INTO consultas (paciente_id, data_consulta, primeira_consulta, valor_consulta, forma_pagamento) 
                            VALUES (:id, :dt, :pr, :vl, :fm)"""), 
                            {"id":paciente_id, "dt":data_hora, "pr":primeira, "vl":valor, "fm":forma})
                        conn.commit()
                    st.success("✅ Agendado!")
    except:
        st.error("Erro ao carregar lista de pacientes.")

# 3. VER PACIENTES
elif menu == "👥 Ver Pacientes":
    st.header("👥 Lista de Pacientes")
    try:
        engine = conectar_banco()
        df = pd.read_sql("SELECT id, nome_completo, telefone, profissao, data_cadastro FROM pacientes WHERE ativo = TRUE", engine)
        st.dataframe(df, use_container_width=True)
    except:
        st.error("Erro ao carregar dados.")

# 4. AGENDA
elif menu == "🗓️ Agenda da Semana":
    st.header("🗓️ Agenda")
    try:
        engine = conectar_banco()
        agenda_df = pd.read_sql("""
            SELECT p.nome_completo, c.data_consulta, c.status, c.valor_consulta
            FROM consultas c JOIN pacientes p ON c.paciente_id = p.id
            ORDER BY c.data_consulta
        """, engine)
        st.dataframe(agenda_df, use_container_width=True)
    except:
        st.error("Erro ao carregar agenda.")

# 5. REGISTRAR REALIZADA
elif menu == "✅ Registrar Consulta Realizada":
    st.header("✅ Confirmar Atendimento")
    try:
        engine = conectar_banco()
        consultas_df = pd.read_sql("SELECT c.id, p.nome_completo, c.data_consulta FROM consultas c JOIN pacientes p ON c.paciente_id = p.id WHERE c.status = 'agendada'", engine)
        
        if not consultas_df.empty:
            selecao = st.selectbox("Escolha a consulta:", consultas_df['nome_completo'])
            if st.button("Marcar como Realizada"):
                c_id = int(consultas_df[consultas_df['nome_completo'] == selecao].iloc[0]['id'])
                with engine.connect() as conn:
                    conn.execute(text("UPDATE consultas SET status = 'realizada' WHERE id = :id"), {"id":c_id})
                    conn.commit()
                st.rerun()
        else:
            st.info("Não há consultas agendadas pendentes.")
    except:
        st.error("Erro ao processar consultas.")

# 6. ESTATÍSTICAS
elif menu == "📊 Estatísticas":
    st.header("📊 Resumo do Mês")
    try:
        engine = conectar_banco()
        total = pd.read_sql("SELECT COUNT(*) as total FROM pacientes WHERE ativo = TRUE", engine).iloc[0]['total']
        st.metric("Total de Pacientes Ativos", int(total))
        
        status_df = pd.read_sql("SELECT status, COUNT(*) as quantidade FROM consultas GROUP BY status", engine)
        if not status_df.empty:
            st.bar_chart(status_df.set_index('status'))
    except:
        st.info("Aguardando dados para gerar estatísticas.")

# RODAPÉ
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>www.atendimentoviana.cv</div>", unsafe_allow_html=True)