# TwitchPi v2

Projeto para Raspberry Pi com Pi-hole e TwitchPi. O ambiente gráfico e RealVNC não fazem parte da instalação: o sistema operacional existente é preservado.

## Instalação completa

```bash
curl -fsSL https://raw.githubusercontent.com/andrefpgomes/twitchpiv2/main/install-all.sh | sudo bash
```

O instalador deteta componentes existentes. Não instala XFCE, LightDM, Xorg ou RealVNC. Se Pi-hole ou Chromium já existirem, a configuração é preservada.

## TwitchPi

Aplicação em `/opt/twitch-pi`, serviço `twitch-pi.service`, interface em:

```text
http://IP_DA_RASPBERRY:8765
```

## Drops

O painel tem um tracker **read-only**. Por defeito, o filtro mostra apenas Fortnite, Minecraft e Rocket League; outros jogos podem ser adicionados no painel. A lista fica em `/opt/twitch-pi/drops_config.json`.

A autenticação OAuth é feita pelo próprio painel através do **Device Code Flow** da Twitch. O utilizador fornece apenas o Client ID da sua aplicação Twitch, carrega em `Ligar conta Twitch`, autoriza a aplicação no Twitch e a Raspberry guarda localmente o access token. A Twitch recomenda validar tokens de terceiros e documenta o Device Code Flow para dispositivos com input/browser limitado. O token fica em `/opt/twitch-pi/config.env` com permissões 600. urlTwitch OAuth — documentação oficialhttps://dev.twitch.tv/docs/authentication/getting-tokens-oauth

### Preparação da autenticação

É necessário criar uma aplicação própria no Twitch Developer Console e obter o **Client ID**. Não é necessário colocar o Client Secret no TwitchPi quando se utiliza um cliente público com Device Code Flow. O Client ID pode ser guardado no painel; o secret nunca deve ser colocado no repositório. urlRegistar uma aplicação Twitchhttps://dev.twitch.tv/docs/authentication/register-app

Depois, no painel:

1. Introduzir o Client ID.
2. `Guardar Client ID`.
3. `Ligar conta Twitch`.
4. Abrir o endereço apresentado e autorizar.
5. Aguardar até aparecer `Conta Twitch autenticada`.

A autenticação dos Drops é separada do login do Chromium usado para abrir a live.

### Limitação importante

A API oficial `Get Drops Entitlements` tem requisitos de organização/propriedade do jogo para determinados acessos. Por isso, o TwitchPi usa a consulta de inventário da sessão Twitch para o tracker quando disponível, em vez de afirmar que a API oficial fornece todas as campanhas de todos os jogos. A estrutura da consulta GraphQL pode mudar pela Twitch sem aviso. urlTwitch Drops Technical Guidehttps://dev.twitch.tv/docs/drops/technical-guide

O TwitchPi **não escolhe automaticamente uma live**. A seleção da live continua sempre sob controlo do utilizador.

## Atualização

```bash
curl -fsSL https://raw.githubusercontent.com/andrefpgomes/twitchpiv2/main/update-from-github.sh | sudo bash
```

O update cria backups e preserva `state.json`, `config.env`, `drops_config.json` existente e o perfil Chromium.

## Componentes

- Pi-hole
- Chromium
- TwitchPi Web Controller
- Drops tracker
- OAuth Device Flow
- systemd

Não instala ambiente gráfico nem RealVNC.

## Segurança

Nunca colocar passwords, OAuth tokens, refresh tokens ou sessões do Chromium no GitHub. O token local fica em `/opt/twitch-pi/config.env` com permissões restritas.
