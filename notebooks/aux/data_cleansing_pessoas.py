import polars as pl
from polars import col as c
from aux.constants import *

def cast_datas(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(c("ano_sinistro").cast(pl.Utf8),
                          c('hora').cast(pl.String).str.zfill(2)) 


def trata_pessoas(df: pl.DataFrame) -> pl.DataFrame:
    return df.filter(c('modo_transporte_vitima').is_not_null()) \
    .with_columns(c("ano_sinistro").cast(pl.Utf8))

