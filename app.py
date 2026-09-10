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
            if "Notas" not in df_v_init.columns:
                df_v_init["Notas"] = ""
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
    """Função auxiliar para salvar os dados instantaneamente no disco local e recalcular o reconhecimento por Ciclo"""
    try:
        if st.session_state.vistorias:
            df_v_temp = pd.DataFrame(st.session_state.vistorias)
            df_v_temp.to_csv(ARQUIVO_VISTORIAS, index=False)
            
            # RECONSTRUÇÃO AUTOMÁTICA SEPARANDO POR CICLO, QUARTEIRÃO E LADO
            lista_rec_cons = []
            if "Ciclo" not in df_v_temp.columns:
                df_v_temp["Ciclo"] = "Ciclo 1"
                
            grupos = df_v_temp.groupby(["Ciclo", "Quarteirao", "Lado"])
            for (ciclo_val, q_val, l_val), grupo in grupos:
                res_val = int(grupo["Tipo Imovel"].str.contains("Residência", case=False, na=False).sum())
                com_val = int(grupo["Tipo Imovel"].str.contains("Comércio", case=False, na=False).sum())
                tb_val = int(grupo["Tipo Imovel"].str.contains("Terreno", case=False, na=False).sum())
                out_val = int(grupo["Tipo Imovel"].str.contains("Outros|Ponto", case=False, na=False).sum())
                total_imoveis = len(grupo)
                
                primeira_linha = grupo.iloc[0]
                lista_rec_cons.append({
                    "Ciclo": str(ciclo_val),
                    "Quarteirao": str(q_val),
                    "Lado": int(l_val),
                    "Residencias": res_val,
                    "Comercio": com_val,
                    "TB": tb_val,
                    "Outros": out_val,
                    "Total": total_imoveis,
                    "Data": primeira_linha.get("Data", datetime.today().strftime("%d/%m/%Y")),
                    "Semana": int(primeira_linha.get("Semana", 1)),
                    "Auditor": str(primeira_linha.get("Agente", "Geral"))
                })
            st.session_state.reconhecimento = lista_rec_cons
            pd.DataFrame(st.session_state.reconhecimento).to_csv(ARQUIVO_RECONHECIMENTO, index=False)
            
        else:
            if os.path.exists(ARQUIVO_VISTORIAS):
                os.remove(ARQUIVO_VISTORIAS)
            if os.path.exists(ARQUIVO_RECONHECIMENTO):
                os.remove(ARQUIVO_RECONHECIMENTO)
            st.session_state.reconhecimento = []
    except Exception as e:
        st.error(f"Erro ao salvar dados localmente: {e}")

def colorir_tabela_vistorias(df):
    """Aplica cores condicionais baseadas no status da vistoria e ações entomológicas"""
    def highlight_rows(row):
        color = ''
        if 'Fechada' in str(row.get('Vistoria', '')):
            color = 'background-color: #fff3cd; color: #856404;' 
        elif int(row.get('Tratados', 0)) > 0 or float(row.get('Gramas', 0)) > 0:
            color = 'background-color: #d4edda; color: #155724;' 
        elif int(row.get('Tubitos', 0)) > 0 or int(row.get('Eliminados', 0)) > 0:
            color = 'background-color: #f8d7da; color: #721c24;' 
        return [color] * len(row)
    return df.style.apply(highlight_rows, axis=1)

def expandir_sequencia_casas(texto_casas):
    """Converte entradas como '10, 12, 15 a 20, 22' em uma lista de strings limpas"""
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

        st.markdown("---")
        notas_imovel = st.text_input("📝 Notas / Observações sobre o Imóvel", placeholder="Ex: Cachorro bravo, morador ausente, etc.")

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
                    "Notas": str(notas_imovel).strip(),
                }
                st.session_state.vistorias.append(novo_registro)
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
                        "Notas": "",
                    }
                    st.session_state.vistorias.append(novo_reg)
                    total_gerado += 1

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
                        "Notas": "",
                    }
                    st.session_state.vistorias.append(novo_reg)
                    total_gerado += 1

                salvar_estado_local()
                st.success(f"🎉 Sucesso! {total_gerado} imóveis foram gerados e salvos!")
                st.rerun()

