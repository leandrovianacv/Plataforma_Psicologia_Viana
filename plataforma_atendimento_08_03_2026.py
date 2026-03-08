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
        
        # Tabela consultas - ADICIONADO CAMPOS PARA PACOTE
        cur.execute("""
            CREATE TABLE IF NOT EXISTS consultas (
                id SERIAL PRIMARY KEY,
                paciente_id INTEGER REFERENCES pacientes(id),
                data_consulta TIMESTAMP NOT NULL,
                primeira_consulta BOOLEAN DEFAULT TRUE,
                valor_consulta DECIMAL(10,2) DEFAULT 0,
                tipo_consulta VARCHAR(20) DEFAULT 'normal',  -- 'normal', 'pacote_4', 'pacote_8'
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

# 1. CADASTRAR PACIENTE - COM DATA DE NASCIMENTO DESDE 1930
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
                min_value=date(1930, 1, 1),
                max_value=date.today(),
                value=None,
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

# 2. MARCAR CONSULTA - COM OPÇÃO DE PACOTE DIRETO NO FORMULÁRIO
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
                
                with col2: 
                    primeira_consulta = st.checkbox("Primeira Consulta", value=True)
                    
                    # OPÇÃO DE TIPO DE CONSULTA: Normal ou Pacotes
                    tipo_consulta = st.radio(
                        "Tipo de Consulta",
                        ["Normal", "Pacote 4 seções (1.750€ cada)", "Pacote 8 seções (1.500€ cada)"],
                        horizontal=True
                    )
                    
                    # Definir valor baseado no tipo de consulta
                    if tipo_consulta == "Normal":
                        valor_consulta = st.number_input("Valor da Consulta (CVE)", 
                                                       min_value=0.0, 
                                                       value=2500.0 if primeira_consulta else 2000.0,
                                                       step=100.0,
                                                       help="Valor para consulta avulsa")
                        tipo_consulta_db = "normal"
                    elif tipo_consulta == "Pacote 4 seções (1.750€ cada)":
                        valor_consulta = 1750.0
                        st.info(f"💰 Valor por sessão: 1.750 CVE (Total do pacote: 7.000 CVE)")
                        tipo_consulta_db = "pacote_4"
                    else:  # Pacote 8 seções
                        valor_consulta = 1500.0
                        st.info(f"💰 Valor por sessão: 1.500 CVE (Total do pacote: 12.000 CVE)")
                        tipo_consulta_db = "pacote_8"
                    
                    forma_pagamento = st.selectbox("Forma de Pagamento", 
                                                 ["Dinheiro", "Transferência", "MB Way", "Outro"])
                
                observacoes = st.text_area("Observações Técnicas")
                
                if st.form_submit_button("📅 Agendar Consulta"):
                    paciente_row = pacientes_df[pacientes_df['nome_completo'] == paciente_nome].iloc[0]
                    paciente_id = converter_numpy_para_python(paciente_row['id'])
                    
                    data_hora = datetime.combine(data_consulta, hora_consulta)
                    
                    cur = conn.cursor()
                    
                    # Inserir consulta com tipo_consulta
                    cur.execute(
                        """INSERT INTO consultas 
                        (paciente_id, data_consulta, primeira_consulta, valor_consulta, 
                         tipo_consulta, forma_pagamento, observacoes_tecnicas) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (paciente_id, data_hora, primeira_consulta, valor_consulta, 
                         tipo_consulta_db, forma_pagamento, observacoes)
                    )
                    conn.commit()
                    
                    mensagem_tipo = "consulta normal" if tipo_consulta_db == "normal" else f"consulta de {tipo_consulta}"
                    st.success(f"✅ {mensagem_tipo.title()} marcada para {data_consulta.strftime('%d/%m/%Y')} às {hora_consulta.strftime('%H:%M')}")
                    
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

