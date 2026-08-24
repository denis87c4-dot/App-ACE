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

# Inicialização de estados globais unificados
if "vistorias" not in st.session_state:
    st.session_state.vistorias = []
if "reconhecimento" not in st.session_state:
    st.session_state.reconhecimento = []

# ==================== ABAS PRINCIPAIS ====================
(
    aba_cadastro,
    aba_busca,
    aba_fechadas,
    aba_semanal,
    aba_backup,
    aba_reconhecimento,
) = st.tabs([
    "📝 Relatório Diário",
    "🔍 Busca Avançada",
    "🚪 Imóveis Fechados & Recusas",
    "📈 Relatório Semanal",
    "💾 Central de Backup",
    "📊 Reconhecimento & Auditoria",
])

# ==================== ABA 1: RELATÓRIO DIÁRIO ====================
with aba_cadastro:
  st.subheader("📋 Relatório Diário de Campo (Modo Rápido)")
  st.markdown(
      "⚡ **Modo de Campo Agilizado:** O sistema memoriza seus últimos dados"
      " preenchidos (data, semana, quarteirão, rua e agente). Ao salvar, apenas"
      " o número da casa é limpo para a próxima vistoria!"
  )

  # Extração de listas históricas para os dropdowns inteligentes
  historico_quart = (
      list(
          set(
              [
                  str(v["Quarteirao"])
                  for v in st.session_state.vistorias
                  if "Quarteirao" in v
              ]
          )
      )
      if st.session_state.vistorias
      else []
  )
  historico_ruas = (
      list(
          set([v["Rua"] for v in st.session_state.vistorias if "Rua" in v])
      )
      if st.session_state.vistorias
      else []
  )
  historico_agentes = (
      list(
          set(
              [
                  v["Agente"]
                  for v in st.session_state.vistorias
                  if "Agente" in v and v["Agente"]
              ]
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

      # Dropdown inteligente para Quarteirão (permite selecionar ou digitar novo)
      q_options = [""] + sorted(historico_quart)
      num_quarteirao = st.selectbox(
          "Nº do Quarteirão",
          options=q_options,
          help="Selecione um quarteirão anterior ou digite direto no campo se preferir",
      )
      # Fallback criativo: se quiser digitar livremente caso não esteja na lista
      if not num_quarteirao:
        num_quarteirao = st.text_input(
            "Ou digite o Quarteirão novo", placeholder="Ex: 142B"
        )

    with col2:
      lado = st.number_input(
          "Lado do Quarteirão", min_value=1, value=1, step=1
      )

      # Dropdown inteligente para Rua
      r_options = [""] + sorted(historico_ruas)
      nome_rua = st.selectbox(
          "Nome da Rua / Logradouro",
          options=r_options,
          help="Selecione uma rua recente ou digite",
      )
      if not nome_rua:
        nome_rua = st.text_input("Ou digite a Rua nova", placeholder="Ex: Rua das Flores")

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

      # Dropdown inteligente para Agente
      a_options = [""] + sorted(historico_agentes)
      agente_resp = st.selectbox("Agente Responsável", options=a_options)
      if not agente_resp:
        agente_resp = st.text_input("Ou digite o Agente novo", placeholder="Ex: Denison")

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
      gramas = st.number_input("Gramas (g)", min_value=0.0, format="%.1f", value=0.0)
    with c5:
      depositos = st.number_input("Depósitos", min_value=0, value=0)
    with c6:
      litros = st.number_input("Litros (L)", min_value=0.0, format="%.1f", value=0.0)

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

        st.success(
            f"✅ Imóvel **{num_casa}** (Semana {num_semana}, Rua {nome_rua})"
            " salvo com sucesso! Os campos principais foram mantidos para o"
            " próximo."
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

    with st.expander("👁️ Ver Todos os Registros Diários na Sessão", expanded=False):
      st.dataframe(df_v, use_container_width=True)

      if st.button("🗑️ Limpar Todos os Registros Diários"):
        st.session_state.vistorias = []
        st.session_state.reconhecimento = []
        st.rerun()

# ==================== ABA 2: BUSCA AVANÇADA ====================
with aba_busca:
  st.subheader("🔍 Busca Avançada e Filtros Globais")

  if st.session_state.reconhecimento or st.session_state.vistorias:
    base_escolhida = st.selectbox(
        "Escolha a base para buscar",
        ["Relatório Diário (Vistorias)", "Reconhecimento Integrado"],
    )

    df_base = (
        pd.DataFrame(st.session_state.vistorias)
        if "Diário" in base_escolhida
        else pd.DataFrame(st.session_state.reconhecimento)
    )

    if not df_base.empty:
      termo = st.text_input(
          "🔍 Digite qualquer termo para buscar na base escolhida:",
          placeholder="Ex: Rua das Flores, 142, Normal...",
      )
      if termo:
        mask = (
            df_base.astype(str)
            .apply(lambda x: x.str.contains(termo, case=False, na=False))
            .any(axis=1)
        )
        df_resultado = df_base[mask]
      else:
        df_resultado = df_base

      st.info(f"Mostrando {len(df_resultado)} registros encontrados.")
      st.dataframe(df_resultado, use_container_width=True)
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

    f1, f2, f3 = st.columns(3)
    f1.metric("🚪 Total Fechadas / Recusas", len(df_fechados))
    f2.metric(
        "🏘️ Quarteirões Afetados",
        df_fechados["Quarteirao"].nunique() if not df_fechados.empty else 0,
    )
    f3.metric(
        "👤 Agentes Envolvidos",
        df_fechados["Agente"].nunique() if not df_fechados.empty else 0,
    )

    st.markdown("---")

    if not df_fechados.empty:
      c_filtro1, c_filtro2 = st.columns(2)
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
      if quart_filtro != "Todos":
        df_filtrado_fechados = df_filtrado_fechados[
            df_filtrado_fechados["Quarteirao"] == quart_filtro
        ]
      if agente_filtro != "Todos":
        df_filtrado_fechados = df_filtrado_fechados[
            df_filtrado_fechados["Agente"] == agente_filtro
        ]

      st.markdown("### 📋 Tabela Detalhada (Roteiro de Retorno)")
      st.dataframe(df_filtrado_fechados, use_container_width=True)

      st.markdown("### 📊 Incidência por Quarteirão")
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

# ==================== ABA 5: RECONHECIMIENTO & AUDITORIA ====================
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

# ==================== ABA 6: BACKUP ROBUSTO EM ZIP ====================
with aba_backup:
  st.subheader("🔐 Central de Segurança e Backup Avançado")

  ARQUIVO_VISTORIAS = "vistorias_diarias.csv"
  ARQUIVO_RECONHECIMENTO = "reconhecimento.csv"


  def salvar_backup_automatico():
    try:
      if "vistorias" in st.session_state and st.session_state.vistorias:
        pd.DataFrame(st.session_state.vistorias).to_csv(
            ARQUIVO_VISTORIAS, index=False
        )
      if (
          "reconhecimento" in st.session_state
          and st.session_state.reconhecimento
      ):
        pd.DataFrame(st.session_state.reconhecimento).to_csv(
            ARQUIVO_RECONHECIMENTO, index=False
        )
    except Exception as e:
      print(f"Erro no backup automático: {e}")


  salvar_backup_automatico()

  col_b1, col_b2 = st.columns(2)
  with col_b1:
    st.markdown("### 📤 Salvar Backup Completo (.zip)")
    arquivos_para_backup = [ARQUIVO_VISTORIAS, ARQUIVO_RECONHECIMENTO]
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
    arquivo_upload = st.file_uploader(
        "Envie seu arquivo ZIP de backup anterior", type="zip"
    )
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
