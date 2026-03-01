import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime, date, time
import os
import numpy as np
import warnings
import base64
import re

warnings.filterwarnings('ignore')

# --- CONFIGURAÇÕES DE CORES (PALETA MODERNA) ---
# Verde Sálvia: #7D9D85 | Fundo Off-White: #FBFBFB | Texto Grafite: #333333
# Destaque Suave: #E9EFEC | Marrom Acinzentado: #5E503F

def converter_numpy_para_python(valor):
    if isinstance(valor, (np.integer, np.int64)):
        return int(valor)
    elif isinstance(valor, (np.floating, np.float64)):
        return float(valor)
    elif isinstance(valor, np.bool_):
        return bool(valor)
    else:
        return valor

def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

img_base64 = get_image_base64("IMG-20260301-WA0000.jpg")

if img_base64:
    st.set_page_config(
        page_title="Belinda Viana - Psicóloga Clínica", 
        page_icon=f"data:image/jpeg;base64,{img_base64}",
        layout="wide"
    )
else:
    st.set_page_config(
        page_title="Belinda Viana - Psicóloga Clínica", 
        page_icon="🌿", 
        layout="wide"
    )

# CSS PERSONALIZADO - ESTILO MINIMALISTA E PROFISSIONAL
st.markdown("""
<style>
    /* Importando fonte elegante */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Fundo Principal */
    .stApp {
        background-color: #FBFBFB;
    }
    
    /* Sidebar moderna */
    [data-testid="stSidebar"] {
        background-color: #E9EFEC !important;
        border-right: 1px solid #DDE2E0;
    }

    /* Títulos */
    h1 {
        color: #4A6351 !important;
        font-weight: 600 !important;
        letter-spacing: -1px;
        margin-bottom: 0px !important;
    }
    
    h3 {
        color: #7D9D85 !important;
        font-weight: 300 !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-size: 16px !important;
        margin-top: 0px !important;
    }

    h2 {
        color: #333333 !important;
        font-weight: 600;
        border-bottom: 2px solid #7D9D85;
        padding-bottom: 10px;
    }

    /* Inputs e Botões */
    .stTextInput input, .stSelectbox [data-baseweb="select"], .stTextArea textarea {
        border-radius: 8px !important;
        border: 1px solid #DDE2E0 !important;
    }

    .stButton > button {
        background-color: #7D9D85 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 2rem !important;
        transition: all 0.3s ease;
        font-weight: 600 !important;
    }

    .stButton > button:hover {
        background-color: #5F7A65 !important;
        box-shadow: 0 4px 12px rgba(125, 157, 133, 0.3);
    }

    /* Cards de métricas */
    [data-testid="stMetricValue"] {
        color: #4A6351 !important;
    }
    
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        border: 1px solid #F0F2F1;
    }

    /* Rodapé */
    .rodape {
        text-align: center;
        color: #5E6D62;
        padding: 25px;
        background-color: #E9EFEC;
        border-radius: 12px;
        margin-top: 50px;
        font-size: 14px;
    }
    
    /* Divisória */
    hr {
        margin: 2em 0;
        border: 0;
        border-top: 1px solid #DDE2E0;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE BANCO ---
def conectar_banco():
    try:
        if "DB_URL" in st.secrets:
            db_url = st.secrets["DB_URL"]
            match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
            if match:
                user, password, host, port, dbname = match.groups()
                return psycopg2.connect(host=host, port=port, database=dbname, user=user, password=password)
        return None
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
        return None

def inicializar_banco():
    try:
        conn = conectar_banco()
        if conn is None: return False
        cur = conn.cursor()
        cur.execute("""
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
        """)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao inicializar: {e}")
        return False

# Inicialização
inicializar_banco()

# --- HEADER ---
st.markdown("<div style='text-align: center'><h1>Belinda Viana</h1><h3>Psicóloga Clínica</h3></div>", unsafe_allow_html=True)
st.markdown("---")

# --- NAVEGAÇÃO ---
st.sidebar.markdown("<h2 style='border:none; font-size: 20px;'>Navegação</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio("", [
    "➕ Cadastrar Paciente", 
    "📅 Marcar Consulta",
    "👥 Ver Pacientes", 
    "🗓️ Agenda da Semana",
    "✅ Registrar Consulta",
    "📊 Estatísticas"
])

def validar_horario(data_consulta, hora_consulta):
    if data_consulta.weekday() >= 5:
        return False, "❌ Não atendemos aos finais de semana."
    hora_min, hora_max = time(7, 0), time(19, 0)
    if hora_consulta < hora_min or hora_consulta > hora_max:
        return False, "❌ Horário disponível: 07:00 às 19:00."
    return True, "✅ Horário disponível!"

# 1. CADASTRAR PACIENTE
if menu == "➕ Cadastrar Paciente":
    st.header("👤 Novo Paciente")
    with st.form("form_paciente"):
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome Completo*")
            tel = st.text_input("Telefone*")
            email = st.text_input("Email")
            nasc = st.date_input("Data de Nascimento", max_value=date.today())
        with c2:
            prof = st.text_input("Profissão")
            origem = st.selectbox("Como chegou", ["Indicação", "Instagram", "Google", "Outro"])
            queixa = st.text_area("Queixa Principal*", height=100)
        
        meds = st.text_input("Medicações em Uso")
        obs = st.text_area("Notas Adicionais")
        
        if st.form_submit_button("CONCLUIR CADASTRO"):
            if nome and tel and queixa:
                try:
                    conn = conectar_banco()
                    cur = conn.cursor()
                    cur.execute("INSERT INTO pacientes (nome_completo, telefone, email, data_nascimento, profissao, como_chegou, queixa_principal, medicacoes_atuais, observacoes_iniciais) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", (nome, tel, email, nasc, prof, origem, queixa, meds, obs))
                    conn.commit()
                    st.success("✨ Paciente registrado com sucesso!")
                    st.balloons()
                except Exception as e: st.error(f"Erro: {e}")
                finally: conn.close()
            else: st.warning("Preencha os campos obrigatórios.")

# 2. MARCAR CONSULTA
elif menu == "📅 Marcar Consulta":
    st.header("📅 Agendamento")
    conn = conectar_banco()
    pacientes_df = pd.read_sql("SELECT id, nome_completo FROM pacientes WHERE ativo = TRUE", conn)
    
    if not pacientes_df.empty:
        with st.form("form_agenda"):
            c1, c2 = st.columns(2)
            with c1:
                p_nome = st.selectbox("Selecione o Paciente", pacientes_df['nome_completo'])
                d_con = st.date_input("Data", min_value=date.today())
                h_con = st.time_input("Horário", value=time(14, 0))
            with c2:
                is_first = st.checkbox("Primeira Consulta?", value=False)
                valor = st.number_input("Valor (CVE)", value=2500.0 if is_first else 2000.0)
                pag_tipo = st.selectbox("Forma de Pagamento", ["Dinheiro", "Transferência", "MB Way"])
            
            if st.form_submit_button("AGENDAR"):
                ok, msg = validar_horario(d_con, h_con)
                if ok:
                    p_id = converter_numpy_para_python(pacientes_df[pacientes_df['nome_completo'] == p_nome].iloc[0]['id'])
                    dt_hr = datetime.combine(d_con, h_con)
                    cur = conn.cursor()
                    cur.execute("INSERT INTO consultas (paciente_id, data_consulta, primeira_consulta, valor_consulta, forma_pagamento) VALUES (%s,%s,%s,%s,%s)", (p_id, dt_hr, is_first, valor, pag_tipo))
                    conn.commit()
                    st.success(f"Consulta agendada para {d_con.strftime('%d/%m')}")
                else: st.error(msg)
    conn.close()

# 3. VER PACIENTES
elif menu == "👥 Ver Pacientes":
    st.header("👥 Seus Pacientes")
    conn = conectar_banco()
    df = pd.read_sql("SELECT nome_completo, telefone, profissao, queixa_principal FROM pacientes WHERE ativo = TRUE", conn)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum paciente encontrado.")
    conn.close()

# 4. AGENDA DA SEMANA
elif menu == "🗓️ Agenda da Semana":
    st.header("🗓️ Próximas Consultas")
    conn = conectar_banco()
    agenda = pd.read_sql("""
        SELECT p.nome_completo, c.data_consulta, c.status, c.valor_consulta
        FROM consultas c JOIN pacientes p ON c.paciente_id = p.id
        WHERE c.data_consulta >= NOW() - INTERVAL '1 day'
        ORDER BY c.data_consulta ASC
    """, conn)
    
    if not agenda.empty:
        for _, r in agenda.iterrows():
            with st.expander(f"🕒 {r['data_consulta'].strftime('%d/%m - %H:%M')} | {r['nome_completo']}"):
                st.write(f"Status: **{r['status'].upper()}**")
                st.write(f"Valor: {r['valor_consulta']} CVE")
    else:
        st.info("Agenda vazia para os próximos dias.")
    conn.close()

# 5. REGISTRAR CONSULTA
elif menu == "✅ Registrar Consulta":
    st.header("✅ Confirmar Realização")
    conn = conectar_banco()
    df = pd.read_sql("""
        SELECT c.id, p.nome_completo, c.data_consulta 
        FROM consultas c JOIN pacientes p ON c.paciente_id = p.id
        WHERE c.status = 'agendada' ORDER BY c.data_consulta
    """, conn)
    
    if not df.empty:
        df['label'] = df['nome_completo'] + " (" + df['data_consulta'].dt.strftime('%d/%m %H:%M') + ")"
        escolha = st.selectbox("Selecione a consulta finalizada", df['label'])
        c1, c2 = st.columns(2)
        c_id = converter_numpy_para_python(df[df['label'] == escolha].iloc[0]['id'])
        
        if c1.button("MARCAR COMO REALIZADA"):
            cur = conn.cursor()
            cur.execute("UPDATE consultas SET status = 'realizada' WHERE id = %s", (c_id,))
            conn.commit()
            st.success("Concluído!")
            st.rerun()
        if c2.button("REGISTRAR FALTA"):
            cur = conn.cursor()
            cur.execute("UPDATE consultas SET status = 'falta' WHERE id = %s", (c_id,))
            conn.commit()
            st.warning("Falta registrada.")
            st.rerun()
    conn.close()

# 6. ESTATÍSTICAS
elif menu == "📊 Estatísticas":
    st.header("📊 Desempenho do Consultório")
    conn = conectar_banco()
    c1, c2, c3 = st.columns(3)
    
    receita = pd.read_sql("SELECT SUM(valor_consulta) FROM consultas WHERE status = 'realizada' AND EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM NOW())", conn).iloc[0,0] or 0
    pacientes = pd.read_sql("SELECT COUNT(*) FROM pacientes WHERE ativo = TRUE", conn).iloc[0,0]
    consultas = pd.read_sql("SELECT COUNT(*) FROM consultas WHERE EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM NOW())", conn).iloc[0,0]
    
    c1.metric("Receita Mensal", f"{receita:,.0f} CVE")
    c2.metric("Pacientes Ativos", pacientes)
    c3.metric("Consultas no Mês", consultas)
    
    st.subheader("Volume de Atendimentos")
    grafico = pd.read_sql("SELECT status, COUNT(*) as qtd FROM consultas GROUP BY status", conn)
    if not grafico.empty:
        st.bar_chart(grafico.set_index('status'))
    conn.close()

# RODAPÉ
st.markdown(f"""
<div class='rodape'>
    <b>Belinda Viana - Psicóloga Clínica</b><br>
    📍 Mindelo, Cabo Verde | 📞 +238 594 99 55<br>
    <span style='opacity: 0.7'>Sistema de Gestão Clínica Profissional</span>
</div>
""", unsafe_allow_html=True)