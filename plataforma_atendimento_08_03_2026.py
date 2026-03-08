import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
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

# --- FUNÇÃO PARA VERIFICAR HORÁRIO DE AULA ---
def eh_horario_de_aula(data_consulta, hora_consulta):
    """
    Verifica se o horário específico é de aula
    Retorna True se for horário de aula, False caso contrário
    """
    dia_semana = data_consulta.weekday()  # 0=Segunda, 1=Terça, 2=Quarta, 3=Quinta, 4=Sexta
    
    # Converter hora para minutos
    minutos = hora_consulta.hour * 60 + hora_consulta.minute
    
    # Segunda-feira: 14:00 às 20:00
    if dia_semana == 0:
        if minutos >= 14*60 and minutos < 20*60:
            return True
    
    # Terça-feira: 9:30 às 11:10
    elif dia_semana == 1:
        if minutos >= 9*60+30 and minutos < 11*60+10:
            return True
    
    # Quinta-feira: 14:00 às 18:00
    elif dia_semana == 3:
        if minutos >= 14*60 and minutos < 18*60:
            return True
    
    # Sexta-feira: 7:30 às 9:30
    elif dia_semana == 4:
        if minutos >= 7*60+30 and minutos < 9*60+30:
            return True
    
    return False

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
st.markdown("<h1 style='text-align: center; color: #1f77b4;'>🧠 ATENDIMENTO VIANA - CONSULTÓRIO DE PSICOLOGIA</h1>", unsafe_allow_html=True)
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

# Informações de horários no sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 Horários de Aula (bloqueados)")
st.sidebar.info(
    "• Segunda: 14:00-20:00\n"
    "• Terça: 9:30-11:10\n"
    "• Quinta: 14:00-18:00\n"
    "• Sexta: 7:30-9:30"
)

# 1. CADASTRAR PACIENTE
if menu == "➕ Cadastrar Paciente":
    st.header("👤 Cadastrar Novo Paciente")
    
    with st.form("form_paciente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome Completo*", placeholder="Nome completo do paciente")
            telefone = st.text_input("Telefone*", placeholder="+238 XXX XX XX") 
            email = st.text_input("Email", placeholder="paciente@email.cv")
            
            # CORREÇÃO: Data de nascimento desde 1930
            data_nascimento = st.date_input(
                "Data de Nascimento", 
                min_value=date(1930, 1, 1),  # Permite anos desde 1930
                max_value=date.today(),
                value=None,  # Sem valor padrão
                format="DD/MM/YYYY"
            )
            
        with col2:
            profissao = st.text_input("Profissão", placeholder="Ex: Professor, Advogado...")
            como_chegou = st.selectbox("Como chegou até nós", 
                                     ["Indicação", "Internet", "Redes Sociais", "Outro"])
            queixa_principal = st.text_area("Queixa Principal*", height=100, placeholder="Descreva a queixa principal...")
        
        medicacoes = st.text_input("Medicações Atuais", placeholder="Medicações em uso...")
        observacoes = st.text_area("Observações Iniciais", height=80, placeholder="Observações relevantes...")
        
        if st.form_submit_button("💾 Salvar Paciente", type="primary"):
            if nome and telefone and queixa_principal:
                try:
                    with engine.connect() as conn:
                        conn.execute(text("""
                            INSERT INTO pacientes 
                            (nome_completo, telefone, email, data_nascimento, profissao, 
                             como_chegou, queixa_principal, medicacoes_atuais, observacoes_iniciais) 
                            VALUES (:n, :t, :e, :d, :p, :c, :q, :m, :o)
                        """), {
                            "n": nome, 
                            "t": telefone, 
                            "e": email, 
                            "d": data_nascimento, 
                            "p": profissao, 
                            "c": como_chegou, 
                            "q": queixa_principal, 
                            "m": medicacoes, 
                            "o": observacoes
                        })
                        conn.commit()
                    st.success("✅ Paciente cadastrado com sucesso!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Erro: {e}")
            else:
                st.error("❌ Preencha os campos obrigatórios (*)")

