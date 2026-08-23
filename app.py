Import streamlit as st
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
if "reconhecimento" not in st.session_state:
    st.session_state.reconhecimento = []

# ==================== ABAS PRINCIPAIS ====================
aba_cadastro, aba_busca, aba_backup, aba_reconhecimento = st.tabs(
    [
        "📝 Relatório Diário",
        "🔍 Busca Avançada & Recuperação",
        "💾 Central de Backup",
        "📊 Reconhecimento & Auditoria",
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
            # CORRIGIDO: Lado do quarteirão apenas com números inteiros
            lado = st.number_input("Lado do Quarteirão", min_value=1, value=1, step=1, help="Digite apenas o número do lado (Ex: 1, 2, 3...)")
            
        with col2:
            nome_rua = st.text_input("Nome da Rua / Logradouro")
            # Suporta alfanuméricos, barras e traços (ex: 2/1, 3A/5, Lote 12)
            num_casa = st.text_input("Nº / Identificação do Imóvel", placeholder="Ex: 3A/5, 2/1")
            
            # Dropdown de Tipos de Imóvel comuns em endemias
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
        
        with c1:
            eliminados = st.number_input("Eliminados", min_value=0, value=0, help="Depósitos eliminados")
        with c2:
            tubitos = st.number_input("Tubitos", min_value=0, value=0, help="Amostras de larvas")
        with c3:
            imoveis_tratados = st.number_input("Tratados", min_value=0, value=0, help="Imóveis tratados")
        with c4:
            gramas = st.number_input("Gramas (g)", min_value=0.0, format="%.1f", value=0.0)
        with c5:
            depositos = st.number_input("Depósitos", min_value=0, value=0, help="Qtd de depósitos")
        with c6:
            litros = st.number_input("Litros (L)", min_value=0.0, format="%.1f", value=0.0)

        submitted = st.form_submit_button("💾 Salvar Registro Diário", use_container_width=True)

        if submitted:
            if not num_quarteirao or not nome_rua or not num_casa:
                st.error("⚠️ Por favor, preencha o Quarteirão, a Rua e o Número/Identificação da Casa.")
            else:
                novo_registro = {
                    "Data": data_visita.strftime("%d/%m/%Y"),
                    "Quarteirao": str(num_quarteirao).strip(),
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

    # --- PAINEL DE RESUMO DO DIA ---
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

# ==================== ABA 2: BUSCA AVANÇADA ====================
with aba_busca:
    st.subheader("🔍 Busca Avançada e Filtros Globais")
    
    if st.session_state.reconhecimento or st.session_state.vistorias:
        base_escolhida = st.selectbox("Escolha a base para buscar", ["Relatório Diário (Vistorias)", "Reconhecimento"])
        
        df_base = pd.DataFrame(st.session_state.vistorias) if "Diário" in base_escolhida else pd.DataFrame(st.session_state.reconhecimento)
        
        if not df_base.empty:
            termo = st.text_input("🔍 Digite qualquer termo para buscar na base escolhida:", placeholder="Ex: Rua das Flores, 142, Normal...")
            if termo:
                mask = df_base.astype(str).apply(lambda x: x.str.contains(termo, case=False, na=False)).any(axis=1)
                df_resultado = df_base[mask]
            else:
                df_resultado = df_base
                
            st.info(f"Mostrando {len(df_resultado)} registros encontrados.")
            st.dataframe(df_resultado, use_container_width=True)
        else:
            st.info("Nenhum dado disponível nesta base.")
    else:
        st.info("⚠️ Nenhum dado cadastrado no sistema ainda.")

# ==================== ABA 4: RECONHECIMENTO & AUDITORIA ====================
with aba_reconhecimento:
    st.subheader("📊 Reconhecimento de Imóveis & Integração com Vistorias")
    st.markdown("Cadastre a quantidade de imóveis por categoria em cada quarteirão e cruze com o relatório diário.")

    with st.form("form_reconhecimento", clear_on_submit=True):
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            quarteirao_rec = st.text_input("Número do Quarteirão", placeholder="Ex: 142")
        with col_r2:
            lado_rec = st.number_input("Lado do Quarteirão", min_value=1, value=1, step=1, key="lado_rec")

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
                    "Lado": int(lado_rec),
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
        st.subheader("📈 Cruzamento: Planejado (Reconhecimento) x Realizado (Diário)")
        
        df_recon = pd.DataFrame(st.session_state.reconhecimento)
        
        if st.session_state.vistorias:
            df_vist = pd.DataFrame(st.session_state.vistorias)
            df_vist_resumo = df_vist.pivot_table(
                index="Quarteirao", 
                columns="Vistoria", 
                values="Casa", 
                aggfunc="count", 
                fill_value=0
            ).reset_index()
            
            df_integrado = pd.merge(df_recon, df_vist_resumo, on="Quarteirao", how="left").fillna(0)
            st.dataframe(df_integrado, use_container_width=True)
        else:
            st.info("ℹ️ Cadastre dados no 'Relatório Diário' para habilitar o cruzamento automático por quarteirão.")
            st.dataframe(df_recon, use_container_width=True)

        # Auditoria comparativa por mês com ordenação cronológica rigorosa
        st.write("---")
        st.subheader("📈 Auditoria Comparativa Mensal por Quarteirão")
        df_recon["Data"] = pd.to_datetime(df_recon["Data Registro"], format="%d/%m/%Y")
        df_recon["AnoMes"] = df_recon["Data"].dt.to_period("M").astype(str)

        df_audit = df_recon.groupby(["AnoMes", "Quarteirao"]).agg({
            "Residencias": "sum", "Outros": "sum", "TB": "sum", "Comercio": "sum", "Total": "sum"
        }).reset_index()

        df_audit = df_audit.sort_values(by=["Quarteirao", "AnoMes"])
        df_audit["Delta_Total"] = df_audit.groupby("Quarteirao")["Total"].pct_change() * 100

        st.dataframe(df_audit, use_container_width=True)

        # Gráfico analítico
        st.write("---")
        quarteiroes_disponiveis = df_audit["Quarteirao"].unique()
        quart_sel = st.selectbox("Selecione o Quarteirão para Auditoria Gráfica", quarteiroes_disponiveis)
        df_quart_audit = df_audit[df_audit["Quarteirao"] == quart_sel].sort_values("AnoMes")

        chart_audit = alt.Chart(
            df_quart_audit.melt(id_vars=["AnoMes"], value_vars=["Residencias","Outros","TB","Comercio","Total"], var_name="Categoria", value_name="Valor")
        ).mark_line(point=True).encode(
            x="AnoMes",
            y="Valor",
            color="Categoria",
            tooltip=["AnoMes","Categoria","Valor"]
        ).properties(height=400, title=f"Evolução do Quarteirão {quart_sel}")
        st.altair_chart(chart_audit, use_container_width=True)

# ==================== ABA 3: BACKUP ROBUSTO EM ZIP ====================
with aba_backup:
    st.subheader("🔐 Central de Segurança e Backup Avançado")

    ARQUIVO_VISTORIAS = "vistorias_diarias.csv"
    ARQUIVO_RECONHECIMENTO = "reconhecimento.csv"
    ARQUIVO_AUDITORIA = "auditoria.csv"

    def salvar_backup_automatico():
        try:
            if "vistorias" in st.session_state and st.session_state.vistorias:
                pd.DataFrame(st.session_state.vistorias).to_csv(ARQUIVO_VISTORIAS, index=False)
            if "reconhecimento" in st.session_state and st.session_state.reconhecimento:
                df_recon = pd.DataFrame(st.session_state.reconhecimento)
                df_recon.to_csv(ARQUIVO_RECONHECIMENTO, index=False)

                if "Data Registro" in df_recon.columns:
                    df_recon["Data"] = pd.to_datetime(df_recon["Data Registro"], format="%d/%m/%Y")
                    df_recon["AnoMes"] = df_recon["Data"].dt.to_period("M").astype(str)
                    df_audit = df_recon.groupby(["AnoMes", "Quarteirao"]).agg({
                        "Residencias": "sum", "Outros": "sum", "TB": "sum", "Comercio": "sum", "Total": "sum"
                    }).reset_index()
                    df_audit = df_audit.sort_values(by=["Quarteirao", "AnoMes"])
                    df_audit["Delta_Total"] = df_audit.groupby("Quarteirao")["Total"].pct_change() * 100
                    df_audit.to_csv(ARQUIVO_AUDITORIA, index=False)
        except Exception as e:
            print(f"Erro no backup automático: {e}")

    salvar_backup_automatico()

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown("### 📤 Salvar Backup Completo (.zip)")
        arquivos_para_backup = [ARQUIVO_VISTORIAS, ARQUIVO_RECONHECIMENTO, ARQUIVO_AUDITORIA]
        arquivos_existentes = [f for f in arquivos_para_backup if os.path.exists(f)]

        if arquivos_existentes:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for arq in arquivos_existentes:
                    zip_file.write(arq)
            zip_buffer.seek(0)
            st.download_button(
                label="💾 Baixar Pacote de Backup (.zip)",
                data=zip_buffer,
                file_name=f"backup_ace_{datetime.today().strftime('%Y-%m-%d')}.zip",
                mime="application/zip",
            )
        else:
            st.info("⚠️ Nenhum dado cadastrado para exportar.")

    with col_b2:
        st.markdown("### 📥 Restaurar Backup")
        arquivo_upload = st.file_uploader("Envie seu arquivo ZIP de backup anterior", type="zip")
        if arquivo_upload is not None:
            try:
                with zipfile.ZipFile(arquivo_upload, "r") as zip_ref:
                    zip_ref.extractall(".")
                
                if os.path.exists(ARQUIVO_VISTORIAS):
                    df_v = pd.read_csv(ARQUIVO_VISTORIAS)
                    st.session_state.vistorias = df_v.to_dict("records")
                
                if os.path.exists(ARQUIVO_RECONHECIMENTO):
                    df_r = pd.read_csv(ARQUIVO_RECONHECIMENTO)
                    st.session_state.reconhecimento = df_r.to_dict("records")
                    
                st.success("✅ Backup restaurado com sucesso! Atualize a página.")
            except Exception as e:
                st.error(f"❌ Erro ao restaurar o backup: {e}")


