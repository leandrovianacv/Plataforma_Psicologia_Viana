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
        page_icon="🧠",  # Fallback se a imagem não for encontrada
        layout="wide"
    )

# --- CSS PERSONALIZADO E ATUALIZADO ---
# NOVA PALETA: Fundo #FAFAFA, Destaque #007681 (Teal), Texto #333333, Cards #FFFFFF
st.markdown("""
<style>
    /* Estilo global e fontes */
    .stApp {
        background-color: #FAFAFA; /* Cinza extremamente claro para o fundo */
    }
    
    /* Garantir cor preta (#333 para conforto visual) em todo o texto */
    .stApp, p, span, label, li, h1, h2, h3, .stMarkdown {
        color: #333333 !important;
    }
    
    /* Estilização da Sidebar (Barra Lateral) */
    .css-1d391kg, [data-testid="stSidebar"] {
        background-color: #F0F2F5 !important; /* Cinza leve para diferenciar o menu */
        border-right: 1px solid #E0E0E0;
    }
    
    /* Cor preta para os textos da barra lateral */
    .css-1d391kg p, .css-1d391kg span, .css-1d391kg label,
    .stSidebar p, .stSidebar span, .stSidebar label, .stSidebar li {
        color: #333333 !important;
    }
    
    /* Cor preta para o texto dentro do menu de navegação (select box) */
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] {
        color: #333333 !important;
    }

    /* Título principal - Belinda Viana */
    h1 {
        color: #007681 !important; /* Cor de destaque (teal) para o nome */
        text-align: center;
        font-size: 42px !important;
        font-weight: 700;
        margin-bottom: 5px !important;
    }
    
    /* Subtítulo - PSICÓLOGA CLÍNICA */
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
        border-bottom: 2px solid #007681;
        padding-bottom: 10px;
        margin-top: 30px !important;
    }
    
    /* Inputs, Textareas e Selectboxes modernizados */
    .stTextInput input, .stSelectbox select, .stDateInput input, .stTimeInput input, .stTextArea textarea {
        background-color: white !important;
        color: #333333 !important;
        border: 1px solid #D9D9D9 !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }
    
    /* Botões modernizados */
    .stButton > button {
        background-color: #007681 !important; /* Cor de destaque */
        color: white !important;
        border: none;
        border-radius: 20px !important; /* Botões arredondados */
        padding: 10px 25px !important;
        font-weight: 600;
        transition: background-color 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #005F68 !important; /* Cor mais escura no hover */
        color: white !important;
    }
    
    /* Cards de Métricas - Substituindo o fundo preto */
    [data-testid="metric-container"], .css-1xarl3l {
        background-color: white !important; /* Fundo branco para os cards */
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important; /* Sombra leve */
        border: 1px solid #F0F0F0 !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #007681 !important; /* Cor de destaque para o valor da métrica */
        font-size: 32px !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #666666 !important; /* Cor suave para o rótulo */
    }
    
    /* DataFrames */
    .stDataFrame {
        background-color: white !important;
        border-radius: 8px;
        padding: 10px;
        border: 1px solid #E0E0E0;
    }
    
    /* Rodapé */
    .rodape {
        text-align: center;
        color: #333333 !important;
        padding: 20px;
        background-color: #F0F2F5; /* Cinza leve igual a sidebar */
        border-radius: 8px;
        margin-top: 40px;
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
            st.error("❌ DB_URL não configurada! Use secrets.")
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
inicializar_banco()

# HEADER PERSONALIZADO
st.markdown("<h1>Belinda Viana</h1>", unsafe_allow_html=True)
st.markdown("<h3>PSICÓLOGA CLÍNICA</h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #007681;'>", unsafe_allow_html=True)

# MENU PERSONALIZADO NA SIDEBAR
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
        
        submit = st.form_submit_button("💾 Salvar Paciente")
        
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
                        st.success("✅ Paciente cadastrado com sucesso!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar: {e}")
                    finally:
                        conn.close()
            else:
                st.error("❌ Preencha os campos obrigatórios (*)")

# 2. MARCAR CONSULTA  
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
                    
                    submit_agendar = st.form_submit_button("📅 Agendar Consulta")
                    
                    if submit_agendar:
                        # Validar horário
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
                st.info("📝 Nenhum paciente cadastrado.")
                
        except Exception as e:
            st.error(f"❌ Erro ao carregar pacientes: {e}")
        finally:
            conn.close()

# 4. AGENDA DA SEMANA  
elif menu == "🗓️ Agenda da Semana":
    st.header("🗓️ Agenda de Consultas")
    
    opcao_agenda = st.radio("Visualizar:", ["Dia Específico", "Próximos 7 Dias"], horizontal=True)
    
    conn = conectar_banco()
    if conn:
        try:
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
                    WHERE c.data_consulta BETWEEN CURRENT_TIMESTAMP - INTERVAL '1 hour' AND CURRENT_TIMESTAMP + INTERVAL '7 days'
                    ORDER BY c.data_consulta
                """, conn)
            
            if not agenda_df.empty:
                st.divider()
                for _, row in agenda_df.iterrows():
                    # Definir cores para o status
                    status_colors = {
                        'agendada': '#1E88E5', # Azul
                        'realizada': '#43A047', # Verde
                        'cancelada': '#E53935', # Vermelho
                        'falta': '#FB8C00'     # Laranja
                    }
                    curr_status = row['status'].lower()
                    color = status_colors.get(curr_status, '#333333')
                    
                    st.markdown(f"""
                    <div style="background-color: white; padding: 15px; border-radius: 8px; border-left: 5px solid {color}; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="font-size: 1.1em; color: #333;">{row['nome_completo']}</strong><br>
                                <span style="color: #666;">📝 {row['tipo']}</span>
                            </div>
                            <div style="text-align: right;">
                                <strong style="font-size: 1.2em; color: {color};">{curr_status.title()}</strong><br>
                                <span style="font-size: 1.1em; color: #333;">🕐 {row['data_consulta'].strftime('%H:%M')} - {row['data_consulta'].strftime('%d/%m/%Y')}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Métricas em cards brancos (conforme CSS definido no topo)
                total_con = len(agenda_df)
                total_fal = len(agenda_df[agenda_df['status'].lower() == 'falta'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total no Período", total_con)
                with col2:
                    st.metric("Total Faltas", total_fal)
                    
            else:
                st.info("📅 Nenhuma consulta agendada para o período selecionado.")
                
        except Exception as e:
            st.error(f"❌ Erro ao carregar agenda: {e}")
        finally:
            conn.close()

# 5. REGISTRAR CONSULTA REALIZADA
elif menu == "✅ Registrar Consulta Realizada":
    st.header("✅ Registrar Consulta Realizada")
    st.markdown("Selecione consultas 'Agendadas' do dia de hoje (ou anteriores) para atualizar o status.")
    
    conn = conectar_banco()
    if conn:
        try:
            # Selecionar consultas agendadas que já deveriam ter ocorrido
            consultas_df = pd.read_sql("""
                SELECT c.id, p.nome_completo, c.data_consulta, c.valor_consulta
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE c.status = 'agendada' 
                  AND c.data_consulta <= CURRENT_TIMESTAMP + INTERVAL '1 hour'
                ORDER BY c.data_consulta ASC
            """, conn)
            
            if not consultas_df.empty:
                # Criar string de exibição
                consultas_df['display'] = consultas_df['data_consulta'].dt.strftime('%d/%m %H:%M') + " - " + consultas_df['nome_completo']
                
                consulta_selecionada = st.selectbox("Selecionar Consulta:", consultas_df['display'])
                row_sel = consultas_df[consultas_df['display'] == consulta_selecionada].iloc[0]
                consulta_id = converter_numpy_para_python(row_sel['id'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ Marcar como Realizada", use_container_width=True, type="primary"):
                        cur = conn.cursor()
                        cur.execute("UPDATE consultas SET status = 'realizada' WHERE id = %s", (consulta_id,))
                        conn.commit()
                        st.success("✅ Consulta registrada como realizada!")
                        st.balloons()
                        # st.rerun()  # Descomentar se necessário no deployment
                
                with col2:
                    if st.button("❌ Marcar como Falta", use_container_width=True):
                        cur = conn.cursor()
                        cur.execute("UPDATE consultas SET status = 'falta' WHERE id = %s", (consulta_id,))
                        conn.commit()
                        st.warning("⚠️ Consulta registrada como falta.")
                        # st.rerun() # Descomentar se necessário no deployment
            else:
                st.info("📝 Nenhuma consulta pendente de registro para hoje.")
                
        except Exception as e:
            st.error(f"❌ Erro ao registrar consulta: {e}")
        finally:
            conn.close()

# 6. ESTATÍSTICAS
elif menu == "📊 Estatísticas":
    st.header("📊 Estatísticas do Consultório")
    
    conn = conectar_banco()
    if conn:
        try:
            # Cards de Métricas Modernos (fundo branco definido no CSS)
            col1, col2, col3, col4 = st.columns(4)
            
            # 1. Total Pacientes Ativos
            total_pac = pd.read_sql("SELECT COUNT(*) as total FROM pacientes WHERE ativo = TRUE", conn).iloc[0]['total']
            
            # 2. Consultas Mês Atual (Total)
            con_mes = pd.read_sql("""
                SELECT COUNT(*) as total FROM consultas 
                WHERE EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM CURRENT_DATE)
                  AND EXTRACT(YEAR FROM data_consulta) = EXTRACT(YEAR FROM CURRENT_DATE)
            """, conn).iloc[0]['total']
            
            # 3. Receita Mês Atual (Realizadas)
            rec_mes = pd.read_sql("""
                SELECT SUM(valor_consulta) as total FROM consultas 
                WHERE status = 'realizada'
                  AND EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM CURRENT_DATE)
                  AND EXTRACT(YEAR FROM data_consulta) = EXTRACT(YEAR FROM CURRENT_DATE)
            """, conn).iloc[0]['total'] or 0.0
            rec_mes = converter_numpy_para_python(rec_mes)
            
            # 4. Taxa de Faltas Mês Atual
            res_fal = pd.read_sql("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'falta' THEN 1 END) as faltas
                FROM consultas 
                WHERE status IN ('realizada', 'falta')
                  AND EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM CURRENT_DATE)
                  AND EXTRACT(YEAR FROM data_consulta) = EXTRACT(YEAR FROM CURRENT_DATE)
            """, conn)
            
            total_atendimentos = res_fal.iloc[0]['total']
            faltas = res_fal.iloc[0]['faltas']
            
            if total_atendimentos > 0:
                taxa_faltas = (faltas / total_atendimentos) * 100
            else:
                taxa_faltas = 0.0
            
            with col1:
                st.metric("Pacientes Ativos", total_pac)
            with col2:
                st.metric("Agenda do Mês", con_mes)
            with col3:
                st.metric("Receita Mês CVE", f"{rec_mes:,.0f}".replace(",", "."))
            with col4:
                st.metric("Taxa Faltas %", f"{taxa_faltas:.1f}%")
                
            # Gráfico de Consultas por Status
            st.markdown("### 📈 Consultas Mês Atual por Status")
            chart_data = pd.read_sql("""
                SELECT status, COUNT(*) as quantidade
                FROM consultas
                WHERE EXTRACT(MONTH FROM data_consulta) = EXTRACT(MONTH FROM CURRENT_DATE)
                  AND EXTRACT(YEAR FROM data_consulta) = EXTRACT(YEAR FROM CURRENT_DATE)
                GROUP BY status
            """, conn)
            
            if not chart_data.empty:
                # Definir cores modernas para o gráfico de barras do Streamlit
                color_scale = pd.DataFrame({
                    'status': chart_data['status'],
                    'color': ['#1E88E5', '#43A047', '#FB8C00'] # agendada, realizada, falta (pode variar se houver cancelada)
                })
                
                st.bar_chart(chart_data.set_index('status'))
            else:
                st.info("📊 Sem dados de consultas para o mês atual.")
                
        except Exception as e:
            st.error(f"❌ Erro ao gerar estatísticas: {e}")
        finally:
            conn.close()

# RODAPÉ PERSONALIZADO (Cor cinza leve conforme sidebar)
st.markdown("---")
st.markdown("""
<div class='rodape'>
    🧠 <b>Belinda Viana</b> - Psicóloga Clínica | 📧 Email: belindaviana08@gmail.com
</div>
""", unsafe_allow_html=True)