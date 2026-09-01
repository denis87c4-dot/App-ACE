from datetime import datetime
import io
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

# Inicialização de estados globais unificados com recuperação automática do disco
if "vistorias" not in st.session_state:
    if os.path.exists(ARQUIVO_VISTORIAS):
        try:
            df_v_init = pd.read_csv(ARQUIVO_VISTORIAS)
            if "Ciclo" not in df_v_init.columns:
                df_v_init["Ciclo"] = "Ciclo 1"
            st.session_state.vistorias = df_v_init.to_dict("records")
        except:
            st.session_state.vistorias = []
    else:
        st.session_state.vistorias = []

if "reconhecimento" not in st.session_state:
    if os.path.exists(ARQUIVO_RECONHECIMENTO):
        try:
            df_r_init = pd.read_csv(ARQUIVO_RECONHECIMENTO)
            st.session_state.reconhecimento = df_r_init.to_dict("records")
        except:
            st.session_state.reconhecimento = []
    else:
        st.session_state.reconhecimento = []

def salvar_estado_local():
    """Função auxiliar para salvar os dados instantaneamente no disco local"""
    if st.session_state.vistorias:
        pd.DataFrame(st.session_state.vistorias).to_csv(ARQUIVO_VISTORIAS, index=False)
    elif os.path.exists(ARQUIVO_VISTORIAS):
        os.remove(ARQUIVO_VISTORIAS)
        
    if st.session_state.reconhecimento:
        pd.DataFrame(st.session_state.reconhecimento).to_csv(ARQUIVO_RECONHECIMENTO, index=False)
    elif os.path.exists(ARQUIVO_RECONHECIMENTO):
        os.remove(ARQUIVO_RECONHECIMENTO)

# ==================== ABAS PRINCIPAIS ====================
(
    aba_cadastro,
    aba_busca,
    aba_fechadas,
    aba_semanal,
    aba_backup,
    aba_reconhecimento,
    aba_foto,
) = st.tabs([
    "📝 Relatório Diário",
    "🔍 Busca Avançada",
    "🚪 Imóveis Fechados & Recusas",
    "📈 Relatório Semanal",
    "💾 Central de Backup",
    "📊 Reconhecimento & Auditoria",
    "📸 Leitura por Foto",
])


