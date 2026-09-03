import polars as pl
import altair as alt

ND = 'NAO DISPONIVEL'


def get_col_order(col: str):
    COL_ORDER = {'dia_da_semana': ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo'],
             'turno': ['MADRUGADA', 'MANHA', 'TARDE', 'NOITE'],
             'fatalidade': ['NAO', 'SIM']}
    
    return {'field': col, 'sort': COL_ORDER.get(col)}

def read_sinistros():
    sinistros_24 = pl.read_csv('dados/sinistros_2022-2024.csv', encoding='latin-1', separator=';').filter(pl.col('ano_sinistro') == 2024)
    sinistros_25 = pl.read_csv('dados/sinistros_2025-2026.csv', encoding='latin-1', separator=';').filter(pl.col('ano_sinistro') == 2025)
    qt_cols = [x for x in sinistros_24.columns if x.startswith('qtd_')]
    return pl.concat([sinistros_24.with_columns(pl.col(qt_cols).cast(pl.Int16)), sinistros_25.with_columns(pl.col(qt_cols).cast(pl.Int16))])


def read_pessoas():
    pessoas_24 = pl.read_csv('dados/pessoas_2022-2024.csv', encoding='latin-1', separator=';').filter(pl.col('ano_sinistro') == 2024)
    pessoas_25 = pl.read_csv('dados/pessoas_2025-2026.csv', encoding='latin-1', separator=';').filter(pl.col('ano_sinistro') == 2025)
    return pl.concat([pessoas_24, pessoas_25])