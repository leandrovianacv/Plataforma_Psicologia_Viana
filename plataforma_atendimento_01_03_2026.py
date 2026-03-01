import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime, date, time
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

# Configuração da página
st.set_page_config(
    page_title="Atendimento Viana - Psicologia", 
    page_icon="🧠",
    layout="wide"
)

# CSS básico para manter a consistência
st.markdown("""
<style>
    /* Fundo branco e texto preto */
    .stApp {
        background-color: white;
    }
    
    /* Título principal */
    h1 {
        color: #1f77b4 !important;  /* Azul suave para o título */
        text-align: center;
    }
    
    h3 {
        text-align: center;
        color: #555 !important;
    }
    
    /* Rodapé */
    .rodape {
        text-align: center;
        color: #666;
        padding: 10px;
        border-top: 1px solid #ddd;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Conexão com Supabase (via Session Pooler) - VERSÃO SEGURA
def conectar_banco():
    """Conecta ao Supabase usando Session Pooler - APENAS via secrets"""
    try:
        # APENAS usa secrets - NUNCA coloque senha no código!
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
            # Para teste local - usa variável de ambiente (mais seguro)
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

# Inicializar banco (criar tabelas se não existirem)
def inicializar_banco():
    """Garante que as tabelas necessárias existam"""
    try:
        conn = conectar_banco()
        if conn is None:
            return False
            
        cur = conn.cursor()
        
        # Tabela pacientes
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
        
        # Tabela consultas
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
st.markdown("<h1>🧠 PSICARE BY BELINDA VIANA</h1>", unsafe_allow_html=True)
st.markdown("<h3>PSICÓLOGA CLÍNICA</h3>", unsafe_allow_html=True)
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

# Função para validar horário de atendimento
def validar_horario(data_consulta, hora_consulta):
    """Valida se o horário está dentro do funcionamento (Segunda a Sexta, 7h-19h)"""
    # Verificar se é sábado (5) ou domingo (6)
    if data_consulta.weekday() >= 5:
        return False, "❌ Não atendemos aos sábados e domingos! (Segunda a Sexta)"
    
    # Verificar horário (7h às 19h)
    hora_min = time(7, 0)  # 07:00
    hora_max = time(19, 0)  # 19:00
    
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
            
        pacientes_df = pd.read_sql("SELECT id, nome_completo FROM pacientes WHERE ativo = TRUE", conn)
        
        if pacientes_df.empty:
            st.warning("⚠️ Cadastre pacientes primeiro!")
        else:
            with st.form("form_consulta", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    paciente_nome = st.selectbox("Paciente*", pacientes_df['nome_completo'])
                    data_consulta = st.date_input("Data*", min_value=date.today())
                    hora_consulta = st.time_input("Horário*", value=time(14, 0))
                    
                    # VALIDAÇÃO DE HORÁRIO
                    horario_valido, mensagem = validar_horario(data_consulta, hora_consulta)
                    if not horario_valido:
                        st.warning(mensagem)
                
                with col2: 
                    primeira_consulta = st.checkbox("Primeira Consulta", value=True)
                    valor_consulta = st.number_input("Valor da Consulta (CVE)", 
                                                   min_value=0.0, 
                                                   value=2500.0 if primeira_consulta else 2000.0,
                                                   step=100.0)
                    forma_pagamento = st.selectbox("Forma de Pagamento", 
                                                 ["Dinheiro", "Transferência", "MB Way", "Outro"])
                
                observacoes = st.text_area("Observações Técnicas")
                
                if st.form_submit_button("📅 Agendar Consulta"):
                    # Validar horário novamente antes de salvar
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
                        st.success(f"✅ Consulta marcada para {data_consulta.strftime('%d/%m/%Y')} às {hora_consulta.strftime('%H:%M')}")
                    
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
                   TO_CHAR(data_cadastro, 'DD/MM/YYYY') as data_cadastro
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
                       c.status, c.valor_consulta
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE DATE(c.data_consulta) = %s
                ORDER BY c.data_consulta
            """, conn, params=(data_selecionada,))
        else:
            agenda_df = pd.read_sql("""
                SELECT p.nome_completo, c.data_consulta, 
                       CASE WHEN c.primeira_consulta THEN 'Primeira' ELSE 'Retorno' END as tipo,
                       c.status, c.valor_consulta
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
            st.metric("Total de Consultas", total_consultas, f"{realizadas} realizadas")
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
            SELECT c.id, p.nome_completo, c.data_consulta, c.valor_consulta
            FROM consultas c
            JOIN pacientes p ON c.paciente_id = p.id
            WHERE c.status = 'agendada' AND c.data_consulta <= NOW() + INTERVAL '1 hour'
            ORDER BY c.data_consulta
        """, conn)
        
        if not consultas_df.empty:
            consultas_df['display'] = consultas_df['nome_completo'] + " - " + consultas_df['data_consulta'].dt.strftime('%d/%m %H:%M')
            consulta_selecionada = st.selectbox("Selecionar Consulta:", consultas_df['display'])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Marcar como Realizada", type="primary"):
                    consulta_id = consultas_df[consultas_df['display'] == consulta_selecionada].iloc[0]['id']
                    consulta_id = converter_numpy_para_python(consulta_id)
                    
                    cur = conn.cursor()
                    cur.execute("UPDATE consultas SET status = 'realizada' WHERE id = %s", (consulta_id,))
                    conn.commit()
                    st.success("✅ Consulta registrada como realizada!")
                    st.rerun()
            
            with col2:
                if st.button("❌ Marcar como Falta"):
                    consulta_id = consultas_df[consultas_df['display'] == consulta_selecionada].iloc[0]['id']
                    consulta_id = converter_numpy_para_python(consulta_id)
                    
                    cur = conn.cursor()
                    cur.execute("UPDATE consultas SET status = 'falta' WHERE id = %s", (consulta_id,))
                    conn.commit()
                    st.warning("⚠️ Consulta registrada como falta")
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

# RODAPÉ PERSONALIZADO
st.markdown("---")
st.markdown("""
<div class='rodape'>
    🧠 <b>Atendimento Viana</b> - Consultório de Psicologia | 
    📞 Contacto: +238 594 99 55 | 
    📧 Email: belindaviana08@gmail.com | 
    🌐 www.atendimentoviana.cv
</div>
""", unsafe_allow_html=True)