# ==================== ABA 1: RELATÓRIO DIÁRIO ====================
with aba_cadastro:
  st.subheader("📋 Relatório Diário de Campo (Modo Rápido)")
  st.markdown(
      "⚡ **Modo de Campo Agilizado:** O sistema memoriza seus últimos dados"
      " preenchidos. Ao salvar, apenas o número da casa é limpo para a próxima"
      " vistoria!"
  )

  # Extração segura de listas históricas para os dropdowns
  historico_quart = (
      sorted(
          list(
              set(
                  [
                      str(v["Quarteirao"])
                      for v in st.session_state.vistorias
                      if "Quarteirao" in v and v["Quarteirao"]
                  ]
              )
          )
      )
      if st.session_state.vistorias
      else []
  )

  historico_ruas = (
      sorted(
          list(
              set(
                  [
                      str(v["Rua"])
                      for v in st.session_state.vistorias
                      if "Rua" in v and v["Rua"]
                  ]
              )
          )
      )
      if st.session_state.vistorias
      else []
  )

  historico_agentes = (
      sorted(
          list(
              set(
                  [
                      str(v["Agente"])
                      for v in st.session_state.vistorias
                      if "Agente" in v and v["Agente"]
                  ]
              )
          )
      )
      if st.session_state.vistorias
      else []
  )

  with st.form("form_relatorio_diario", clear_on_submit=False):
    col1, col2, col3 = st.columns(3)

    with col1:
      data_visita = st.date_input("Data da Visita", value=datetime.today())
      semana_padrao = int(data_visita.strftime("%V"))
      num_semana = st.number_input(
          "📅 Número da Semana Epidemiológica",
          min_value=1,
          max_value=53,
          value=semana_padrao,
          step=1,
      )

      ciclo_selecionado = st.selectbox(
          "🔄 Ciclo Epidemiológico",
          ["Ciclo 1", "Ciclo 2", "Ciclo 3", "Ciclo 4", "Ciclo 5", "Ciclo 6"],
      )

      opcoes_q = historico_quart + ["➕ Digitar novo quarteirão..."]
      sel_q = st.selectbox("Nº do Quarteirão", options=opcoes_q, key="select_quarteirao")
      
      if sel_q == "➕ Digitar novo quarteirão..." or not historico_quart:
        num_quarteirao = st.text_input(
            "Digite o Novo Quarteirão", placeholder="Ex: 142B", key="input_novo_quarteirao"
        )
      else:
        num_quarteirao = sel_q

    with col2:
      lado = st.number_input(
          "Lado do Quarteirão", min_value=1, value=1, step=1
      )

      opcoes_r = historico_ruas + ["➕ Digitar nova rua..."]
      sel_r = st.selectbox("Nome da Rua / Logradouro", options=opcoes_r, key="select_rua")
      
      if sel_r == "➕ Digitar nova rua..." or not historico_ruas:
        nome_rua = st.text_input(
            "Digite a Nova Rua", placeholder="Ex: Rua das Flores", key="input_nova_rua"
        )
      else:
        nome_rua = sel_r

      num_casa = st.text_input(
          "Nº / Identificação do Imóvel",
          placeholder="Ex: 3A/5, 2/1 (Este limpa a cada salvamento)",
      )

    with col3:
      tipo_imovel = st.selectbox(
          "Tipo de Imóvel",
          [
              "Residência (RES)",
              "Comércio (COM)",
              "Terreno Baldio (TB)",
              "Ponto Estratégico (PE)",
              "Outros (OUT)",
          ],
      )
      hora_entrada = st.time_input(
          "Hora de Entrada", value=datetime.now().time()
      )
      vistoria = st.selectbox(
          "Condição da Vistoria", ["Normal", "Recuperada", "Fechada / Recusa"]
      )

      opcoes_a = historico_agentes + ["➕ Digitar novo agente..."]
      sel_a = st.selectbox("Agente Responsável", options=opcoes_a, key="select_agente")
      
      if sel_a == "➕ Digitar novo agente..." or not historico_agentes:
        agente_resp = st.text_input(
            "Digite o Nome do Agente", placeholder="Ex: Denison", key="input_novo_agente"
        )
      else:
        agente_resp = sel_a

    st.markdown("---")
    st.subheader("🔬 Dados Entomológicos e Tratamento")

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
      eliminados = st.number_input("Eliminados", min_value=0, value=0)
    with c2:
      tubitos = st.number_input("Tubitos", min_value=0, value=0)
    with c3:
      imoveis_tratados = st.number_input("Tratados", min_value=0, value=0)
    with c4:
      gramas = st.number_input(
          "Gramas (g)", min_value=0.0, format="%.1f", value=0.0
      )
    with c5:
      depositos = st.number_input("Depósitos", min_value=0, value=0)
    with c6:
      litros = st.number_input(
          "Litros (L)", min_value=0.0, format="%.1f", value=0.0
      )

    submitted = st.form_submit_button(
        "💾 Salvar Registro Diário", use_container_width=True
    )

    if submitted:
      if not num_quarteirao or not nome_rua or not num_casa:
        st.error(
            "⚠️ Por favor, preencha o Quarteirão, a Rua e o"
            " Número/Identificação da Casa."
        )
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
        if "Residência" in tipo_imovel:
          res_val = 1
        elif "Comércio" in tipo_imovel:
          com_val = 1
        elif "Terreno" in tipo_imovel:
          tb_val = 1
        else:
          out_val = 1

        registro_rec = {
            "Quarteirao": str(num_quarteirao).strip(),
            "Lado": int(lado),
            "Residencias": res_val,
            "Outros": out_val,
            "TB": tb_val,
            "Comercio": com_val,
            "Total": 1,
            "Data Registro": data_visita.strftime("%d/%m/%Y"),
            "Auditor": agente_resp if agente_resp else "Geral",
        }
        st.session_state.reconhecimento.append(registro_rec)

        # 💾 SALVA AUTOMATICAMENTE NO DISCO
        salvar_estado_local()

        st.success(
            f"✅ Imóvel **{num_casa}** na rua **{nome_rua}** salvo com"
            " sucesso!"
        )
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

    st.markdown("---")
    st.subheader("✏️ Gerenciar, Editar ou Excluir Lançamentos")
    st.markdown(
        "Selecione um lançamento abaixo para modificá-lo ou excluí-lo individualmente de forma rápida."
    )

    opcoes_registros = {}
    for idx, reg in enumerate(st.session_state.vistorias):
      ciclo_lbl = reg.get("Ciclo", "Ciclo 1")
      label = (
          f"#{idx+1} | {ciclo_lbl} | Data: {reg['Data']} | Quarteirão: {reg['Quarteirao']} | "
          f"Rua: {reg['Rua']} | Casa: {reg['Casa']} | Condição: {reg['Vistoria']}"
      )
      opcoes_registros[label] = idx

    registro_selecionado = st.selectbox(
        "Selecione o registro para gerenciar",
        options=list(opcoes_registros.keys()),
        key="select_gerenciar_registro"
    )
    idx_selecionado = opcoes_registros[registro_selecionado]
    reg_atual = st.session_state.vistorias[idx_selecionado]

    col_acao1, col_acao2 = st.columns(2)

    with col_acao1:
      if st.button("🗑️ Excluir Este Registro", use_container_width=True, type="secondary"):
        st.session_state.vistorias.pop(idx_selecionado)
        if st.session_state.reconhecimento and idx_selecionado < len(
            st.session_state.reconhecimento
        ):
          st.session_state.reconhecimento.pop(idx_selecionado)
        
        # 💾 SALVA AUTOMATICAMENTE NO DISCO
        salvar_estado_local()

        st.success("✅ Registro excluído com sucesso!")
        st.rerun()

    with col_acao2:
      editar_toggle = st.toggle("✏️ Abrir modo de edição rápida para este item", key="toggle_edicao_rapida")

    if editar_toggle:
      st.markdown("#### 📝 Editando Registro Selecionado")
      with st.form(f"form_edicao_{idx_selecionado}"):
        e_col1, e_col2, e_col3 = st.columns(3)

        with e_col1:
          try:
            dt_parse = datetime.strptime(reg_atual["Data"], "%d/%m/%Y").date()
          except:
            dt_parse = datetime.today()
            
          novo_data_visita = st.date_input("Data da Visita", value=dt_parse, key="edit_dt")
          novo_num_semana = st.number_input("Semana Epidemiológica", min_value=1, max_value=53, value=int(reg_atual.get("Semana", 1)), key="edit_sem")
          
          ciclos_possiveis = ["Ciclo 1", "Ciclo 2", "Ciclo 3", "Ciclo 4", "Ciclo 5", "Ciclo 6"]
          val_ciclo_atual = reg_atual.get("Ciclo", "Ciclo 1")
          idx_ciclo = ciclos_possiveis.index(val_ciclo_atual) if val_ciclo_atual in ciclos_possiveis else 0
          novo_ciclo = st.selectbox("Ciclo Epidemiológico", ciclos_possiveis, index=idx_ciclo, key="edit_ciclo")

        with e_col2:
          novo_quarteirao = st.text_input("Nº do Quarteirão", value=str(reg_atual["Quarteirao"]), key="edit_quart")
          novo_lado = st.number_input("Lado", min_value=1, value=int(reg_atual.get("Lado", 1)), key="edit_lado")
          novo_nome_rua = st.text_input("Nome da Rua", value=str(reg_atual["Rua"]), key="edit_rua")

        with e_col3:
          novo_num_casa = st.text_input("Nº / Identificação do Imóvel", value=str(reg_atual["Casa"]), key="edit_casa")
          
          tipos_possiveis = [
              "Residência (RES)",
              "Comércio (COM)",
              "Terreno Baldio (TB)",
              "Ponto Estratégico (PE)",
              "Outros (OUT)",
          ]
          idx_tipo = tipos_possiveis.index(reg_atual["Tipo Imovel"]) if reg_atual["Tipo Imovel"] in tipos_possiveis else 0
          novo_tipo_imovel = st.selectbox("Tipo de Imóvel", tipos_possiveis, index=idx_tipo, key="edit_tipo")
          
          try:
            hr_parse = datetime.strptime(reg_atual["Hora"], "%H:%M").time()
          except:
            hr_parse = datetime.now().time()
          novo_hora_entrada = st.time_input("Hora de Entrada", value=hr_parse, key="edit_hora")

          condicoes_possiveis = ["Normal", "Recuperada", "Fechada / Recusa"]
          idx_vist = condicoes_possiveis.index(reg_atual["Vistoria"]) if reg_atual["Vistoria"] in condicoes_possiveis else 0
          novo_vistoria = st.selectbox("Condição da Vistoria", condicoes_possiveis, index=idx_vist, key="edit_vist")
          novo_agente_resp = st.text_input("Agente Responsável", value=str(reg_atual["Agente"]), key="edit_agente")

        st.markdown("---")
        st.subheader("🔬 Dados Entomológicos e Tratamento (Edição)")
        ec1, ec2, ec3, ec4, ec5, ec6 = st.columns(6)

        with ec1:
          novo_eliminados = st.number_input("Eliminados", min_value=0, value=int(reg_atual.get("Eliminados", 0)), key="edit_elim")
        with ec2:
          novo_tubitos = st.number_input("Tubitos", min_value=0, value=int(reg_atual.get("Tubitos", 0)), key="edit_tub")
        with ec3:
          novo_imoveis_tratados = st.number_input("Tratados", min_value=0, value=int(reg_atual.get("Tratados", 0)), key="edit_trat")
        with ec4:
          novo_gramas = st.number_input("Gramas (g)", min_value=0.0, format="%.1f", value=float(reg_atual.get("Gramas", 0.0)), key="edit_gram")
        with ec5:
          novo_depositos = st.number_input("Depósitos", min_value=0, value=int(reg_atual.get("Depósitos", 0)), key="edit_dep")
        with ec6:
          novo_litros = st.number_input("Litros (L)", min_value=0.0, format="%.1f", value=float(reg_atual.get("Litros", 0.0)), key="edit_lit")

        salvar_edicao = st.form_submit_button("💾 Salvar Alterações do Registro", use_container_width=True)

        if salvar_edicao:
          st.session_state.vistorias[idx_selecionado] = {
              "Data": novo_data_visita.strftime("%d/%m/%Y"),
              "Semana": int(novo_num_semana),
              "Ciclo": novo_ciclo,
              "Quarteirao": str(novo_quarteirao).strip(),
              "Lado": int(novo_lado),
              "Rua": str(novo_nome_rua).strip(),
              "Casa": str(novo_num_casa).strip(),
              "Tipo Imovel": novo_tipo_imovel,
              "Hora": novo_hora_entrada.strftime("%H:%M"),
              "Vistoria": novo_vistoria,
              "Agente": str(novo_agente_resp).strip(),
              "Eliminados": int(novo_eliminados),
              "Tubitos": int(novo_tubitos),
              "Tratados": int(novo_imoveis_tratados),
              "Gramas": float(novo_gramas),
              "Depósitos": int(novo_depositos),
              "Litros": float(novo_litros),
          }

          if idx_selecionado < len(st.session_state.reconhecimento):
            res_val, com_val, tb_val, out_val = 0, 0, 0, 0
            if "Residência" in novo_tipo_imovel:
              res_val = 1
            elif "Comércio" in novo_tipo_imovel:
              com_val = 1
            elif "Terreno" in novo_tipo_imovel:
              tb_val = 1
            else:
              out_val = 1

            st.session_state.reconhecimento[idx_selecionado] = {
                "Quarteirao": str(novo_quarteirao).strip(),
                "Lado": int(novo_lado),
                "Residencias": res_val,
                "Outros": out_val,
                "TB": tb_val,
                "Comercio": com_val,
                "Total": 1,
                "Data Registro": novo_data_visita.strftime("%d/%m/%Y"),
                "Auditor": novo_agente_resp if novo_agente_resp else "Geral",
            }

          # 💾 SALVA AUTOMATICAMENTE NO DISCO
          salvar_estado_local()

          st.success("✅ Registro atualizado com sucesso!")
          st.rerun()

    with st.expander("👁️ Ver Todos os Registros Diários na Sessão", expanded=False):
      st.dataframe(df_v, use_container_width=True)

      if st.button("🗑️ Limpar Todos os Registros Diários"):
        st.session_state.vistorias = []
        st.session_state.reconhecimento = []
        salvar_estado_local()
        st.rerun()

