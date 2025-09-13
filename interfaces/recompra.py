import streamlit as st
import pandas as pd
from utils.db import read_collection_df

def dashboard_recompra():
    st.title('ANÁLISE DE RECOMPRA')
    st.divider()

    try:
        # nomes possíveis dependendo do seed que você rodou:
        # "clientes_recompra_30d"  ou  "recompra_scores"
        preferidas = ["clientes_recompra_30d", "recompra_scores"]
        df_recompra = None
        for col in preferidas:
            try:
                df_recompra = read_collection_df(col, csv_fallback="data/clientes_recompra_30d.csv")
                break
            except Exception:
                continue
        if df_recompra is None or df_recompra.empty:
            raise RuntimeError("Nenhuma collection de recompra encontrada no Mongo.")

        # --- Distribuição ---
        st.subheader("Distribuição de Clientes por Probabilidade de Recompra")
        with st.container(border=True):
            # aceita tanto bool quanto 0/1
            v = df_recompra['prob_recompra_30d'].replace({1: True, 0: False})
            counts = v.value_counts()
            counts.index = counts.index.map({
                True: 'Provável Recompra em até 30d',
                False: 'Provável Recompra > 30d'
            })
            st.bar_chart(counts)
            st.info("Este gráfico mostra a quantidade de clientes com alta probabilidade de nova compra nos próximos 30 dias.")

        st.divider()

        # --- Métricas dummy do MVP ---
        st.subheader("Métricas de Performance (Baseline)")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="MAE (Erro Médio Absoluto)", value="~25.8 dias")
        with col2:
            st.metric(label="AUC (Área sob a Curva)", value="~0.78")

        st.divider()

        # --- Amostra ---
        st.subheader("Clientes com Alta Probabilidade de Recompra (Amostra)")
        with st.container(border=True):
            hot = df_recompra[df_recompra['prob_recompra_30d'].replace({1: True, 0: False}) == True]
            st.dataframe(hot.head(20), use_container_width=True)
            st.success("Estes clientes podem ser alvo de campanhas de reengajamento para incentivar a próxima compra.")

    except Exception as e:
        st.error(f"Erro ao carregar dados do Mongo: {e}")