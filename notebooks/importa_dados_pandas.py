import pandas as pd
import numpy as np
import zipfile


with zipfile.ZipFile("dados_infosiga.zip") as z:
    sinistros_22_24 = pd.read_csv(z.open('sinistros_2022-2024.csv'), encoding='latin-1', delimiter=';')
    sinistros_25_26 = pd.read_csv(z.open('sinistros_2025-2026.csv'), encoding='latin-1', delimiter=';')
    sinistros_24 = sinistros_22_24[sinistros_22_24['ano_sinistro'] == 2024]
    sinistros_25 = sinistros_25_26[sinistros_25_26['ano_sinistro'] == 2025]
    sinistros = pd.concat([sinistros_24, sinistros_25], ignore_index=True)
    sinistros = sinistros[sinistros['tipo_registro'] != 'NOTIFICACAO']
    del sinistros_22_24, sinistros_25_26, sinistros_24, sinistros_25  

    pessoas_22_24 = pd.read_csv(z.open('pessoas_2022-2024.csv'), encoding='latin-1', delimiter=';')
    pessoas_25_26 = pd.read_csv(z.open('pessoas_2025-2026.csv'), encoding='latin-1', delimiter=';')
    pessoas_24 = pessoas_22_24[pessoas_22_24['ano_mes_sinistro'].str.startswith('2024')]
    pessoas_25 = pessoas_25_26[pessoas_25_26['ano_mes_sinistro'].str.startswith('2025')]
    pessoas = pd.concat([pessoas_24, pessoas_25], ignore_index=True)
    del pessoas_22_24, pessoas_25_26, pessoas_24, pessoas_25
    veiculos_22_24 = pd.read_csv(z.open('veiculos_2022-2024.csv'), encoding='latin-1', delimiter=';')
    veiculos_25_26 = pd.read_csv(z.open('veiculos_2025-2026.csv'), encoding='latin-1', delimiter=';')
    veiculos_24 = veiculos_22_24[veiculos_22_24['ano_mes_sinistro'].str.startswith('2024')]
    veiculos_25 = veiculos_25_26[veiculos_25_26['ano_mes_sinistro'].str.startswith('2025')]
    veiculos = pd.concat([veiculos_24, veiculos_25], ignore_index=True)
    del veiculos_22_24, veiculos_25_26, veiculos_24, veiculos_25