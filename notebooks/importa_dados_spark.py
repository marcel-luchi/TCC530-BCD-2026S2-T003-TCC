from pyspark.sql import SparkSession
from pyspark.sql.functions import col

import zipfile

# Build a standard new session
spark = SparkSession.builder \
        .appName("AnaliseInfosiga") \
        .master("local[*]") \
        .config("spark.driver.memory", "8g") \
        .config("spark.driver.maxResultSize", "4g") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")


sinistros = spark.read.csv('dados/sinistros_2022-2024.csv', encoding='ISO-8859-1', sep=';', header=True)\
                 .unionAll(spark.read.csv('dados/sinistros_2025-2026.csv', encoding='ISO-8859-1', sep=';', header=True)) \
                 .filter(col('ano_sinistro').isin('2024', '2025')) \
                 .filter(col('regiao_administrativa') == 'METROPOLITANA DE SÃO PAULO')

pessoas = spark.read.csv('dados/pessoas_2022-2024.csv', encoding='ISO-8859-1', sep=';', header=True)\
                 .unionAll(spark.read.csv('dados/pessoas_2025-2026.csv', encoding='ISO-8859-1', sep=';', header=True)) \
                 .join(sinistros.select('id_sinistro'), 'id_sinistro')

veiculos = spark.read.csv('dados/veiculos_2022-2024.csv', encoding='ISO-8859-1', sep=';', header=True)\
                 .unionAll(spark.read.csv('dados/veiculos_2025-2026.csv', encoding='ISO-8859-1', sep=';', header=True)) \
                 .join(sinistros.select('id_sinistro'), 'id_sinistro')