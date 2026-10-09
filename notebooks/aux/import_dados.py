import polars as pl
import altair as alt
import polars_ds as pds
import seaborn as sns

from aux.data_cleasing_sinistros import trata_sinistros
from aux.data_cleansing_pessoas import trata_pessoas
from matplotlib import pyplot as plt
sns.set_theme(context="notebook")

pl.Config.set_tbl_rows(30)


def read_sinistros_raw() -> pl.DataFrame:
    sinistros_24 = pl.read_csv('dados/sinistros_2022-2024.csv', encoding='latin-1', separator=';')
    sinistros_25 = pl.read_csv('dados/sinistros_2025-2026.csv', encoding='latin-1', separator=';').filter(pl.col('ano_sinistro') == 2025)
    qt_cols = [x for x in sinistros_24.columns if x.startswith('qtd_')]
    return pl.concat([sinistros_24.with_columns(pl.col(qt_cols).cast(pl.Int16)), sinistros_25.with_columns(pl.col(qt_cols).cast(pl.Int16))]) \
            .filter(pl.col('tipo_registro') != 'NOTIFICACAO')

def read_sinistros() -> pl.DataFrame:
    return read_sinistros_raw().pipe(trata_sinistros)

def read_pessoas_raw() -> pl.DataFrame:
    pessoas_24 = pl.read_csv('dados/pessoas_2022-2024.csv', encoding='latin-1', separator=';')
    pessoas_25 = pl.read_csv('dados/pessoas_2025-2026.csv', encoding='latin-1', separator=';').filter(pl.col('ano_sinistro') == 2025)

    sinistros = read_sinistros().select('id_sinistro', 'tipo_via')

    return pl.concat([pessoas_24, pessoas_25]).drop('tipo_via').join(sinistros, on='id_sinistro')

def read_pessoas() -> pl.DataFrame:
    return read_pessoas_raw().pipe(trata_pessoas)

def read_veiculos() -> pl.DataFrame:
    veiculos_24 = pl.read_csv('dados/veiculos_2022-2024.csv', encoding='latin-1', separator=';')
    veiculos_25 = pl.read_csv('dados/veiculos_2025-2026.csv', encoding='latin-1', separator=';').filter(pl.col('ano_sinistro') == 2025)

    sinistros = read_sinistros().pipe(trata_sinistros).select('id_sinistro')

    return pl.concat([veiculos_24, veiculos_25]).join(sinistros, on='id_sinistro')
