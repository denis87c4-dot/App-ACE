from datetime import datetime
import os
import zipfile
import altair as alt
import pandas as pd
import streamlit as st

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    page_title="Sistema ACE - Gestão Integrada de Endemias", layout="wide"
)

st.title("🛡️ Sistema de Controle de Endemias (ACE - Painel Integrado)")

# ==================== PERSISTÊNCIA AUTOMÁTICA EM DISCO ====================
ARQUIVO_VISTORIAS = "vistorias_diarias.csv"
ARQUIVO_RECONHECIMENTO = "reconhecimento.csv"

# Inicialização de estados globais unificados com recuperação segura do disco
if "vistorias" not in st.session_state:
    if os.path.exists(ARQUIVO_VISTORIAS):
        try:
            df_v_init = pd.read_csv(ARQUIVO_VISTORIAS)
            if "Ciclo" not in df_v_init.columns:
                df_v_init["Ciclo"] = "Ciclo 1"
            st.session_state.vistorias = df_v_init.to_dict("records")
        except Exception:
            st.session_state.vistorias = []
    else:
        st.session_state.vistorias = []

if "reconhecimento" not in st.session_state:
    if os.path.exists(ARQUIVO_RECONHECIMENTO):
        try:
            df_r_init = pd.read_csv(ARQUIVO_RECONHECIMENTO)
            st.session_state.reconhecimento = df_r_init.to_dict("records")
        except Exception:
            st.session_state.reconhecimento = []
    else:
        st.session_state.reconhecimento = []

def salvar_estado_local():
    """Função auxiliar para salvar os dados instantaneamente no disco local"""
    try:
        if st.session_state.vistorias:
            pd.DataFrame(st.session_state.vistorias).to_csv(ARQUIVO_VISTORIAS, index=False)
        elif os.path.exists(ARQUIVO_VISTORIAS):
            os.remove(ARQUIVO_VISTORIAS)
            
        if st.session_state.reconhecimento:
            pd.DataFrame(st.session_state.reconhecimento).to_csv(ARQUIVO_RECONHECIMENTO, index=False)
        elif os.path.exists(ARQUIVO_RECONHECIMENTO):
            os.remove(ARQUIVO_RECONHECIMENTO)
    except Exception as e:
        st.error(f"Erro ao salvar dados localmente: {e}")

def expandir_sequencia_casas(texto_casas):
    """
    Converte entradas como '10, 12, 15 a 20, 22' em uma lista de strings limpas
    """
    if not texto_casas:
        return []
    
    casas_finais = []
    partes = str(texto_casas).split(",")
    for parte in partes:
        parte = parte.strip()
        if not parte:
            continue
        if " a " in parte.lower() or "-" in parte:
            separador = " a " if " a " in parte.lower() else "-"
            sub = parte.lower().split(separador)
            if len(sub) == 2:
                try:
                    inicio = int(''.join(filter(str.isdigit, sub[0])))
                    fim = int(''.join(filter(str.isdigit, sub[1])))
                    prefixo = ''.join(filter(str.isalpha, sub[0]))
                    for n in range(min(inicio, fim), max(inicio, fim) + 1):
                        casas_finais.append(f"{prefixo}{n}" if prefixo else str(n))
                except Exception:
                    casas_finais.append(parte)
            else:
                casas_finais.append(parte)
        else:
            casas_finais.append(parte)
    return casas_finais

# ==================== ABAS PRINCIPAIS ====================
(
    aba_cadastro,
    aba_lote,
    aba_busca,
    aba_gerenciar,
    aba_tratamentos,
    aba_fechadas,
    aba_semanal,
    aba_backup,
    aba_reconhecimento,
    aba_foto,
) = st.tabs([
    "📝 Relatório Diário",
    "⚡ Lote Rápido por Lado",
    "🔍 Busca Avançada & Edição",
    "✏️ Gerenciar Lançamentos",
    "🧪 Análise de Tratamentos",
    "🚪 Imóveis Fechados & Recusas",
    "📈 Relatório Semanal",
    "💾 Central de Backup",
    "📊 Reconhecimento & Auditoria",
    "📸 Leitura por Foto",
])