# 4. AGENDA DA SEMANA - COM INDICAÇÃO DE TIPO DE CONSULTA
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
                       c.status, c.valor_consulta, c.tipo_consulta,
                       c.forma_pagamento, c.pagamento_realizado
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE DATE(c.data_consulta) = CURRENT_DATE
                ORDER BY c.data_consulta
            """, conn)
        elif opcao_agenda == "Amanhã":
            agenda_df = pd.read_sql("""
                SELECT c.id, p.nome_completo, c.data_consulta, 
                       CASE WHEN c.primeira_consulta THEN 'Primeira' ELSE 'Retorno' END as tipo,
                       c.status, c.valor_consulta, c.tipo_consulta,
                       c.forma_pagamento, c.pagamento_realizado
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE DATE(c.data_consulta) = CURRENT_DATE + INTERVAL '1 day'
                ORDER BY c.data_consulta
            """, conn)
        else:
            agenda_df = pd.read_sql("""
                SELECT c.id, p.nome_completo, c.data_consulta, 
                       CASE WHEN c.primeira_consulta THEN 'Primeira' ELSE 'Retorno' END as tipo,
                       c.status, c.valor_consulta, c.tipo_consulta,
                       c.forma_pagamento, c.pagamento_realizado
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE c.data_consulta BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
                ORDER BY c.data_consulta
            """, conn)
        
        if not agenda_df.empty:
            # Criar colunas para os cabeçalhos
            col1, col2, col3, col4, col5, col6 = st.columns([2.5, 1, 1, 1, 1.2, 1])
            with col1:
                st.markdown("**Paciente**")
            with col2:
                st.markdown("**Horário**")
            with col3:
                st.markdown("**Tipo**")
            with col4:
                st.markdown("**Status**")
            with col5:
                st.markdown("**Valor/Tipo**")
            with col6:
                st.markdown("**Ações**")
            
            st.divider()
            
            for _, row in agenda_df.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5, col6 = st.columns([2.5, 1, 1, 1, 1.2, 1])
                    
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
                        }.get(row['status'], 'gray')
                        st.markdown(f"<span style='color:{status_color}'>{row['status'].title()}</span>", 
                                  unsafe_allow_html=True)
                    
                    with col5:
                        tipo_consulta = row['tipo_consulta']
                        if tipo_consulta == 'pacote_4':
                            st.markdown("📦 **Pacote 4**")
                        elif tipo_consulta == 'pacote_8':
                            st.markdown("📦 **Pacote 8**")
                        else:
                            st.markdown(f"💰 {converter_numpy_para_python(row['valor_consulta']):,.0f} CVE")
                    
                    with col6:
                        # Só mostrar botão de cancelar se a consulta estiver agendada
                        if row['status'] == 'agendada':
                            consulta_id = converter_numpy_para_python(row['id'])
                            if st.button(f"❌ Cancelar", key=f"cancel_{consulta_id}", use_container_width=True):
                                try:
                                    cur = conn.cursor()
                                    cur.execute("UPDATE consultas SET status = 'cancelada' WHERE id = %s", (consulta_id,))
                                    conn.commit()
                                    st.success("✅ Consulta cancelada com sucesso!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao cancelar: {e}")
                        else:
                            st.write("—")
                    
                    st.divider()
                    
            # Estatísticas no final
            total_consultas = len(agenda_df)
            realizadas = len(agenda_df[agenda_df['status'] == 'realizada'])
            faltas = len(agenda_df[agenda_df['status'] == 'falta'])
            canceladas = len(agenda_df[agenda_df['status'] == 'cancelada'])
            consultas_pacote = len(agenda_df[agenda_df['tipo_consulta'].str.startswith('pacote', na=False)])
            
            col_res1, col_res2, col_res3, col_res4, col_res5 = st.columns(5)
            with col_res1:
                st.metric("Total", total_consultas)
            with col_res2:
                st.metric("Realizadas", realizadas)
            with col_res3:
                st.metric("Faltas", faltas)
            with col_res4:
                st.metric("Canceladas", canceladas)
            with col_res5:
                st.metric("Em Pacote", consultas_pacote)
        else:
            st.info("📅 Nenhuma consulta agendada para o período selecionado")
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar agenda: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# 5. REGISTRAR CONSULTA REALIZADA - COM OPÇÃO NÃO COMPARECEU
elif menu == "✅ Registrar Consulta Realizada":
    st.header("✅ Registrar Consulta Realizada")
    
    try:
        conn = conectar_banco()
        if conn is None:
            st.error("❌ Não foi possível conectar ao banco de dados")
            st.stop()
            
        consultas_df = pd.read_sql("""
            SELECT c.id, p.nome_completo, c.data_consulta, c.valor_consulta,
                   c.pagamento_realizado, c.status, c.tipo_consulta
            FROM consultas c
            JOIN pacientes p ON c.paciente_id = p.id
            WHERE c.status = 'agendada' AND c.data_consulta <= NOW() + INTERVAL '1 day'
            ORDER BY c.data_consulta
        """, conn)
        
        if not consultas_df.empty:
            consultas_df['display'] = consultas_df.apply(
                lambda x: f"{x['nome_completo']} - {x['data_consulta'].strftime('%d/%m/%Y %H:%M')}" + 
                         (f" (📦 {x['tipo_consulta']})" if x['tipo_consulta'].startswith('pacote') else ""), 
                axis=1
            )
            consulta_selecionada = st.selectbox("Selecionar Consulta:", consultas_df['display'])
            
            consulta_info = consultas_df[consultas_df['display'] == consulta_selecionada].iloc[0]
            
            info_text = f"""
            **Detalhes da Consulta:**
            - **Paciente:** {consulta_info['nome_completo']}
            - **Data/Hora:** {consulta_info['data_consulta'].strftime('%d/%m/%Y %H:%M')}
            """
            
            if consulta_info['tipo_consulta'].startswith('pacote'):
                info_text += f"- **Tipo:** 📦 {consulta_info['tipo_consulta']} (consulta incluída no pacote)\n"
            else:
                info_text += f"- **Valor:** {converter_numpy_para_python(consulta_info['valor_consulta']):,.0f} CVE\n"
                info_text += f"- **Pagamento:** {'✅ Pago' if consulta_info['pagamento_realizado'] else '⏳ Pendente'}\n"
            
            st.info(info_text)
            
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
                if st.button("❌ Não compareceu", use_container_width=True):
                    consulta_id = converter_numpy_para_python(consulta_info['id'])
                    
                    cur = conn.cursor()
                    cur.execute("UPDATE consultas SET status = 'falta' WHERE id = %s", (consulta_id,))
                    conn.commit()
                    st.warning("⚠️ Consulta registrada como falta (paciente não compareceu)")
                    st.rerun()
            
            with col3:
                if not consulta_info['tipo_consulta'].startswith('pacote') and not consulta_info['pagamento_realizado'] and consulta_info['status'] == 'realizada':
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

# 6. ESTATÍSTICAS - ATUALIZADAS PARA INCLUIR PACOTES
elif menu == "📊 Estatísticas":
    st.header("📊 Estatísticas do Consultório")
    
    try:
        conn = conectar_banco()
        if conn is None:
            st.error("❌ Não foi possível conectar ao banco de dados")
            st.stop()
            
        col1, col2, col3, col4, col5 = st.columns(5)
        
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
                AND tipo_consulta = 'normal'
            """, conn)
            receita_valor = converter_numpy_para_python(receita_mes.iloc[0]['total'])
            st.metric("Receita Normal (CVE)", f"{receita_valor:,.0f}")
        
        with col4:
            consultas_pacote_mes = pd.read_sql("""
                SELECT COUNT(*) as total 
                FROM consultas 
                WHERE EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM NOW())
                AND tipo_consulta LIKE 'pacote%'
            """, conn)
            st.metric("Consultas em Pacote", converter_numpy_para_python(consultas_pacote_mes.iloc[0]['total']))
        
        with col5:
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
        
        st.subheader("📊 Distribuição por Tipo de Consulta")
        tipo_df = pd.read_sql("""
            SELECT 
                CASE 
                    WHEN tipo_consulta = 'normal' THEN 'Consultas Normais'
                    WHEN tipo_consulta = 'pacote_4' THEN 'Pacote 4 seções'
                    WHEN tipo_consulta = 'pacote_8' THEN 'Pacote 8 seções'
                END as tipo,
                COUNT(*) as quantidade
            FROM consultas
            WHERE EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM NOW())
            GROUP BY tipo_consulta
        """, conn)
        
        if not tipo_df.empty:
            tipo_df['quantidade'] = tipo_df['quantidade'].apply(converter_numpy_para_python)
            st.bar_chart(tipo_df.set_index('tipo'))
        else:
            st.info("📊 Sem dados para o mês atual")
            
    except Exception as e:
        st.error(f"❌ Erro ao gerar estatísticas: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# RODAPÉ PERSONALIZADO
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 10px;'>"
    "🧠 <b>Atendimento Viana</b> - Consultório de Psicologia | "
    "📞 Contacto: +238 594 99 55 | "
    "📧 Email: belindaviana08@gmail.com | "
    "🌐 https://plataformapsicologiaviana-belinda1988.streamlit.app/"
    "</div>", 
    unsafe_allow_html=True
)