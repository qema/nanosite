import nanosite.util as util
import nanosite.build as build

import os
from datetime import datetime
import traceback
import time
import http.server
import socketserver
import threading
import atexit

def update(top, ctx, handler):
    def last_update_time(walk, ignore=[], last_t=None):
        for path, dirs, files in walk:
            fs = [(os.path.join(path, f),
                   os.path.getmtime(os.path.join(path, f))) for f in files \
                  if list(filter(lambda x:
                                 util.same_path(x, os.path.join(path, f)),
                                 ignore)) == [] \
                  and f[0] != "."]
            for n, t in fs:
                if last_t is not None and t > last_t: print(n, "modified")
            fs = list(zip(*fs))[1] if fs != [] else []
            m = max(fs) if fs != [] else 0
            m_sub = max(last_update_time(os.walk(os.path.join(path, d)),
                                         ignore, last_t) for d in dirs) \
                                         if dirs != [] else 0
            return max(m, m_sub)
    needs_update = True
    last_t = None
    last_walk = None
    while True:
        if needs_update:
            needs_update = False
            try:
                mf = build.make_site(top, ctx)
                handler.error = None
                print("[" + str(datetime.now()) + "]", "Built site.")
            except:
                last_t = None
                mf = []
                traceback.print_exc()
                handler.error = traceback.format_exc()
        walk = sorted(os.walk(top))
        t = last_update_time(walk, mf, last_t)
        time.sleep(1)
        # file updated or dirtree changed
        if last_t is not None and (t != last_t or walk != last_walk):
            needs_update = True
        last_t = t
        last_walk = walk

def run_server(port, site_dir, ctx):
    output_dir = ctx["OutputDir"]

    # start server
    class RequestHandler(http.server.SimpleHTTPRequestHandler):
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
    httpd = socketserver.TCPServer(("", port), handler)
    atexit.register(lambda: httpd.shutdown())
    
    # start update thread
    thread = threading.Thread(target=update, args=(site_dir, ctx, handler))
    thread.daemon = True
    thread.start()
    
    print("Serving at http://localhost:" + str(port) + "/")
    httpd.serve_forever()