# ==================== ABA 1: RELATÓRIO DIÁRIO ====================
with aba_cadastro:
    st.subheader("📋 Relatório Diário de Campo (Modo Rápido Individual)")
    
    historico_quart = sorted(list(set([str(v["Quarteirao"]) for v in st.session_state.vistorias if "Quarteirao" in v and v["Quarteirao"]]))) if st.session_state.vistorias else []
    historico_ruas = sorted(list(set([str(v["Rua"]) for v in st.session_state.vistorias if "Rua" in v and v["Rua"]]))) if st.session_state.vistorias else []
    historico_agentes = sorted(list(set([str(v["Agente"]) for v in st.session_state.vistorias if "Agente" in v and v["Agente"]]))) if st.session_state.vistorias else []

    with st.form("form_relatorio_diario", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            data_visita = st.date_input("Data da Visita", value=datetime.today())
            semana_padrao = int(data_visita.strftime("%V"))
            num_semana = st.number_input("📅 Número da Semana Epidemiológica", min_value=1, max_value=53, value=semana_padrao, step=1)
            ciclo_selecionado = st.selectbox("🔄 Ciclo Epidemiológico", ["Ciclo 1", "Ciclo 2", "Ciclo 3", "Ciclo 4", "Ciclo 5", "Ciclo 6"])
            opcoes_q = historico_quart + ["➕ Digitar novo quarteirão..."]
            sel_q = st.selectbox("Nº do Quarteirão", options=opcoes_q, key="select_quarteirao")
            if sel_q == "➕ Digitar novo quarteirão..." or not historico_quart:
                num_quarteirao = st.text_input("Digite o Novo Quarteirão", placeholder="Ex: 56")
            else:
                num_quarteirao = sel_q

        with col2:
            lado = st.number_input("Lado do Quarteirão", min_value=1, value=1, step=1)
            opcoes_r = historico_ruas + ["➕ Digitar nova rua..."]
            sel_r = st.selectbox("Nome da Rua / Logradouro", options=opcoes_r, key="select_rua")
            if sel_r == "➕ Digitar nova rua..." or not historico_ruas:
                nome_rua = st.text_input("Digite a Nova Rua", placeholder="Ex: Rua Menino Jesus")
            else:
                nome_rua = sel_r
            num_casa = st.text_input("Nº / Identificação do Imóvel", placeholder="Ex: 05")

        with col3:
            tipo_imovel = st.selectbox("Tipo de Imóvel", ["Residência (RES)", "Comércio (COM)", "Terreno Baldio (TB)", "Ponto Estratégico (PE)", "Outros (OUT)"])
            hora_entrada = st.time_input("Hora de Entrada", value=datetime.now().time())
            vistoria = st.selectbox("Condição da Vistoria", ["Normal", "Recuperada", "Fechada / Recusa"])
            opcoes_a = historico_agentes + ["➕ Digitar novo agente..."]
            sel_a = st.selectbox("Agente Responsável", options=opcoes_a, key="select_agente")
            if sel_a == "➕ Digitar novo agente..." or not historico_agentes:
                agente_resp = st.text_input("Digite o Nome do Agente", placeholder="Ex: Denison Oliveira")
            else:
                agente_resp = sel_a

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
                st.error("⚠️ Preencha Quarteirão, Rua e Número da Casa.")
            else:
                novo_registro = {
                    "Data": data_visita.strftime("%d/%m/%Y"),
                    "Semana": int(num_semana),
                    "Ciclo": ciclo_selecionado,
                    "Quarteirao": str(num_quarteirao).strip(),
                    "Lado": int(lado),
                    "Rua": str(nome_rua).strip(),
                    "Casa": str(num_casa).strip(),
                    "Tipo Imovel": tipo_imovel,
                    "Hora": hora_entrada.strftime("%H:%M"),
                    "Vistoria": vistoria,
                    "Agente": str(agente_resp).strip(),
                    "Eliminados": int(eliminados),
                    "Tubitos": int(tubitos),
                    "Tratados": int(imoveis_tratados),
                    "Gramas": float(gramas),
                    "Depósitos": int(depositos),
                    "Litros": float(litros),
                }
                st.session_state.vistorias.append(novo_registro)

                res_val, com_val, tb_val, out_val = 0, 0, 0, 0
                if "Residência" in tipo_imovel: res_val = 1
                elif "Comércio" in tipo_imovel: com_val = 1
                elif "Terreno" in tipo_imovel: tb_val = 1
                else: out_val = 1

                registro_rec = {
                    "Quarteirao": str(num_quarteirao).strip(),
                    "Lado": int(lado),
                    "Residencias": res_val,
                    "Outros": out_val,
                    "TB": tb_val,
                    "Comercio": com_val,
                    "Total": 1,
                    "Data": data_visita.strftime("%d/%m/%Y"),
                    "Semana": int(num_semana),
                    "Auditor": agente_resp if agente_resp else "Geral",
                }
                st.session_state.reconhecimento.append(registro_rec)
                salvar_estado_local()
                st.success(f"✅ Imóvel **{num_casa}** salvo com sucesso!")
                st.rerun()

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

# ==================== ABA 2: LOTE RÁPIDO POR LADO ====================
with aba_lote:
    st.subheader("⚡ Cadastro em Lote Rápido por Lado de Quarteirão")
    
    with st.form("form_lote_lado"):
        lc1, lc2, lc3 = st.columns(3)
        with lc1:
            lote_data = st.date_input("Data do Lote", value=datetime.today())
            lote_semana = st.number_input("Semana Epidemiológica", min_value=1, max_value=53, value=int(lote_data.strftime("%V")))
            lote_ciclo = st.selectbox("Ciclo", ["Ciclo 1", "Ciclo 2", "Ciclo 3", "Ciclo 4", "Ciclo 5", "Ciclo 6"])
        with lc2:
            lote_quarteirao = st.text_input("Nº do Quarteirão", placeholder="Ex: 56")
            lote_lado = st.number_input("Lado do Quarteirão", min_value=1, value=1, step=1)
            lote_rua = st.text_input("Nome da Rua / Logradouro", placeholder="Ex: Rua São Benedito")
        with lc3:
            lote_agente = st.text_input("Agente Responsável", placeholder="Ex: Denison Oliveira")
            lote_tipo_padrao = st.selectbox("Tipo Padrão dos Imóveis", ["Residência (RES)", "Comércio (COM)", "Terreno Baldio (TB)", "Ponto Estratégico (PE)", "Outros (OUT)"])

        st.markdown("---")
        casas_abertas_input = st.text_area("1️⃣ Casas Abertas / Vistorias Normais:", placeholder="Ex: 02, 04, 06 a 38, 42")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            casas_fechadas_input = st.text_area("2️⃣ Casas Fechadas / Recusas:", placeholder="Ex: 12, 28")
        with col_f2:
            casas_tratadas_input = st.text_area("3️⃣ Casas que receberam Tratamento:", placeholder="Ex: 08, 14")

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            gramas_padrao = st.number_input("Média de Gramas (g) por imóvel tratado", min_value=0.0, format="%.1f", value=0.0)
        with col_t2:
            depositos_padrao = st.number_input("Média de Depósitos por imóvel tratado", min_value=0, value=0)

        btn_salvar_lote = st.form_submit_button("🚀 Salvar Lote Completo de Imóveis", use_container_width=True)

        if btn_salvar_lote:
            if not lote_quarteirao or not lote_rua or not lote_agente:
                st.error("⚠️ Preencha o Quarteirão, a Rua e o Agente Responsável.")
            else:
                lista_abertas = expandir_sequencia_casas(casas_abertas_input)
                lista_fechadas = expandir_sequencia_casas(casas_fechadas_input)
                lista_tratadas_ids = expandir_sequencia_casas(casas_tratadas_input)

                total_gerado = 0
                data_str = lote_data.strftime("%d/%m/%Y")

                for casa in lista_abertas:
                    foi_tratada = casa in lista_tratadas_ids
                    novo_reg = {
                        "Data": data_str,
                        "Semana": int(lote_semana),
                        "Ciclo": lote_ciclo,
                        "Quarteirao": str(lote_quarteirao).strip(),
                        "Lado": int(lote_lado),
                        "Rua": str(lote_rua).strip(),
                        "Casa": str(casa).strip(),
                        "Tipo Imovel": lote_tipo_padrao,
                        "Hora": "08:00",
                        "Vistoria": "Normal",
                        "Agente": str(lote_agente).strip(),
                        "Eliminados": 1 if foi_tratada else 0,
                        "Tubitos": 0,
                        "Tratados": 1 if foi_tratada else 0,
                        "Gramas": float(gramas_padrao) if foi_tratada else 0.0,
                        "Depósitos": int(depositos_padrao) if foi_tratada else 0,
                        "Litros": 0.0,
                    }
                    st.session_state.vistorias.append(novo_reg)
                    total_gerado += 1

                    res_val, com_val, tb_val, out_val = 0, 0, 0, 0
                    if "Residência" in lote_tipo_padrao: res_val = 1
                    elif "Comércio" in lote_tipo_padrao: com_val = 1
                    elif "Terreno" in lote_tipo_padrao: tb_val = 1
                    else: out_val = 1

                    st.session_state.reconhecimento.append({
                        "Quarteirao": str(lote_quarteirao).strip(),
                        "Lado": int(lote_lado),
                        "Residencias": res_val,
                        "Outros": out_val,
                        "TB": tb_val,
                        "Comercio": com_val,
                        "Total": 1,
                        "Data": data_str,
                        "Semana": int(lote_semana),
                        "Auditor": lote_agente,
                    })

                for casa in lista_fechadas:
                    novo_reg = {
                        "Data": data_str,
                        "Semana": int(lote_semana),
                        "Ciclo": lote_ciclo,
                        "Quarteirao": str(lote_quarteirao).strip(),
                        "Lado": int(lote_lado),
                        "Rua": str(lote_rua).strip(),
                        "Casa": str(casa).strip(),
                        "Tipo Imovel": lote_tipo_padrao,
                        "Hora": "08:00",
                        "Vistoria": "Fechada / Recusa",
                        "Agente": str(lote_agente).strip(),
                        "Eliminados": 0,
                        "Tubitos": 0,
                        "Tratados": 0,
                        "Gramas": 0.0,
                        "Depósitos": 0,
                        "Litros": 0.0,
                    }
                    st.session_state.vistorias.append(novo_reg)
                    total_gerado += 1

                salvar_estado_local()
                st.success(f"🎉 Sucesso! {total_gerado} imóveis foram gerados e salvos!")
                st.rerun()

# ==================== ABA 3: BUSCA AVANÇADA ====================
with aba_busca:
    st.subheader("🔍 Busca Avançada e Edição Direta")
    if st.session_state.vistorias:
        df_base = pd.DataFrame(st.session_state.vistorias)
        for col in df_base.columns:
            if col not in ["Semana", "Lado", "Eliminados", "Tubitos", "Tratados", "Gramas", "Depósitos", "Litros"]:
                df_base[col] = df_base[col].astype(str)

        termo = st.text_input("🔎 Pesquisa rápida por termo:", placeholder="Ex: 56, Rua...")
        df_filtrado = df_base.copy()
        if termo:
            mask = df_filtrado.astype(str).apply(lambda x: x.str.contains(termo, case=False, na=False)).any(axis=1)
            df_filtrado = df_filtrado[mask]

        df_editado = st.data_editor(df_filtrado, use_container_width=True, num_rows="dynamic")

        if st.button("💾 Salvar Alterações Feitas na Tabela", type="primary", use_container_width=True):
            st.session_state.vistorias = df_editado.to_dict("records")
            salvar_estado_local()
            st.success("✅ Alterações salvas com sucesso!")
            st.rerun()
    else:
        st.info("Nenhum registro cadastrado.")

# ==================== ABA 4: GERENCIAR LANÇAMENTOS ====================
with aba_gerenciar:
    st.subheader("✏️ Gerenciamento e Edição Inteligente em Massa")
    if st.session_state.vistorias:
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1: coluna_alvo = st.selectbox("Coluna para alterar", ["Quarteirao", "Semana", "Ciclo", "Agente", "Rua", "Data"])
        with col_m2: valor_antigo = st.text_input("Valor antigo")
        with col_m3: valor_novo = st.text_input("Novo valor")
        with col_m4:
            st.markdown("<br>", unsafe_allow_html=True)
            btn_aplicar_massa = st.button("🚀 Aplicar em Massa", type="primary", use_container_width=True)

        if btn_aplicar_massa and valor_antigo:
            alterados = 0
            for item in st.session_state.vistorias:
                if str(item.get(coluna_alvo, "")).strip().lower() == valor_antigo.strip().lower():
                    item[coluna_alvo] = valor_novo.strip()
                    alterados += 1
            salvar_estado_local()
            st.success(f"✅ {alterados} registros atualizados em massa!")
            st.rerun()
    else:
        st.info("Nenhum lançamento registrado.")

# ==================== ABA 5: ANÁLISE DE TRATAMENTOS ====================
with aba_tratamentos:
    st.subheader("🧪 Painel de Tratamentos")
    if st.session_state.vistorias:
        df_trat = pd.DataFrame(st.session_state.vistorias)
        tot_tratados = int(df_trat["Tratados"].sum()) if "Tratados" in df_trat.columns else 0
        tot_gramas = float(df_trat["Gramas"].sum()) if "Gramas" in df_trat.columns else 0.0
        
        tm1, tm2 = st.columns(2)
        tm1.metric("🏠 Imóveis Tratados", tot_tratados)
        tm2.metric("⚖️ Larvicida Aplicado (g)", f"{tot_gramas:.1f}g")
    else:
        st.info("Nenhum lançamento registrado.")

# ==================== ABA 6: IMÓVEIS FECHADOS & RECUSAS ====================
with aba_fechadas:
    st.subheader("🚪 Imóveis Fechados e Recusas")
    if st.session_state.vistorias:
        df_v = pd.DataFrame(st.session_state.vistorias)
        df_fechados = df_v[df_v["Vistoria"].str.contains("Fechada", case=False, na=False)]
        st.metric("Total Fechadas / Recusas", len(df_fechados))
        st.dataframe(df_fechados, use_container_width=True)
    else:
        st.info("Sem dados cadastrados.")

# ==================== ABA 7: RELATÓRIO SEMANAL ====================
with aba_semanal:
    st.subheader("📈 Boletim Semanal Consolidado")
    if st.session_state.vistorias:
        df_v = pd.DataFrame(st.session_state.vistorias)
        df_agrupado = df_v.groupby("Semana").agg(Total_Visitas=("Casa", "count"), Eliminados=("Eliminados", "sum"), Tratados=("Tratados", "sum")).reset_index()
        st.dataframe(df_agrupado, use_container_width=True)
    else:
        st.info("Sem dados cadastrados.")

# ==================== ABA 8: CENTRAL DE BACKUP ====================
with aba_backup:
    st.subheader("🔐 Central de Segurança e Backup")
    col_b1, col_b2 = st.columns(2)

    with col_b1:
        st.markdown("### 📤 Exportar Dados")
        salvar_estado_local()
        if os.path.exists(ARQUIVO_VISTORIAS):
            with open(ARQUIVO_VISTORIAS, "rb") as f:
                st.download_button("📥 Baixar vistorias_diarias.csv", data=f, file_name="vistorias_diarias.csv", mime="text/csv", use_container_width=True)

    with col_b2:
        st.markdown("### 📥 Importação de Planilha CSV")
        arquivo_upload = st.file_uploader("Enviar arquivo CSV", type=["csv", "txt"])

        if arquivo_upload is not None:
            try:
                df_novo_importado = pd.read_csv(arquivo_upload)
                st.success("✅ Arquivo lido com sucesso!")
                st.dataframe(df_novo_importado.head(5), use_container_width=True)

                if st.button("🔄 Confirmar e Inserir na Base", type="primary", use_container_width=True):
                    st.session_state.vistorias.extend(df_novo_importado.to_dict("records"))
                    salvar_estado_local()
                    st.success("✅ Dados importados com sucesso!")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao processar o arquivo: {e}")

    st.markdown("---")
    if st.button("🗑️ Deletar TODOS os Lançamentos do Sistema", type="primary", use_container_width=True):
        st.session_state.vistorias = []
        st.session_state.reconhecimento = []
        if os.path.exists(ARQUIVO_VISTORIAS): os.remove(ARQUIVO_VISTORIAS)
        if os.path.exists(ARQUIVO_RECONHECIMENTO): os.remove(ARQUIVO_RECONHECIMENTO)
        st.success("🧹 Dados apagados com sucesso!")
        st.rerun()

# ==================== ABA 9: RECONHECIMENTO GEOGRÁFICO ====================
with aba_reconhecimento:
    st.subheader("📊 Reconhecimento Geográfico")
    if st.session_state.reconhecimento:
        df_rec = pd.DataFrame(st.session_state.reconhecimento)
        st.dataframe(df_rec, use_container_width=True)
    else:
        st.info("Sem dados de reconhecimento geográfico.")

# ==================== ABA 10: LEITURA INTELIGENTE POR FOTO ====================
with aba_foto:
    st.subheader("📸 Leitura Inteligente de Boletim por Foto (IA)")
    st.info("Insira sua chave Gemini API para habilitar a leitura por foto.")
    api_key_input = st.text_input("🔑 Chave de API do Gemini", type="password")
    foto_boletim = st.file_uploader("Foto do boletim", type=["png", "jpg", "jpeg"])
    if foto_boletim and api_key_input:
        st.image(foto_boletim, caption="Boletim enviado", use_container_width=True)
