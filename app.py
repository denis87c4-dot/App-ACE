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

  historico_quart = (
      sorted(list(set([str(v["Quarteirao"]) for v in st.session_state.vistorias if "Quarteirao" in v and v["Quarteirao"]])))
      if st.session_state.vistorias else []
  )
  historico_ruas = (
      sorted(list(set([str(v["Rua"]) for v in st.session_state.vistorias if "Rua" in v and v["Rua"]])))
      if st.session_state.vistorias else []
  )
  historico_agentes = (
      sorted(list(set([str(v["Agente"]) for v in st.session_state.vistorias if "Agente" in v and v["Agente"]])))
      if st.session_state.vistorias else []
  )

  with st.form("form_relatorio_diario", clear_on_submit=False):
    col1, col2, col3 = st.columns(3)

    with col1:
      data_visita = st.date_input("Data da Visita", value=datetime.today())
      semana_padrao = int(data_visita.strftime("%V"))
      num_semana = st.number_input(
          "📅 Número da Semana Epidemiológica", min_value=1, max_value=53, value=semana_padrao, step=1
      )
      ciclo_selecionado = st.selectbox(
          "🔄 Ciclo Epidemiológico", ["Ciclo 1", "Ciclo 2", "Ciclo 3", "Ciclo 4", "Ciclo 5", "Ciclo 6"]
      )
      opcoes_q = historico_quart + ["➕ Digitar novo quarteirão..."]
      sel_q = st.selectbox("Nº do Quarteirão", options=opcoes_q, key="select_quarteirao")
      if sel_q == "➕ Digitar novo quarteirão..." or not historico_quart:
        num_quarteirao = st.text_input("Digite o Novo Quarteirão", placeholder="Ex: 325", key="input_novo_quarteirao")
      else:
        num_quarteirao = sel_q

    with col2:
      lado = st.number_input("Lado do Quarteirão", min_value=1, value=1, step=1)
      opcoes_r = historico_ruas + ["➕ Digitar nova rua..."]
      sel_r = st.selectbox("Nome da Rua / Logradouro", options=opcoes_r, key="select_rua")
      if sel_r == "➕ Digitar nova rua..." or not historico_ruas:
        nome_rua = st.text_input("Digite a Nova Rua", placeholder="Ex: Rua da Palmeira", key="input_nova_rua")
      else:
        nome_rua = sel_r
      num_casa = st.text_input("Nº / Identificação do Imóvel", placeholder="Ex: 15F")

    with col3:
      tipo_imovel = st.selectbox(
          "Tipo de Imóvel",
          ["Residência (RES)", "Comércio (COM)", "Terreno Baldio (TB)", "Ponto Estratégico (PE)", "Outros (OUT)"]
      )
      hora_entrada = st.time_input("Hora de Entrada", value=datetime.now().time())
      vistoria = st.selectbox("Condição da Vistoria", ["Normal", "Recuperada", "Fechada / Recusa"])
      opcoes_a = historico_agentes + ["➕ Digitar novo agente..."]
      sel_a = st.selectbox("Agente Responsável", options=opcoes_a, key="select_agente")
      if sel_a == "➕ Digitar novo agente..." or not historico_agentes:
        agente_resp = st.text_input("Digite o Nome do Agente", placeholder="Ex: Denison Oliveira", key="input_novo_agente")
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
            "Data Registro": data_visita.strftime("%d/%m/%Y"),
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

# ==================== ABA 2: BUSCA AVANÇADA ====================
with aba_busca:
    st.subheader("🔍 Busca Avançada e Filtros Globais")
    if st.session_state.vistorias:
        df_base = pd.DataFrame(st.session_state.vistorias)
        termo = st.text_input("🔎 Buscar em todos os campos:", placeholder="Ex: 325, Rua da Palmeira...")
        if termo:
            mask = df_base.astype(str).apply(lambda x: x.str.contains(termo, case=False, na=False)).any(axis=1)
            df_base = df_base[mask]
        st.dataframe(df_base, use_container_width=True)
        csv_exp = df_base.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar CSV Filtrado", data=csv_exp, file_name="vistorias_filtradas.csv", mime="text/csv")
    else:
        st.info("Nenhum registro cadastrado.")

