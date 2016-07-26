import nanosite.util as util
import nanosite.build as build

import os
from datetime import datetime
from traceback import print_exc as trace_print_exc
from traceback import format_exc as trace_format_exc
from time import sleep
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from threading import Thread
from atexit import register as atexit_register

def update(top, ctx, handler, port):
    def last_update_time(walk, ignore=[], last_t=None):
        # getmtime may fail if files changed since os.walk call
        def mtime_or_zero(path):
            try:
                return os.path.getmtime(path)
            except FileNotFoundError:
                return 0
            
        cur_max = 0
        for path, dirs, files in walk:
            fs = [(os.path.join(path, f),
                   mtime_or_zero(os.path.join(path, f))) for f in files \
                  if list(filter(lambda x:
                                 util.same_path(x, os.path.join(path, f)),
                                 ignore)) == [] \
                  and f[0] != "."]
            for n, t in fs:
                if last_t is not None and t > last_t: print(n, "modified")
            if fs != []:
                fs = list(zip(*fs))[1]
                cur_max = max(cur_max, max(fs))
        return cur_max
    
    needs_update = True
    last_t = None
    last_walk = None
    while True:
        if needs_update:
            needs_update = False
            try:  # attempt to build site
                end_slash = "/" if "site" in ctx and "url" in ctx["site"] and \
                            ctx["site"]["url"][-1] == "/" else ""
                fake_url = "http://localhost:" + str(port) + end_slash
                mf = build.make_site(top, ctx, fake_url=fake_url)
                handler.error = None
                print("[" + str(datetime.now()) + "]", "Built site.")
            except:  # if error occurred, display it
                last_t = None
                mf = []
                trace_print_exc()
                handler.error = trace_format_exc()
        walk = sorted(list(os.walk(top)))
        t = last_update_time(walk, mf, last_t)
        sleep(0.5)
        # file updated or dirtree changed
        if last_t is not None and (t != last_t or walk != last_walk):
            needs_update = True
        last_t = t
        last_walk = walk

def run_server(port, site_dir, ctx):
    output_dir = ctx["OutputDir"]

    # start server
    class RequestHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if hasattr(self, "error") and self.error is not None:
                self.send_response(200, 'OK')
                self.send_header('Content-type', 'html')
                self.end_headers()
                self.wfile.write(bytes(self.error, 'UTF-8'))
            else:
                super().do_GET()
        def translate_path(self, path):
            return os.path.join(site_dir, output_dir, path[1:])
    handler = RequestHandler
    httpd = TCPServer(("", port), handler)
    atexit_register(lambda: httpd.shutdown())
    
    # start update thread
    thread = Thread(target=update, args=(site_dir, ctx, handler, port))
    thread.daemon = True
    thread.start()
    
    print("Serving at http://localhost:" + str(port) + "/")
    httpd.serve_forever()
