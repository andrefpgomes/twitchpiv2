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

O painel tem um tracker **read-only** inspirado na arquitetura de trackers de Drops: inventário/progresso é lido da sessão Twitch através da consulta GraphQL de inventário quando existe um token OAuth local válido. Não envia watch events e não faz claim automático nesta camada.

Por defeito, o filtro mostra apenas:

- Fortnite
- Minecraft
- Rocket League

Outros jogos podem ser adicionados no próprio painel. A lista fica em `/opt/twitch-pi/drops_config.json`.

A informação de Drops depende da sessão/autorizações da Twitch e dos campos/consultas que a Twitch disponibiliza; estes podem mudar sem aviso. A API oficial documenta que Drops acompanham atividade de visualização e que o acesso a determinados endpoints depende do contexto de desenvolvedor. citehttps://dev.twitch.tv/docs/drops

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
- systemd

Não instala ambiente gráfico nem RealVNC.

## Segurança

Nunca colocar passwords, OAuth tokens ou sessões do Chromium no GitHub. O token local, quando usado para o tracker, fica em `/opt/twitch-pi/config.env` com permissões restritas.
