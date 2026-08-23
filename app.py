import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import io, zipfile, os

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(page_title="Sistema ACE - Gestão Integrada de Endemias", layout="wide")

st.title("🛡️ Sistema de Controle de Endemias (ACE - Painel Integrado)")

# Inicialização de estados globais unificados
if "vistorias" not in st.session_state:
    st.session_state.vistorias = []

# ==================== ABAS PRINCIPAIS ====================
aba_cadastro, aba_reconhecimento, aba_fechadas, aba_busca, aba_backup = st.tabs(
    [
        "📝 Relatório Diário",
        "📊 Reconhecimento",
        "🚪 Casas Fechadas / Recusa",
        "🔍 Busca & Auditoria",
        "💾 Central de Backup",
    ]
)

# ==================== ABA 1: RELATÓRIO DIÁRIO ====================
with aba_cadastro:
    st.subheader("📋 Relatório Diário de Campo")
    st.markdown("Preencha os dados da visita domiciliar ou comercial realizada no quarteirão.")

    with st.form("form_relatorio_diario", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            data_visita = st.date_input("Data da Visita", value=datetime.today())
            num_quarteirao = st.text_input("Nº do Quarteirão", placeholder="Ex: 142B")
            lado = st.number_input("Lado do Quarteirão", min_value=1, value=1, step=1)
        with col2:
            nome_rua = st.text_input("Nome da Rua / Logradouro")
            num_casa = st.text_input("Nº / Identificação do Imóvel", placeholder="Ex: 3A/5, 2/1")
            tipo_imovel = st.selectbox(
                "Tipo de Imóvel", 
                ["Residência (RES)", "Comércio (COM)", "Terreno Baldio (TB)", "Ponto Estratégico (PE)", "Outros (OUT)"]
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
        with c4: gramas = st.number_input("Gramas (g)", min_value=0.0, format="%.1f", value=0.0)
        with c5: depositos = st.number_input("Depósitos", min_value=0, value=0)
        with c6: litros = st.number_input("Litros (L)", min_value=0.0, format="%.1f", value=0.0)

        submitted = st.form_submit_button("💾 Salvar Registro Diário", use_container_width=True)
        if submitted:
            if not num_quarteirao or not nome_rua or not num_casa:
                st.error("⚠️ Por favor, preencha o Quarteirão, a Rua e o Número/Identificação da Casa.")
            else:
                novo_registro = {
                    "Data": data_visita.strftime("%d/%m/%Y"),
                    "Quarteirao": str(num_quarteirao).strip().upper(),
                    "Lado": int(lado),
                    "Rua": nome_rua,
                    "Casa": str(num_casa), 
                    "Tipo Imovel": tipo_imovel,
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
                st.success(f"✅ Imóvel **{num_casa}** (Lado {lado}, {nome_rua}) registrado com sucesso!")

    if st.session_state.vistorias:
        st.markdown("---")
        st.subheader("📊 Resumo Operacional Acumulado")
        df_v = pd.DataFrame(st.session_state.vistorias)
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Visitas", len(df_v))
        m2.metric("Dep. Eliminados", int(df_v["Eliminados"].sum()))
        m3.metric("Tubitos Coletados", int(df_v["Tubitos"].sum()))
        m4.metric("Imóveis Tratados", int(df_v["Tratados"].sum()))
        m5.metric("Larvicida (g)", f"{df_v['Gramas'].sum():.1f}g")
        with st.expander("👁️ Ver Todos os Registros Diários na Sessão", expanded=False):
            st.dataframe(df_v, use_container_width=True)
            if st.button("🗑️ Limpar Todos os Registros Diários"):
                st.session_state.vistorias = []
                st.rerun()

# ==================== ABA 2: RECONHECIMENTO AUTOMÁTICO ====================
with aba_reconhecimento:
    st.subheader("📊 Reconhecimento Automático de Imóveis")
    st.markdown("Resumo automático baseado nos registros do Relatório Diário.")

    if st.session_state.vistorias:
        df_v = pd.DataFrame(st.session_state.vistorias)
        df_v["Data"] = pd.to_datetime(df_v["Data"], format="%d/%m/%Y")
        df_v["AnoMes"] = df_v["Data"].dt.to_period("M").astype(str)

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_mes = st.selectbox("Selecione o Mês/Ano", ["Todos"] + sorted(df_v["AnoMes"].unique()))
        with col_f2:
            filtro_quart = st.selectbox("Selecione o Quarteirão", ["Todos"] + sorted(df_v["Quarteirao"].unique()))

        df_filtrado = df_v.copy()
        if filtro_mes != "Todos":
            df_filtrado = df_filtrado[df_filtrado["AnoMes"] == filtro_mes]
        if filtro_quart != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Quarteirao"] == filtro_quart]

        df_resumo = df_filtrado.groupby(["Quarteirao", "Tipo Imovel"]).size().reset_index(name="Qtd Imóveis")
        st.dataframe(df_resumo, use_container_width=True)

        df_mensal = df_filtrado.groupby(["AnoMes", "Tipo Imovel"]).size().reset_index(name="Qtd Imóveis")
        chart_mensal = alt.Chart(df_mensal).mark_bar().encode(
            x="AnoMes", y="Qtd Imóveis", color="Tipo Imovel",
            tooltip=["AnoMes","Tipo Imovel","Qtd Imóveis"]
        ).properties(height=400, title="Distribuição Mensal por Tipo de Imóvel")
        st.altair_chart(chart_mensal, use_container_width=True)
    else:
        st.info("ℹ️ Nenhum dado cadastrado no Relatório Diário ainda.")

# ==================== ABA 3: CASAS FECHADAS / RECUSA ====================
with aba_fechadas:
    st.subheader("🚪 Monitoramento de Imóveis Fechados e Recusas")
    if st.session_state.vistorias:
        df_vistorias = pd.DataFrame(st.session_state.vistorias)
        df_fechadas = df_vistorias[df_vistorias["Vistoria"] == "Fechada / Recusa"]
        if not df_fechadas.empty:
            st.warning(f"⚠️ Foram encontrados **{len(df_fechadas)}** imóveis fechados ou com recusa.")
            quart_filtro = st.selectbox("Filtrar por Quarteirão", ["Todos"] + list(df_fechadas["Quarteirao"].unique()))
            if quart_filtro != "Todos":
                df_fechadas = df_fechadas[df_fechadas["Quarteirao"] == quart_filtro]
            st.dataframe(df_fechadas[["Data","Quarteirao","Lado","Rua","Casa","Tipo Imovel","Agente"]], use_container_width=True)
            csv_fech
