from pathlib import Path
import pandas as pd
from pymongo import MongoClient
import tomllib

# === caminhos ===
DATA_DIR = Path("data")
ARQ_CLUSTERS = DATA_DIR / "customers_clusters.csv"
ARQ_RECOMPRA = DATA_DIR / "clientes_recompra_30d.csv"
ARQ_RECOS_L = DATA_DIR / "next_route_recos_label.csv"  # preferencial (tem cidades)
ARQ_RECOS    = DATA_DIR / "next_route_recos.csv"       # fallback
ARQ_CIDADES  = DATA_DIR / "Cidades.csv"                # opcional (usa ';')

# === lê segredos ===
with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomllib.load(f)
MONGO_URI = secrets["MONGO_URI"]
MONGO_DB  = secrets.get("MONGO_DB", "unravel_iq")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

def upsert_df(df: pd.DataFrame, coll_name: str, key: str):
    """Insere/atualiza DataFrame no Mongo, usando 'key' como chave única."""
    df = df.where(pd.notnull(df), None)  # NaN -> None
    coll = db[coll_name]
    coll.create_index(key, unique=False)

    recs = df.to_dict(orient="records")
    for rec in recs:
        coll.update_one({key: rec[key]}, {"$set": rec}, upsert=True)
    print(f"✅ {coll_name}: {len(recs)} documentos upsertados (chave='{key}')")

# --------------------------------------------------------------------
# 1) customers_features (clusters por cliente)
# - chave: fk_contact -> customer_id
# --------------------------------------------------------------------
print("→ Processando customers_clusters.csv ...")
df_feat = pd.read_csv(ARQ_CLUSTERS)
df_feat = df_feat.rename(columns={
    "fk_contact": "customer_id"
})
# mantém recency_days, frequency, monetary, cluster_id
upsert_df(df_feat, "customers_features", "customer_id")

# --------------------------------------------------------------------
# 2) repurchase_scores (probabilidade 30d)
# - chave: fk_contact -> customer_id
# --------------------------------------------------------------------
print("→ Processando clientes_recompra_30d.csv ...")
df_rep = pd.read_csv(ARQ_RECOMPRA)
df_rep = df_rep.rename(columns={
    "fk_contact": "customer_id"
})
upsert_df(df_rep, "repurchase_scores", "customer_id")

# --------------------------------------------------------------------
# 3) route_recos (recomendações)
# - chave: fk_contact -> customer_id
# - preferimos o arquivo *_label (tem campos de cidade); se não existir, usa o outro
# --------------------------------------------------------------------
src_recos = ARQ_RECOS_L if ARQ_RECOS_L.exists() else ARQ_RECOS
print(f"→ Processando {src_recos.name} ...")
df_rec = pd.read_csv(src_recos)
df_rec = df_rec.rename(columns={
    "fk_contact": "customer_id",
    "recommended_destination": "destino_recomendado",
    "reason": "motivo",
    "backup_destination": "destino_backup",
    "recommended_city": "cidade_recomendada",
    "backup_city": "cidade_backup",
})
upsert_df(df_rec, "route_recos", "customer_id")

# --------------------------------------------------------------------
# 4) cities (opcional) — arquivo separado por ';'
# --------------------------------------------------------------------
if ARQ_CIDADES.exists():
    print("→ Processando Cidades.csv ...")
    try:
        df_cid = pd.read_csv(ARQ_CIDADES, sep=";")
        # normaliza nomes (se vierem como 'Origem Viagem Ida' e 'Cidade')
        cols = [c.strip() for c in df_cid.columns]
        if len(cols) == 2:
            df_cid.columns = ["origem", "cidade"]
        upsert_df(df_cid, "cities", key="origem")
    except Exception as e:
        print(f"⚠️  Falha ao importar Cidades.csv: {e}")

print("\n🏁 Seed concluído com sucesso.")