# ==================== ABA 3: IMÓVEIS FECHADOS & RECUSAS ====================
with aba_fechadas:
  st.subheader("🚪 Painel de Imóveis Fechados e Recusas")
  if st.session_state.vistorias:
    df_v = pd.DataFrame(st.session_state.vistorias)
    df_fechados = df_v[df_v["Vistoria"].str.contains("Fechada", case=False, na=False)]
    st.metric("Total Fechadas / Recusas", len(df_fechados))
    st.dataframe(df_fechados, use_container_width=True)
  else:
    st.info("Sem dados cadastrados.")

# ==================== ABA 4: RELATÓRIO SEMANAL ====================
with aba_semanal:
  st.subheader("📈 Boletim Semanal Consolidado")
  if st.session_state.vistorias:
    df_v = pd.DataFrame(st.session_state.vistorias)
    df_agrupado = df_v.groupby("Semana").agg(Total_Visitas=("Casa", "count"), Eliminados=("Eliminados", "sum"), Tratados=("Tratados", "sum")).reset_index()
    st.dataframe(df_agrupado, use_container_width=True)
  else:
    st.info("Sem dados cadastrados.")

# ==================== ABA 5: CENTRAL DE SEGURANÇA E RESTAURAÇÃO ====================
with aba_backup:
  st.subheader("🔐 Central de Segurança, Backup e Importação de CSV")
  st.markdown("Baixe seus dados em ZIP ou **importe arquivos CSV avulsos** gerados pelas fotos rapidamente.")

  col_b1, col_b2 = st.columns(2)

  with col_b1:
    st.markdown("### 📤 Exportar Dados")
    salvar_estado_local()
    if os.path.exists(ARQUIVO_VISTORIAS):
      with open(ARQUIVO_VISTORIAS, "rb") as f:
        st.download_button("📥 Baixar vistorias_diarias.csv", data=f, file_name="vistorias_diarias.csv", mime="text/csv", use_container_width=True)

  with col_b2:
    st.markdown("### 📥 Importar CSV em Massa (Via Foto/IA)")
    st.markdown("Suba um arquivo `.csv` formatado com as vistorias extraídas:")
    csv_upload = st.file_uploader("Enviar arquivo .csv de vistorias", type="csv", key="upload_csv_avulso")

    if csv_upload is not None:
      if st.button("🔄 Adicionar Lançamentos do CSV à Base", type="primary", use_container_width=True):
        try:
          df_novo_csv = pd.read_csv(csv_upload)
          registros_novos = df_novo_csv.to_dict("records")
          
          for r in registros_novos:
            st.session_state.vistorias.append(r)
            tipo_imovel = r.get("Tipo Imovel", "Residência (RES)")
            res_val, com_val, tb_val, out_val = 0, 0, 0, 0
            if "Residência" in tipo_imovel: res_val = 1
            elif "Comércio" in tipo_imovel: com_val = 1
            elif "Terreno" in tipo_imovel: tb_val = 1
            else: out_val = 1

            st.session_state.reconhecimento.append({
                "Quarteirao": str(r["Quarteirao"]).strip(),
                "Lado": int(r.get("Lado", 1)),
                "Residencias": res_val,
                "Outros": out_val,
                "TB": tb_val,
                "Comercio": com_val,
                "Total": 1,
                "Data Registro": r["Data"],
                "Auditor": r.get("Agente", "Geral"),
            })

          salvar_estado_local()
          st.success(f"✅ {len(registros_novos)} registros importados com sucesso! Atualizando...")
          st.rerun()
        except Exception as e:
          st.error(f"❌ Erro ao importar CSV: {e}")

