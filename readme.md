# Análise dos dados de acidentes no Estado de São Paulo de 2024 a 2025

<img src="imagem.png" alt="Exemplo imagem">

> Análise sobre os principais fatores relacionados aos acidentes de trânsito nos anos de 2024 e 2025.

## 💻 Pré-requisitos

Antes de começar, verifique se você atendeu aos seguintes requisitos:

- Baixar o [arquivo de dados do infosiga](https://infosiga.detran.sp.gov.br/painel/download/file/dados_infosiga.zip) para a pasta do projeto 
- As dependências Python estão no arquivo requirements.txt

## 🚀 Instalando

Para instalar, siga estas etapas:


```
pip install -r requirements.txt
```

## ☕ Usando

Para usar, siga estas etapas:

Abrir o projeto no Visual Studio Code ou executar o comando

```
jupyter notebook
```

Para utilizar os dados em um novo notebook, rodar o comando 
```
%run importa_dados.ipynb
``` 

Os dados do infosiga ficarão diponíveis nos três dataframes:

sinistros: Sinistros dos anos de 2024 a 2025 da base do infosiga  
veiculos: Veículos envolvidos em sinistros anos de 2024 a 2025 da base do infosiga  
pessoas: Vítimas envolvidos em sinistros anos de 2024 a 2025 da base do infosiga  


## 📝 Licença

Esse projeto está sob licença. Veja o arquivo [LICENÇA](LICENSE.md) para mais detalhes.