# ==================== ABA 3: BUSCA AVANÇADA ====================
with aba_busca:
    st.subheader("🔍 Busca Avançada, Filtros Dinâmicos e Edição Direta")
    if st.session_state.vistorias:
        df_base = pd.DataFrame(st.session_state.vistorias)
        if "Notas" not in df_base.columns:
            df_base["Notas"] = ""
            
        for col in df_base.columns:
            if col not in ["Semana", "Lado", "Eliminados", "Tubitos", "Tratados", "Gramas", "Depósitos", "Litros"]:
                df_base[col] = df_base[col].astype(str)

        with st.expander("🎛️ Filtros Dinâmicos Avançados", expanded=True):
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1:
                lista_qs = sorted(df_base["Quarteirao"].unique().tolist())
                filtro_q = st.multiselect("Filtrar por Quarteirão", options=lista_qs)
            with f_col2:
                lista_agentes = sorted(df_base["Agente"].unique().tolist())
                filtro_a = st.multiselect("Filtrar por Agente", options=lista_agentes)
            with f_col3:
                lista_tipos = sorted(df_base["Tipo Imovel"].unique().tolist())
                filtro_tipo = st.multiselect("Filtrar por Tipo de Imóvel", options=lista_tipos)
            with f_col4:
                lista_vistorias = sorted(df_base["Vistoria"].unique().tolist())
                filtro_vistoria = st.multiselect("Filtrar por Condição Vistoria", options=lista_vistorias)

        termo = st.text_input("🔎 Pesquisa rápida por termo livre (Rua, Casa, etc.):", placeholder="Ex: Rua São Benedito, 05...")
        
        df_filtrado = df_base.copy()
        if filtro_q:
            df_filtrado = df_filtrado[df_filtrado["Quarteirao"].isin(filtro_q)]
        if filtro_a:
            df_filtrado = df_filtrado[df_filtrado["Agente"].isin(filtro_a)]
        if filtro_tipo:
            df_filtrado = df_filtrado[df_filtrado["Tipo Imovel"].isin(filtro_tipo)]
        if filtro_vistoria:
            df_filtrado = df_filtrado[df_filtrado["Vistoria"].isin(filtro_vistoria)]
            
        if termo:
            mask = df_filtrado.astype(str).apply(lambda x: x.str.contains(termo, case=False, na=False)).any(axis=1)
            df_filtrado = df_filtrado[mask]

        st.info(f"Mostrando {len(df_filtrado)} registros filtrados de um total de {len(df_base)}.")
        st.dataframe(colorir_tabela_vistorias(df_filtrado), use_container_width=True)

        df_editado = st.data_editor(df_filtrado, use_container_width=True, num_rows="dynamic", key="editor_busca")

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
        st.info("Utilize os filtros abaixo para selecionar exatamente quais registros deseja atualizar em massa.")
        
        df_massa_base = pd.DataFrame(st.session_state.vistorias)
        
        gm1, gm2, gm3 = st.columns(3)
        with gm1:
            filtro_m_ciclo = st.selectbox("Filtrar por Ciclo Alvo", ["Todos os Ciclos"] + sorted(df_massa_base["Ciclo"].unique().tolist()))
        with gm2:
            filtro_m_agente = st.selectbox("Filtrar por Agente Alvo", ["Todos os Agentes"] + sorted(df_massa_base["Agente"].unique().tolist()))
        with gm3:
            filtro_m_quart = st.selectbox("Filtrar por Quarteirão Alvo", ["Todos os Quarteirões"] + sorted(df_massa_base["Quarteirao"].unique().tolist()))

        df_alvo_massa = df_massa_base.copy()
        if filtro_m_ciclo != "Todos os Ciclos":
            df_alvo_massa = df_alvo_massa[df_alvo_massa["Ciclo"] == filtro_m_ciclo]
        if filtro_m_agente != "Todos os Agentes":
            df_alvo_massa = df_alvo_massa[df_alvo_massa["Agente"] == filtro_m_agente]
        if filtro_m_quart != "Todos os Quarteirões":
            df_alvo_massa = df_alvo_massa[df_alvo_massa["Quarteirao"] == filtro_m_quart]

        st.warning(f"⚠️ A alteração em massa afetará apenas os **{len(df_alvo_massa)}** registros correspondentes aos filtros acima.")

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1: coluna_alvo = st.selectbox("Coluna para alterar", ["Quarteirao", "Semana", "Ciclo", "Agente", "Rua", "Data"])
        with col_m2: valor_antigo = st.text_input("Valor antigo a substituir")
        with col_m3: valor_novo = st.text_input("Novo valor")
        with col_m4:
            st.markdown("<br>", unsafe_allow_html=True)
            btn_aplicar_massa = st.button("🚀 Aplicar em Massa Filtrado", type="primary", use_container_width=True)

        if btn_aplicar_massa and valor_antigo:
            alterados = 0
            indices_validos = df_alvo_massa.index.tolist()
            for idx in indices_validos:
                item = st.session_state.vistorias[idx]
                if str(item.get(coluna_alvo, "")).strip().lower() == valor_antigo.strip().lower():
                    item[coluna_alvo] = valor_novo.strip()
                    alterados += 1
            salvar_estado_local()
            st.success(f"✅ {alterados} registros atualizados com sucesso!")
            st.rerun()
    else:
        st.info("Nenhum lançamento registrado.")

