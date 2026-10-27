import polars as pl
from polars import col as c
from aux.constants import *


def cast_datas(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(c("ano_sinistro").cast(pl.Utf8),
                           c('hora').cast(pl.String).str.zfill(2))


def trata_sinistros(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.pipe(filtra_tipo_via)
        .pipe(trata_logradouro)
        .pipe(trata_hora)
        .pipe(cria_coluna_sinistro_fatal)
        .pipe(trata_rodovia_castelo_branco)
        .pipe(trata_populacao)
        .pipe(cast_datas)
        .pipe(trata_veiculos_presentes)
        .pipe(set_enum_columns)
    )
        


def set_enum_columns(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns([
        c(col).cast(pl.Enum(COL_ORDER[col]))
        for col in COL_ORDER
    ])


def trata_populacao(df: pl.DataFrame) -> pl.DataFrame:
    return df.filter(c('municipio').is_in(['GUARULHOS', 'CAMPINAS'])) \
        .with_columns(pl.when(c('logradouro').is_in(['SP 280', 'BR 116'])
                              & (c('regiao_administrativa') == 'METROPOLITANA DE SÃO PAULO'))
                      .then(pl.lit('SIM'))
                      .otherwise(pl.lit('NAO'))
                        .alias('populacao_alvo'))


def filtra_tipo_via(df: pl.DataFrame) -> pl.DataFrame:
    # Remove os registros sem o tipo de via preenchido
    return df.filter(c('tipo_via') != ND)


def trata_rodovia_castelo_branco(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(pl.when(c('logradouro').str.to_uppercase().str.contains('BRANCO') & (c('tipo_via') == 'RODOVIARIO'))
                           .then(pl.lit('SP 280'))
                           .otherwise(c('logradouro'))
                           .alias('logradouro'))


def cria_coluna_sinistro_fatal(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(pl.when(c('tipo_registro') == 'SINISTRO FATAL').then(pl.lit('SIM')).otherwise(pl.lit('NAO')).alias('sinistro_fatal'))


def trata_logradouro(df: pl.DataFrame) -> pl.DataFrame:
    # Trata registros sem o local definido com base no logradouro, considera como locais públicos os logradouros com o prefixo
    # 'RUA', 'AVENIDA', 'SP', 'BR', 'AV', 'R'

    df_sinistros_tipo_logradouro = df.with_columns(c('logradouro').str.split_exact(by=' ', n=1)
                                                   .struct.rename_fields(['tipo_logradouro', 'resto']).alias('logradouro_struct')).unnest('logradouro_struct') \
        .drop('resto') \
        .with_columns(c('tipo_logradouro').str.to_uppercase()) \
        .with_columns(c('tipo_logradouro')
                      .is_in(['RUA', 'AVENIDA', 'SP', 'BR', 'AV', 'R']).alias('tipo_local_publico_estimado'))

    sinistros = df_sinistros_tipo_logradouro.filter(
        (c('tipo_local') == 'PUBLICO') | (((c('tipo_local') == ND) | c('tipo_local').is_null()) & c('tipo_local_publico_estimado'))) \
        .with_columns(pl.lit('PUBLICO').alias('tipo_local'))

    map_tipo_via = {'ESTRADAS E RODOVIAS': 'RODOVIARIO',
                    'VIAS URBANAS': 'URBANO'}
    sinistros = sinistros.with_columns(
        c('tipo_via').replace(map_tipo_via))
    return sinistros


def trata_hora(df: pl.DataFrame) -> pl.DataFrame:
   # Faz o fill dos registros sem hora preenchida com a hora mais provável com base no dia_da_semana, tipo_via, regiao_administrativa
    # Estas colunas foram as encontradas com maior correlação com a hora do acidente.
    chave_fill = ['dia_da_semana', 'tipo_via', 'regiao_administrativa']
    chave_fill_2 = ['dia_da_semana', 'tipo_via']

    sinistros = df.with_columns(
        c('hora_sinistro').str.split_exact(by=':', n=1)
        .struct.rename_fields(['hora', 'minuto']).alias('hora_struct')).unnest('hora_struct') \
        .with_columns(c('hora').cast(pl.Int16),
                      c('minuto').cast(pl.Int16))

    hora_media_por_grupo = sinistros.group_by(chave_fill).agg(
        pl.mean('hora').floor().cast(pl.Int16).alias('hora_media'))

    hora_media_por_grupo_2 = sinistros.group_by(chave_fill_2).agg(
        pl.mean('hora').floor().cast(pl.Int16).alias('hora_media_2'))

    sinistros = sinistros.join(hora_media_por_grupo, on=chave_fill) \
        .join(hora_media_por_grupo_2, on=chave_fill_2) \
        .with_columns(
        pl.coalesce(c('hora'), c('hora_media'), c('hora_media_2')).alias('hora')) \
        .drop('hora_media', 'hora_media_2') \
        .with_columns(pl.when(c('hora') < 6).then(pl.lit('MADRUGADA'))
                      .when(c('hora') < 12).then(pl.lit('MANHA'))
                      .when(c('hora') < 18).then(pl.lit('TARDE'))
                      .otherwise(pl.lit('NOITE')).alias('turno'))

    return sinistros.filter(c('hora').is_not_null())


def trata_veiculos_presentes(df: pl.DataFrame) -> pl.DataFrame:
    cols_veiculos = ['qtd_pedestre',
                     'qtd_bicicleta',
                     'qtd_motocicleta',
                     'qtd_automovel',
                     'qtd_onibus',
                     'qtd_caminhao',
                     'qtd_veic_outros',
                     'qtd_veic_nao_disponivel']

    return df.with_columns(
        pl.concat_list([
            pl.when(pl.col(col).is_not_null())
          .then(pl.lit(col.removeprefix("qtd_")))
          .otherwise(None)
            for col in cols_veiculos
        ])
        .list.drop_nulls()
        .list.sort()
        .list.unique()
        .alias("veiculos_presentes"))