# ==================== ABA 2: BUSCA AVANÇADA ====================
with aba_busca:
    st.subheader("🔍 Busca Avançada e Filtros Globais")
    st.markdown(
        "Filtre os dados cruzando múltiplos critérios (intervalo de datas, ciclo, semana epidemiológica, "
        "condição da vistoria, tipo de imóvel, agente, quarteirão, rua) ou faça uma busca textual livre."
    )

    if st.session_state.vistorias or st.session_state.reconhecimento:
        base_escolhida = st.selectbox(
            "Escolha a base para filtrar",
            ["Relatório Diário (Vistorias)", "Reconhecimento Integrado"],
            key="select_base_busca"
        )

        df_base = (
            pd.DataFrame(st.session_state.vistorias)
            if "Diário" in base_escolhida
            else pd.DataFrame(st.session_state.reconhecimento)
        )

        if not df_base.empty:
            st.markdown("---")
            st.markdown("### 🎛️ Painel de Filtros Avançados")

            if "Diário" in base_escolhida:
                df_filtrado = df_base.copy()

                if "Ciclo" not in df_filtrado.columns:
                    df_filtrado["Ciclo"] = "Ciclo 1"

                if "Data" in df_filtrado.columns:
                    df_filtrado["Data_dt"] = pd.to_datetime(df_filtrado["Data"], format="%d/%m/%Y", errors="coerce")

                if "Semana" in df_filtrado.columns:
                    df_filtrado["Semana"] = pd.to_numeric(df_filtrado["Semana"], errors="coerce").fillna(1).astype(int)

                if "Data_dt" in df_filtrado.columns and not df_filtrado["Data_dt"].isna().all():
                    st.markdown("📅 **Filtro por Período / Data da Visita**")
                    tipo_filtro_data = st.radio(
                        "Modo de Filtro de Data",
                        ["Todas as Datas", "Data Específica", "Intervalo de Datas (De - Até)"],
                        horizontal=True,
                        key="radio_modo_data"
                    )

                    if tipo_filtro_data == "Data Específica":
                        min_d = df_filtrado["Data_dt"].min().date()
                        max_d = df_filtrado["Data_dt"].max().date()
                        data_especifica = st.date_input("Selecione a Data Exata", value=min_d, min_value=min_d, max_value=max_d, key="filtro_data_unica")
                        df_filtrado = df_filtrado[df_filtrado["Data_dt"].dt.date == data_especifica]

                    elif tipo_filtro_data == "Intervalo de Datas (De - Até)":
                        min_d = df_filtrado["Data_dt"].min().date()
                        max_d = df_filtrado["Data_dt"].max().date()
                        intervalo_datas = st.date_input(
                            "Selecione o Intervalo (Início e Fim)",
                            value=(min_d, max_d),
                            min_value=min_d,
                            max_value=max_d,
                            key="filtro_intervalo_datas"
                        )
                        if isinstance(intervalo_datas, tuple) and len(intervalo_datas) == 2:
                            inicio_dt, fim_dt = intervalo_datas
                            df_filtrado = df_filtrado[
                                (df_filtrado["Data_dt"].dt.date >= inicio_dt) & 
                                (df_filtrado["Data_dt"].dt.date <= fim_dt)
                            ]

                st.markdown("---")
                c_f1, c_f2, c_f3 = st.columns(3)

                with c_f1:
                    if "Ciclo" in df_filtrado.columns:
                        ciclos_disponiveis = ["Todos"] + sorted(list(df_filtrado["Ciclo"].dropna().unique()))
                        filtro_ciclo = st.selectbox("Ciclo Epidemiológico", ciclos_disponiveis, key="filtro_avancado_ciclo")
                        if filtro_ciclo != "Todos":
                            df_filtrado = df_filtrado[df_filtrado["Ciclo"] == filtro_ciclo]

                    if "Vistoria" in df_filtrado.columns:
                        condicoes_disponiveis = ["Todas"] + sorted(list(df_filtrado["Vistoria"].dropna().unique()))
                        filtro_vistoria = st.selectbox("Condição da Vistoria", condicoes_disponiveis, key="filtro_avancado_vistoria")
                        if filtro_vistoria != "Todas":
                            df_filtrado = df_filtrado[df_filtrado["Vistoria"] == filtro_vistoria]

                with c_f2:
                    if "Tipo Imovel" in df_filtrado.columns:
                        tipos_disponiveis = ["Todos"] + sorted(list(df_filtrado["Tipo Imovel"].dropna().unique()))
                        filtro_tipo = st.selectbox("Tipo de Imóvel", tipos_disponiveis, key="filtro_avancado_tipo")
                        if filtro_tipo != "Todos":
                            df_filtrado = df_filtrado[df_filtrado["Tipo Imovel"] == filtro_tipo]

                    if "Semana" in df_filtrado.columns:
                        semanas_disponiveis = ["Todas"] + sorted(list(df_filtrado["Semana"].unique()))
                        filtro_semana = st.selectbox("Semana Epidemiológica", semanas_disponiveis, key="filtro_avancado_semana")
                        if filtro_semana != "Todas":
                            df_filtrado = df_filtrado[df_filtrado["Semana"] == int(filtro_semana)]

                with c_f3:
                    if "Agente" in df_filtrado.columns:
                        agentes_disponiveis = ["Todos"] + sorted(list(df_filtrado["Agente"].dropna().unique()))
                        filtro_agente = st.selectbox("Agente Responsável", agentes_disponiveis, key="filtro_avancado_agente")
                        if filtro_agente != "Todos":
                            df_filtrado = df_filtrado[df_filtrado["Agente"] == filtro_agente]

                    if "Quarteirao" in df_filtrado.columns:
                        quarts_disponiveis = ["Todos"] + sorted(list(df_filtrado["Quarteirao"].dropna().astype(str).unique()))
                        filtro_quart = st.selectbox("Quarteirão", quarts_disponiveis, key="filtro_avancado_quart")
                        if filtro_quart != "Todos":
                            df_filtrado = df_filtrado[df_filtrado["Quarteirao"].astype(str) == filtro_quart]

                if "Data_dt" in df_filtrado.columns:
                    df_filtrado = df_filtrado.drop(columns=["Data_dt"])

                st.markdown("---")
                termo_livre = st.text_input(
                    "🔎 Busca Textual Complementar (Opcional):",
                    placeholder="Digite para refinar ainda mais...",
                    key="filtro_avancado_termo"
                )
                if termo_livre:
                    mask = (
                        df_filtrado.astype(str)
                        .apply(lambda x: x.str.contains(termo_livre, case=False, na=False))
                        .any(axis=1)
                    )
                    df_filtrado = df_filtrado[mask]

                st.markdown("---")
                
                # --- MÉTRICAS DESTACADAS NA FRENTE ---
                if "Vistoria" in df_filtrado.columns:
                    total_normais = len(df_filtrado[df_filtrado["Vistoria"].str.contains("Normal", case=False, na=False)])
                    total_fechadas = len(df_filtrado[df_filtrado["Vistoria"].str.contains("Fechada", case=False, na=False)])
                else:
                    total_normais, total_fechadas = 0, 0

                col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
                col_m1.metric("📊 Total Filtrado", len(df_filtrado))
                col_m2.metric("🏡 Imóveis Normais", total_normais)
                col_m3.metric("🚪 Fechadas / Recusas", total_fechadas)
                if "Eliminados" in df_filtrado.columns:
                    col_m4.metric("🗑️ Dep. Eliminados", int(df_filtrado["Eliminados"].sum()))
                if "Tratados" in df_filtrado.columns:
                    col_m5.metric("🛠️ Imóveis Tratados", int(df_filtrado["Tratados"].sum()))

            else:
                termo_livre = st.text_input(
                    "🔍 Digite qualquer termo para buscar na base de Reconhecimento:",
                    placeholder="Ex: Quarteirão, Auditor...",
                    key="filtro_avancado_recon"
                )
                if termo_livre:
                    mask = (
                        df_base.astype(str)
                        .apply(lambda x: x.str.contains(termo_livre, case=False, na=False))
                        .any(axis=1)
                    )
                    df_filtrado = df_base[mask]
                else:
                    df_filtrado = df_base.copy()

                st.markdown("---")
                col_m1, col_m2 = st.columns(2)
                col_m1.metric("📊 Total de Registros Filtrados", len(df_filtrado))

            st.markdown("### 📋 Resultados da Busca e Filtros")
            st.dataframe(df_filtrado, use_container_width=True)

            if not df_filtrado.empty:
                csv_export = df_filtrado.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Baixar Dados Filtrados (CSV)",
                    data=csv_export,
                    file_name=f"busca_filtrada_ace_{datetime.today().strftime('%Y-%m-%d')}.csv",
                    mime="text/csv",
                    key="btn_download_busca_filtrada"
                )
        else:
            st.info("Nenhum dado disponível nesta base.")
    else:
        st.info("⚠️ Nenhum dado cadastrado no sistema ainda.")

