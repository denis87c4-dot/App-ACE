import io, zipfile, os
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from datetime import datetime

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

        # Gráfico de Pizza
        fig1, ax1 = plt.subplots()
        categorias = ["Residências", "Outros", "TB", "Comércio"]
        valores = [total_resid, total_outros, total_tb, total_comercio]
        ax1.pie(valores, labels=categorias, autopct="%1.1f%%", startangle=90)
        ax1.axis("equal")
        st.pyplot(fig1)

        # Gráfico de Barras
        fig2, ax2 = plt.subplots()
        ax2.bar(categorias, valores, color=["#2563EB", "#10B981", "#F59E0B", "#DC2626"])
        ax2.set_ylabel("Quantidade de Imóveis")
        ax2.set_title("Distribuição por Categoria")
        st.pyplot(fig2)

        # Filtro por quarteirão
        st.write("---")
        st.subheader("🔍 Visualização por Quarteirão")
        quarts_unicos = df_recon["Quarteirao"].unique().tolist()
        quart_sel = st.selectbox("Selecione o Quarteirão", quarts_unicos)
        df_quart = df_recon[df_recon["Quarteirao"] == quart_sel]

        if not df_quart.empty:
            vals_q = [
                df_quart["Residencias"].sum(),
                df_quart["Outros"].sum(),
                df_quart["TB"].sum(),
                df_quart["Comercio"].sum(),
            ]
            fig_q, ax_q = plt.subplots()
            ax_q.bar(categorias, vals_q, color=["#2563EB", "#10B981", "#F59E0B", "#DC2626"])
            ax_q.set_title(f"Distribuição no Quarteirão {quart_sel}")
            st.pyplot(fig_q)

# ==================== BACKUP ROBUSTO EM ZIP ====================
with aba_backup:
    st.subheader("🔐 Central de Segurança e Backup Avançado")

    ARQUIVO_VISTORIAS = "vistorias.csv"
    ARQUIVO_RECONHECIMENTO = "reconhecimento.csv"

    def salvar_backup_automatico():
        try:
            if "vistorias" in st.session_state and st.session_state.vistorias:
                pd.DataFrame(st.session_state.vistorias).to_csv(ARQUIVO_VISTORIAS, index=False)
            if "reconhecimento" in st.session_state and st.session_state.reconhecimento:
                pd.DataFrame(st.session_state.reconhecimento).to_csv(ARQUIVO_RECONHECIMENTO, index=False)
        except:
            pass

    salvar_backup_automatico()

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown("### 📤 Salvar Backup Completo")
        arquivos_para_backup = [ARQUIVO_VISTORIAS, ARQUIVO_RECONHECIMENTO]
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
        else:
            st.info("⚠️ Nenhum dado cadastrado para exportar.")

    with col_b2:
        st.markdown("### 📥 Restaurar Backup")
        arquivo_upload = st.file_uploader("Envie seu arquivo ZIP de backup", type="zip")
        if arquivo_upload is not None:
            try:
                with zipfile.ZipFile(arquivo_upload, "r") as zip_ref:
                    zip_ref.extractall(".")
                if os.path.exists(ARQUIVO_VISTORIAS):
                    st.session_state.vistorias = pd.read_csv(ARQUIVO_VISTORIAS).to_dict(orient="records")
                if os.path.exists(ARQUIVO_RECONHECIMENTO):
                    st.session_state.reconhecimento = pd.read_csv(ARQUIVO_RECONHECIMENTO).to_dict(orient="records")
                st.success("✅ Dados restaurados com sucesso! Recarregue a página.")
                if st.button("🔄 Recarregar App"):
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao restaurar arquivo: {e}")
