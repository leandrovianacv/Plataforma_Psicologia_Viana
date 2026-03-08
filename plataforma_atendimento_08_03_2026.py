import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime, date, time, timedelta
import os
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Função para converter numpy.int64
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

# Configuração da página
st.set_page_config(
    page_title="Atendimento Viana - Psicologia", 
    page_icon="🧠",
    layout="wide"
)

# Conexão com Supabase (via Session Pooler)
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
            db_url = os.getenv("DB_URL")
            if db_url:
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
                st.error("❌ DB_URL não configurada! Use secrets ou variável de ambiente.")
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
                queixa_principal TEXT,
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
if inicializar_banco():
    st.sidebar.success("✅ Conectado ao Supabase")
else:
    st.sidebar.error("❌ Falha na conexão com Supabase")

# HEADER PERSONALIZADO
st.markdown("<h1 style='text-align: center; color: #1f77b4;'>🧠 PSICARE BY BELINDA VIANA</h1>", unsafe_allow_html=True)
st.markdown("---")

# MENU PERSONALIZADO
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
            
            data_nascimento = st.date_input(
                "Data de Nascimento", 
                min_value=date(1930, 1, 1),
                max_value=date.today(),
                value=None,
                format="DD/MM/YYYY"
            )
            
        with col2:
            profissao = st.text_input("Profissão", placeholder="Profissão atual")
            como_chegou = st.selectbox("Como chegou até nós", 
                                     ["Indicação", "Internet", "Redes Sociais", "Outro"])
            queixa_principal = st.text_area("Queixa Principal", 
                                          placeholder="Descreva a queixa principal (opcional)...", 
                                          height=100)
        
        medicacoes = st.text_input("Medicações Atuais", placeholder="Medicações em uso")
        observacoes = st.text_area("Observações Iniciais", 
                                 placeholder="Observações relevantes...",
                                 height=80)
        
        st.caption("* Campos obrigatórios: Nome Completo e Telefone")
        
        if st.form_submit_button("💾 Salvar Paciente"):
            if nome and telefone:
                try:
                    conn = conectar_banco()
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
                    st.success("✅ Paciente cadastrado com sucesso!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Erro ao salvar: {e}")
                finally:
                    if conn:
                        conn.close()
            else:
                st.error("❌ Preencha os campos obrigatórios: Nome Completo e Telefone")