# ==================== ABA 3: IMÓVEIS FECHADOS & RECUSAS ====================
with aba_fechadas:
  st.subheader("🚪 Painel de Imóveis Fechados e Recusas")
  st.markdown(
      "Monitore os imóveis que exigem retorno ou ação de recuperação, filtrados"
      " inteligentemente a partir das vistorias de campo."
  )

  if st.session_state.vistorias:
    df_vistorias = pd.DataFrame(st.session_state.vistorias)
    df_fechados = df_vistorias[
        df_vistorias["Vistoria"].str.contains("Fechada", case=False, na=False)
    ]

    if not df_fechados.empty:
      st.markdown("---")
      c_filtro0, c_filtro1, c_filtro2 = st.columns(3)
      with c_filtro0:
        datas_f = ["Todas as Datas"] + sorted(list(df_fechados["Data"].unique()))
        data_filtro = st.selectbox(
            "Filtrar por Data da Visita", datas_f, key="filtro_data_fechados"
        )
      with c_filtro1:
        quarteiroes_f = ["Todos"] + list(df_fechados["Quarteirao"].unique())
        quart_filtro = st.selectbox(
            "Filtrar por Quarteirão", quarteiroes_f, key="filtro_quart_fechados"
        )
      with c_filtro2:
        agentes_f = ["Todos"] + list(df_fechados["Agente"].unique())
        agente_filtro = st.selectbox(
            "Filtrar por Agente", agentes_f, key="filtro_agente_fechados"
        )

      df_filtrado_fechados = df_fechados.copy()
      if data_filtro != "Todas as Datas":
        df_filtrado_fechados = df_filtrado_fechados[
            df_filtrado_fechados["Data"] == data_filtro
        ]
      if quart_filtro != "Todos":
        df_filtrado_fechados = df_filtrado_fechados[
            df_filtrado_fechados["Quarteirao"] == quart_filtro
        ]
      if agente_filtro != "Todos":
        df_filtrado_fechados = df_filtrado_fechados[
            df_filtrado_fechados["Agente"] == agente_filtro
        ]

      st.markdown("---")
      f1, f2, f3 = st.columns(3)
      f1.metric("🚪 Total Fechadas / Recusas (Filtrado)", len(df_filtrado_fechados))
      f2.metric(
          "🏘️ Quarteirões Afetados",
          df_filtrado_fechados["Quarteirao"].nunique() if not df_filtrado_fechados.empty else 0,
      )
      f3.metric(
          "👤 Agentes Envolvidos",
          df_filtrado_fechados["Agente"].nunique() if not df_filtrado_fechados.empty else 0,
      )

      st.markdown("---")
      st.markdown("### 📋 Tabela Detalhada (Roteiro de Retorno)")
      st.dataframe(df_filtrado_fechados, use_container_width=True)

      st.markdown("### 📊 Incidência por Quarteirão (Base Geral)")
      chart_fechados = (
          alt.Chart(df_fechados)
          .mark_bar(color="#e74c3c")
          .encode(
              x=alt.X("Quarteirao:N", title="Quarteirão"),
              y=alt.Y("count():Q", title="Qtd. Fechadas / Recusas"),
              tooltip=["Quarteirao", "count()"],
          )
          .properties(height=350, title="Concentração de Imóveis Fechados")
      )
      st.altair_chart(chart_fechados, use_container_width=True)
    else:
      st.success(
          "🎉 Excelente! Não há registros de imóveis fechados ou recusas no"
          " momento."
      )
  else:
    st.info(
        "ℹ️ Preencha o 'Relatório Diário' para popular o painel inteligente de"
        " imóveis fechados."
    )

