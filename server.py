import http.server
import socketserver
import urllib.request
import urllib.error
import json
import os

PORT = 8000
API_URL = os.environ.get("API_URL", "http://cog-api:5000/predictions")

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_POST(self):
        if self.path == '/predictions':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                req = urllib.request.Request(API_URL, data=post_data, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req) as res:
                    response_data = res.read()
                    self.send_response(res.status)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(response_data)
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(e.read())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                error_msg = json.dumps({"error": str(e)})
                self.wfile.write(error_msg.encode())
        else:
            self.send_error(404, "Not Found")

with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
    print(f"Sunucu basariyla baslatildi!")
    print(f"Lutfen asagidaki adresi tarayicinizda acin:")
    print(f"http://127.0.0.1:{PORT}")
    print(f"-------------------------------------------")
    httpd.serve_forever()
