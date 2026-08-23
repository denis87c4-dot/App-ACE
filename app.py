import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import io, zipfile, os

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(page_title="Sistema ACE - Gestão Integrada de Endemias", layout="wide")

st.title("🛡️ Sistema de Controle de Endemias (ACE)")

# Inicialização de estados globais unificados
if "vistorias" not in st.session_state:
    st.session_state.vistorias = []

# Mapeamento para simplificar os nomes nas colunas do relatório
MAPA_TIPOS = {
    "Residência (RES)": "Residencial",
    "Comércio (COM)": "Comercial",
    "Terreno Baldio (TB)": "TB",
    "Ponto Estratégico (PE)": "PE",
    "Outros (OUT)": "Outros"
}

# ==================== ABAS PRINCIPAIS ====================
aba_cadastro, aba_reconhecimento, aba_busca, aba_backup = st.tabs(
    [
        "📝 Relatório Diário",
        "📊 Painel de Reconhecimento & Métricas",
        "🔍 Busca Avançada",
        "💾 Central de Backup",
    ]
)

# ==================== ABA 1: RELATÓRIO DIÁRIO ====================
with aba_cadastro:
    st.subheader("📋 Relatório Diário de Campo")
    st.markdown("Preencha os dados da visita domiciliar. **O reconhecimento do quarteirão é gerado automaticamente a partir daqui.**")

    with st.form("form_relatorio_diario", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            data_visita = st.date_input("Data da Visita", value=datetime.today())
            num_quarteirao = st.text_input("Nº do Quarteirão", placeholder="Ex: 142B").upper()
            lado = st.number_input("Lado do Quarteirão", min_value=1, value=1, step=1)
            
        with col2:
            nome_rua = st.text_input("Nome da Rua / Logradouro")
            num_casa = st.text_input("Nº / Identificação do Imóvel", placeholder="Ex: 3A/5, 2/1")
            tipo_imovel = st.selectbox(
                "Tipo de Imóvel", 
                list(MAPA_TIPOS.keys())
            )

        with col3:
            hora_entrada = st.time_input("Hora de Entrada", value=datetime.now().time())
            vistoria = st.selectbox("Condição da Vistoria", ["Normal", "Recuperada", "Fechada / Recusa"])
            agente_resp = st.text_input("Agente Responsável", placeholder="Ex: Denison")

        st.markdown("---")
        st.subheader("🔬 Dados Entomológicos e Tratamento")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1: eliminados = st.number_input("Eliminados", min_value=0, value=0)
        with c2: tubitos = st.number_input("Tubitos", min_value=0, value=0)
        with c3: imoveis_tratados = st.number_input("Tratados", min_value=0, value=0)
        with c4: gramas = st.number_input("Gramas (g)", min_value=0.0, format="%.1f")
        with c5: depositos = st.number_input("Depósitos", min_value=0, value=0)
        with c6: litros = st.number_input("Litros (L)", min_value=0.0, format="%.1f")

        submitted = st.form_submit_button("💾 Salvar Registro Diário", use_container_width=True)

        if submitted:
            if not num_quarteirao or not nome_rua or not num_casa:
                st.error("⚠️ Preencha o Quarteirão, a Rua e o Número/Identificação da Casa.")
            else:
                novo_registro = {
                    "Data": data_visita.strftime("%d/%m/%Y"),
                    "Quarteirao": str(num_quarteirao).strip(),
                    "Lado": int(lado),
                    "Rua": nome_rua,
                    "Casa": str(num_casa), 
                    "Tipo Imovel": tipo_imovel,
                    "Tipo Simplificado": MAPA_TIPOS[tipo_imovel],
                    "Hora": hora_entrada.strftime("%H:%M"),
                    "Vistoria": vistoria,
                    "Agente": agente_resp,
                    "Eliminados": int(eliminados),
                    "Tubitos": int(tubitos),
                    "Tratados": int(imoveis_tratados),
                    "Gramas": float(gramas),
                    "Depósitos": int(depositos),
                    "Litros": float(litros)
                }
                st.session_state.vistorias.append(novo_registro)
                st.success(f"✅ Imóvel **{num_casa}** registrado com sucesso!")

# ==================== ABA 2: PAINEL DE RECONHECIMENTO ====================
with aba_reconhecimento:
    st.subheader("📊 Reconhecimento Automático e Inteligência de Dados")
    
    if not st.session_state.vistorias:
        st.info("ℹ️ Nenhum dado cadastrado. Preencha o Relatório Diário para gerar as estatísticas de reconhecimento.")
    else:
        # Prepara o DataFrame
        df = pd.DataFrame(st.session_state.vistorias)
        df['Data_DT'] = pd.to_datetime(df['Data'], format="%d/%m/%Y")
        df['MesAno'] = df['Data_DT'].dt.strftime('%m/%Y')
        df['AnoMes_Ord'] = df['Data_DT'].dt.to_period("M").astype(str) # Para ordenação lógica

        # --- SEÇÃO DE FILTROS ---
        st.markdown("### 🔎 Filtros Potentes")
        f_col1, f_col2, f_col3 = st.columns(3)
        
        meses_disponiveis = ["Todos"] + list(df['MesAno'].unique())
        mes_filtro = f_col1.selectbox("Filtrar por Mês/Ano:", meses_disponiveis)
        
        quarteiroes_disp = sorted(df['Quarteirao'].unique())
        quart_filtro = f_col2.multiselect("Filtrar por Quarteirão:", quarteiroes_disp, default=quarteiroes_disp)
        
        agentes_disp = ["Todos"] + list(df['Agente'].unique())
        agente_filtro = f_col3.selectbox("Filtrar por Agente:", agentes_disp)

        # Aplicando os filtros
        df_filtrado = df[df['Quarteirao'].isin(quart_filtro)]
        if mes_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado['MesAno'] == mes_filtro]
        if agente_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Agente'] == agente_filtro]

        st.markdown("---")
        
        # --- CARDS DE CRESCIMENTO E TOTAIS (MÊS ATUAL VS ANTERIOR) ---
        if not df_filtrado.empty:
            st.markdown("### 📈 Resumo Geral do Período Filtrado")
            
            # Lógica para comparar meses (evolução)
            df_agrupado_mes = df.groupby('AnoMes_Ord').size().reset_index(name='Total')
            df_agrupado_mes = df_agrupado_mes.sort_values('AnoMes_Ord')
            
            total_atual = len(df_filtrado)
            residencia_total = len(df_filtrado[df_filtrado['Tipo Simplificado'] == 'Residencial'])
            comercio_total = len(df_filtrado[df_filtrado['Tipo Simplificado'] == 'Comercial'])
            tb_total = len(df_filtrado[df_filtrado['Tipo Simplificado'] == 'TB'])
            outros_total = len(df_filtrado[df_filtrado['Tipo Simplificado'].isin(['Outros', 'PE'])])

            kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
            
            # Tentando achar o mês anterior para gerar o Delta (Variação)
            delta_texto = None
            if mes_filtro != "Todos" and len(df_agrupado_mes) > 1:
                periodo_atual = pd.to_datetime(mes_filtro, format='%m/%Y').to_period("M").astype(str)
                idx_atual = df_agrupado_mes.index[df_agrupado_mes['AnoMes_Ord'] == periodo_atual].tolist()
                
                if idx_atual and idx_atual[0] > 0:
                    total_mes_ant = df_agrupado_mes.iloc[idx_atual[0] - 1]['Total']
                    variacao = total_atual - total_mes_ant
                    delta_texto = f"{variacao} vs mês anterior"

            kpi1.metric("Total de Imóveis", total_atual, delta=delta_texto)
            kpi2.metric("🏠 Residenciais", residencia_total)
            kpi3.metric("🏪 Comerciais", comercio_total)
            kpi4.metric("🌿 Terrenos Baldios", tb_total)
            kpi5.metric("📌 Outros / PE", outros_total)

            st.markdown("---")
            # --- TABELA DE RECONHECIMENTO DINÂMICA ---
            st.markdown("### 📑 Tabela de Reconhecimento por Quarteirão")
            
            # Pivot Table automática
            df_reconhecimento = df_filtrado.pivot_table(
                index=['Quarteirao', 'MesAno'], 
                columns='Tipo Simplificado', 
                values='Casa', 
                aggfunc='count', 
                fill_value=0
            ).reset_index()

            # Garantir que todas as colunas existam mesmo se não houver dados no filtro atual
            colunas_esperadas = ['Residencial', 'Comercial', 'TB', 'Outros', 'PE']
            for col in colunas_esperadas:
                if col not in df_reconhecimento.columns:
                    df_reconhecimento[col] = 0

            # Organizar ordem das colunas e adicionar total
            colunas_finais = ['Quarteirao', 'MesAno', 'Residencial', 'Comercial', 'TB', 'PE', 'Outros']
            df_reconhecimento = df_reconhecimento[colunas_finais]
            df_reconhecimento['Total Geral'] = df_reconhecimento[['Residencial', 'Comercial', 'TB', 'PE', 'Outros']].sum(axis=1)

            st.dataframe(df_reconhecimento, use_container_width=True, hide_index=True)

            # --- GRÁFICO DE EVOLUÇÃO ---
            st.markdown("---")
            st.markdown("### 📊 Evolução Diária / Mensal")
            
            # Agrupar por data e tipo para o gráfico
            df_grafico = df_filtrado.groupby(['Data_DT', 'Tipo Simplificado']).size().reset_index(name='Quantidade')
            
            grafico = alt.Chart(df_grafico).mark_line(point=True, strokeWidth=3).encode(
                x=alt.X('Data_DT:T', title='Data da Vistoria'),
                y=alt.Y('Quantidade:Q', title='Qtd de Imóveis'),
                color=alt.Color('Tipo Simplificado:N', title='Tipo de Imóvel', 
                                scale=alt.Scale(scheme='set2')),
                tooltip=['Data_DT', 'Tipo Simplificado', 'Quantidade']
            ).properties(height=350).interactive()

            st.altair_chart(grafico, use_container_width=True)

        else:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")

