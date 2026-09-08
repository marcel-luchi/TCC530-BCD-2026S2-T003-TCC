import polars as pl
import altair as alt
import polars_ds as pds

ND = 'NAO DISPONIVEL'


def get_col_order(col: str):
    COL_ORDER = {'dia_da_semana': ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo'],
             'turno': ['MADRUGADA', 'MANHA', 'TARDE', 'NOITE'],
             'acidente_fatal': ['NAO', 'SIM']}
    
    return {'field': col, 'sort': COL_ORDER.get(col)}

def read_sinistros():
    sinistros_24 = pl.read_csv('dados/sinistros_2022-2024.csv', encoding='latin-1', separator=';').filter(pl.col('ano_sinistro') == 2024)
    sinistros_25 = pl.read_csv('dados/sinistros_2025-2026.csv', encoding='latin-1', separator=';').filter(pl.col('ano_sinistro') == 2025)
    qt_cols = [x for x in sinistros_24.columns if x.startswith('qtd_')]
    return pl.concat([sinistros_24.with_columns(pl.col(qt_cols).cast(pl.Int16)), sinistros_25.with_columns(pl.col(qt_cols).cast(pl.Int16))]) \
             #.filter(pl.col('tipo_registro') != 'NOTIFICACAO') \
             #.filter(pl.col('tipo_local') == 'PUBLICO')

def trata_sinistros(df: pl.DataFrame) -> pl.DataFrame:
    local_estimado = df.with_columns(pl.col('logradouro').str.split_exact(by=' ', n=1) \
                   .struct.rename_fields(['tipo_logradouro', 'resto']).alias('logradouro_struct')).unnest('logradouro_struct') \
                   .drop('resto') \
                   .with_columns(pl.col('tipo_logradouro').str.to_uppercase()) \
                   .with_columns(pl.col('tipo_logradouro')
                       .is_in(['RUA', 'AVENIDA', 'SP', 'BR', 'AV', 'R',]).alias('tipo_local_publico_estimado'))
    
    sinistros = local_estimado.filter(
        (pl.col('tipo_local') == 'PUBLICO') | ((pl.col('tipo_local') == ND) & pl.col('tipo_local_publico_estimado'))) \
             .with_columns(
                pl.col('hora_sinistro').str.split_exact(by=':', n=1)
                    .struct.rename_fields(['hora', 'minuto']).alias('hora_struct')).unnest('hora_struct') \
             .with_columns(
                pl.col('hora').cast(pl.Int16), 
                pl.col('minuto').cast(pl.Int16),
                pl.when(pl.col('tipo_registro') == 'SINISTRO FATAL') \
                .then(pl.lit('SIM')) \
                .otherwise(pl.lit('NAO')).alias('acidente_fatal'))

    
    chave_fill = ['dia_da_semana', 'tipo_via', 'regiao_administrativa']
    chave_fill_2 = ['dia_da_semana', 'tipo_via']
    hora_media_por_grupo = sinistros.group_by(chave_fill).agg(
        pl.mean('hora').floor().cast(pl.Int16).alias('hora_media'))
    hora_media_por_grupo_2 = sinistros.group_by(chave_fill_2).agg(
        pl.mean('hora').floor().cast(pl.Int16).alias('hora_media_2'))

    return sinistros.join(hora_media_por_grupo, on=chave_fill) \
    .join(hora_media_por_grupo_2, on=chave_fill_2) \
    .with_columns(
    pl.coalesce(pl.col('hora'), pl.col('hora_media'), pl.col('hora_media_2')).alias('hora')) \
    .drop('hora_media', 'hora_media_2') \
    .with_columns(pl.when(pl.col('hora') < 6).then(pl.lit('MADRUGADA'))
                         .when(pl.col('hora') < 12).then(pl.lit('MANHA'))
                         .when(pl.col('hora') < 18).then(pl.lit('TARDE'))
                         .otherwise(pl.lit('NOITE')))



def read_pessoas():
    pessoas_24 = pl.read_csv('dados/pessoas_2022-2024.csv', encoding='latin-1', separator=';').filter(pl.col('ano_sinistro') == 2024)
    pessoas_25 = pl.read_csv('dados/pessoas_2025-2026.csv', encoding='latin-1', separator=';').filter(pl.col('ano_sinistro') == 2025)
    return pl.concat([pessoas_24, pessoas_25])

def read_veiculos():
    veiculos_24 = pl.read_csv('dados/veiculos_2022-2024.csv', encoding='latin-1', separator=';').filter(pl.col('ano_sinistro') == 2024)
    veiculos_25 = pl.read_csv('dados/veiculos_2025-2026.csv', encoding='latin-1', separator=';').filter(pl.col('ano_sinistro') == 2025)
    return pl.concat([veiculos_24, veiculos_25])