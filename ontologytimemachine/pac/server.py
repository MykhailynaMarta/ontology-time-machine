# ontologytimemachine/pac/server.py
from http.server import BaseHTTPRequestHandler, HTTPServer
from ontologytimemachine.pac.generator import build_pac  # <- ЦЕЙ ІМПОРТ ОБОВ'ЯЗКОВИЙ ТУТ


def start_pac_server(config):

    class Handler(BaseHTTPRequestHandler):

        def do_GET(self):
            if self.path != "/proxy.pac":
                self.send_response(404)
                self.end_headers()
                return

            # ТУТ викликається функція, яку сервер не міг знайти
            pac = build_pac(config)

            self.send_response(200)
            self.send_header("Content-Type", "application/x-ns-proxy-autoconfig")
            self.end_headers()

            self.wfile.write(pac.encode("utf-8"))

        def log_message(self, format, *args):
            return  # Прибирає зайвий шум у консолі

    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print("[PAC] http://localhost:8000/proxy.pac")
    server.serve_forever()