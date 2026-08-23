import altair as alt
import pandas as pd
import streamlit as st
from datetime import datetime
import io, zipfile, os

# ==================== ABAS PRINCIPAIS ====================
aba_cadastro, aba_busca, aba_backup, aba_reconhecimento = st.tabs(
    [
        "📝 Registrar Visita",
        "🔍 Busca Avançada & Recuperação",
        "💾 Central de Backup",
        "📊 Reconhecimento",
    ]
)

# ==================== ABA RECONHECIMENTO ====================
with aba_reconhecimento:
    st.subheader("📊 Reconhecimento de Imóveis por Quarteirão")
    st.markdown("Cadastre a quantidade de imóveis por categoria em cada quarteirão.")

    if "reconhecimento" not in st.session_state:
        st.session_state.reconhecimento = []

    with st.form("form_reconhecimento", clear_on_submit=True):
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            quarteirao_rec = st.text_input("Número do Quarteirão", placeholder="Ex: 142")
        with col_r2:
            lado_rec = st.text_input("Lado", placeholder="Ex: A ou Norte")

        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        with col_c1: residencias = st.number_input("Residências", min_value=0, step=1)
        with col_c2: outros = st.number_input("Outros", min_value=0, step=1)
        with col_c3: tb = st.number_input("TB", min_value=0, step=1)
        with col_c4: comercio = st.number_input("Comércio", min_value=0, step=1)

        submitted_rec = st.form_submit_button("💾 Salvar Reconhecimento")
        if submitted_rec:
            if not quarteirao_rec:
                st.warning("⚠️ Informe o número do quarteirão.")
            else:
                total = residencias + outros + tb + comercio
                novo_reconhecimento = {
                    "Quarteirao": str(quarteirao_rec).strip(),
                    "Lado": lado_rec,
                    "Residencias": residencias,
                    "Outros": outros,
                    "TB": tb,
                    "Comercio": comercio,
                    "Total": total,
                    "Data Registro": datetime.today().strftime("%d/%m/%Y"),
                }
                st.session_state.reconhecimento.append(novo_reconhecimento)
                st.success("✅ Reconhecimento cadastrado com sucesso!")

    if st.session_state.reconhecimento:
        st.write("---")
        st.subheader("📊 Histórico de Reconhecimento")
        df_recon = pd.DataFrame(st.session_state.reconhecimento)
        st.dataframe(df_recon, use_container_width=True)

        # Totais gerais
        total_resid = df_recon["Residencias"].sum()
        total_outros = df_recon["Outros"].sum()
        total_tb = df_recon["TB"].sum()
        total_comercio = df_recon["Comercio"].sum()
        total_geral = df_recon["Total"].sum()

        st.write("---")
        st.subheader("📈 Totais por Categoria")
        col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns(5)
        with col_t1: st.metric("Residências", total_resid)
        with col_t2: st.metric("Outros", total_outros)
        with col_t3: st.metric("TB", total_tb)
        with col_t4: st.metric("Comércio", total_comercio)
        with col_t5: st.metric("Total Geral", total_geral)

        st.write("---")
        st.subheader("📊 Visualização Gráfica")

        # DataFrame para gráficos
        df_cat = pd.DataFrame({
            "Categoria": ["Residências", "Outros", "TB", "Comércio"],
            "Valor": [total_resid, total_outros, total_tb, total_comercio]
        })

        # Gráfico de Barras
        chart_bar = alt.Chart(df_cat).mark_bar().encode(
            x="Categoria",
            y="Valor",
            color="Categoria",
            tooltip=["Categoria", "Valor"]
        ).properties(height=300)
        st.altair_chart(chart_bar, use_container_width=True)

        # Gráfico de Pizza
        chart_pie = alt.Chart(df_cat).mark_arc().encode(
            theta="Valor",
            color="Categoria",
            tooltip=["Categoria", "Valor"]
        ).properties(height=300)
        st.altair_chart(chart_pie, use_container_width=True)

        # Filtro por quarteirão
        st.write("---")
        st.subheader("🔍 Visualização por Quarteirão")
        quarts_unicos = df_recon["Quarteirao"].unique().tolist()
        quart_sel = st.selectbox("Selecione o Quarteirão", quarts_unicos)
        df_quart = df_recon[df_recon["Quarteirao"] == quart_sel]

        if not df_quart.empty:
            df_quart_cat = pd.DataFrame({
                "Categoria": ["Residências", "Outros", "TB", "Comércio"],
                "Valor": [
                    df_quart["Residencias"].sum(),
                    df_quart["Outros"].sum(),
                    df_quart["TB"].sum(),
                    df_quart["Comercio"].sum(),
                ]
            })
            chart_quart = alt.Chart(df_quart_cat).mark_bar().encode(
                x="Categoria",
                y="Valor",
                color="Categoria",
                tooltip=["Categoria", "Valor"]
            ).properties(height=300, title=f"Distribuição no Quarteirão {quart_sel}")
            st.altair_chart(chart_quart, use_container_width=True)
