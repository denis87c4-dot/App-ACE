%%writefile app.py
from datetime import datetime
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
    .stApp {
        background-color: #FFFFFF;
        color: #1E293B;
    }
    h1, h2, h3 {
        color: #0F172A;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    .metric-card h3 {
        margin: 0;
        color: #64748B;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-card p {
        margin: 5px 0 0 0;
        color: #0F172A;
        font-size: 28px;
        font-weight: bold;
    }
    .stButton>button {
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        border: none;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
    }
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
        <p style="margin:5px 0 0 0; color: #64748B; font-size: 16px;">Sistema inteligente de registro de visitas e controle de imóveis fechados.</p>
    </div>
""",
    unsafe_allow_html=True,
)

col_m1, col_m2, col_m3 = st.columns(3)
total_visitas = len(st.session_state.vistorias)
fechadas_count = sum(
    1
    for v in st.session_state.vistorias
    if v.get("Visita") == "Fechada"
)

with col_m1:
    st.markdown(
        f"""
        <div class="metric-card">
            <h3>Total Registrado</h3>
            <p>{total_visitas}</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

with col_m2:
    st.markdown(
        f"""
        <div class="metric-card">
            <h3>Imóveis Fechados</h3>
            <p style="color: #DC2626;">{fechadas_count}</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

with col_m3:
    st.markdown(
        """
        <div class="metric-card">
            <h3>Status do Sistema</h3>
            <p style="color: #16A34A; font-size: 20px; margin-top: 10px;">● Online</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

st.write("---")
st.subheader("📝 Novo Registro de Visita")

with st.form("form_ace", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        data_visita = st.date_input("Data", value=datetime.today())
        quarteirao = st.text_input(
            "Número do Quarteirão", placeholder="Ex: 142"
        )
        lado = st.text_input("Lado", placeholder="Ex: A ou Norte")

    with col2:
        rua = st.text_input("Rua / Logradouro", placeholder="Ex: Rua das Flores")
        numero_imovel = st.text_input("Número do Imóvel", placeholder="Ex: 450")
        hora_entrada = st.time_input("Hora da Entrada", value=datetime.now())

    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        tipo_imovel = st.selectbox(
            "Tipo do Imóvel", ["Outros", "Residencia", "TB", "Comércio"]
        )
        status_visita = st.selectbox(
            "Condição da Visita", ["Normal", "Recuperada", "Fechada"]
        )

    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("💾 Salvar Registro de Visita")

    if submitted:
        if not quarteirao or not rua:
            st.warning(
                "⚠️ Por favor, preencha pelo menos o Quarteirão e a Rua."
            )
        else:
            nova_vistoria = {
                "Data": data_visita.strftime("%d/%m/%Y"),
                "Quarteirão": quarteirao,
                "Lado": lado,
                "Rua": rua,
                "Número": numero_imovel,
                "Tipo Imóvel": tipo_imovel,
                "Hora": hora_entrada.strftime("%H:%M"),
                "Visita": status_visita,
            }
            st.session_state.vistorias.append(nova_vistoria)
            st.success("✅ Visita cadastrada com sucesso!")

if st.session_state.vistorias:
    st.write("---")
    st.subheader("📊 Vistorias Realizadas Nesta Sessão")
    df = pd.DataFrame(st.session_state.vistorias)
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Baixar Relatório em CSV",
        data=csv,
        file_name=f"vistorias_ace_{datetime.today().strftime('%Y-%m-%d')}.csv",
        mime="text/csv",
    )