# ==================== ABA 4: RELATÓRIO SEMANAL ====================
with aba_semanal:
  st.subheader("📈 Boletim de Relatório Semanal Consolidado")
  st.markdown(
      "Acompanhe o rendimento e a produtividade agrupados por **Semana"
      " Epidemiológica**, cruzando todas as informações dos relatórios"
      " diários."
  )

  if st.session_state.vistorias:
    df_v = pd.DataFrame(st.session_state.vistorias)
    df_v["Semana"] = (
        pd.to_numeric(df_v["Semana"], errors="coerce").fillna(1).astype(int)
    )

    semanas_disponiveis = sorted(df_v["Semana"].unique())
    col_s1, col_s2 = st.columns([2, 2])
    with col_s1:
      semana_selecionada = st.selectbox(
          "Filtrar por Semana Específica",
          ["Todas as Semanas"] + [f"Semana {s}" for s in semanas_disponiveis],
      )

    if semana_selecionada != "Todas as Semanas":
      num_s_sel = int(semana_selecionada.replace("Semana ", ""))
      df_semana_filtrada = df_v[df_v["Semana"] == num_s_sel]
    else:
      df_semana_filtrada = df_v.copy()

    st.markdown("---")
    st.markdown(f"### 📊 Métricas de Produtividade: **{semana_selecionada}**")

    ws1, ws2, ws3, ws4, ws5 = st.columns(5)
    ws1.metric("🏠 Visitas Realizadas", len(df_semana_filtrada))
    ws2.metric("🗑️ Dep. Eliminados", int(df_semana_filtrada["Eliminados"].sum()))
    ws3.metric("🧪 Tubitos Coletados", int(df_semana_filtrada["Tubitos"].sum()))
    ws4.metric("🛠️ Imóveis Tratados", int(df_semana_filtrada["Tratados"].sum()))
    ws5.metric("⚖️ Larvicida Total", f"{df_semana_filtrada['Gramas'].sum():.1f}g")

    st.markdown("---")

    st.markdown("### 📋 Consolidação Geral por Semana Epidemiológica")
    df_agrupado_semana = (
        df_v.groupby("Semana")
        .agg(
            Total_Visitas=("Casa", "count"),
            Total_Eliminados=("Eliminados", "sum"),
            Total_Tubitos=("Tubitos", "sum"),
            Total_Tratados=("Tratados", "sum"),
            Total_Gramas=("Gramas", "sum"),
            Total_Litros=("Litros", "sum"),
        )
        .reset_index()
    )
    st.dataframe(df_agrupado_semana, use_container_width=True)

    st.markdown("### 📉 Evolução do Volume de Visitas por Semana")
    chart_semanal = (
        alt.Chart(df_agrupado_semana)
        .mark_bar(color="#2980b9", cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X("Semana:N", title="Semana Epidemiológica"),
            y=alt.Y("Total_Visitas:Q", title="Total de Visitas Realizadas"),
            tooltip=[
                "Semana",
                "Total_Visitas",
                "Total_Eliminados",
                "Total_Tratados",
            ],
        )
        .properties(height=350, title="Produtividade Semanal de Campo")
    )
    st.altair_chart(chart_semanal, use_container_width=True)

    if semana_selecionada != "Todas as Semanas":
      with st.expander(
          f"🔎 Ver Detalhes Brutos da {semana_selecionada}", expanded=False
      ):
        st.dataframe(df_semana_filtrada, use_container_width=True)
  else:
    st.info(
        "ℹ️ Preencha o 'Relatório Diário' informando a semana para gerar os"
        " dados consolidados aqui."
    )