# 2. MARCAR CONSULTA - CORREÇÃO DA LÓGICA DE DATA/HORA
elif menu == "📅 Marcar Consulta":
    st.header("📅 Marcar Nova Consulta")
    
    try:
        conn = conectar_banco()
        if conn is None:
            st.error("❌ Não foi possível conectar ao banco de dados")
            st.stop()
            
        pacientes_df = pd.read_sql("SELECT id, nome_completo FROM pacientes WHERE ativo = TRUE ORDER BY nome_completo", conn)
        
        if pacientes_df.empty:
            st.warning("⚠️ Cadastre pacientes primeiro!")
        else:
            with st.form("form_consulta", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    paciente_nome = st.selectbox("Paciente*", pacientes_df['nome_completo'])
                    data_consulta = st.date_input("Data*", min_value=date.today())
                    
                    # 1. Gerar todos os horários padrão (8h às 20h)
                    todos_horarios = []
                    for hora in range(8, 21):
                        for minuto in [0, 30]:
                            if hora == 20 and minuto > 0:
                                continue
                            todos_horarios.append(time(hora, minuto))
                    
                    # 2. Determinar horários permitidos baseados na data selecionada
                    agora_utc = datetime.utcnow()
                    agora_cv = agora_utc - timedelta(hours=1)
                    hoje_cv = agora_cv.date()
                    hora_cv = agora_cv.time()

                    horarios_permitidos = []
                    
                    # Se a data selecionada for HOJE, filtra apenas horários futuros
                    if data_consulta == hoje_cv:
                        for h in todos_horarios:
                            if h > hora_cv:
                                horarios_permitidos.append(h)
                    # Se for AMANHÃ ou qualquer dia futuro, permite TODOS os horários da grade
                    else:
                        horarios_permitidos = todos_horarios

                    # 3. Remover horários já ocupados no banco de dados
                    horarios_livres = []
                    cur = conn.cursor()
                    for horario in horarios_permitidos:
                        data_hora = datetime.combine(data_consulta, horario)
                        cur.execute(
                            "SELECT id FROM consultas WHERE data_consulta = %s AND status IN ('agendada', 'realizada')",
                            (data_hora,)
                        )
                        if cur.fetchone() is None:
                            horarios_livres.append(horario)
                    
                    if horarios_livres:
                        hora_consulta = st.selectbox(
                            "Horário*", 
                            horarios_livres,
                            format_func=lambda x: x.strftime('%H:%M')
                        )
                    else:
                        st.error("❌ Não há horários disponíveis para esta data!")
                        hora_consulta = None
                
                with col2:
                    primeira_consulta = st.checkbox("Primeira Consulta", value=True)
                    valor_consulta = st.number_input("Valor da Consulta (CVE)", 
                                                   min_value=0.0, 
                                                   value=2500.0 if primeira_consulta else 2000.0,
                                                   step=100.0,
                                                   format="%.0f")
                    forma_pagamento = st.selectbox("Forma de Pagamento", 
                                                 ["Dinheiro", "Transferência", "MB Way", "Cartão", "Outro"])
                
                observacoes = st.text_area("Observações Técnicas")
                
                if st.form_submit_button("📅 Agendar Consulta"):
                    if hora_consulta is None:
                        st.error("❌ Selecione um horário válido!")
                    else:
                        data_hora = datetime.combine(data_consulta, hora_consulta)
                        
                        cur.execute(
                            "SELECT id FROM consultas WHERE data_consulta = %s AND status IN ('agendada', 'realizada')",
                            (data_hora,)
                        )
                        
                        if cur.fetchone() is not None:
                            st.error("❌ Este horário acabou de ser ocupado! Escolha outro.")
                        else:
                            paciente_row = pacientes_df[pacientes_df['nome_completo'] == paciente_nome].iloc[0]
                            paciente_id = converter_numpy_para_python(paciente_row['id'])
                            
                            cur.execute(
                                """INSERT INTO consultas 
                                (paciente_id, data_consulta, primeira_consulta, valor_consulta, 
                                 forma_pagamento, observacoes_tecnicas) 
                                VALUES (%s, %s, %s, %s, %s, %s)""",
                                (paciente_id, data_hora, primeira_consulta, valor_consulta, 
                                 forma_pagamento, observacoes)
                            )
                            conn.commit()
                            st.success(f"✅ Consulta marcada para {data_consulta.strftime('%d/%m/%Y')} às {hora_consulta.strftime('%H:%M')}")
                            st.balloons()
                    
    except Exception as e:
        st.error(f"❌ Erro: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# 3. VER PACIENTES
elif menu == "👥 Ver Pacientes":
    st.header("👥 Lista de Pacientes")
    
    try:
        conn = conectar_banco()
        if conn is None:
            st.error("❌ Não foi possível conectar ao banco de dados")
            st.stop()
            
        pacientes_df = pd.read_sql("""
            SELECT 
                nome_completo as "Nome",
                telefone as "Telefone",
                email as "Email",
                profissao as "Profissão",
                TO_CHAR(data_nascimento, 'DD/MM/YYYY') as "Nascimento",
                queixa_principal as "Queixa Principal",
                TO_CHAR(data_cadastro, 'DD/MM/YYYY') as "Cadastro"
            FROM pacientes 
            WHERE ativo = TRUE
            ORDER BY nome_completo
        """, conn)
        
        if not pacientes_df.empty:
            st.dataframe(pacientes_df, use_container_width=True)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total de Pacientes", len(pacientes_df))
            with col2:
                hoje_cv = (datetime.utcnow() - timedelta(hours=1)).date()
                primeiro_dia_mes = hoje_cv.replace(day=1)
                cadastros_mes = 0
                for data_str in pacientes_df['Cadastro']:
                    try:
                        data_obj = datetime.strptime(data_str, '%d/%m/%Y').date()
                        if data_obj >= primeiro_dia_mes:
                            cadastros_mes += 1
                    except:
                        pass
                st.metric("Cadastros este Mês", cadastros_mes)
        else:
            st.info("📝 Nenhum paciente cadastrado")
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar pacientes: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# 4. AGENDA DA SEMANA
elif menu == "🗓️ Agenda da Semana":
    st.header("🗓️ Agenda de Consultas")
    
    opcao_agenda = st.radio("Visualizar:", ["Hoje", "Amanhã", "Próximos 7 Dias"], horizontal=True)
    
    try:
        conn = conectar_banco()
        if conn is None:
            st.error("❌ Não foi possível conectar ao banco de dados")
            st.stop()
            
        if opcao_agenda == "Hoje":
            agenda_df = pd.read_sql("""
                SELECT c.id, p.nome_completo, c.data_consulta, 
                       CASE WHEN c.primeira_consulta THEN 'Primeira' ELSE 'Retorno' END as tipo,
                       c.status, c.valor_consulta,
                       c.forma_pagamento
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE DATE(c.data_consulta AT TIME ZONE 'UTC-1') = CURRENT_DATE
                ORDER BY c.data_consulta
            """, conn)
        elif opcao_agenda == "Amanhã":
            agenda_df = pd.read_sql("""
                SELECT c.id, p.nome_completo, c.data_consulta, 
                       CASE WHEN c.primeira_consulta THEN 'Primeira' ELSE 'Retorno' END as tipo,
                       c.status, c.valor_consulta,
                       c.forma_pagamento
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE DATE(c.data_consulta AT TIME ZONE 'UTC-1') = CURRENT_DATE + INTERVAL '1 day'
                ORDER BY c.data_consulta
            """, conn)
        else:
            agenda_df = pd.read_sql("""
                SELECT c.id, p.nome_completo, c.data_consulta, 
                       CASE WHEN c.primeira_consulta THEN 'Primeira' ELSE 'Retorno' END as tipo,
                       c.status, c.valor_consulta,
                       c.forma_pagamento
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE (c.data_consulta AT TIME ZONE 'UTC-1') BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
                ORDER BY c.data_consulta
            """, conn)
        
        if not agenda_df.empty:
            col_header1, col_header2, col_header3, col_header4, col_header5 = st.columns([3, 1, 1, 1, 1])
            with col_header1: st.markdown("**Paciente**")
            with col_header2: st.markdown("**Horário**")
            with col_header3: st.markdown("**Tipo**")
            with col_header4: st.markdown("**Status**")
            with col_header5: st.markdown("**Ações**")
            
            st.divider()
            
            for _, row in agenda_df.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                    with col1: st.write(f"**{row['nome_completo']}**")
                    with col2: st.write(f"🕐 {row['data_consulta'].strftime('%H:%M')}")
                    with col3: st.write(f"📝 {row['tipo']}")
                    with col4:
                        status_color = {'agendada': 'blue', 'realizada': 'green', 'cancelada': 'red', 'falta': 'orange'}.get(row['status'], 'gray')
                        st.markdown(f"<span style='color:{status_color}'>{row['status'].title()}</span>", unsafe_allow_html=True)
                    
                    with col5:
                        if row['status'] == 'agendada':
                            consulta_id = converter_numpy_para_python(row['id'])
                            if st.button(f"❌ Cancelar", key=f"cancel_{consulta_id}", use_container_width=True):
                                cur = conn.cursor()
                                cur.execute("UPDATE consultas SET status = 'cancelada' WHERE id = %s", (consulta_id,))
                                conn.commit()
                                st.rerun()
                        else:
                            st.write("—")
                    
                    st.caption(f"💰 {converter_numpy_para_python(row['valor_consulta']):,.0f} CVE")
                    st.divider()
        else:
            st.info("📅 Nenhuma consulta agendada para o período selecionado")
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar agenda: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# 5. REGISTRAR CONSULTA REALIZADA
elif menu == "✅ Registrar Consulta Realizada":
    st.header("✅ Registrar Consulta Realizada")
    
    try:
        conn = conectar_banco()
        if conn is None:
            st.error("❌ Não foi possível conectar ao banco de dados")
            st.stop()
            
        consultas_df = pd.read_sql("""
            SELECT c.id, p.nome_completo, c.data_consulta, c.valor_consulta,
                   c.pagamento_realizado, c.status
            FROM consultas c
            JOIN pacientes p ON c.paciente_id = p.id
            WHERE c.status = 'agendada' AND c.data_consulta <= CURRENT_TIMESTAMP + INTERVAL '1 day'
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
            """)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Realizada", type="primary", use_container_width=True):
                    cur = conn.cursor()
                    cur.execute("UPDATE consultas SET status = 'realizada' WHERE id = %s", (converter_numpy_para_python(consulta_info['id']),))
                    conn.commit()
                    st.rerun()
            with col2:
                if st.button("❌ Não compareceu", type="secondary", use_container_width=True):
                    cur = conn.cursor()
                    cur.execute("UPDATE consultas SET status = 'falta' WHERE id = %s", (converter_numpy_para_python(consulta_info['id']),))
                    conn.commit()
                    st.rerun()
            with col3:
                if not consulta_info['pagamento_realizado']:
                    if st.button("💰 Pagamento", use_container_width=True):
                        cur = conn.cursor()
                        cur.execute("UPDATE consultas SET pagamento_realizado = TRUE WHERE id = %s", (converter_numpy_para_python(consulta_info['id']),))
                        conn.commit()
                        st.rerun()
        else:
            st.info("📝 Nenhuma consulta agendada para registrar")
            
    except Exception as e:
        st.error(f"❌ Erro ao registrar consulta: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# 6. ESTATÍSTICAS
elif menu == "📊 Estatísticas":
    st.header("📊 Estatísticas do Consultório")
    
    try:
        conn = conectar_banco()
        if conn is None:
            st.error("❌ Não foi possível conectar ao banco de dados")
            st.stop()
            
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_pacientes = pd.read_sql("SELECT COUNT(*) as total FROM pacientes WHERE ativo = TRUE", conn)
            st.metric("Total de Pacientes", converter_numpy_para_python(total_pacientes.iloc[0]['total']))
        
        with col2:
            consultas_mes = pd.read_sql("""
                SELECT COUNT(*) as total FROM consultas 
                WHERE EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM CURRENT_DATE)
            """, conn)
            st.metric("Consultas este Mês", converter_numpy_para_python(consultas_mes.iloc[0]['total']))
        
        with col3:
            receita_mes = pd.read_sql("""
                SELECT COALESCE(SUM(valor_consulta), 0) as total FROM consultas 
                WHERE status = 'realizada' AND EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM CURRENT_DATE)
            """, conn)
            st.metric("Receita do Mês (CVE)", f"{converter_numpy_para_python(receita_mes.iloc[0]['total']):,.0f}")
        
        with col4:
            taxa_falta = pd.read_sql("""
                SELECT ROUND(COUNT(CASE WHEN status = 'falta' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 1) as taxa
                FROM consultas WHERE EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM CURRENT_DATE)
            """, conn)
            taxa_v = converter_numpy_para_python(taxa_falta.iloc[0]['taxa']) if not pd.isna(taxa_falta.iloc[0]['taxa']) else 0
            st.metric("Taxa de Faltas (%)", f"{taxa_v}")
            
    except Exception as e:
        st.error(f"❌ Erro: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# RODAPÉ
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 10px;'>"
    "🧠 <b>Psicare by Belinda Viana</b> - Consultório de Psicologia | "
    "📞 Contacto: +238 5949955 | "
    "📧 Email: contato@atendimentoviana.cv"
    "</div>", 
    unsafe_allow_html=True
)