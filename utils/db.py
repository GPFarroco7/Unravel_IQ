from __future__ import annotations
import os
import pandas as pd
import streamlit as st

try:
    from pymongo import MongoClient
except Exception as _:
    MongoClient = None 

def _get_secrets(key: str, default: str | None = None) -> str | None:
    try:
        val = st.secrets.get(key, None)
    except Exception:
        val = None
    return val or os.environ.get(key, default)

def get_mongo():
    """
    Retorna (client, db). Lança um erro amigável se pymongo não estiver instalado.
    """
    if MongoClient is None:
        raise RuntimeError(
            "pymongo não está instalado. Rode: pip install pymongo"
        )

    uri = _get_secrets("MONGO_URI")
    dbname = _get_secrets("MONGO_DB", "unravel_iq")
    if not uri:
        raise RuntimeError(
            "MONGO_URI não encontrado. Defina em .streamlit/secrets.toml ou como variável de ambiente."
        )
    client = MongoClient(uri)
    return client, client[dbname]

def read_collection_df(
    collection: str,
    query: dict | None = None,
    projection: dict | None = None,
    limit: int | None = None,
    csv_fallback: str | None = None
) -> pd.DataFrame:
    """
    Lê uma collection do Mongo em DataFrame.
    Se o Mongo não estiver acessível e csv_fallback for fornecido/existir, usa o CSV.
    """
    try:
        _, db = get_mongo()
        cur = db[collection].find(query or {}, projection)
        if limit:
            cur = cur.limit(limit)
        df = pd.DataFrame(list(cur))
        if not df.empty and "_id" in df.columns:
            df = df.drop(columns=["_id"])
        return df
    except Exception as err:
        if csv_fallback and os.path.exists(csv_fallback):
            df = pd.read_csv(csv_fallback)
            return df
        
        raise RuntimeError(
            f"Falha ao ler '{collection}' no Mongo e sem fallback CSV disponível. "
            f"Detalhe: {err}"
        )

def collection_exists(name: str) -> bool:
    try:
        _, db = get_mongo()
        return name in db.list_collection_names()
    except Exception:
        return False