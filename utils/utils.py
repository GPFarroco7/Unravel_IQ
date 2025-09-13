from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
import pandas as pd

# Função para leitura e tratamento básico do arquivo clickbus
def leitura_arquivo_clickbus(path):
    # Lendo o arquivo
    df = pd.read_csv(path, sep=',', encoding='utf-8', low_memory=False)
    # Ajustando o tipo de dados de algumas colunas
    df['date_purchase'] = pd.to_datetime(df['date_purchase'], errors='coerce')
    df['gmv_success'] = pd.to_numeric(df['gmv_success'], errors='coerce')
    df['total_tickets_quantity_success'] = pd.to_numeric(df['total_tickets_quantity_success'], errors='coerce')
    return df # Retornando o Dataframe tratado

# Função para ler o arquivo contendo as cidades e seu hash
def leitura_arquivo_cidades(path):
    # Lendo e retornando o arquivo
    return pd.read_csv(path, sep=';', encoding='ISO8859-1')

# Segmentação de clientes (RFM + KMeans)
def segamentacao_clientes(df):
    # Copiando o Dataframe original, ordenado por cliente e data
    df_segmentacao = df.sort_values(['fk_contact', 'date_purchase']).copy()
    # Salvando a última data da base
    max_date = df_segmentacao['date_purchase'].max()
    # Criando métricas RFM
    rfm = (df.groupby('fk_contact').agg(
        last_purchase=('date_purchase', 'max'),
        frequency=('nk_ota_localizer_id', 'count'),
        monetary=('gmv_success', 'mean')).reset_index())
    # Recência = Diferença entre última compra e data máxima da base
    rfm['recency_days'] = (max_date - rfm['last_purchase']).dt.days
    # Seleciona as variáveis numéricas
    x = rfm[['recency_days', 'frequency', 'monetary']].fillna(0)
    # Normlizando os dados
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)
    # Rodar KMeans (4 clusters como exemplo)
    kmenas = KMeans(n_clusters=4, random_state=42, n_init=10)
    rfm['cluster_id'] = kmenas.fit_predict(x_scaled)
    # Retonnando o Dataframe de output
    return rfm[['fk_contact', 'recency_days', 'frequency', 'monetary', 'cluster_id']].copy()

# Recompra em 30 dias
def recompra_30d(df):
    # Copiando o Dataframe original
    df_recompra = df.dropna(subset=['fk_contact', 'nk_ota_localizer_id', 'date_purchase']).copy()
    # Ordendo os valores por cliente e data e removendo valores duplicados
    df_recompra.sort_values(['fk_contact', 'date_purchase']).drop_duplicates(
        subset=['fk_contact', 'nk_ota_localizer_id'], keep='first', inplace=True)
    # Próxima compra de cada cliente e intervalo entre compras
    df_recompra['next_purchase_date'] = df_recompra.groupby('fk_contact')['date_purchase'].shift(-1)
    df_recompra['days_to_next'] = (df_recompra['next_purchase_date'] - df_recompra['date_purchase']).dt.days
    # Calulando o tempo médio entre compras por cliente (considerando apenas quem tem próxima compra)
    tempo_medio = (df_recompra.groupby('fk_contact', as_index=False)['days_to_next']
                .mean(numeric_only=True)
                .rename(columns={'days_to_next': 'avg_days_to_next'})
                .dropna(subset=['avg_days_to_next']))
    # Flag de provável recompra em 30d
    tempo_medio['prob_recompra_30d'] = tempo_medio['avg_days_to_next'] <= 30
    # Relatório simples
    # total_clientes = df_recompra['fk_contact'].nunique()
    # clientes_com_hist = df_recompra.loc[df_recompra['next_purchase_date'].notna(), 'fk_contact'].nunique()
    # print(f'Total de clientes únicos: {total_clientes}')
    # print(f'Clientes com histórico (>= 2 compras): {clientes_com_hist}\n')
    # Retornando o Dataframe de output
    return tempo_medio

# Previsão do Próximo trecho/destino
def previsao(df, clusters):
    # Destino mais frequente do clinte pelo histórico pessoal
    personal = (df.groupby(['fk_contact', 'place_destination_departure']).size().reset_index(name='cnt'))
    top_dest = (personal.sort_values(['fk_contact', 'cnt'], ascending=[True, False])
                .groupby('fk_contact').head(1)
                .rename(columns={'place_destination_departure': 'recommended_destination'}))
    top_dest['reason'] = 'historico_pessoal'
    # Fallback por origem global (rota mais popular por origem)
    cooc = (df.groupby(['place_origin_departure', 'place_destination_departure']).size().reset_index(name='cnt'))
    by_origin = (cooc.sort_values(['place_origin_departure', 'cnt'], ascending=[True, False])
                 .groupby('place_origin_departure').head(1)
                 .rename(columns={'place_destination_departure': 'backup_destination'})
                 [['place_origin_departure', 'backup_destination']])
    # Última origem do cliente
    last_origin = (df.sort_values('date_purchase').groupby('fk_contact').tail(1)[['fk_contact', 'place_origin_departure']])
    # Montando a recomendação final usando os clusters da segmentação
    recos = (last_origin.merge(top_dest[['fk_contact', 'recommended_destination', 'reason']], on='fk_contact', how='left')
             .merge(by_origin, on='place_origin_departure', how='left')
             .merge(clusters[['fk_contact', 'cluster_id']], on='fk_contact', how='left'))
    # Retornando o Dataframe com as recomendações
    return recos[['fk_contact', 'recommended_destination', 'reason', 'backup_destination', 'cluster_id']]