# 2. MARCAR CONSULTA
elif menu == "📅 Marcar Consulta":
    st.header("📅 Marcar Nova Consulta")
    
    try:
        pacientes_df = pd.read_sql("SELECT id, nome_completo FROM pacientes WHERE ativo = TRUE ORDER BY nome_completo", engine)
        
        if pacientes_df.empty:
            st.warning("⚠️ Cadastre pacientes primeiro!")
        else:
            with st.form("form_consulta", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    paciente_nome = st.selectbox("Paciente*", pacientes_df['nome_completo'])
                    data_consulta = st.date_input("Data*", min_value=date.today())
                    
                    # CORREÇÃO: Gerar horários disponíveis (excluindo aulas)
                    dia_semana = data_consulta.weekday()
                    
                    # Gerar todos os horários possíveis (8h às 20h, de 30 em 30 min)
                    todos_horarios = []
                    for hora in range(8, 21):
                        for minuto in [0, 30]:
                            if hora == 20 and minuto > 0:
                                continue
                            todos_horarios.append(time(hora, minuto))
                    
                    # Filtrar apenas os que NÃO são horários de aula
                    horarios_disponiveis = []
                    for horario in todos_horarios:
                        if not eh_horario_de_aula(data_consulta, horario):
                            horarios_disponiveis.append(horario)
                    
                    # Verificar horários já ocupados no banco
                    horarios_livres = []
                    horarios_ocupados = []
                    
                    for horario in horarios_disponiveis:
                        data_hora = datetime.combine(data_consulta, horario)
                        with engine.connect() as conn:
                            result = conn.execute(
                                text("SELECT id FROM consultas WHERE data_consulta = :dt AND status IN ('agendada', 'realizada')"),
                                {"dt": data_hora}
                            ).fetchone()
                            if result is None:
                                horarios_livres.append(horario)
                            else:
                                horarios_ocupados.append(horario)
                    
                    # Mostrar estatísticas
                    col_info1, col_info2, col_info3 = st.columns(3)
                    with col_info1:
                        st.metric("Horários disponíveis", len(horarios_livres))
                    with col_info2:
                        st.metric("Horários de aula", len(todos_horarios) - len(horarios_disponiveis))
                    with col_info3:
                        st.metric("Já agendados", len(horarios_ocupados))
                    
                    # Selecionar horário
                    if not horarios_livres:
                        st.error("❌ Não há horários disponíveis para esta data!")
                        hora_consulta = None
                    else:
                        hora_consulta = st.selectbox(
                            "Horário*", 
                            horarios_livres,
                            format_func=lambda x: x.strftime('%H:%M')
                        )
                    
                    # Aviso sobre horários de aula
                    if dia_semana == 0:
                        st.warning("⚠️ Segunda-feira: Horários das 14h às 20h são de AULA (bloqueados)")
                    elif dia_semana == 1:
                        st.warning("⚠️ Terça-feira: Horários das 9:30 às 11:10 são de AULA (bloqueados)")
                    elif dia_semana == 3:
                        st.warning("⚠️ Quinta-feira: Horários das 14h às 18h são de AULA (bloqueados)")
                    elif dia_semana == 4:
                        st.warning("⚠️ Sexta-feira: Horários das 7:30 às 9:30 são de AULA (bloqueados)")
                
                with col2:
                    primeira_consulta = st.checkbox("Primeira Consulta", value=True)
                    valor_consulta = st.number_input(
                        "Valor da Consulta (CVE)", 
                        min_value=0.0, 
                        value=2500.0 if primeira_consulta else 2000.0,
                        step=100.0,
                        format="%.0f"
                    )
                    forma_pagamento = st.selectbox("Forma de Pagamento", 
                                                 ["Dinheiro", "Transferência", "MB Way", "Cartão", "Outro"])
                
                observacoes = st.text_area("Observações Técnicas", height=100)
                
                if st.form_submit_button("📅 Agendar Consulta", type="primary"):
                    if hora_consulta is None:
                        st.error("❌ Selecione um horário válido!")
                    else:
                        # Verificações finais
                        if eh_horario_de_aula(data_consulta, hora_consulta):
                            st.error("❌ Este é um horário de aula! Escolha outro horário.")
                            st.stop()
                        
                        data_hora = datetime.combine(data_consulta, hora_consulta)
                        
                        # Verificar se horário ainda está livre
                        with engine.connect() as conn:
                            result = conn.execute(
                                text("SELECT id FROM consultas WHERE data_consulta = :dt AND status IN ('agendada', 'realizada')"),
                                {"dt": data_hora}
                            ).fetchone()
                            
                            if result is not None:
                                st.error("❌ Este horário já está ocupado! Escolha outro.")
                                st.stop()
                            
                            # Inserir consulta
                            paciente_id = int(pacientes_df[pacientes_df['nome_completo'] == paciente_nome].iloc[0]['id'])
                            
                            conn.execute(text("""
                                INSERT INTO consultas 
                                (paciente_id, data_consulta, primeira_consulta, valor_consulta, 
                                 forma_pagamento, observacoes_tecnicas) 
                                VALUES (:id, :dt, :pr, :vl, :fm, :obs)
                            """), {
                                "id": paciente_id,
                                "dt": data_hora,
                                "pr": primeira_consulta,
                                "vl": valor_consulta,
                                "fm": forma_pagamento,
                                "obs": observacoes
                            })
                            conn.commit()
                        
                        st.success(f"✅ Consulta marcada para {data_consulta.strftime('%d/%m/%Y')} às {hora_consulta.strftime('%H:%M')}")
                        st.balloons()
                        
    except Exception as e:
        st.error(f"❌ Erro: {e}")

# 3. VER PACIENTES
elif menu == "👥 Ver Pacientes":
    st.header("👥 Lista de Pacientes")
    
    try:
        df = pd.read_sql("""
            SELECT 
                nome_completo as "Nome",
                telefone as "Telefone",
                email as "Email",
                profissao as "Profissão",
                TO_CHAR(data_nascimento, 'DD/MM/YYYY') as "Nascimento",
                TO_CHAR(data_cadastro, 'DD/MM/YYYY') as "Cadastro"
            FROM pacientes 
            WHERE ativo = TRUE 
            ORDER BY nome_completo
        """, engine)
        
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.metric("Total de Pacientes", len(df))
        else:
            st.info("📝 Nenhum paciente cadastrado")
            
    except Exception as e:
        st.error(f"❌ Erro: {e}")

# 4. AGENDA
elif menu == "🗓️ Agenda":
    st.header("🗓️ Agenda de Consultas")
    
    opcao = st.radio("Visualizar:", ["Hoje", "Próximos 7 dias", "Todas"], horizontal=True)
    
    try:
        if opcao == "Hoje":
            query = """
                SELECT 
                    p.nome_completo as "Paciente",
                    TO_CHAR(c.data_consulta, 'HH24:MI') as "Horário",
                    CASE WHEN c.primeira_consulta THEN 'Primeira' ELSE 'Retorno' END as "Tipo",
                    c.status as "Status",
                    c.valor_consulta as "Valor"
                FROM consultas c 
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE DATE(c.data_consulta) = CURRENT_DATE
                ORDER BY c.data_consulta
            """
        elif opcao == "Próximos 7 dias":
            query = """
                SELECT 
                    p.nome_completo as "Paciente",
                    TO_CHAR(c.data_consulta, 'DD/MM HH24:MI') as "Data/Hora",
                    CASE WHEN c.primeira_consulta THEN 'Primeira' ELSE 'Retorno' END as "Tipo",
                    c.status as "Status",
                    c.valor_consulta as "Valor"
                FROM consultas c 
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE c.data_consulta BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
                ORDER BY c.data_consulta
            """
        else:
            query = """
                SELECT 
                    p.nome_completo as "Paciente",
                    TO_CHAR(c.data_consulta, 'DD/MM/YYYY HH24:MI') as "Data/Hora",
                    CASE WHEN c.primeira_consulta THEN 'Primeira' ELSE 'Retorno' END as "Tipo",
                    c.status as "Status",
                    c.valor_consulta as "Valor"
                FROM consultas c 
                JOIN pacientes p ON c.paciente_id = p.id
                ORDER BY c.data_consulta DESC
                LIMIT 50
            """
        
        df = pd.read_sql(query, engine)
        
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            
            # Resumo
            total = len(df)
            realizadas = len(df[df['Status'] == 'realizada'])
            st.metric("Total de Consultas", total, f"{realizadas} realizadas")
        else:
            st.info("📅 Nenhuma consulta encontrada")
            
    except Exception as e:
        st.error(f"❌ Erro: {e}")

# 5. REGISTRAR CONSULTA
elif menu == "✅ Registrar Consulta":
    st.header("✅ Registrar Consulta Realizada")
    
    try:
        consultas_df = pd.read_sql("""
            SELECT 
                c.id, 
                p.nome_completo, 
                c.data_consulta,
                c.valor_consulta,
                c.pagamento_realizado
            FROM consultas c 
            JOIN pacientes p ON c.paciente_id = p.id 
            WHERE c.status = 'agendada' 
            ORDER BY c.data_consulta
        """, engine)
        
        if not consultas_df.empty:
            consultas_df['display'] = consultas_df['nome_completo'] + " - " + consultas_df['data_consulta'].dt.strftime('%d/%m/%Y %H:%M')
            selecao = st.selectbox("Selecione a consulta:", consultas_df['display'])
            
            consulta_info = consultas_df[consultas_df['display'] == selecao].iloc[0]
            
            st.info(f"""
            **Detalhes:**
            - **Paciente:** {consulta_info['nome_completo']}
            - **Data/Hora:** {consulta_info['data_consulta'].strftime('%d/%m/%Y %H:%M')}
            - **Valor:** {float(consulta_info['valor_consulta']):,.0f} CVE
            - **Pagamento:** {'✅ Pago' if consulta_info['pagamento_realizado'] else '⏳ Pendente'}
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Marcar como Realizada", type="primary"):
                    c_id = int(consulta_info['id'])
                    with engine.connect() as conn:
                        conn.execute(text("UPDATE consultas SET status = 'realizada' WHERE id = :id"), {"id": c_id})
                        conn.commit()
                    st.success("✅ Consulta registrada!")
                    st.rerun()
            
            with col2:
                if not consulta_info['pagamento_realizado']:
                    if st.button("💰 Registrar Pagamento"):
                        c_id = int(consulta_info['id'])
                        with engine.connect() as conn:
                            conn.execute(text("UPDATE consultas SET pagamento_realizado = TRUE WHERE id = :id"), {"id": c_id})
                            conn.commit()
                        st.success("💰 Pagamento registrado!")
                        st.rerun()
        else:
            st.info("📝 Nenhuma consulta agendada")
            
    except Exception as e:
        st.error(f"❌ Erro: {e}")

# 6. ESTATÍSTICAS
elif menu == "📊 Estatísticas":
    st.header("📊 Estatísticas do Consultório")
    
    try:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total = pd.read_sql("SELECT COUNT(*) as total FROM pacientes WHERE ativo = TRUE", engine)
            st.metric("Total de Pacientes", int(total.iloc[0]['total']))
        
        with col2:
            consultas_mes = pd.read_sql("""
                SELECT COUNT(*) as total 
                FROM consultas 
                WHERE EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM CURRENT_DATE)
            """, engine)
            st.metric("Consultas este Mês", int(consultas_mes.iloc[0]['total']))
        
        with col3:
            receita_mes = pd.read_sql("""
                SELECT COALESCE(SUM(valor_consulta), 0) as total 
                FROM consultas 
                WHERE status = 'realizada' 
                AND EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM CURRENT_DATE)
            """, engine)
            st.metric("Receita do Mês (CVE)", f"{float(receita_mes.iloc[0]['total']):,.0f}")
        
        with col4:
            taxa_falta = pd.read_sql("""
                SELECT 
                    COUNT(CASE WHEN status = 'falta' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as taxa
                FROM consultas 
                WHERE EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM CURRENT_DATE)
            """, engine)
            taxa = float(taxa_falta.iloc[0]['taxa']) if not pd.isna(taxa_falta.iloc[0]['taxa']) else 0
            st.metric("Taxa de Faltas", f"{taxa:.1f}%")
        
        # Gráfico de status
        st.subheader("📊 Consultas por Status (Este Mês)")
        status_df = pd.read_sql("""
            SELECT status, COUNT(*) as quantidade
            FROM consultas
            WHERE EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM CURRENT_DATE)
            GROUP BY status
        """, engine)
        
        if not status_df.empty:
            st.bar_chart(status_df.set_index('status'))
        else:
            st.info("📊 Sem dados para o mês atual")
            
    except Exception as e:
        st.error(f"❌ Erro: {e}")

# RODAPÉ
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 10px;'>"
    "🧠 <b>Atendimento Viana</b> - Consultório de Psicologia | "
    "📞 Contacto: +238 953 67 33 | "
    "🌐 <a href='http://www.atendimentoviana.cv' target='_blank'>www.atendimentoviana.cv</a><br>"
    "<small>✅ Data de nascimento desde 1930 | ✅ Horários de aula bloqueados</small>"
    "</div>", 
    unsafe_allow_html=True
)
