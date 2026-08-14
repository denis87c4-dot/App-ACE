from datetime import datetime
import json
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="App ACE - Controle de Imóveis",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background-color: #FFFFFF; color: #1E293B; }
    h1, h2, h3 { color: #0F172A; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .metric-card { background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); text-align: center; }
    .metric-card h3 { margin: 0; color: #64748B; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-card p { margin: 5px 0 0 0; color: #0F172A; font-size: 28px; font-weight: bold; }
    .stButton>button { background-color: #2563EB; color: white; border-radius: 8px; padding: 10px 24px; font-weight: 600; border: none; width: 100%; }
    .stButton>button:hover { background-color: #1D4ED8; }
    </style>
""",
    unsafe_allow_html=True,
)

if "vistorias" not in st.session_state:
    st.session_state.vistorias = []

st.markdown(
    """
    <div style="padding: 15px 0; border-bottom: 2px solid #F1F5F9; margin-bottom: 25px;">
        <h1 style="margin:0; font-size: 32px;">🏡 Gestão de Campo - ACE</h1>
        <p style="margin:5px 0 0 0; color: #64748B; font-size: 16px;">Sistema inteligente de registro, filtros avançados e recuperação rápida de fechadas.</p>
    </div>
""",
    unsafe_allow_html=True,
)

aba_cadastro, aba_busca, aba_backup = st.tabs(
    ["📝 Registrar Visita", "🔍 Busca Avançada & Cruzada", "💾 Central de Backup"]
)

with aba_cadastro:
    col_m1, col_m2, col_m3 = st.columns(3)
    total_visitas = len(st.session_state.vistorias)
    imoveis_recuperados_geral = set()
    for v in st.session_state.vistorias:
        if v.get("Visita") == "Recuperada":
            chave = f"{v.get('Quarteirao')} - {v.get('Rua')} - N° {v.get('Numero')}"
            imoveis_recuperados_geral.add(chave)
            
    fechadas_pendentes_count = sum(
        1 for v in st.session_state.vistorias
        if v.get("Visita") == "Fechada" and f"{v.get('Quarteirao')} - {v.get('Rua')} - N° {v.get('Numero')}" not in imoveis_recuperados_geral
    )

    with col_m1:
        st.markdown(f"<div class='metric-card'><h3>Total Registrado</h3><p>{total_visitas}</p></div>", unsafe_allow_html=True)
    with col_m2:
        st.markdown(f"<div class='metric-card'><h3>Fechadas Pendentes</h3><p style='color: #DC2626;'>{fechadas_pendentes_count}</p></div>", unsafe_allow_html=True)
    with col_m3:
        st.markdown("<div class='metric-card'><h3>Status do Sistema</h3><p style='color: #16A34A; font-size: 20px; margin-top: 10px;'>● Online</p></div>", unsafe_allow_html=True)

    st.write("---")
    with st.form("form_ace", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            data_visita = st.date_input("Data", value=datetime.today())
            quarteirao = st.text_input("Número do Quarteirão")
            lado = st.text_input("Lado")
        with col2:
            rua = st.text_input("Rua / Logradouro")
            numero_imovel = st.text_input("Número do Imóvel")
            hora_entrada = st.time_input("Hora da Entrada", value=datetime.now())
        with col3:
            tipo_imovel = st.selectbox("Tipo do Imóvel", ["Outros", "Residencia", "TB", "Comércio"])
            status_visita = st.selectbox("Condição da Visita", ["Normal", "Recuperada", "Fechada"])
        submitted = st.form_submit_button("💾 Salvar Registro de Visita")
        if submitted:
            if not quarteirao or not rua or not numero_imovel:
                st.warning("⚠️ Preencha Quarteirão, Rua e Número.")
            else:
                nova_vistoria = {
                    "Data": data_visita.strftime("%d/%m/%Y"),
                    "Quarteirao": str(quarteirao).strip(),
                    "Lado": lado,
                    "Rua": str(rua).strip().title(),
                    "Numero": str(numero_imovel).strip(),
                    "Tipo Imovel": tipo_imovel,
                    "Hora": hora_entrada.strftime("%H:%M"),
                    "Visita": status_visita
                }
                st.session_state.vistorias.append(nova_vistoria)
                st.success("✅ Visita cadastrada!")

with aba_busca:
    st.subheader("🔍 Gerenciamento & Recuperação")
    if not st.session_state.vistorias:
        st.info("Nenhuma vistoria registrada.")
    else:
        df_busca = pd.DataFrame(st.session_state.vistorias)
        df_busca["Chave_Imovel"] = df_busca["Quarteirao"] + " - " + df_busca["Rua"] + " - N° " + df_busca["Numero"]
        imoveis_recuperados_set = set(df_busca[df_busca["Visita"] == "Recuperada"]["Chave_Imovel"])
        
        st.subheader("⚡ Painel: Marcar como Recuperadas")
        df_pendentes_painel = df_busca[(df_busca["Visita"] == "Fechada") & (~df_busca["Chave_Imovel"].isin(imoveis_recuperados_set))]
        
        if not df_pendentes_painel.empty:
            for idx, row in df_pendentes_painel.iterrows():
                col_info, col_check = st.columns([4, 1])
                with col_info:
                    st.markdown(f"**Q:** {row['Quarteirao']} | **Rua:** {row['Rua']}, **N° {row['Numero']}**")
                with col_check:
                    if st.checkbox("Recuperar", key=f"rec_{idx}"):
                        st.session_state.vistorias[idx]["Visita"] = "Recuperada"
                        st.rerun()
        else:
            st.success("✨ Tudo em dia!")

with aba_backup:
    st.subheader("💾 Backup")
    if st.session_state.vistorias:
        st.download_button("💾 Baixar Backup", data=json.dumps(st.session_state.vistorias, ensure_ascii=False), file_name="backup.json", mime="application/json")
