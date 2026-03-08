import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime, date, time
import os
import numpy as np
import warnings
import base64
warnings.filterwarnings('ignore')

# CORREÇÃO 1: Função para converter numpy.int64
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

# Função para carregar imagem como base64 (para o favicon)
def get_image_base64(image_path):
    """Converte imagem para base64"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# Tenta carregar a imagem (assumindo que está na mesma pasta)
img_base64 = get_image_base64("IMG-20260301-WA0000.jpg")

# Configuração da página com imagem como ícone
if img_base64:
    st.set_page_config(
        page_title="Belinda Viana - Psicóloga Clínica", 
        page_icon=f"data:image/jpeg;base64,{img_base64}",
        layout="wide"
    )
else:
    st.set_page_config(
        page_title="Belinda Viana - Psicóloga Clínica", 
        page_icon="🧠",
        layout="wide"
    )

# --- CSS PERSONALIZADO E ATUALIZADO ---
st.markdown("""
<style>
    /* Estilo global e fontes */
    .stApp {
        background-color: #FBFBFB !important;
    }
    
    /* Garantir cor preta em todo o texto */
    .stApp, p, span, label, li, h1, h2, h3, .stMarkdown {
        color: #333333 !important;
    }
    
    /* Estilização da Sidebar */
    .css-1d391kg, [data-testid="stSidebar"] {
        background-color: #E9EFEC !important;
        border-right: 1px solid #E0E0E0;
    }
    
    /* Título principal */
    h1 {
        color: #7D9D85 !important;
        text-align: center;
        font-size: 42px !important;
        font-weight: 700;
        margin-bottom: 5px !important;
    }
    
    /* Subtítulo */
    h3 {
        text-align: center;
        color: #555555 !important;
        font-weight: 400;
        font-size: 18px !important;
        letter-spacing: 2px;
        margin-top: 0px !important;
    }
    
    /* Títulos de seção */
    h2 {
        color: #333333 !important;
        border-bottom: 2px solid #7D9D85;
        padding-bottom: 10px;
        margin-top: 30px !important;
    }
    
    /* Botões */
    .stButton > button {
        background-color: #7D9D85 !important;
        color: white !important;
        border: none;
        border-radius: 20px !important;
        padding: 10px 25px !important;
        font-weight: 600;
        transition: background-color 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #5F7A65 !important;
    }
    
    /* Botão cancelar */
    .stButton > button[kind="secondary"] {
        background-color: #e74c3c !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background-color: #c0392b !important;
    }
    
    /* Cards de Métricas */
    [data-testid="metric-container"] {
        background-color: white !important;
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
        border: 1px solid #F0F0F0 !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #7D9D85 !important;
        font-size: 32px !important;
    }
    
    /* Cards de consulta na agenda */
    .consulta-card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Rodapé */
    .rodape {
        text-align: center;
        color: #333333 !important;
        padding: 20px;
        background-color: #E9EFEC;
        border-radius: 8px;
        margin-top: 40px;
    }
