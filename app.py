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
        <p style="margin:5px 0 0 0; color: #64748B; font-size: 16px;">Sistema inteligente de registro, filtros avançados de campo e inteligência de busca cruzada.</p>
    </div>
""",
    unsafe_allow_html=True,
)

# Abas do Aplicativo
aba_cadastro, aba_busca, aba_backup = st.tabs(
    [
        "📝 Registrar Visita",
        "🔍 Busca Avançada & Cruzada",
        "💾 Central de Backup",
    ]
)

with aba_cadastro:
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
                <p style="color: #16A34A; font-size: 20px; margin-top: 10px;">● Online & Seguro</p>
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
            rua = st.text_input(
                "Rua / Logradouro", placeholder="Ex: Rua das Flores"
            )
            numero_imovel = st.text_input(
                "Número do Imóvel", placeholder="Ex: 450"
            )
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
            if not quarteirao or not rua or not numero_imovel:
                st.warning(
                    "⚠️ Por favor, preencha Quarteirão, Rua e Número do Imóvel."
                )
            else:
                nova_vistoria = {
                    "Data": data_visita.strftime("%d/%m/%Y"),
                    "Quarteirao": str(quarteirao).strip(),
                    "Lado": lado,
                    "Rua": str(rua).strip().title(),
                    "Numero": str(numero_imovel).strip(),
                    "Tipo Imovel": tipo_imovel,
                    "Hora": hora_entrada.strftime("%H:%M"),
                    "Visita": status_visita,
                }
                st.session_state.vistorias.append(nova_vistoria)
                st.success("✅ Visita cadastrada com sucesso!")

    if st.session_state.vistorias:
        st.write("---")
        st.subheader("📊 Histórico Geral da Sessão")
        df_geral = pd.DataFrame(st.session_state.vistorias)
        st.dataframe(df_geral, use_container_width=True)

        csv = df_geral.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Baixar Relatório em CSV",
            data=csv,
            file_name=f"vistorias_ace_{datetime.today().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
        )

with aba_busca:
    st.subheader(
        "🔍 Gerenciamento Avançado, Filtros e Inteligência de Cruzamento"
    )
    st.markdown(
        "Filtre por **Quarteirão**, **Rua** e **Data**, ou utilize a inteligência de busca cruzada para mapear imóveis fechados e evitar duplicidades."
    )

    if not st.session_state.vistorias:
        st.info("Nenhuma vistoria registrada ainda para realizar buscas.")
    else:
        df_busca = pd.DataFrame(st.session_state.vistorias)

        # Filtros novos (Data, Quarteirão, Rua e Status)
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)

        with col_f1:
            quart_unicos = sorted(df_busca["Quarteirao"].unique().tolist())
            filtro_quarteirao = st.selectbox(
                "Quarteirão", ["Todos"] + quart_unicos
            )

        with col_f2:
            ruas_unicas = sorted(df_busca["Rua"].unique().tolist())
            filtro_rua = st.selectbox("Rua", ["Todas"] + ruas_unicas)

        with col_f3:
            datas_unicas = sorted(df_busca["Data"].unique().tolist())
            filtro_data = st.selectbox("Data da Visita", ["Todas"] + datas_unicas)

        with col_f4:
            filtro_status = st.selectbox(
                "Status",
                ["Todos", "Apenas Fechadas Pendentes", "Recuperadas", "Normal"],
            )

        # Chave única para cruzamento de imóveis
        df_busca["Chave_Imovel"] = (
            df_busca["Quarteirao"]
            + " - "
            + df_busca["Rua"]
            + " - N° "
            + df_busca["Numero"]
        )

        # Aplicando filtros
        df_filtrado = df_busca.copy()
        if filtro_quarteirao != "Todos":
            df_filtrado = df_filtrado[
                df_filtrado["Quarteirao"] == filtro_quarteirao
            ]
        if filtro_rua != "Todas":
            df_filtrado = df_filtrado[df_filtrado["Rua"] == filtro_rua]
        if filtro_data != "Todas":
            df_filtrado = df_filtrado[df_filtrado["Data"] == filtro_data]

        if filtro_status == "Apenas Fechadas Pendentes":
            imoveis_recuperados = set(
                df_busca[df_busca["Visita"] == "Recuperada"]["Chave_Imovel"]
            )
            df_filtrado = df_filtrado[
                (df_filtrado["Visita"] == "Fechada")
                & (~df_filtrado["Chave_Imovel"].isin(imoveis_recuperados))
            ]
        elif filtro_status == "Recuperadas":
            df_filtrado = df_filtrado[df_filtrado["Visita"] == "Recuperada"]
        elif filtro_status == "Normal":
            df_filtrado = df_filtrado[df_filtrado["Visita"] == "Normal"]

        st.write("---")
        st.markdown(
            f"### 📋 Lista Filtrada de Imóveis ({len(df_filtrado)} registros)"
        )

        if not df_filtrado.empty:
            st.dataframe(
                df_filtrado[
                    [
                        "Data",
                        "Quarteirao",
                        "Lado",
                        "Rua",
                        "Numero",
                        "Tipo Imovel",
                        "Visita",
                    ]
                ],
                use_container_width=True,
            )
        else:
            st.success(
                "🎉 Nenhum imóvel encontrado com estes filtros específicos!"
            )

        # RECURSO SURPRESA: Busca Cruzada e Matriz de Alerta de Pendências Críticas
        st.write("---")
        st.subheader("⚡ Mecanismo de Inteligência: Painel de Alerta de Fechadas")
        st.markdown(
            "Este painel cruza automaticamente todo o seu histórico para mostrar apenas os **imóveis que continuam fechados**, agrupados por quarteirão, para você planejar seu retorno imediato:"
        )

        # Isolar apenas casas fechadas sem recuperação posterior
        imoveis_recuperados_geral = set(
            df_busca[df_busca["Visita"] == "Recuperada"]["Chave_Imovel"]
        )
        df_pendentes = df_busca[
            (df_busca["Visita"] == "Fechada")
            & (~df_busca["Chave_Imovel"].isin(imoveis_recuperados_geral))
        ]

        if not df_pendentes.empty:
            st.warning(
                f"⚠️ Atenção ACE: Existem atualmente **{len(df_pendentes)} imóveis fechados pendentes** aguardando recuperação."
            )
            st.dataframe(
                df_pendentes[
                    [
                        "Data",
                        "Quarteirao",
                        "Lado",
                        "Rua",
                        "Numero",
                        "Tipo Imovel",
                    ]
                ],
                use_container_width=True,
            )
        else:
            st.success(
                "✨ Excelente trabalho! Não há imóveis fechados pendentes em nenhum quarteirão no momento."
            )

with aba_backup:
    st.subheader("🔒 Central de Segurança e Backup Manual")
    st.markdown(
        "Proteja seus dados! Clique no botão abaixo para baixar um arquivo de segurança com todas as suas vistorias diretamente para o seu celular."
    )

    if st.session_state.vistorias:
        dados_json = json.dumps(
            st.session_state.vistorias, ensure_ascii=False, indent=4
        )
        data_atual = datetime.today().strftime("%Y-%m-%d_%H-%M")

        st.download_button(
            label="💾 Salvar Backup Manual",
            data=dados_json,
            file_name=f"backup_ace_{data_atual}.json",
            mime="application/json",
        )
        st.success(
            "💡 Dica: Após salvar o arquivo de backup, guarde-o no seu Google Drive ou envie para você mesmo no WhatsApp!"
        )
    else:
        st.info(
            "⚠️ Não há dados cadastrados ainda para gerar o backup de segurança."
        )
