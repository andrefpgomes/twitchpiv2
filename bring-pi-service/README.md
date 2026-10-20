# Bring! para Raspberry Pi (serviço independente)

Interface web local para preparar e enviar vários produtos para uma lista Bring! a partir de um Android.

- Porta padrão: **8766**
- Unidade systemd: `bring-pi.service`
- Diretório de instalação: `/opt/bring-pi`
- Não altera os ficheiros nem a unidade TwitchPi.
- Integração não oficial: pode deixar de funcionar se a Bring! alterar os seus serviços internos.

## Instalação

1. Copia esta pasta para a Raspberry Pi.
2. Executa `sudo bash install.sh` dentro desta pasta.
3. Edita `sudo nano /opt/bring-pi/config.env` e configura `BRING_EMAIL` e `BRING_PASSWORD`.
4. Executa `sudo systemctl restart bring-pi`.
5. Obtém o IP local com `hostname -I`.
6. No Android, ligado à mesma rede, abre `http://IP_DA_PI:8766`.
7. Introduz o valor `BRING_WEB_TOKEN` do ficheiro de configuração.

Formato: um produto por linha. Opcionalmente usa `produto | quantidade ou detalhe`.

## Diagnóstico

```bash
sudo systemctl status bring-pi
sudo journalctl -u bring-pi -n 80 --no-pager
curl http://127.0.0.1:8766/health
```

## Segurança

Não encaminhes a porta 8766 para a Internet. O ficheiro `config.env` contém credenciais e não deve ser partilhado. Não uses uma palavra-passe reutilizada noutros serviços. Confirma a lista Bring! antes de repetir um pedido que tenha falhado, para evitar duplicados.

O serviço foi preparado, mas precisa de ser testado na conta Bring! real. A biblioteca e API usadas são comunitárias e não oficiais.
