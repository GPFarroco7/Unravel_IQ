from utils.utils import leitura_arquivo_clickbus, segamentacao_clientes 
from utils.db import read_collection_df
import plotly.express as px
import streamlit as st
import pandas as pd

def dashboard_segmentacao():
    st.title('SEGMENTAÇÃO DE CLIENTES')
    st.divider()

    try:
        # 1) Lê direto do Mongo
        #    collection padrão do nosso seed: "customers_clusters"
        df = read_collection_df(
            collection="customers_clusters",
            csv_fallback="data/customers_clusters.csv"  # opcional
        )

        # --- Gráficos Principais ---
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                clientes_por_cluster = df.groupby('cluster_id')['fk_contact'].count().reset_index()
                clientes_por_cluster.rename(columns={'fk_contact': 'qtd_clientes'}, inplace=True)
                fig_bar = px.bar(
                    clientes_por_cluster,
                    x='cluster_id',
                    y='qtd_clientes',
                    title='Clientes por Cluster',
                    labels={'cluster_id':'Cluster', 'qtd_clientes':'Quantidade de Clientes'}
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            with st.container(border=True):
                rfm_cluster = df.groupby('cluster_id')[['recency_days','frequency','monetary']].mean(numeric_only=True).reset_index()
                rfm_melted = rfm_cluster.melt(id_vars='cluster_id', var_name='variable', value_name='value')
                fig_col = px.bar(
                    rfm_melted,
                    x='cluster_id',
                    y='value',
                    color='variable',
                    title='Média de Recency, Frequency e Monetary por Cluster',
                    barmode='group',
                    labels={'cluster_id':'Cluster', 'value':'Valor', 'variable': 'Métrica'}
                )
                st.plotly_chart(fig_col, use_container_width=True)

        st.divider()

        # --- Cartões (distribuição) ---
        st.subheader("Distribuição dos Clientes por Cluster")
        cluster_counts = df['cluster_id'].value_counts(normalize=True).sort_index() * 100
        cols = st.columns(4)
        cluster_names = {
            0: "Clientes em Risco",
            1: "Clientes Fiéis",
            2: "Novos Clientes",
            3: "Clientes VIP"
        }
        for i, col in enumerate(cols):
            with col:
                st.metric(
                    label=f"Cluster {i} ({cluster_names.get(i, 'N/D')})",
                    value=f"{cluster_counts.get(i, 0):.2f}%"
                )

        st.divider()

        # --- Tabela de Amostra com Destinos ---
        st.subheader("Amostra de Clientes e seus Destinos Preferidos")
        with st.container(border=True):
            colunas_tabela = ['fk_contact', 'cluster_id', 'recency_days', 'frequency', 'monetary', 'recommended_city']
            cols_existentes = [c for c in colunas_tabela if c in df.columns]
            st.dataframe(df[cols_existentes].head(20), use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao carregar dados do Mongo: {e}")