# ==================== ABA 5: ANÁLISE DE TRATAMENTOS ====================
with aba_tratamentos:
    st.subheader("🧪 Painel Avançado de Análise de Tratamentos e Larvicidas")
    if st.session_state.vistorias:
        df_trat = pd.DataFrame(st.session_state.vistorias)
        df_apenas_tratados = df_trat[(df_trat["Tratados"] > 0) | (df_trat["Gramas"] > 0)]
        
        tot_tratados = int(df_trat["Tratados"].sum()) if "Tratados" in df_trat.columns else 0
        tot_gramas = float(df_trat["Gramas"].sum()) if "Gramas" in df_trat.columns else 0.0
        tot_depositos = int(df_trat["Depósitos"].sum()) if "Depósitos" in df_trat.columns else 0
        media_gramas = (tot_gramas / tot_tratados) if tot_tratados > 0 else 0.0

        tm1, tm2, tm3, tm4 = st.columns(4)
        tm1.metric("🏠 Imóveis Tratados", tot_tratados)
        tm2.metric("⚖️ Larvicida Total Aplicado", f"{tot_gramas:.1f}g")
        tm3.metric("🚰 Depósitos Tratados", tot_depositos)
        tm4.metric("📊 Média de Gramas / Imóvel", f"{media_gramas:.2f}g")

        st.markdown("---")
        if not df_apenas_tratados.empty:
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown("### 📊 Larvicida (g) por Quarteirão")
                df_q_gramas = df_apenas_tratados.groupby("Quarteirao")["Gramas"].sum().reset_index()
                chart_q = alt.Chart(df_q_gramas).mark_bar(color="#28a745").encode(
                    x=alt.X("Quarteirao:N", title="Quarteirão"),
                    y=alt.Y("Gramas:Q", title="Total Gramas (g)"),
                    tooltip=["Quarteirao", "Gramas"]
                ).interactive()
                st.altair_chart(chart_q, use_container_width=True)

            with col_g2:
                st.markdown("### 👨‍💼 Tratamentos por Agente")
                df_a_trat = df_apenas_tratados.groupby("Agente")["Tratados"].sum().reset_index()
                chart_a = alt.Chart(df_a_trat).mark_bar(color="#17a2b8").encode(
                    x=alt.X("Agente:N", title="Agente"),
                    y=alt.Y("Tratados:Q", title="Imóveis Tratados"),
                    tooltip=["Agente", "Tratados"]
                ).interactive()
                st.altair_chart(chart_a, use_container_width=True)

            st.markdown("### 📋 Relação Detalhada de Imóveis Tratados")
            st.dataframe(colorir_tabela_vistorias(df_apenas_tratados), use_container_width=True)
        else:
            st.info("Nenhum imóvel com registro de tratamento encontrado.")
    else:
        st.info("Nenhum lançamento registrado.")

