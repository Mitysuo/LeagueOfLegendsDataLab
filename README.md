# LeagueOfLegendsDataLab

## Objetivo

Este projeto visa prever os resultados das partidas de League of Legends usando dados fornecidos gratuitamente pela desenvolvedora Riot Games, complementados com informações de fontes externas, como [OP.GG](https://www.op.gg) e [League of Items](https://leagueofitems.com). Essas fontes adicionais acabou sendo necessárias devido às limitações no uso da API que usuários padrões possuem.

Para isso, serão analisados dados sobre o desempenho dos jogadores, estatísticas das partidas e informações específicas, como runas, com o objetivo de identificar o time vencedor.

## Pré-requisitos

### Python

- Versão: 3.10.4

### Pacotes do Python

Para instalar os pacotes necessários, acesse o diretório raiz do projeto e execute:

```bash
pip install -r requirements.txt
```

### Variáveis de Ambiente

Para obter novos dados e realizar análises adicionais, é necessário replicar o arquivo example.env, renomeando-o para .env e configurando as variáveis corretamente.

#### Riot API

A chave de API da Riot pode ser encontrada no [site para desenvolvedores da Riot Games](https://developer.riotgames.com/), onde você também encontrará informações sobre todas as funcionalidades disponíveis. Note que é necessário ter uma conta da Riot para conseguir gerar a chave de acesso, no qual é possível criar entrando no próprio site da desenvolvedora.

## Base de Dados
Ao final do processo de extração, teremos três tabelas principais:

- Matches: informações sobre a partida, como tempo de início e duração.
- Teams: dados gerais de cada time, incluindo jogadores e resultado da partida.
- PlayerMatch: informações gerais dos jogadores, como o desempenho individual durante a partida.

## Extração dos Dados

Com o arquivo .env configurado, o processo de extração de dados envolve três etapas.

- **Coleta dos dados**: Primeiro, o sistema coleta uma certa quantidade de jogadores mais bem colocados no ranking (definidos pela variável AMOUNT), depois as informações da partida que cada jogador realizou durante o patch definido pela variável GAME_VERSION e, por fim, dados de maestria dos campeões de cada jogador. Esses dados são armazenados nas tabelas PLAYER, MATCH, TEAMS, PLAYER_MATCH e em uma tabela específica chamada PlayerChampionMastery. Para iniciar o processo, execute:

```bash
    python lol_data_pipeline.py
```

- **Dados adicionais:** Logo na sequência para a obtenção dos dados relacionados a runas e campeões do patch, execute:

```bash
    python extract_stats.py
```

- **Processamento das Informações:** Com os dados adicionais coletados, para atualizar as informaçõese processá-las na tabela PLAYER_MATCH, execute:

```bash
    python lol_data_processing.py
```

## Melhorias

O processo de extração ainda apresenta alguns desafios devido às limitações da API, e a instabilidades que ocorrem devido a isso. Assim, é importante monitorar o processo, pois ele pode precisar ser reiniciado devido à sua longa duração.