# ==================== ABA 5: RECONHECIMENTO & AUDITORIA ====================
with aba_reconhecimento:
  st.subheader("📊 Painel de Reconhecimento Geográfico & Auditoria")
  st.markdown(
      "Visualize o dimensionamento dos quarteirões consolidado a partir das"
      " vistorias de campo e acompanhe a evolução analítica."
  )

  if st.session_state.reconhecimento:
    df_recon = pd.DataFrame(st.session_state.reconhecimento)

    df_consolidado = (
        df_recon.groupby("Quarteirao")
        .agg({
            "Residencias": "sum",
            "Outros": "sum",
            "TB": "sum",
            "Comercio": "sum",
            "Total": "sum",
        })
        .reset_index()
    )

    st.markdown("### 🏘️ Consolidação de Imóveis por Quarteirão")
    st.dataframe(df_consolidado, use_container_width=True)

    if st.session_state.vistorias:
      st.write("---")
      st.subheader("📈 Cruzamento: Planejado x Realizado por Quarteirão")

      df_vist = pd.DataFrame(st.session_state.vistorias)
      df_vist_resumo = (
          df_vist.pivot_table(
              index="Quarteirao",
              columns="Vistoria",
              values="Casa",
              aggfunc="count",
              fill_value=0,
          )
          .reset_index()
      )

      df_integrado = pd.merge(
          df_consolidado, df_vist_resumo, on="Quarteirao", how="left"
      ).fillna(0)
      st.dataframe(df_integrado, use_container_width=True)

    st.write("---")
    st.subheader("📈 Auditoria Comparativa Mensal")
    df_recon["Data"] = pd.to_datetime(
        df_recon["Data Registro"], format="%d/%m/%Y", errors="coerce"
    )
    df_recon["AnoMes"] = df_recon["Data"].dt.to_period("M").astype(str)

    df_audit = (
        df_recon.groupby(["AnoMes", "Quarteirao"])
        .agg({
            "Residencias": "sum",
            "Outros": "sum",
            "TB": "sum",
            "Comercio": "sum",
            "Total": "sum",
        })
        .reset_index()
    )

    df_audit = df_audit.sort_values(by=["Quarteirao", "AnoMes"])
    df_audit["Delta_Total"] = (
        df_audit.groupby("Quarteirao")["Total"].pct_change() * 100
    )

    st.dataframe(df_audit, use_container_width=True)

    st.write("---")
    quarteiroes_disponiveis = df_audit["Quarteirao"].unique()
    if len(quarteiroes_disponiveis) > 0:
      quart_sel = st.selectbox(
          "Selecione o Quarteirão para Auditoria Gráfica", quarteiroes_disponiveis
      )
      df_quart_audit = df_audit[df_audit["Quarteirao"] == quart_sel].sort_values(
          "AnoMes"
      )

      df_melted = df_quart_audit.melt(
          id_vars=["AnoMes"],
          value_vars=["Residencias", "Outros", "TB", "Comercio", "Total"],
          var_name="Categoria",
          value_name="Valor",
      )

      chart_audit = (
          alt.Chart(df_melted)
          .mark_line(point=True)
          .encode(
              x="AnoMes:N",
              y="Valor:Q",
              color="Categoria:N",
              tooltip=["AnoMes", "Categoria", "Valor"],
          )
          .properties(height=400, title=f"Evolução do Quarteirão {quart_sel}")
      )
      st.altair_chart(chart_audit, use_container_width=True)
  else:
    st.info(
        "ℹ️ Realize registros no 'Relatório Diário' para gerar os dados de"
        " reconhecimento e auditoria automaticamente."
    )