</style>
""", unsafe_allow_html=True)

# Conexão com Supabase
def conectar_banco():
    """Conecta ao Supabase usando Session Pooler"""
    try:
        if "DB_URL" in st.secrets:
            db_url = st.secrets["DB_URL"]
            import re
            match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
            if match:
                user, password, host, port, dbname = match.groups()
                return psycopg2.connect(
                    host=host,
                    port=port,
                    database=dbname,
                    user=user,
                    password=password
                )
        else:
            st.error("❌ DB_URL não configurada! Use secrets.")
            return None
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
        return None

# Inicializar banco
def inicializar_banco():
    """Garante que as tabelas necessárias existam"""
    try:
        conn = conectar_banco()
        if conn is None:
            return False
            
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
        """)
        
        cur.execute("""
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
        st.error(f"Erro ao inicializar banco: {e}")
        return False

# Executar inicialização
inicializar_banco()

# HEADER PERSONALIZADO
st.markdown("<div style='text-align: center'><h1>Belinda Viana</h1><h3>Psicóloga Clínica</h3></div>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #7D9D85;'>", unsafe_allow_html=True)

# MENU PERSONALIZADO NA SIDEBAR
st.sidebar.markdown("<h2 style='border:none; font-size: 20px;'>Navegação</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio("", [
    "➕ Cadastrar Paciente", 
    "📅 Marcar Consulta",
    "👥 Ver Pacientes", 
    "🗓️ Agenda da Semana",
    "✅ Registrar Consulta Realizada",
    "📊 Estatísticas"
])

# Função para validar horário de atendimento
def validar_horario(data_consulta, hora_consulta):
    """Valida se o horário está dentro do funcionamento (Segunda a Sexta, 7h-19h)"""
    if data_consulta.weekday() >= 5:
        return False, "❌ Não atendemos aos sábados e domingos!"
    
    hora_min = time(7, 0)
    hora_max = time(19, 0)
    
    if hora_consulta < hora_min or hora_consulta > hora_max:
        return False, "❌ Horário de atendimento: 07:00 às 19:00"
    
    return True, "✅ Horário disponível!"

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
            como_chegou = st.selectbox("Como chegou até nós", 
                                     ["Indicação", "Internet", "Redes Sociais", "Outro"])
            queixa_principal = st.text_area("Queixa Principal*", 
                                          placeholder="Descreva a queixa principal...", 
                                          height=100)
        
        medicacoes = st.text_input("Medicações Atuais", placeholder="Medicações em uso")
        observacoes = st.text_area("Observações Iniciais", 
                                 placeholder="Observações relevantes...",
                                 height=80)
        
        submit = st.form_submit_button("Salvar Paciente")
        
        if submit:
            if nome and telefone and queixa_principal:
                conn = conectar_banco()
                if conn:
                    try:
                        cur = conn.cursor()
                        cur.execute(
                            """INSERT INTO pacientes 
                            (nome_completo, telefone, email, data_nascimento, profissao, 
                             como_chegou, queixa_principal, medicacoes_atuais, observacoes_iniciais) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                            (nome, telefone, email, data_nascimento, profissao, como_chegou, 
                             queixa_principal, medicacoes, observacoes)
                        )
                        conn.commit()
                        st.success("✨ Paciente registrado com sucesso!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar: {e}")
                    finally:
                        conn.close()
            else:
                st.error("Preencha os campos obrigatórios (*)")

