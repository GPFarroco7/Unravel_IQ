import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db import read_collection_df

def dashboard_recomendacoes():
    st.title('RECOMENDAÇÃO DE PRÓXIMO TRECHO')
    st.divider()

    try:
        preferidas = ["next_route_recos_label", "next_route_recos"]
        df_recos = None
        for col in preferidas:
            try:
                df_recos = read_collection_df(col, csv_fallback="data/next_route_recos_label.csv")
                break
            except Exception:
                continue
        if df_recos is None or df_recos.empty:
            raise RuntimeError("Nenhuma collection de recomendações encontrada no Mongo.")

        df_recos = df_recos.dropna(subset=['recommended_city'])

        # Top 10 geral
        st.subheader("Top 10 Destinos Mais Recomendados (Geral)")
        with st.container(border=True):
            col1, col2 = st.columns([1, 2])

            with col1:
                top_destinos = df_recos['recommended_city'].value_counts().nlargest(10).reset_index()
                top_destinos.columns = ['Destino', 'Qtd. Recomendações']
                st.dataframe(top_destinos, hide_index=True, use_container_width=True)

            with col2:
                fig_bar = px.bar(
                    top_destinos,
                    x='Qtd. Recomendações',
                    y='Destino',
                    orientation='h',
                    title='Top 10 Destinos Recomendados'
                )
                fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()

        # Amostra
        st.subheader("Amostra das Recomendações Geradas")
        with st.container(border=True):
            colunas = ['fk_contact', 'recommended_city', 'reason', 'backup_city', 'cluster_id']
            cols_existentes = [c for c in colunas if c in df_recos.columns]
            st.dataframe(df_recos[cols_existentes].head(20), use_container_width=True)
            st.info("A coluna 'reason' indica que a recomendação foi baseada no histórico pessoal do cliente.")

        st.divider()

        # Filtro por cluster
        st.subheader("Explorar Recomendações por Cluster de Cliente")
        with st.container(border=True):
            if 'cluster_id' in df_recos.columns:
                cluster_names = {0: "Clientes em Risco", 1: "Clientes Fiéis", 2: "Novos Clientes", 3: "Clientes VIP"}
                options = sorted([int(x) for x in df_recos['cluster_id'].dropna().unique()])
                sel = st.selectbox(
                    'Selecione um Cluster para analisar os destinos preferidos:',
                    options=options,
                    format_func=lambda x: f"Cluster {x} - {cluster_names.get(x, '')}"
                )
                df_filtrado = df_recos[df_recos['cluster_id'] == sel]
                top_cluster = df_filtrado['recommended_city'].value_counts().nlargest(5)
                st.bar_chart(top_cluster)
            else:
                st.info("Este dataset não possui 'cluster_id' nas recomendações.")

    except Exception as e:
        st.error(f"Erro ao carregar dados do Mongo: {e}")