# ==================== ABA 6: IMÓVEIS FECHADOS & RECUSAS ====================
with aba_fechadas:
    st.subheader("🚪 Imóveis Fechados e Recusas (Recuperação Rápida)")
    if st.session_state.vistorias:
        df_v = pd.DataFrame(st.session_state.vistorias)
        df_fechados = df_v[df_v["Vistoria"].str.contains("Fechada", case=False, na=False)]
        
        st.metric("Total Fechadas / Recusas Pendentes", len(df_fechados))
        
        if not df_fechados.empty:
            st.markdown("### 🔄 Recuperar Imóvel Fechado Instantaneamente")
            st.info("Se encontrou um morador e realizou a vistoria em um imóvel fechado, selecione-o abaixo para mudar o status para **Recuperada** ou **Normal**:")
            
            df_fechados["Opcao_Display"] = df_fechados.apply(lambda r: f"Quarteirão: {r['Quarteirao']} | Rua: {r['Rua']} | Nº: {r['Casa']} (Lado {r['Lado']})", axis=1)
            
            imovel_escolhido = st.selectbox("Selecione o Imóvel Fechado para Atualizar", options=df_fechados["Opcao_Display"].tolist())
            
            if imovel_escolhido:
                idx_original = df_fechados[df_fechados["Opcao_Display"] == imovel_escolhido].index[0]
                
                col_up1, col_up2, col_up3 = st.columns(3)
                with col_up1:
                    novo_status_vistoria = st.selectbox("Novo Status da Vistoria", ["Recuperada", "Normal", "Fechada / Recusa"])
                with col_up2:
                    qtd_tratados_rec = st.number_input("Tratados?", min_value=0, value=0)
                with col_up3:
                    qtd_gramas_rec = st.number_input("Gramas (g)?", min_value=0.0, format="%.1f", value=0.0)
                
                if st.button("✅ Atualizar Status deste Imóvel Agora", type="primary", use_container_width=True):
                    st.session_state.vistorias[idx_original]["Vistoria"] = novo_status_vistoria
                    st.session_state.vistorias[idx_original]["Tratados"] = int(qtd_tratados_rec)
                    st.session_state.vistorias[idx_original]["Gramas"] = float(qtd_gramas_rec)
                    if qtd_tratados_rec > 0:
                        st.session_state.vistorias[idx_original]["Eliminados"] = 1
                    
                    salvar_estado_local()
                    st.success(f"🎉 Imóvel atualizado com sucesso para '{novo_status_vistoria}'!")
                    st.rerun()

        st.markdown("---")
        st.dataframe(colorir_tabela_vistorias(df_fechados), use_container_width=True)
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
    st.subheader("🔐 Central de Segurança, Backup de Emergência e Compactação ZIP")
    salvar_estado_local()
    
    col_b1, col_b2, col_b3 = st.columns(3)

    with col_b1:
        st.markdown("### 📄 Exportar CSV Simples")
        if os.path.exists(ARQUIVO_VISTORIAS):
            with open(ARQUIVO_VISTORIAS, "rb") as f:
                st.download_button("📥 Baixar vistorias_diarias.csv", data=f, file_name="vistorias_diarias.csv", mime="text/csv", use_container_width=True)

    with col_b2:
        st.markdown("### 📦 Backup Compactado (ZIP)")
        if st.button("🗜️ Gerar Arquivo ZIP de Emergência", use_container_width=True):
            zip_nome = "backup_emergencia_ace.zip"
            with zipfile.ZipFile(zip_nome, 'w') as zipf:
                if os.path.exists(ARQUIVO_VISTORIAS):
                    zipf.write(ARQUIVO_VISTORIAS)
                if os.path.exists(ARQUIVO_RECONHECIMENTO):
                    zipf.write(ARQUIVO_RECONHECIMENTO)
            
            with open(zip_nome, "rb") as f:
                st.download_button("📥 Baixar ZIP de Emergência", data=f, file_name=zip_nome, mime="application/zip", use_container_width=True)

    with col_b3:
        st.markdown("### 🔄 Restaurar de Backup")
        arquivo_upload = st.file_uploader("Enviar CSV ou ZIP", type=["csv", "txt", "zip"])
        if arquivo_upload is not None:
            try:
                if arquivo_upload.name.endswith('.zip'):
                    with zipfile.ZipFile(arquivo_upload, 'r') as z:
                        z.extractall()
                    st.success("✅ Backup ZIP restaurado com sucesso no disco!")
                else:
                    df_novo_importado = pd.read_csv(arquivo_upload)
                    st.session_state.vistorias.extend(df_novo_importado.to_dict("records"))
                    salvar_estado_local()
                    st.success("✅ Dados do CSV incorporados com sucesso!")
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

