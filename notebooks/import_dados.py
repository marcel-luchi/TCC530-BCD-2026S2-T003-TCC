import polars as pl
import altair as alt
import polars_ds as pds
pl.Config.set_tbl_rows(30)

ND = 'NAO DISPONIVEL'

COL_ORDER = {'dia_da_semana': ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo'],
             'turno': ['MADRUGADA', 'MANHA', 'TARDE', 'NOITE'],
             'acidente_fatal': ['NAO', 'SIM'], 'municipio': ['CAMPINAS', 'GUARULHOS']}
SNS_ORDER = COL_ORDER

def get_col_order(col: str):
    return {'field': col, 'sort': COL_ORDER.get(col)}

def read_sinistros():
    sinistros_24 = pl.read_csv('dados/sinistros_2022-2024.csv', encoding='latin-1', separator=';')
    sinistros_25 = pl.read_csv('dados/sinistros_2025-2026.csv', encoding='latin-1', separator=';').filter(pl.col('ano_sinistro') == 2025)
    qt_cols = [x for x in sinistros_24.columns if x.startswith('qtd_')]
    return pl.concat([sinistros_24.with_columns(pl.col(qt_cols).cast(pl.Int16)), sinistros_25.with_columns(pl.col(qt_cols).cast(pl.Int16))]) \
            .filter(pl.col('tipo_registro') != 'NOTIFICACAO')

def trata_sinistros(df: pl.DataFrame) -> pl.DataFrame:
    return trata_populacao(
        trata_rodovia_castelo_branco(
            cria_coluna_acidente_fatal(
                trata_hora(
                    trata_logradouro(
                        filtra_tipo_via(df)
                    )
                )
            )
        )
    )
def trata_populacao(df: pl.DataFrame) -> pl.DataFrame:
    return df.filter(pl.col('municipio').is_in(['GUARULHOS', 'CAMPINAS'])) \
        .with_columns(pl.when(pl.col('logradouro').is_in(['SP 280', 'BR 116']) & (pl.col('regiao_administrativa') == 'METROPOLITANA DE SÃO PAULO'))
                           .then(pl.lit('SIM')).otherwise(pl.lit('NAO')).alias('populacao_alvo'))

def filtra_tipo_via(df: pl.DataFrame) -> pl.DataFrame:
    # Remove os registros sem o tipo de via preenchido
    return df.filter(pl.col('tipo_via') != ND)

def trata_rodovia_castelo_branco(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(pl.when(pl.col('logradouro').str.to_uppercase().str.contains('BRANCO') & (pl.col('tipo_via') == 'RODOVIARIO'))
                         .then(pl.lit('SP 280'))
                         .otherwise(pl.col('logradouro'))
                       .alias('logradouro'))

def cria_coluna_acidente_fatal(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(pl.when(pl.col('tipo_registro') == 'SINISTRO FATAL').then(pl.lit('SIM')).otherwise(pl.lit('NAO')).alias('acidente_fatal'))
    
def trata_logradouro(df: pl.DataFrame) -> pl.DataFrame:
    # Trata registros sem o local definido com base no logradouro, considera como locais públicos os logradouros com o prefixo
    # 'RUA', 'AVENIDA', 'SP', 'BR', 'AV', 'R'

    df_sinistros_tipo_logradouro = df.with_columns(pl.col('logradouro').str.split_exact(by=' ', n=1) \
                   .struct.rename_fields(['tipo_logradouro', 'resto']).alias('logradouro_struct')).unnest('logradouro_struct') \
                   .drop('resto') \
                   .with_columns(pl.col('tipo_logradouro').str.to_uppercase()) \
                   .with_columns(pl.col('tipo_logradouro')
                       .is_in(['RUA', 'AVENIDA', 'SP', 'BR', 'AV', 'R']).alias('tipo_local_publico_estimado'))
    
    sinistros = df_sinistros_tipo_logradouro.filter(
        (pl.col('tipo_local') == 'PUBLICO') | (((pl.col('tipo_local') == ND) | pl.col('tipo_local').is_null()) & pl.col('tipo_local_publico_estimado'))) \
             .with_columns(pl.lit('PUBLICO').alias('tipo_local'))
    map_tipo_via = {'ESTRADAS E RODOVIAS': 'RODOVIARIO', 'VIAS URBANAS': 'URBANO'}

    sinistros = sinistros.with_columns(pl.col('tipo_via').replace(map_tipo_via))
    return sinistros

def trata_hora(df: pl.DataFrame) -> pl.DataFrame:
   # Faz o fill dos registros sem hora preenchida com a hora mais provável com base no dia_da_semana, tipo_via, regiao_administrativa
    # Estas colunas foram as encontradas com maior correlação com a hora do acidente.
    chave_fill = ['dia_da_semana', 'tipo_via', 'regiao_administrativa']
    chave_fill_2 = ['dia_da_semana', 'tipo_via']

    sinistros = df.with_columns(
                pl.col('hora_sinistro').str.split_exact(by=':', n=1)
                    .struct.rename_fields(['hora', 'minuto']).alias('hora_struct')).unnest('hora_struct') \
                .with_columns(pl.col('hora').cast(pl.Int16), 
                pl.col('minuto').cast(pl.Int16))
    
    hora_media_por_grupo = sinistros.group_by(chave_fill).agg(
        pl.mean('hora').floor().cast(pl.Int16).alias('hora_media'))
    
    hora_media_por_grupo_2 = sinistros.group_by(chave_fill_2).agg(
        pl.mean('hora').floor().cast(pl.Int16).alias('hora_media_2'))
    
    sinistros = sinistros.join(hora_media_por_grupo, on=chave_fill) \
    .join(hora_media_por_grupo_2, on=chave_fill_2) \
    .with_columns(
    pl.coalesce(pl.col('hora'), pl.col('hora_media'), pl.col('hora_media_2')).alias('hora')) \
    .drop('hora_media', 'hora_media_2') \
    .with_columns(pl.when(pl.col('hora') < 6).then(pl.lit('MADRUGADA'))
                         .when(pl.col('hora') < 12).then(pl.lit('MANHA'))
                         .when(pl.col('hora') < 18).then(pl.lit('TARDE'))
                         .otherwise(pl.lit('NOITE')).alias('turno')) \
    .with_columns(pl.col('dia_da_semana').cast(pl.Enum(COL_ORDER['dia_da_semana'])))
    
    return sinistros.filter(pl.col('hora').is_not_null())




def read_pessoas():
    pessoas_24 = pl.read_csv('dados/pessoas_2022-2024.csv', encoding='latin-1', separator=';')
    pessoas_25 = pl.read_csv('dados/pessoas_2025-2026.csv', encoding='latin-1', separator=';').filter(pl.col('ano_sinistro') == 2025)
    return pl.concat([pessoas_24, pessoas_25])

def read_veiculos():
    veiculos_24 = pl.read_csv('dados/veiculos_2022-2024.csv', encoding='latin-1', separator=';')
    veiculos_25 = pl.read_csv('dados/veiculos_2025-2026.csv', encoding='latin-1', separator=';').filter(pl.col('ano_sinistro') == 2025)
    return pl.concat([veiculos_24, veiculos_25])