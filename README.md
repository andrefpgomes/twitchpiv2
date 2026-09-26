# TwitchPi v2

Projeto para Raspberry Pi com Pi-hole e TwitchPi. O ambiente gráfico e RealVNC não fazem parte da instalação: o sistema operacional existente é preservado.

## Instalação completa

Numa Raspberry com acesso à Internet:

```bash
curl -fsSL https://raw.githubusercontent.com/andrefpgomes/twitchpiv2/main/install-all.sh | sudo bash
```

O instalador verifica o que já existe. Se o Pi-hole estiver instalado, não o reinstala nem substitui a configuração. O mesmo vale para Chromium. O ambiente gráfico e RealVNC não são instalados.

## TwitchPi

A aplicação fica em `/opt/twitch-pi` e usa o serviço `twitch-pi.service`.

Interface:

```text
http://IP_DA_RASPBERRY:8765
```

## Atualização

```bash
curl -fsSL https://raw.githubusercontent.com/andrefpgomes/twitchpiv2/main/update-from-github.sh | sudo bash
```

O update cria um backup da aplicação e preserva `state.json`, configurações locais e o perfil do Chromium.

## Componentes

- Pi-hole
- Chromium
- TwitchPi Web Controller
- systemd

Não instala XFCE, LightDM, Xorg ou RealVNC.

## Segurança

Não guardar passwords, tokens Twitch ou sessões do Chromium no GitHub.