# ==================== ABA 6: RECONHECIMENTO ====================
with aba_reconhecimento:
  st.subheader("📊 Reconhecimento Geográfico")
  if st.session_state.reconhecimento:
    df_r = pd.DataFrame(st.session_state.reconhecimento)
    st.dataframe(df_r.groupby("Quarteirao").sum(numeric_only=True).reset_index(), use_container_width=True)
  else:
    st.info("Sem dados de reconhecimento.")

# ==================== ABA 7: LEITURA INTELIGENTE POR FOTO ====================
with aba_foto:
    st.subheader("📸 Leitura Inteligente de Boletim por Foto (IA)")
    st.markdown("Envie a foto do seu boletim. A IA extrairá os dados e gerará um botão para baixar o **CSV pronto para importação**!")

    api_key_input = st.text_input("🔑 Chave de API do Gemini", type="password", key="input_gemini_key_foto")
    foto_boletim = st.file_uploader("Foto do boletim", type=["png", "jpg", "jpeg"], key="upload_foto_boletim_ia")

    if foto_boletim is not None:
        st.image(foto_boletim, caption="Boletim enviado", use_container_width=True)

        if st.button("🚀 Processar Foto e Gerar CSV", type="primary", use_container_width=True):
            if not api_key_input:
                st.error("Insira sua chave de API do Gemini.")
            else:
                try:
                    import json
                    import base64
                    import requests

                    with st.spinner("🤖 Lendo boletim e estruturando os dados..."):
                        image_bytes = foto_boletim.getvalue()
                        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                        mime_type = foto_boletim.type if foto_boletim.type else "image/jpeg"

                        prompt_extracao = """
                        Analise esta imagem de um Resumo Diário de Serviço Antivetorial preenchido à mão.
                        Extraia todas as linhas de vistorias. Retorne um array JSON com objetos contendo exatamente estes campos:
                        - "Data": string DD/MM/YYYY
                        - "Semana": inteiro
                        - "Ciclo": string (ex: "Ciclo 1")
                        - "Quarteirao": string
                        - "Lado": inteiro
                        - "Rua": string
                        - "Casa": string
                        - "Tipo Imovel": "Residência (RES)", "Comércio (COM)", "Terreno Baldio (TB)", "Ponto Estratégico (PE)" ou "Outros (OUT)"
                        - "Hora": string HH:MM
                        - "Vistoria": "Normal", "Recuperada", ou "Fechada / Recusa"
                        - "Agente": string
                        - "Eliminados": inteiro
                        - "Tubitos": inteiro
                        - "Tratados": inteiro
                        - "Gramas": float
                        - "Depósitos": inteiro
                        - "Litros": float
                        Retorne APENAS o JSON puro sem markdown extra.
                        """

                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key_input}"
                        payload = {
                            "contents": [{"parts": [{"text": prompt_extracao}, {"inline_data": {"mime_type": mime_type, "data": image_base64}}]}]
                        }
                        response = requests.post(url, json=payload)
                        
                        if response.status_code == 200:
                            texto_resp = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                            if texto_resp.startswith("```json"): texto_resp = texto_resp[7:-3].strip()
                            elif texto_resp.startswith("```"): texto_resp = texto_resp[3:-3].strip()
                            
                            lista_regs = json.loads(texto_resp)
                            df_lido = pd.DataFrame(lista_regs)
                            
                            st.success("✅ Leitura realizada com sucesso abaixo!")
                            st.dataframe(df_lido, use_container_width=True)

                            csv_data = df_lido.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Baixar CSV deste Boletim (Para Importar na Central de Backup)",
                                data=csv_data,
                                file_name="boletim_lido_ia.csv",
                                mime="text/csv",
                                type="primary"
                            )
                        else:
                            st.error(f"Erro na API: {response.text}")
                except Exception as e:
                    st.error(f"Erro ao processar: {e}")