# ==================== ABA 6: CENTRAL DE SEGURANÇA E RESTAURAÇÃO ====================
with aba_backup:
  st.subheader("🔐 Central de Segurança e Recuperação de Dados (.zip)")
  st.markdown(
      "O sistema agora salva seus dados **automaticamente no disco local** toda vez que você altera algo. "
      "Mesmo que você fique em background ou feche a aba, seus dados estarão seguros. "
      "Ainda assim, você pode baixar um pacote `.zip` de segurança quando desejar."
  )

  col_b1, col_b2 = st.columns(2)

  with col_b1:
    st.markdown("### 📤 Gerar e Baixar Backup")
    st.markdown(
        "Clique abaixo para baixar um pacote `.zip` atualizado com todos os"
        " seus cadastros atuais."
    )

    salvar_estado_local()
    arquivos_para_backup = [ARQUIVO_VISTORIAS, ARQUIVO_RECONHECIMENTO]
    arquivos_existentes = [f for f in arquivos_para_backup if os.path.exists(f)]

    if arquivos_existentes and (
        st.session_state.vistorias or st.session_state.reconhecimento
    ):
      zip_buffer = io.BytesIO()
      with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for arq in arquivos_existentes:
          zip_file.write(arq)
      zip_buffer.seek(0)
      st.download_button(
          label="💾 Baixar Meu Pacote ZIP de Segurança",
          data=zip_buffer,
          file_name=f"backup_ace_{datetime.today().strftime('%Y-%m-%d')}.zip",
          mime="application/zip",
          use_container_width=True,
      )
    else:
      st.info(
          "ℹ️ Não há registros ativos na sessão atual para gerar o pacote"
          " agora."
      )

  with col_b2:
    st.markdown("### 📥 Recarregar Dados via Backup (.zip)")
    st.markdown(
        "Caso mude de dispositivo ou precise forçar a restauração de um arquivo externo:"
    )

    arquivo_upload = st.file_uploader(
        "Selecione o seu arquivo .zip de backup", type="zip"
    )

    if arquivo_upload is not None:
      st.info(
          "📁 Arquivo ZIP carregado com sucesso. Clique no botão abaixo para"
          " processar e aplicar os dados."
      )

      if st.button(
          "🔄 Confirmar e Recarregar Dados no Sistema",
          use_container_width=True,
          type="primary",
      ):
        try:
          with zipfile.ZipFile(arquivo_upload, "r") as zip_ref:
            zip_ref.extractall(".")

          dados_carregados = False

          if os.path.exists(ARQUIVO_VISTORIAS):
            df_v = pd.read_csv(ARQUIVO_VISTORIAS)
            if "Ciclo" not in df_v.columns:
              df_v["Ciclo"] = "Ciclo 1"
            st.session_state.vistorias = df_v.to_dict("records")
            dados_carregados = True

          if os.path.exists(ARQUIVO_RECONHECIMENTO):
            df_r = pd.read_csv(ARQUIVO_RECONHECIMENTO)
            st.session_state.reconhecimento = df_r.to_dict("records")
            dados_carregados = True

          if dados_carregados:
            salvar_estado_local()
            st.success(
                "✅ Sucesso absoluto! Seus dados foram recarregados e salvos localmente. Atualizando tela..."
            )
            st.rerun()
          else:
            st.warning(
                "⚠️ O arquivo ZIP enviado não continha as tabelas esperadas."
            )
        except Exception as e:
          st.error(f"❌ Erro ao processar o arquivo ZIP: {e}")

