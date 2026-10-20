#!/usr/bin/env python3
import os, asyncio, html, secrets, logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import aiohttp
from bring_api import Bring

HOST = os.getenv("BRING_HOST", "0.0.0.0")
PORT = int(os.getenv("BRING_PORT", "8766"))
APP_TOKEN = os.environ["BRING_WEB_TOKEN"]
BRING_EMAIL = os.environ["BRING_EMAIL"]
BRING_PASSWORD = os.environ["BRING_PASSWORD"]
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def esc(v): return html.escape(str(v), quote=True)

async def get_lists():
    async with aiohttp.ClientSession() as session:
        bring = Bring(session, BRING_EMAIL, BRING_PASSWORD)
        await bring.login()
        data = await bring.load_lists()
        return data.get("lists", [])

async def add_items(list_uuid, lines):
    async with aiohttp.ClientSession() as session:
        bring = Bring(session, BRING_EMAIL, BRING_PASSWORD)
        await bring.login()
        for line in lines:
            parts = [p.strip() for p in line.split("|", 1)]
            if parts[0]:
                await bring.save_item(list_uuid, parts[0], parts[1] if len(parts) > 1 else "")

def page(title, body):
    return ('''<!doctype html><html lang="pt-PT"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>''' + esc(title) + '''</title>
<style>body{font-family:system-ui,sans-serif;max-width:680px;margin:24px auto;padding:0 16px;background:#f6f7f8;color:#202124}
main{background:white;border-radius:16px;padding:22px;box-shadow:0 2px 12px #0001}
label{display:block;margin:14px 0 6px;font-weight:600}input,select,textarea{box-sizing:border-box;width:100%;padding:12px;border:1px solid #bbb;border-radius:8px;font:inherit}
button{margin-top:16px;padding:12px 16px;border:0;border-radius:9px;background:#146c43;color:white;font-weight:700;font:inherit;width:100%}
code{overflow-wrap:anywhere}.small{font-size:.9rem;color:#555}a{color:#146c43}</style><main><h1>''' + esc(title) + "</h1>" + body + "</main></html>")

class Handler(BaseHTTPRequestHandler):
    server_version = "BringPi/1.0"
    def log_message(self, fmt, *args):
        logging.info("%s - %s", self.client_address[0], fmt % args)
    def authorized(self, params=None):
        token = self.headers.get("X-Bring-Token", "")
        if params: token = params.get("token", [token])[0]
        return bool(token) and secrets.compare_digest(token, APP_TOKEN)
    def respond(self, status, body, content_type="text/html; charset=utf-8"):
        raw = body.encode("utf-8")
        self.send_response(status); self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw))); self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if self.path.split("?", 1)[0] == "/health":
            self.respond(200, '{"status":"ok","port":8766}', "application/json"); return
        params = parse_qs(urlparse(self.path).query)
        if not self.authorized(params):
            self.respond(401, page("Acesso protegido", '<p>Introduz o token de acesso.</p><form method="get"><label>Token</label><input type="password" name="token" required><button>Entrar</button></form>')); return
        token = params.get("token", [""])[0]
        try:
            lists = asyncio.run(get_lists())
            options = "".join('<option value="' + esc(x["listUuid"]) + '">' + esc(x.get("name", "Lista")) + '</option>' for x in lists)
            body = ('<p>Escolhe a lista e cola um produto por linha. Usa <code>produto | detalhe</code> para incluir quantidade ou notas.</p>'
              '<form method="post" action="/add"><input type="hidden" name="token" value="' + esc(token) + '">'
              '<label>Lista Bring!</label><select name="list_uuid" required>' + options + '</select>'
              '<label>Produtos</label><textarea name="items" rows="10" placeholder="Leite | 2 litros&#10;Ovos | 12 unidades&#10;Tomates" required></textarea>'
              '<button type="submit">Adicionar à Bring!</button></form>'
              '<p class="small">Só adiciona produtos; não elimina nem conclui itens existentes.</p>')
            self.respond(200, page("Bring! para Raspberry Pi", body))
        except Exception:
            logging.exception("Failed to load Bring lists")
            self.respond(502, page("Erro na ligação à Bring!", '<p>Não foi possível carregar as listas. Verifica as credenciais e a ligação.</p><p>Diagnóstico: <code>sudo journalctl -u bring-pi -n 80</code></p>'))
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > 100000:
            self.respond(413, "Pedido demasiado grande", "text/plain; charset=utf-8"); return
        params = parse_qs(self.rfile.read(length).decode("utf-8", "replace"))
        if not self.authorized(params):
            self.respond(401, page("Acesso negado", "<p>Token inválido.</p>")); return
        if self.path.split("?", 1)[0] != "/add":
            self.respond(404, "Não encontrado", "text/plain; charset=utf-8"); return
        list_uuid = params.get("list_uuid", [""])[0]
        lines = [x.strip() for x in params.get("items", [""])[0].splitlines() if x.strip()]
        if not list_uuid or not lines or len(lines) > 100:
            self.respond(400, page("Dados inválidos", "<p>Indica uma lista e entre 1 e 100 produtos.</p>")); return
        try:
            asyncio.run(add_items(list_uuid, lines))
            logging.info("Submitted %d items to Bring", len(lines))
            self.respond(200, page("Pedido enviado", '<p>Foram enviados ' + str(len(lines)) + ' produto(s) à Bring!.</p><p>Confirma o resultado na app Android.</p><p><a href="/">Voltar</a></p>'))
        except Exception:
            logging.exception("Failed to add Bring items")
            self.respond(502, page("Erro ao adicionar", '<p>Não foi possível confirmar a operação. Confirma a lista na app antes de repetir, para evitar duplicados.</p><p><code>sudo journalctl -u bring-pi -n 80</code></p>'))

if __name__ == "__main__":
    logging.info("Bring! service listening on %s:%s", HOST, PORT)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
