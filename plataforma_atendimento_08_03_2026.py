import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime, date, time, timedelta
import os
import numpy as np
import warnings
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

# CORREÇÃO 2: Função para verificar horários de aula (Cabo Verde - UTC-1)
def eh_horario_de_aula(data_consulta, hora_consulta):
    """
    Verifica se o horário específico é de aula (Cabo Verde)
    Retorna True se for horário de aula, False caso contrário
    """
    dia_semana = data_consulta.weekday()  # 0=Segunda, 1=Terça, 2=Quarta, 3=Quinta, 4=Sexta
    
    # Converter hora para minutos
    minutos = hora_consulta.hour * 60 + hora_consulta.minute
    
    # SEGUNDA-FEIRA: 14:00 às 20:00
    if dia_semana == 0:
        if minutos >= 14*60 and minutos < 20*60:  # 14:00 até 19:59
            return True
        if minutos == 20*60:  # 20:00 exato
            return True
    
    # TERÇA-FEIRA: 9:30 às 11:10
    elif dia_semana == 1:
        if minutos >= 9*60+30 and minutos <= 11*60+10:  # 9:30 até 11:10
            return True
    
    # QUINTA-FEIRA: 14:00 às 18:00
    elif dia_semana == 3:
        if minutos >= 14*60 and minutos < 18*60:  # 14:00 até 17:59
            return True
    
    # SEXTA-FEIRA: 7:30 às 9:30
    elif dia_semana == 4:
        if minutos >= 7*60+30 and minutos < 9*60+30:  # 7:30 até 9:29
            return True
    
    return False

# Configuração da página
st.set_page_config(
    page_title="Atendimento Viana - Psicologia", 
    page_icon="🧠",
    layout="wide"
)

# Conexão com Supabase (via Session Pooler) - VERSÃO SEGURA
def conectar_banco():
    """Conecta ao Supabase usando Session Pooler - APENAS via secrets"""
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
if inicializar_banco():
    st.sidebar.success("✅ Conectado ao Supabase")
else:
    st.sidebar.error("❌ Falha na conexão com Supabase")

# Função para obter hora atual de Cabo Verde (UTC-1)
def hora_cv_agora():
    """Retorna a data e hora atual em Cabo Verde (UTC-1)"""
    utc_agora = datetime.utcnow()
    cv_agora = utc_agora - timedelta(hours=1)  # Cabo Verde é UTC-1
    return cv_agora

# Informações de horários no sidebar (APENAS AQUI - removido do layout principal)
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 Horários de Aula (Cabo Verde)")
st.sidebar.info(
    "**Horários bloqueados:**\n"
    "• Segunda: 14:00 às 20:00\n"
    "• Terça: 9:30 às 11:10\n"
    "• Quinta: 14:00 às 18:00\n"
    "• Sexta: 7:30 às 9:30\n\n"
    f"**Hora atual em CV:**\n"
    f"{hora_cv_agora().strftime('%d/%m/%Y %H:%M')}"
)

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
            
            # Data de nascimento desde 1930
            data_nascimento = st.date_input(
                "Data de Nascimento", 
                min_value=date(1930, 1, 1),  # Permite anos desde 1930
                max_value=date.today(),
                value=None,  # Sem valor padrão
                format="DD/MM/YYYY"
            )
            
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
        
        if st.form_submit_button("💾 Salvar Paciente"):
            if nome and telefone and queixa_principal:
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
                st.error("❌ Preencha os campos obrigatórios (*)")