# ==================== ABA 7: LEITURA INTELIGENTE POR FOTO ====================
with aba_foto:
    st.subheader("📸 Leitura Inteligente de Boletim por Foto (IA)")
    st.markdown(
        "Envie uma foto nítida do seu boletim de campo preenchido à mão. "
        "A IA vai ler todas as linhas e cadastrar os dados automaticamente para você, "
        "separando apenas o que é necessário para o sistema!"
    )

    api_key_input = st.text_input(
        "🔑 Insira sua Chave de API do Gemini (Google AI Studio)",
        type="password",
        placeholder="AIzaSy...",
        key="input_gemini_key_foto"
    )

    foto_boletim = st.file_uploader(
        "Escolha a foto do boletim de campo (PNG, JPG, JPEG)",
        type=["png", "jpg", "jpeg"],
        key="upload_foto_boletim_ia"
    )

    if foto_boletim is not None:
        st.image(foto_boletim, caption="Boletim enviado para leitura", use_container_width=True)

        if st.button("🚀 Processar Foto e Inserir Todos os Lançamentos", type="primary", use_container_width=True):
            if not api_key_input:
                st.error("⚠️ Por favor, insira sua chave de API do Gemini para continuar.")
            else:
                try:
                    import json
                    from google import genai
                    from google.genai import types

                    client = genai.Client(api_key=api_key_input)
                    image_bytes = foto_boletim.getvalue()

                    prompt_extracao = """
                    Você é um especialista em digitalização de boletins de campo do PNCD (Controle de Endemias).
                    Analise esta imagem de um Resumo Diário de Serviço Antivetorial preenchido à mão.
                    Extraia todas as linhas de vistorias preenchidas na tabela.
                    Para cada linha, retorne estritamente um objeto JSON com os seguintes campos exatos:
                    - "Data": string no formato DD/MM/YYYY (veja no cabeçalho do boletim, ex: "01/09/2026")
                    - "Semana": número inteiro da semana epidemiológica (ex: 36)
                    - "Ciclo": string (ex: "Ciclo 1")
                    - "Quarteirao": string (do campo 'Nº do quarteirão', ex: "56")
                    - "Lado": inteiro (ex: 3 ou 4)
                    - "Rua": string (do campo 'Nome do Logradouro', ex: "Rua Frei Henrique")
                    - "Casa": string (do campo 'Nº' do imóvel, ex: "21", "75C")
                    - "Tipo Imovel": string exatos aceitos pelo app: "Residência (RES)", "Comércio (COM)", "Terreno Baldio (TB)", "Ponto Estratégico (PE)" ou "Outros (OUT)"
                    - "Hora": string no formato HH:MM (ex: "08:00")
                    - "Vistoria": string exata aceita pelo app: "Normal", "Recuperada", ou "Fechada / Recusa"
                    - "Agente": string (do campo 'Assinatura do Agente', ex: "Denison Oliveira")
                    - "Eliminados": inteiro (0 se não houver)
                    - "Tubitos": inteiro (0 se não houver)
                    - "Tratados": inteiro (1 se houver marcação de tratamento, ex: Im. Trat., senão 0)
                    - "Gramas": float (valor numérico do larvicida em gramas, ex: 12.0, senão 0.0)
                    - "Depósitos": inteiro (0 se não houver)
                    - "Litros": float (valor numérico se houver litros, ex: 1200.0, senão 0.0)

                    Retorne APENAS um array JSON válido (começando com [ e terminando com ]) contendo esses objetos, sem markdown extra ou explicações.
                    """

                    with st.spinner("🤖 A IA está lendo o boletim e estruturando os dados..."):
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[
                                types.Part.from_bytes(
                                    data=image_bytes,
                                    mime_type=foto_boletim.type,
                                ),
                                prompt_extracao
                            ]
                        )

                        texto_resposta = response.text.strip()
                        if texto_resposta.startswith("```json"):
                            texto_resposta = texto_resposta[7:-3].strip()
                        elif texto_resposta.startswith("```"):
                            texto_resposta = texto_resposta[3:-3].strip()

                        registros_lidos = json.loads(texto_resposta)

                        if isinstance(registros_lidos, list) and len(registros_lidos) > 0:
                            count_novos = 0
                            for reg in registros_lidos:
                                st.session_state.vistorias.append(reg)

                                tipo_imovel = reg.get("Tipo Imovel", "Residência (RES)")
                                res_val, com_val, tb_val, out_val = 0, 0, 0, 0
                                if "Residência" in tipo_imovel:
                                    res_val = 1
                                elif "Comércio" in tipo_imovel:
                                    com_val = 1
                                elif "Terreno" in tipo_imovel:
                                    tb_val = 1
                                else:
                                    out_val = 1

                                registro_rec = {
                                    "Quarteirao": str(reg["Quarteirao"]).strip(),
                                    "Lado": int(reg.get("Lado", 1)),
                                    "Residencias": res_val,
                                    "Outros": out_val,
                                    "TB": tb_val,
                                    "Comercio": com_val,
                                    "Total": 1,
                                    "Data Registro": reg["Data"],
                                    "Auditor": reg.get("Agente", "Geral"),
                                }
                                st.session_state.reconhecimento.append(registro_rec)
                                count_novos += 1

                            salvar_estado_local()
                            st.success(f"✅ Sucesso! {count_novos} lançamentos foram lidos da foto e salvos automaticamente no sistema!")
                            st.rerun()
                        else:
                            st.warning("⚠️ A IA não conseguiu identificar registros válidos nesta imagem. Tente uma foto mais iluminada e de perto.")

                except Exception as e:
                    st.error(f"❌ Erro ao processar a imagem: {e}")