# ==================== ABA 9: RECONHECIMENTO GEOGRÁFICO & COMPARATIVO DE CICLOS ====================
with aba_reconhecimento:
    st.subheader("📊 Reconhecimento Geográfico Consolidado & Comparativo entre Ciclos")
    salvar_estado_local()
    
    if st.session_state.reconhecimento:
        df_rec = pd.DataFrame(st.session_state.reconhecimento)
        
        # 🎛️ Filtro por Ciclo para a Tabela Principal
        ciclos_disponiveis = sorted(df_rec["Ciclo"].unique().tolist())
        ciclo_selecionado_rec = st.selectbox("🔄 Selecione o Ciclo para Visualizar o Reconhecimento", options=ciclos_disponiveis)
        
        df_rec_filtrado = df_rec[df_rec["Ciclo"] == ciclo_selecionado_rec]
        
        # Métricas Globais do Ciclo Selecionado
        rc1, rc2, rc3, rc4, rc5 = st.columns(5)
        rc1.metric("🏠 Total Imóveis", int(df_rec_filtrado["Total"].sum()))
        rc2.metric("🏡 Residências", int(df_rec_filtrado["Residencias"].sum()))
        rc3.metric("🛒 Comércios", int(df_rec_filtrado["Comercio"].sum()))
        rc4.metric("🧱 Terrenos Baldios", int(df_rec_filtrado["TB"].sum()))
        rc5.metric("📌 Outros / PE", int(df_rec_filtrado["Outros"].sum()))

        st.markdown("---")
        st.markdown(f"### 📋 Tabela Principal Consolidada por Quarteirão ({ciclo_selecionado_rec})")
        
        # Agrupando por Quarteirão para a tabela principal ficar somada perfeitamente
        df_tabela_mestre = df_rec_filtrado.groupby(["Quarteirao", "Lado"]).agg({
            "Residencias": "sum",
            "Comercio": "sum",
            "TB": "sum",
            "Outros": "sum",
            "Total": "sum",
            "Auditor": "first"
        }).reset_index()
        
        st.dataframe(df_tabela_mestre, use_container_width=True)

        st.markdown("---")
        st.markdown("### 📊 Gráficos de Distribuição do Reconhecimento")
        c_gr1, c_gr2 = st.columns(2)
        
        with c_gr1:
            st.markdown("#### Total de Imóveis por Quarteirão")
            chart_rec_q = alt.Chart(df_tabela_mestre).mark_bar(color="#007bff").encode(
                x=alt.X("Quarteirao:N", title="Quarteirão"),
                y=alt.Y("Total:Q", title="Total de Imóveis"),
                tooltip=["Quarteirao", "Lado", "Total", "Residencias"]
            ).interactive()
            st.altair_chart(chart_rec_q, use_container_width=True)

        with c_gr2:
            st.markdown("#### Proporção por Tipo de Imóvel")
            df_pizza = pd.DataFrame({
                "Tipo": ["Residências", "Comércio", "Terrenos Baldios", "Outros"],
                "Quantidade": [
                    df_tabela_mestre["Residencias"].sum(),
                    df_tabela_mestre["Comercio"].sum(),
                    df_tabela_mestre["TB"].sum(),
                    df_tabela_mestre["Outros"].sum()
                ]
            })
            chart_pizza = alt.Chart(df_pizza).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Quantidade", type="quantitative"),
                color=alt.Color(field="Tipo", type="nominal"),
                tooltip=["Tipo", "Quantidade"]
            ).interactive()
            st.altair_chart(chart_pizza, use_container_width=True)

        # 🔄 COMPARATIVO ENTRE CICLOS
        if len(ciclos_disponiveis) > 1:
            st.markdown("---")
            st.markdown("### 📈 Comparativo de Reconhecimento entre os Ciclos")
            st.info("Veja abaixo a evolução e a variação do total de imóveis catalogados de um ciclo para o outro.")
            
            df_comparativo = df_rec.groupby("Ciclo").agg({
                "Total": "sum",
                "Residencias": "sum",
                "Comercio": "sum",
                "TB": "sum"
            }).reset_index()
            
            st.dataframe(df_comparativo, use_container_width=True)
            
            chart_comp = alt.Chart(df_comparativo).mark_bar().encode(
                x=alt.X("Ciclo:N", title="Ciclo Epidemiológico"),
                y=alt.Y("Total:Q", title="Total Geral de Imóveis Vistoriados"),
                color=alt.Color("Ciclo:N", legend=None),
                tooltip=["Ciclo", "Total", "Residencias", "Comercio", "TB"]
            ).interactive()
            st.altair_chart(chart_comp, use_container_width=True)
        else:
            st.info("💡 Dica: Quando você registrar dados em mais de um ciclo (ex: Ciclo 1 e Ciclo 2), aparecerá aqui um painel comparativo completo entre eles.")
    else:
        st.info("Sem dados de reconhecimento geográfico acumulados.")

# ==================== ABA 10: LEITURA INTELIGENTE POR FOTO ====================
with aba_foto:
    st.subheader("📸 Leitura Inteligente de Boletim por Foto (IA)")
    st.info("Insira sua chave Gemini API para habilitar a leitura por foto.")
    api_key_input = st.text_input("🔑 Chave de API do Gemini", type="password")
    foto_boletim = st.file_uploader("Foto do boletim", type=["png", "jpg", "jpeg"])
    if foto_boletim and api_key_input:
        st.image(foto_boletim, caption="Boletim enviado", use_container_width=True)