# 2. MARCAR CONSULTA
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
                    
                    # Gerar horários de 30 em 30 minutos
                    todos_horarios = []
                    for hora in range(8, 21):  # 8h às 20h
                        for minuto in [0, 30]:
                            if hora == 20 and minuto > 0:
                                continue
                            horario = time(hora, minuto)
                            todos_horarios.append(horario)
                    
                    # Filtrar apenas horários que NÃO são de aula
                    horarios_disponiveis = []
                    horarios_bloqueados = []
                    
                    for horario in todos_horarios:
                        if eh_horario_de_aula(data_consulta, horario):
                            horarios_bloqueados.append(horario)
                        else:
                            horarios_disponiveis.append(horario)
                    
                    # Verificar horários já ocupados
                    horarios_livres = []
                    horarios_ocupados = []
                    
                    for horario in horarios_disponiveis:
                        data_hora = datetime.combine(data_consulta, horario)
                        cur = conn.cursor()
                        cur.execute(
                            "SELECT id FROM consultas WHERE data_consulta = %s AND status IN ('agendada', 'realizada')",
                            (data_hora,)
                        )
                        if cur.fetchone() is None:
                            horarios_livres.append(horario)
                        else:
                            horarios_ocupados.append(horario)
                    
                    # Mostrar informações de disponibilidade
                    dia_semana = data_consulta.weekday()
                    
                    if dia_semana == 0:
                        st.warning(f"⚠️ Segunda-feira: {len(horarios_bloqueados)} horários bloqueados (14:00-20:00)")
                    elif dia_semana == 1:
                        st.warning(f"⚠️ Terça-feira: {len(horarios_bloqueados)} horários bloqueados (9:30-11:10)")
                    elif dia_semana == 3:
                        st.warning(f"⚠️ Quinta-feira: {len(horarios_bloqueados)} horários bloqueados (14:00-18:00)")
                    elif dia_semana == 4:
                        st.warning(f"⚠️ Sexta-feira: {len(horarios_bloqueados)} horários bloqueados (7:30-9:30)")
                    
                    # Mostrar lista de horários disponíveis
                    if horarios_livres:
                        hora_consulta = st.selectbox(
                            "Horário*", 
                            horarios_livres,
                            format_func=lambda x: x.strftime('%H:%M')
                        )
                        
                        # Mostrar horários bloqueados em texto menor
                        if horarios_bloqueados:
                            horarios_bloq_str = ", ".join([h.strftime('%H:%M') for h in horarios_bloqueados])
                            st.caption(f"🚫 Horários de aula bloqueados: {horarios_bloq_str}")
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
                        # Verificação final
                        if eh_horario_de_aula(data_consulta, hora_consulta):
                            st.error("❌ Este é um horário de aula! Escolha outro horário.")
                            st.stop()
                        
                        data_hora = datetime.combine(data_consulta, hora_consulta)
                        
                        # Verificar se horário já está ocupado
                        cur.execute(
                            "SELECT id FROM consultas WHERE data_consulta = %s AND status IN ('agendada', 'realizada')",
                            (data_hora,)
                        )
                        
                        if cur.fetchone() is not None:
                            st.error("❌ Este horário já está ocupado! Escolha outro.")
                            st.stop()
                        
                        # Inserir consulta
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
                        st.success(f"✅ Consulta marcada para {data_consulta.strftime('%d/%m/%Y')} às {hora_consulta.strftime('%H:%M')} (CVT)")
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
            SELECT id, nome_completo, telefone, email, profissao, queixa_principal, 
                   TO_CHAR(data_cadastro, 'DD/MM/YYYY') as data_cadastro,
                   TO_CHAR(data_nascimento, 'DD/MM/YYYY') as data_nascimento
            FROM pacientes 
            WHERE ativo = TRUE
            ORDER BY nome_completo
        """, conn)
        
        if not pacientes_df.empty:
            st.dataframe(pacientes_df, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Pacientes", len(pacientes_df))
            with col2:
                from datetime import datetime
                primeiro_dia_mes = datetime.now().replace(day=1)
                
                cadastros_mes = 0
                for data_str in pacientes_df['data_cadastro']:
                    try:
                        data_obj = datetime.strptime(data_str, '%d/%m/%Y')
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
    
    opcao_agenda = st.radio("Visualizar:", ["Dia Específico", "Próximos 7 Dias"], horizontal=True)
    
    try:
        conn = conectar_banco()
        if conn is None:
            st.error("❌ Não foi possível conectar ao banco de dados")
            st.stop()
            
        if opcao_agenda == "Dia Específico":
            data_selecionada = st.date_input("Selecione a data:", value=date.today())
            
            agenda_df = pd.read_sql("""
                SELECT p.nome_completo, c.data_consulta, 
                       CASE WHEN c.primeira_consulta THEN 'Primeira' ELSE 'Retorno' END as tipo,
                       c.status, c.valor_consulta,
                       c.forma_pagamento
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE DATE(c.data_consulta) = %s
                ORDER BY c.data_consulta
            """, conn, params=(data_selecionada,))
        else:
            agenda_df = pd.read_sql("""
                SELECT p.nome_completo, c.data_consulta, 
                       CASE WHEN c.primeira_consulta THEN 'Primeira' ELSE 'Retorno' END as tipo,
                       c.status, c.valor_consulta,
                       c.forma_pagamento
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE c.data_consulta BETWEEN NOW() AND NOW() + INTERVAL '7 days'
                ORDER BY c.data_consulta
            """, conn)
        
        if not agenda_df.empty:
            for _, row in agenda_df.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    with col1:
                        st.write(f"**{row['nome_completo']}**")
                    with col2:
                        st.write(f"🕐 {row['data_consulta'].strftime('%H:%M')}")
                        st.write(f"📝 {row['tipo']}")
                    with col3:
                        status_color = {
                            'agendada': 'blue',
                            'realizada': 'green', 
                            'cancelada': 'red',
                            'falta': 'orange'
                        }.get(row['status'], 'gray')
                        st.markdown(f"**Status:** <span style='color:{status_color}'>{row['status'].title()}</span>", 
                                  unsafe_allow_html=True)
                    with col4:
                        valor = converter_numpy_para_python(row['valor_consulta'])
                        st.write(f"**{valor:,.0f} CVE**")
                    st.divider()
                    
            total_consultas = len(agenda_df)
            realizadas = len(agenda_df[agenda_df['status'] == 'realizada'])
            faltas = len(agenda_df[agenda_df['status'] == 'falta'])
            st.metric("Total de Consultas", total_consultas, f"{realizadas} realizadas, {faltas} faltas")
        else:
            st.info("📅 Nenhuma consulta agendada para o período selecionado")
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar agenda: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# 5. REGISTRAR CONSULTA REALIZADA - CORRIGIDO com opção "Paciente não compareceu"
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
            WHERE c.status = 'agendada' AND c.data_consulta <= NOW() + INTERVAL '1 day'
            ORDER BY c.data_consulta
        """, conn)
        
        if not consultas_df.empty:
            consultas_df['display'] = consultas_df['nome_completo'] + " - " + consultas_df['data_consulta'].dt.strftime('%d/%m/%Y %H:%M')
            consulta_selecionada = st.selectbox("Selecione a consulta:", consultas_df['display'])
            
            consulta_info = consultas_df[consultas_df['display'] == consulta_selecionada].iloc[0]
            
            st.info(f"""
            **Detalhes da Consulta:**
            - **Paciente:** {consulta_info['nome_completo']}
            - **Data/Hora:** {consulta_info['data_consulta'].strftime('%d/%m/%Y %H:%M')} (CVT)
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
                    st.success("✅ Consulta registrada como realizada!")
                    st.rerun()
            
            with col2:
                if st.button("❌ Não compareceu", type="secondary", use_container_width=True):
                    consulta_id = converter_numpy_para_python(consulta_info['id'])
                    
                    cur = conn.cursor()
                    cur.execute("UPDATE consultas SET status = 'falta' WHERE id = %s", (consulta_id,))
                    conn.commit()
                    st.warning("⚠️ Consulta registrada como falta (paciente não compareceu)")
                    st.rerun()
            
            with col3:
                if not consulta_info['pagamento_realizado'] and consulta_info['status'] == 'realizada':
                    if st.button("💰 Pagamento", use_container_width=True):
                        consulta_id = converter_numpy_para_python(consulta_info['id'])
                        
                        cur = conn.cursor()
                        cur.execute("UPDATE consultas SET pagamento_realizado = TRUE WHERE id = %s", (consulta_id,))
                        conn.commit()
                        st.success("💰 Pagamento registrado com sucesso!")
                        st.rerun()
                else:
                    st.button("💰 Pagamento", disabled=True, use_container_width=True)
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
                SELECT COUNT(*) as total 
                FROM consultas 
                WHERE EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM NOW())
            """, conn)
            st.metric("Consultas este Mês", converter_numpy_para_python(consultas_mes.iloc[0]['total']))
        
        with col3:
            receita_mes = pd.read_sql("""
                SELECT COALESCE(SUM(valor_consulta), 0) as total 
                FROM consultas 
                WHERE status = 'realizada' 
                AND EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM NOW())
            """, conn)
            receita_valor = converter_numpy_para_python(receita_mes.iloc[0]['total'])
            st.metric("Receita do Mês (CVE)", f"{receita_valor:,.0f}")
        
        with col4:
            taxa_falta = pd.read_sql("""
                SELECT 
                    ROUND(
                        COUNT(CASE WHEN status = 'falta' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0),
                        1
                    ) as taxa
                FROM consultas 
                WHERE EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM NOW())
            """, conn)
            taxa_valor = converter_numpy_para_python(taxa_falta.iloc[0]['taxa']) if not pd.isna(taxa_falta.iloc[0]['taxa']) else 0
            st.metric("Taxa de Faltas (%)", f"{taxa_valor}")
        
        st.subheader("📊 Consultas por Status (Este Mês)")
        status_df = pd.read_sql("""
            SELECT status, COUNT(*) as quantidade
            FROM consultas
            WHERE EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM NOW())
            GROUP BY status
        """, conn)
        
        if not status_df.empty:
            status_df['quantidade'] = status_df['quantidade'].apply(converter_numpy_para_python)
            st.bar_chart(status_df.set_index('status'))
        else:
            st.info("📊 Sem dados para o mês atual")
            
    except Exception as e:
        st.error(f"❌ Erro ao gerar estatísticas: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# RODAPÉ PERSONALIZADO (sem a seção de horários)
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 10px;'>"
    "🧠 <b>Psicare by Belinda Viana</b> - Consultório de Psicologia | "
    "📞 Contacto: +238 5949955 | "
    "📧 Email: contato@atendimentoviana.cv | "
    "🌐 www.atendimentoviana.cv"
    "</div>", 
    unsafe_allow_html=True
)