# 2. MARCAR CONSULTA - SEM ALTERAÇÕES
elif menu == "📅 Marcar Consulta":
    st.header("📅 Marcar Nova Consulta")
    
    conn = conectar_banco()
    if conn:
        try:
            pacientes_df = pd.read_sql("SELECT id, nome_completo FROM pacientes WHERE ativo = TRUE ORDER BY nome_completo", conn)
            
            if pacientes_df.empty:
                st.warning("⚠️ Cadastre pacientes primeiro!")
            else:
                with st.form("form_consulta", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        paciente_nome = st.selectbox("Paciente*", pacientes_df['nome_completo'])
                        data_consulta = st.date_input("Data*", min_value=date.today())
                        hora_consulta = st.time_input("Horário*", value=time(14, 0))
                        
                    with col2: 
                        primeira_consulta = st.checkbox("Primeira Consulta", value=False)
                        valor_consulta = st.number_input("Valor da Consulta (CVE)", 
                                                       min_value=0.0, 
                                                       value=2000.0,
                                                       step=100.0)
                        forma_pagamento = st.selectbox("Forma de Pagamento", 
                                                     ["Transferência", "Dinheiro", "MB Way", "Outro"])
                    
                    observacoes = st.text_area("Observações Técnicas")
                    
                    submit_agendar = st.form_submit_button("Agendar Consulta")
                    
                    if submit_agendar:
                        horario_valido, mensagem = validar_horario(data_consulta, hora_consulta)
                        if not horario_valido:
                            st.error(mensagem)
                        else:
                            paciente_row = pacientes_df[pacientes_df['nome_completo'] == paciente_nome].iloc[0]
                            paciente_id = converter_numpy_para_python(paciente_row['id'])
                            
                            data_hora = datetime.combine(data_consulta, hora_consulta)
                            
                            cur = conn.cursor()
                            cur.execute(
                                """INSERT INTO consultas 
                                (paciente_id, data_consulta, primeira_consulta, valor_consulta, 
                                 forma_pagamento, observacoes_tecnicas) 
                                VALUES (%s, %s, %s, %s, %s, %s)""",
                                (paciente_id, data_hora, primeira_consulta, valor_consulta, 
                                 forma_pagamento, observacoes)
                            )
                            conn.commit()
                            st.success(f"✅ Consulta agendada para {data_consulta.strftime('%d/%m/%Y')} às {hora_consulta.strftime('%H:%M')}")
                            
        except Exception as e:
            st.error(f"❌ Erro: {e}")
        finally:
            conn.close()

# 3. VER PACIENTES
elif menu == "👥 Ver Pacientes":
    st.header("👥 Lista de Pacientes")
    
    conn = conectar_banco()
    if conn:
        try:
            pacientes_df = pd.read_sql("""
                SELECT id, nome_completo, telefone, email, profissao, queixa_principal, 
                       TO_CHAR(data_cadastro, 'DD/MM/YYYY') as data_cadastro
                FROM pacientes 
                WHERE ativo = TRUE
                ORDER BY nome_completo
            """, conn)
            
            if not pacientes_df.empty:
                st.dataframe(pacientes_df, use_container_width=True)
                st.metric("Total de Pacientes Ativos", len(pacientes_df))
            else:
                st.info("Nenhum paciente cadastrado.")
                
        except Exception as e:
            st.error(f"❌ Erro ao carregar pacientes: {e}")
        finally:
            conn.close()

# 4. AGENDA DA SEMANA - COM OPÇÃO DE CANCELAR
elif menu == "🗓️ Agenda da Semana":
    st.header("🗓️ Agenda de Consultas")
    
    opcao_agenda = st.radio("Visualizar:", ["Hoje", "Amanhã", "Próximos 7 Dias"], horizontal=True)
    
    conn = conectar_banco()
    if conn:
        try:
            if opcao_agenda == "Hoje":
                agenda_df = pd.read_sql("""
                    SELECT c.id, p.nome_completo, c.data_consulta, 
                           CASE WHEN c.primeira_consulta THEN 'Primeira' ELSE 'Retorno' END as tipo,
                           c.status, c.valor_consulta, c.forma_pagamento
                    FROM consultas c
                    JOIN pacientes p ON c.paciente_id = p.id
                    WHERE DATE(c.data_consulta) = CURRENT_DATE
                    ORDER BY c.data_consulta
                """, conn)
            elif opcao_agenda == "Amanhã":
                agenda_df = pd.read_sql("""
                    SELECT c.id, p.nome_completo, c.data_consulta, 
                           CASE WHEN c.primeira_consulta THEN 'Primeira' ELSE 'Retorno' END as tipo,
                           c.status, c.valor_consulta, c.forma_pagamento
                    FROM consultas c
                    JOIN pacientes p ON c.paciente_id = p.id
                    WHERE DATE(c.data_consulta) = CURRENT_DATE + INTERVAL '1 day'
                    ORDER BY c.data_consulta
                """, conn)
            else:
                agenda_df = pd.read_sql("""
                    SELECT c.id, p.nome_completo, c.data_consulta, 
                           CASE WHEN c.primeira_consulta THEN 'Primeira' ELSE 'Retorno' END as tipo,
                           c.status, c.valor_consulta, c.forma_pagamento
                    FROM consultas c
                    JOIN pacientes p ON c.paciente_id = p.id
                    WHERE c.data_consulta BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
                    ORDER BY c.data_consulta
                """, conn)
            
            if not agenda_df.empty:
                # Criar colunas para os cabeçalhos
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                with col1:
                    st.markdown("**Paciente**")
                with col2:
                    st.markdown("**Horário**")
                with col3:
                    st.markdown("**Tipo**")
                with col4:
                    st.markdown("**Status**")
                with col5:
                    st.markdown("**Ações**")
                
                st.divider()
                
                for _, row in agenda_df.iterrows():
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                        
                        with col1:
                            st.write(f"**{row['nome_completo']}**")
                        
                        with col2:
                            st.write(f"🕐 {row['data_consulta'].strftime('%H:%M')}")
                        
                        with col3:
                            st.write(f"📝 {row['tipo']}")
                        
                        with col4:
                            status_color = {
                                'agendada': 'blue',
                                'realizada': 'green', 
                                'cancelada': 'red',
                                'falta': 'orange'
                            }.get(row['status'].lower(), 'gray')
                            st.markdown(f"<span style='color:{status_color}'>{row['status'].title()}</span>", 
                                      unsafe_allow_html=True)
                        
                        with col5:
                            if row['status'].lower() == 'agendada':
                                consulta_id = converter_numpy_para_python(row['id'])
                                if st.button(f"❌ Cancelar", key=f"cancel_{consulta_id}"):
                                    try:
                                        cur = conn.cursor()
                                        cur.execute("UPDATE consultas SET status = 'cancelada' WHERE id = %s", (consulta_id,))
                                        conn.commit()
                                        st.success("✅ Consulta cancelada!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao cancelar: {e}")
                            else:
                                st.write("—")
                        
                        st.caption(f"💰 {converter_numpy_para_python(row['valor_consulta']):,.0f} CVE")
                        st.divider()
                
                # Estatísticas
                total = len(agenda_df)
                realizadas = len(agenda_df[agenda_df['status'].str.lower() == 'realizada'])
                faltas = len(agenda_df[agenda_df['status'].str.lower() == 'falta'])
                canceladas = len(agenda_df[agenda_df['status'].str.lower() == 'cancelada'])
                
                col_res1, col_res2, col_res3, col_res4 = st.columns(4)
                with col_res1:
                    st.metric("Total", total)
                with col_res2:
                    st.metric("Realizadas", realizadas)
                with col_res3:
                    st.metric("Faltas", faltas)
                with col_res4:
                    st.metric("Canceladas", canceladas)
            else:
                st.info("📅 Nenhuma consulta agendada para o período selecionado.")
                
        except Exception as e:
            st.error(f"❌ Erro ao carregar agenda: {e}")
        finally:
            conn.close()

# 5. REGISTRAR CONSULTA REALIZADA
elif menu == "✅ Registrar Consulta Realizada":
    st.header("✅ Registrar Consulta Realizada")
    
    conn = conectar_banco()
    if conn:
        try:
            consultas_df = pd.read_sql("""
                SELECT c.id, p.nome_completo, c.data_consulta, c.valor_consulta,
                       c.pagamento_realizado, c.status
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE c.status = 'agendada' AND c.data_consulta <= CURRENT_DATE + INTERVAL '1 day'
                ORDER BY c.data_consulta
            """, conn)
            
            if not consultas_df.empty:
                consultas_df['display'] = consultas_df['nome_completo'] + " - " + consultas_df['data_consulta'].dt.strftime('%d/%m/%Y %H:%M')
                consulta_selecionada = st.selectbox("Selecione a consulta:", consultas_df['display'])
                
                consulta_info = consultas_df[consultas_df['display'] == consulta_selecionada].iloc[0]
                
                st.info(f"""
                **Detalhes da Consulta:**
                - **Paciente:** {consulta_info['nome_completo']}
                - **Data/Hora:** {consulta_info['data_consulta'].strftime('%d/%m/%Y %H:%M')}
                - **Valor:** {converter_numpy_para_python(consulta_info['valor_consulta']):,.0f} CVE
                - **Pagamento:** {'✅ Pago' if consulta_info['pagamento_realizado'] else '⏳ Pendente'}
                """)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("✅ Realizada", type="primary", use_container_width=True):
                        consulta_id = converter_numpy_para_python(consulta_info['id'])
                        cur = conn.cursor()
                        cur.execute("UPDATE consultas SET status = 'realizada' WHERE id = %s", (consulta_id,))
                        conn.commit()
                        st.success("✅ Consulta registrada!")
                        st.rerun()
                
                with col2:
                    if st.button("❌ Não compareceu", use_container_width=True):
                        consulta_id = converter_numpy_para_python(consulta_info['id'])
                        cur = conn.cursor()
                        cur.execute("UPDATE consultas SET status = 'falta' WHERE id = %s", (consulta_id,))
                        conn.commit()
                        st.warning("⚠️ Falta registrada")
                        st.rerun()
                
                with col3:
                    if not consulta_info['pagamento_realizado'] and consulta_info['status'] == 'realizada':
                        if st.button("💰 Pagamento", use_container_width=True):
                            consulta_id = converter_numpy_para_python(consulta_info['id'])
                            cur = conn.cursor()
                            cur.execute("UPDATE consultas SET pagamento_realizado = TRUE WHERE id = %s", (consulta_id,))
                            conn.commit()
                            st.success("💰 Pagamento registrado!")
                            st.rerun()
            else:
                st.info("📝 Nenhuma consulta para registrar.")
                
        except Exception as e:
            st.error(f"❌ Erro: {e}")
        finally:
            conn.close()

# 6. ESTATÍSTICAS
elif menu == "📊 Estatísticas":
    st.header("📊 Estatísticas do Consultório")
    
    conn = conectar_banco()
    if conn:
        try:
            col1, col2, col3 = st.columns(3)
            
            total_pac = pd.read_sql("SELECT COUNT(*) as total FROM pacientes WHERE ativo = TRUE", conn).iloc[0]['total']
            
            con_mes = pd.read_sql("""
                SELECT COUNT(*) as total FROM consultas 
                WHERE EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM data_consulta) = EXTRACT(YEAR FROM CURRENT_DATE)
            """, conn).iloc[0]['total']
            
            rec_mes = pd.read_sql("""
                SELECT COALESCE(SUM(valor_consulta), 0) as total FROM consultas 
                WHERE status = 'realizada'
                AND EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM data_consulta) = EXTRACT(YEAR FROM CURRENT_DATE)
            """, conn).iloc[0]['total'] or 0.0
            rec_mes = converter_numpy_para_python(rec_mes)
            
            with col1:
                st.metric("Receita Mensal", f"{rec_mes:,.0f} CVE".replace(",", "."))
            with col2:
                st.metric("Pacientes Ativos", total_pac)
            with col3:
                st.metric("Consultas no Mês", con_mes)
                
            st.markdown("### 📈 Consultas por Status (Este Mês)")
            chart_data = pd.read_sql("""
                SELECT status, COUNT(*) as quantidade
                FROM consultas
                WHERE EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM data_consulta) = EXTRACT(YEAR FROM CURRENT_DATE)
                GROUP BY status
            """, conn)
            
            if not chart_data.empty:
                st.bar_chart(chart_data.set_index('status'))
            else:
                st.info("📊 Sem dados para o mês atual.")
                
        except Exception as e:
            st.error(f"❌ Erro: {e}")
        finally:
            conn.close()

# RODAPÉ
st.markdown("---")
st.markdown("""
<div class='rodape'>
    🧠 <b>Belinda Viana</b> - Psicóloga Clínica | 📞 Contacto: +238 594 99 55<br>
    📧 Email: belindaviana08@gmail.com
</div>
""", unsafe_allow_html=True)