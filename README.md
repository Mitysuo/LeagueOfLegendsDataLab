# LeagueOfLegendsDataLab

## Objetivo

Este projeto visa prever os resultados das partidas de League of Legends usando dados fornecidos gratuitamente pela desenvolvedora Riot Games, complementados com informações de fontes externas, como [OP.GG](https://www.op.gg) e [League of Items](https://leagueofitems.com). Essas fontes adicionais acabou sendo necessárias devido às limitações no uso da API que usuários padrões possuem.

Para isso, serão analisados dados sobre o desempenho dos jogadores, estatísticas das partidas e informações específicas, como runas, com o objetivo de identificar o time vencedor.

## Pré-requisitos

### Python

- Versão: 3.10 ou Superior

### Poetry

Para conseguir executar os códigos é necessário fazer a [instalação do Poetry](https://python-poetry.org/docs/). Estaremos utilizando a versão 1.8.3. Após instalar o Poetry, execute os comandos abaixo na raiz do diretório para atualizar todas as dependências:

```bash
poetry lock
poetry install --with test,dev
```

### SQL Management Studio

Este projeto foi testado e validado exclusivamente utilizando o SQL Management Studio como sistema de gerenciamento de banco de dados para o armazenamento das informações.

### Sistema Operacional

O sistema operacional utilizado e validado foi o Windows 11.

## Execução do projeto

Após concluir as configurações iniciais, você pode executar os arquivos `.py` utilizando o seguinte comando:

```bash
poetry run python -m [caminho-do-arquivo]
```

Certifique-se de substituir [caminho-do-arquivo] pelo caminho completo do arquivo que deseja executar, como, por exemplo, `project.extract_stats`. Além disso, verifique se a estrutura do módulo no projeto está correta e garanta que você esteja na raiz do projeto ao executar o comando para assegurar seu sucesso.

Para executar arquivos do tipo notebook, é necessário executar previamente o comando:

```bash
poetry run jupyter lab
```

Esse comando abrirá uma aba no Jupyter Lab, permitindo a execução do código de maneira interativa

### Variáveis de Ambiente

Para obter novos dados e realizar análises adicionais, é necessário replicar o arquivo `.env.template`, renomeando-o para `.env` e configurando as variáveis corretamente.

#### Riot API

A chave de API da Riot pode ser encontrada no [site para desenvolvedores da Riot Games](https://developer.riotgames.com/), onde você também encontrará informações sobre todas as funcionalidades disponíveis. Note que é necessário ter uma conta da Riot para conseguir gerar a chave de acesso, no qual é possível criar entrando no próprio site da desenvolvedora.

## Base de Dados

Ao final do processo de extração, teremos três tabelas principais:

- MATCH_TABLE: informações sobre a partida, como tempo de início e duração.
- TEAM_TABLE: dados gerais de cada time, incluindo jogadores e resultado da partida.
- PLAYER_MATCH_TABLE: informações gerais dos jogadores, como o desempenho individual durante a partida.

## Extração dos Dados

Com o arquivo `.env` devidamente configurado, o processo de extração de dados é dividido em três etapas:

- **Coleta dos dados**: Inicialmente, o sistema coleta informações sobre os jogadores mais bem classificados no ranking, conforme o valor definido pela variável AMOUNT. Em seguida, são obtidas as partidas realizadas por esses jogadores durante o patch especificado pela variável GAME_VERSION, além dos dados de maestria dos campeões de cada jogador. Esses dados são armazenados nas tabelas PLAYER_TABLE, MATCH_TABLE, TEAM_TABLE, PLAYER_MATCH_TABLE e em uma tabela específica CHAMPION_MASTERY_TABLE. Para iniciar o processo, execute o seguinte comando:

```bash
    poetry run python -m project.data_manager
```

- **Dados adicionais:** Na etapa seguinte, para obter informações relacionadas a runas e campeões do patch, execute:

```bash
    poetry run python -m project.extract_stats
```

- **Processamento das Informações:** Após a coleta dos dados adicionais, as informações são atualizadas e processadas na tabela PLAYER_MATCH. Além disso, é realizado o processamento completo das tabelas para gerar a tabela utilizada nas análises e modelagens. Para isso, execute:

```bash
    poetry run python -m project.data_processing
```

## Melhorias

O processo de extração ainda apresenta alguns desafios devido às limitações da API, e a instabilidades que ocorrem devido a isso. Assim, é importante monitorar o processo, pois ele pode precisar ser reiniciado devido à sua longa duração.