# ==================== ABA 3: BUSCA AVANÇADA ====================
with aba_busca:
    st.subheader("🔍 Busca Avançada e Recuperação")
    
    if st.session_state.vistorias:
        df_busca = pd.DataFrame(st.session_state.vistorias)
        termo = st.text_input("🔍 Pesquise por Rua, Número, Quarteirão ou Agente:", placeholder="Ex: Rua das Flores, 142, Normal...")
        
        if termo:
            mask = df_busca.astype(str).apply(lambda x: x.str.contains(termo, case=False, na=False)).any(axis=1)
            df_resultado = df_busca[mask]
        else:
            df_resultado = df_busca
            
        st.info(f"Mostrando {len(df_resultado)} registros encontrados.")
        st.dataframe(df_resultado, use_container_width=True)
    else:
        st.info("⚠️ Nenhum dado cadastrado no sistema ainda.")

# ==================== ABA 4: BACKUP ====================
with aba_backup:
    st.subheader("🔐 Central de Segurança e Backup")
    st.markdown("Como o reconhecimento agora é 100% automatizado, você só precisa fazer o backup de um único arquivo!")

    ARQUIVO_VISTORIAS = "vistorias_diarias.csv"

    # Salva localmente
    if st.session_state.vistorias:
        pd.DataFrame(st.session_state.vistorias).to_csv(ARQUIVO_VISTORIAS, index=False)

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown("### 📤 Exportar Dados (Backup)")
        if os.path.exists(ARQUIVO_VISTORIAS):
            with open(ARQUIVO_VISTORIAS, "rb") as file:
                st.download_button(
                    label="💾 Baixar Base Completa (.csv)",
                    data=file,
                    file_name=f"backup_ace_completo_{datetime.today().strftime('%Y-%m-%d')}.csv",
                    mime="text/csv",
                )
        else:
            st.info("⚠️ Nenhum dado para exportar.")

    with col_b2:
        st.markdown("### 📥 Restaurar Backup")
        arquivo_upload = st.file_uploader("Envie seu arquivo .csv de backup anterior", type="csv")
        if arquivo_upload is not None:
            try:
                df_restaurado = pd.read_csv(arquivo_upload)
                st.session_state.vistorias = df_restaurado.to_dict("records")
                st.success("✅ Backup restaurado com sucesso! Atualize a página.")
            except Exception as e:
                st.error(f"❌ Erro ao restaurar: {e}")
