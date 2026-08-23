import streamlit as st
import pandas as pd
import altair as alt
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
    st.markdown("Cadastre a quantidade de imóveis por categoria em cada quarteirão, com data e auditoria.")

    if "reconhecimento" not in st.session_state:
        st.session_state.reconhecimento = []

    with st.form("form_reconhecimento", clear_on_submit=True):
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            quarteirao_rec = st.text_input("Número do Quarteirão", placeholder="Ex: 142")
        with col_r2:
            lado_rec = st.text_input("Lado", placeholder="Ex: A ou Norte")

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            data_rec = st.date_input("Data do Reconhecimento", value=datetime.today())
        with col_d2:
            auditor = st.text_input("Responsável/Auditor", placeholder="Ex: Denison")

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
                    "Data Registro": data_rec.strftime("%d/%m/%Y"),
                    "Auditor": auditor,
                }
                st.session_state.reconhecimento.append(novo_reconhecimento)
                st.success("✅ Reconhecimento cadastrado com sucesso!")

    if st.session_state.reconhecimento:
        st.write("---")
        st.subheader("📊 Histórico de Reconhecimento")
        df_recon = pd.DataFrame(st.session_state.reconhecimento)
        st.dataframe(df_recon, use_container_width=True)

        # Auditoria comparativa por mês
        st.write("---")
        st.subheader("📈 Auditoria Comparativa por Mês")
        df_recon["Data"] = pd.to_datetime(df_recon["Data Registro"], format="%d/%m/%Y")
        df_recon["AnoMes"] = df_recon["Data"].dt.to_period("M").astype(str)

        df_audit = df_recon.groupby(["AnoMes", "Quarteirao"]).agg({
            "Residencias": "sum",
            "Outros": "sum",
            "TB": "sum",
            "Comercio": "sum",
            "Total": "sum"
        }).reset_index()

        st.dataframe(df_audit, use_container_width=True)

        # Seleção de quarteirão para auditoria
        quart_sel = st.selectbox("Selecione o Quarteirão para Auditoria", df_audit["Quarteirao"].unique())
        df_quart_audit = df_audit[df_audit["Quarteirao"] == quart_sel].sort_values("AnoMes")

        # Detectar variações críticas
        st.write("---")
        st.subheader("🚨 Variações Críticas")
        df_quart_audit["Delta_Total"] = df_quart_audit["Total"].pct_change() * 100
        for idx, row in df_quart_audit.iterrows():
            if not pd.isna(row["Delta_Total"]):
                if row["Delta_Total"] > 20:
                    st.markdown(f"<span style='color:green; font-weight:bold;'>⬆️ Crescimento de {row['Delta_Total']:.1f}% em {row['AnoMes']}</span>", unsafe_allow_html=True)
                elif row["Delta_Total"] < -20:
                    st.markdown(f"<span style='color:red; font-weight:bold;'>⬇️ Queda de {row['Delta_Total']:.1f}% em {row['AnoMes']}</span>", unsafe_allow_html=True)

        # Gráfico de evolução por quarteirão
        chart_audit = alt.Chart(
            df_quart_audit.melt(id_vars=["AnoMes"], value_vars=["Residencias","Outros","TB","Comercio","Total"], var_name="Categoria", value_name="Valor")
        ).mark_line(point=True).encode(
            x="AnoMes",
            y="Valor",
            color="Categoria",
            tooltip=["AnoMes","Categoria","Valor"]
        ).properties(height=400, title=f"Evolução do Quarteirão {quart_sel}")
        st.altair_chart(chart_audit, use_container_width=True)

# ==================== BACKUP ROBUSTO EM ZIP ====================
with aba_backup:
    st.subheader("🔐 Central de Segurança e Backup Avançado")

    ARQUIVO_VISTORIAS = "vistorias.csv"
    ARQUIVO_RECONHECIMENTO = "reconhecimento.csv"
    ARQUIVO_AUDITORIA = "auditoria.csv"

    def salvar_backup_automatico():
        try:
            if "vistorias" in st.session_state and st.session_state.vistorias:
                pd.DataFrame(st.session_state.vistorias).to_csv(ARQUIVO_VISTORIAS, index=False)
            if "reconhecimento" in st.session_state and st.session_state.reconhecimento:
                df_recon = pd.DataFrame(st.session_state.reconhecimento)
                df_recon.to_csv(ARQUIVO_RECONHECIMENTO, index=False)

                # Gerar relatório de auditoria
                df_recon["Data"] = pd.to_datetime(df_recon["Data Registro"], format="%d/%m/%Y")
                df_recon["AnoMes"] = df_recon["Data"].dt.to_period("M").astype(str)
                df_audit = df_recon.groupby(["AnoMes", "Quarteirao"]).agg({
                    "Residencias": "sum",
                    "Outros": "sum",
                    "TB": "sum",
                    "Comercio": "sum",
                    "Total": "sum"
                }).reset_index()
                df_audit["Delta_Total"] = df_audit.groupby("Quarteirao")["Total"].pct_change() * 100
                df_audit.to_csv(ARQUIVO_AUDITORIA, index=False)
        except:
            pass

    salvar_backup_automatico()

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown("### 📤 Salvar Backup Completo")
        arquivos_para_backup = [ARQUIVO_VISTORIAS, ARQUIVO_RECONHECIMENTO, ARQUIVO_AUDITORIA]
        arquivos_existentes = [f for f in arquivos_para_backup if os.path.exists(f)]

        if arquivos_existentes:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for arq in arquivos_existentes:
                    zip_file.write(arq)
            zip_buffer.seek(0)
            st.download_button(
                label="💾 Baixar Backup (.zip)",
                data=zip_buffer,
                file_name=f"backup_ace_{datetime.today().strftime('%Y-%m-%d')}.zip",
                mime="application/zip",
            )
            # Botão extra para baixar auditoria separada
            if os.path.exists(ARQUIVO_AUDITORIA):
                st.download_button(
                    label="📥 Baixar Relatório de Auditoria (CSV)",
                    data=open(ARQUIVO_AUDITORIA, "rb").read(),
                    file_name=f"auditoria_ace_{datetime.today().strftime('%Y-%m-%d')}.csv",
                    mime="text/csv",
                )
        else:
            st.info("⚠️ Nenhum dado cadastrado para exportar.")

    with col_b2:
        st.markdown("### 📥 Restaurar Backup")
        arquivo_upload = st.file_uploader("Envie seu arquivo ZIP de backup", type="zip")
        if arquivo_upload is not None:
            try:
                with zipfile.ZipFile(arquivo_upload, "r") as zip_ref:
                    zip_ref.extractall(".")
                if os
