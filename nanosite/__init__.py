import markdown
import os
import json
import shutil
import argparse
import time
import http.server
import socketserver
import threading
import atexit
from datetime import datetime
from html import escape as escape_HTML

# fetch key, possibly nested thru dot notation
def ctx_fetch(ctx, line):
    key, params = (line.split(" ", 1) + [""])[:2]
    parts = key.split(".", 1)
    if parts[0] in ctx:
        if len(parts) == 1:
            value = ctx[parts[0]]
            # if it's a macro, call it with parameter [ctx]
            if callable(value):
                value = value(ctx, *tokenize_params(params))
            return value
        else:
            return ctx_fetch(ctx[parts[0]], parts[1])
    else:
        return None

# compile markdown to HTML, returning (html, meta_info) tuple
def compile_markdown(md_text):
    md = markdown.Markdown(extensions=["markdown.extensions.meta"])
    html = md.convert(md_text)
    try:
        meta = {k: "".join(v) for k, v in md.Meta.items()} \
           if md.Meta is not None else {}
    except AttributeError:
        meta = {}
    return (html, meta)

def tokenize_params(params):
    out = []
    in_string = False
    for token in params.split(" "):
        if token != "":
            if token[0] == '"':
                in_string = True
                out.append(token[1:])
            elif in_string:
                if token[-1] == '"':
                    token = token[:-1]
                    in_string = False
                out[-1] += " " + token
            elif token.isdecimal():
                out.append(int(token))
            else:
                try:
                    out.append(float(token))
                except ValueError:
                    out.append(token)
    return out

template_cache = {}
# get template from path (cached)
def get_template(path):
    global template_cache
    if path in template_cache:
        return template_cache[path]
    else:
        tmpl = open(path, "r").read()
        template_cache[path] = tmpl
        return tmpl

# fill template according to rules in doc.txt
def fill_template(tmpl, ctx):
    #print("FILLING TEMPLATE ", tmpl, "WITH CONTEXT", ctx)
    
    # get part before delim and part after
    def get_chunk(s, delim):
        a = s.split(delim, 1)
        return (a[0], "") if len(a) <= 1 else a
    rest = tmpl
    out = ""
    seeking = None
    seek_depth = 0
    depth_if = 0
    depth_for = 0
    for_block_accum = ""
    for_variable = ""
    for_collection = None
    while len(rest) > 0:
        cur, rest = get_chunk(rest, "{{")
        #print("}}", cur, "{{", rest, seeking, seek_depth, depth_if)
        #print()
        if seeking is None:
            out += cur
        else:
            for_block_accum += cur
        key, rest = get_chunk(rest, "}}")
        key = key.strip()
        cmd = key.lower().split()

        #print("{{", key, "}}", rest, seeking, seek_depth, depth_if)
        #print()
        #print()

        if seeking is not None:
            run_for_block = False
            if cmd[0] == "#if":
                depth_if += 1
            elif cmd[0] == "#else":
                if "#else" in seeking and seek_depth == depth_if:
                    #print("FOUND MATCHING ELSE", seek_depth, depth_if)
                    seeking = None
            elif cmd[0] == "#elif":
                if "#elif" in seeking and seek_depth == depth_if:
                    if ctx_fetch(ctx, cmd[1]):
                        #print("FOUND MATCHING ELIF", seek_depth, depth_if)
                        seeking = None
            elif cmd[0] == "#endif":
                if "#endif" in seeking and seek_depth == depth_if:
                    #print("FOUND MATCHING ENDIF", seek_depth, depth_if)
                    seeking = None
                depth_if -= 1
            elif cmd[0] == "#for":
                depth_for += 1
            elif cmd[0] == "#endfor":
                if "#endfor" in seeking and seek_depth == depth_for:
                    seeking = None
                    run_for_block = True
                depth_for -= 1
                    
            if run_for_block:
                orig = None
                if for_variable in ctx:
                    orig = ctx["for_variable"]
                    
                for item in for_collection:
                    ctx[for_variable] = item
                    out += fill_template(for_block_accum, ctx)
                if orig is None:
                    ctx.pop(for_variable)
                else:
                    ctx[for_variable] = orig
            else:
                for_block_accum += "{{" + key + "}}"
        else:
            if cmd == [] or cmd[0] == "":
                pass
            elif cmd[0] == "#if":
                depth_if += 1
                if not ctx_fetch(ctx, cmd[1]):  # if ctx[key] evaluates to True
                    seeking = {"#elif", "#else", "#endif"}
                    seek_depth = depth_if
            elif cmd[0] == "#else" or cmd[0] == "#elif":
                if depth_if == 0:
                    raise Exception(cmd[0] + " without #if")
                seeking = {"#endif"}
                seek_depth = depth_if
            elif cmd[0] == "#endif":
                depth_if -= 1
            elif cmd[0] == "#for":
                depth_for += 1
                for_block_accum = ""
                seeking = {"#endfor"}
                seek_depth = depth_for
                for_variable = cmd[1]
                for_collection = ctx_fetch(ctx, " ".join(cmd[3:]))
            elif cmd[0] == "#endfor":
                depth_for -= 1
            else:
                if key[0] == "{":
                    val = str(ctx_fetch(ctx, key[1:]))
                    _, rest = get_chunk(rest, "}") # get matching close brace
                else:
                   val = escape_HTML(str(ctx_fetch(ctx, key)))
                out += fill_template(val, ctx)
    if depth_if > 0:
        raise Exception("#if without #endif")
    elif depth_if < 0:
        raise Exception("#endif without #if")
    if depth_for > 0:
        raise Exception("#for without #endfor")
    elif depth_for < 0:
        raise Exception("#endfor without #for")
    return out

def build_file(top, node, ctx):
    assert(node["is_file"])
    
    path = node["input_path"]
    root, ext = os.path.splitext(path)

    modified_files = []
    if ext.lower() in {".md", ".md+", ".html+"}:  # compile against templates
        # copy all node properties
        for k in node:
            ctx[k] = node[k]

        # fill local template
        template_path = node["template_path"]
        if template_path is not None:
            local_tmpl = get_template(template_path)
            local_out_html = fill_template(local_tmpl, ctx)
        else:
            local_out_html = node["content"]

        # get master template
        master_tmpl_path = os.path.join(top, ctx["MetaDir"], "master.tmpl")
        master_tmpl = get_template(master_tmpl_path)

        # fill master template
        ctx["content"] = local_out_html
        out_html = fill_template(master_tmpl, ctx)

        relpath = os.path.relpath(root + ".html", top)
        out_path = os.path.join(top, ctx["OutputDir"], relpath)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        # create output file in output folder
        with open(out_path, "w") as f:
            # get/create output path
            f.write(out_html)
        modified_files = [os.path.abspath(out_path)]
    elif ext.lower() == ".tmpl":
        pass
    else:   # copy file (make hard link on unix)
        relpath = os.path.relpath(path, top)
        out_path = os.path.join(top, ctx["OutputDir"], relpath)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        # copy if src and dest are different (i.e. OutputDir != ".")
        if os.path.abspath(path) != os.path.abspath(out_path):
            if os.name == "nt":
                shutil.copyfile(path, out_path)
            else:
                if os.path.exists(out_path):
                    os.unlink(out_path)
                os.link(path, out_path)
            modified_files = [os.path.abspath(out_path)]
    return modified_files
    
def add_dirtree_file(top, path, ctx, template_path):
    root, ext = os.path.splitext(path)

    out_dict = {}
    new_ext = ext
    if ext.lower() == ".md" or ext.lower() == ".md+":
        html, meta = compile_markdown(open(path, "r").read())
        if ext.lower() == ".md+":
            html = fill_template(html, ctx)
        out_dict = {"content": html}
        for k in meta:
            out_dict[k] = meta[k]
        new_ext = ".html"
        
        #ctx["content"] = html
        #ctx["meta"] = meta
    elif ext.lower() == ".html+":
        contents = open(path, "r").read()
        #local_out_html = fill_template(contents, ctx)
        out_dict = {"content": contents}#local_out_html}
 
        new_ext = ".html"
        #ctx["content"] = local_out_html
    elif ext.lower() == ".tmpl":
        out_dict = {}
    else:  # copy file
        #relpath = os.path.relpath(path, top)
        #out_path = os.path.join(top, ctx["OutputDir"], relpath)
        #os.makedirs(os.path.dirname(out_path), exist_ok=True)
        #shutil.copyfile(path, out_path)
        out_dict = {}

    out_dict["is_file"] = True
    out_dict["input_path"] = os.path.relpath(path, top)
    out_dict["path"] = os.path.splitext(os.path.relpath(path, top))[0] + new_ext
    out_dict["template_path"] = template_path
    out_dict["date"] = time.localtime(os.path.getmtime(path))
    return out_dict

def make_dirtree(top, path, ctx, template_path=None):
    files = []
    dirs = []
    tree = {}
    for subdir in os.listdir(path):
        if subdir[0] != ".":  # don't include hidden files
            subpath = os.path.join(path, subdir)
            if os.path.isfile(subpath):
                # update template path if there is a template in this folder
                root, ext = os.path.splitext(os.path.basename(subpath))
                if root.lower() == "template" and ext.lower() == ".tmpl":
                    template_path = subpath
                else:
                    files.append((subdir, subpath))
            elif os.path.isdir(subpath):
                rp = os.path.abspath(subpath)
                md = os.path.join(top, ctx["MetaDir"])
                od = os.path.join(top, ctx["OutputDir"])
                if rp != os.path.abspath(md) and rp != os.path.abspath(od):
                    dirs.append((subdir, subpath))

    for short_path, full_path in dirs:
        path_name = short_path.lower()
        tree[path_name] = make_dirtree(top, full_path, ctx, template_path)
        
    for short_path, full_path in files:
        name = os.path.splitext(short_path)[0].lower()  # remove extension
        tree[name] = add_dirtree_file(top, full_path, dict(ctx), template_path)

    return tree

# traverse tree to build all site files
def compile_dirtree(top, tree, ctx):
    modified_files = []
    for k, node in tree.items():
        if "is_file" in node and node["is_file"]:
            mf = build_file(top, node, dict(ctx))
        else:
            mf = compile_dirtree(top, node, ctx)
        modified_files.append(mf)
    return modified_files
            
def load_meta(top, ctx):
    meta_path = os.path.join(top, ctx["MetaDir"], "meta.json")
    if os.path.isfile(meta_path):
        meta = json.loads(open(meta_path, "r").read())
        for key in meta:
            ctx[key] = meta[key]
    return ctx
    
def register_macros(top, ctx):
    def macro(s, fun):
        ctx[s] = fun
    pgm_path = os.path.join(top, ctx["MetaDir"], "macros.py")
    if os.path.isfile(pgm_path):
        pgm = open(pgm_path, "r").read()
        exec(pgm, dict(list(globals().items()) + list(locals().items())))
    return ctx

# returns array of absolute paths of the files modified
def make_site(top, ctx):
    ctx = load_meta(top, ctx)
    ctx = register_macros(top, ctx)
    tree = make_dirtree(top, top, ctx)
    
    # copy dirtree to context
    for k in tree:
        ctx[k] = tree[k]
        
    mf = compile_dirtree(top, tree, ctx)
    return mf

def is_in_nanosite_dir(path="."):
    if os.path.isfile(os.path.join(path, ".nanosite")):
        return True
    else:
        up = os.path.join("..", path)
        if os.path.abspath(up) == os.path.abspath(path):  # reached root
            return False
        else:
            return is_in_nanosite_dir(up)

def update(top, ctx):
    def last_update_time(walk, ignore=[]):
        for path, dirs, files in walk:
            if dirs == []:
                fs = [os.path.getmtime(os.path.join(path, f)) for f in files \
                      if os.path.abspath(os.path.join(path, f)) not in ignore \
                      and f[0] != "."]
                return time.ctime(max(fs)) if fs != [] else 0
            else:
                return max(last_update_time(os.walk(os.path.join(path, d)),
                                            ignore) for d in dirs)
    needs_update = True
    last_t = None
    last_walk = None
    while True:
        if needs_update:
            needs_update = False
            mf = make_site(top, ctx)
            print("[" + str(datetime.now()) + "]", "Built site.")
        walk = sorted(os.walk(top))
        t = last_update_time(walk, mf)
        time.sleep(1)
        # file updated or dirtree changed
        if last_t is not None and (t != last_t or walk != last_walk):
            needs_update = True
        last_t = t
        last_walk = walk

def run_server(port, site_dir, ctx):
    output_dir = ctx["OutputDir"]
    
    # start update thread
    thread = threading.Thread(target=update, args=(site_dir, ctx))
    thread.daemon = True
    thread.start()

    # start server
    class RequestHandler(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            return os.path.join(site_dir, output_dir, path[1:])
    handler = RequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    atexit.register(lambda: httpd.shutdown())
    print("Serving at port", port)
    httpd.serve_forever()

def clean_output_dir(site_dir, output_dir):
    path = os.path.join(site_dir, output_dir)
    if os.path.isdir(path):
        shutil.rmtree(path)
        print("Cleaned output directory.")
    else:
        print("Nothing to clean.")

def get_cmdline_args():
    parser = argparse.ArgumentParser(prog="nanosite")
    parser.add_argument("action", nargs="?", default="",
                        help="options: build, serve, clean, delete")
    parser.add_argument("--port", action="store", dest="port",
                        default="8000", type=int, help="server port")
    parser.add_argument("-p", action="store", dest="site_dir",
                        default=os.getcwd(), help="site directory")
    parser.add_argument("-o", action="store", dest="output_dir",
                        default="output/", help="set output directory")
    parser.add_argument("-m", action="store", dest="meta_dir",
                        default="meta/", help="set meta directory")
    return parser.parse_args()

def setup_blank_site(top, ctx, meta):
    open(".nanosite", "w").close()
    open("index.html+", "w").close()
    meta_dir = os.path.join(top, ctx["MetaDir"])
    os.makedirs(meta_dir, exist_ok=True)
    with open(os.path.join(meta_dir, "master.tmpl"), "w") as f:
        f.write("{{content}}")
    with open(os.path.join(meta_dir, "macros.py"), "w") as f:
        f.write('# macro("example", lambda ctx: ctx_fetch(ctx, "site.title"))')
    with open(os.path.join(meta_dir, "meta.json"), "w") as f:
        json.dump(meta, f)

def prompt_YN(prompt):
    full_prompt = prompt + " [y/n] "
    print(full_prompt, end="")
    x = input()
    while x[0].lower() != "y" and x[0].lower() != "n":
        print("Invalid option. Type 'y' for yes and 'n' for no.")
        print(full_prompt, end="")
        x = input()
    return x[0].lower() == "y"

def setup_site_interactive(top, ctx):
    if prompt_YN("Would you like to set up a site in this directory?"):
        print("Enter a title for your site: ", end="")
        title = input()
        print("Enter a tagline for your site: ", end="")
        tagline = input()
        print("Enter the author name for your site: ", end="")
        author = input()
        meta = {"site": {"title": title, "tagline": tagline,
                         "author": author, "url": "/"}}
        setup_blank_site(top, ctx, meta)
        print("Success! Generated site.")
    else:
        print("Canceled.")

def delete_site_dir(top):
    for f in os.listdir(top):
        path = os.path.join(top, f)
        if os.path.isfile(path):
            os.unlink(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
    
def main():
    args = get_cmdline_args()
    action = args.action.lower()

    ctx = {"OutputDir": args.output_dir, "MetaDir": args.meta_dir}
    if action == "build" or action == "b":
        make_site(args.site_dir, ctx)
        print("Built site.")
    elif action == "clean" or action == "c":
        clean_output_dir(args.site_dir, args.output_dir)
    elif action == "delete" or action == "d":
        if is_in_nanosite_dir():
            if prompt_YN("Are you sure you want to delete the site " +
                         "in this directory?"):
                delete_site_dir(args.site_dir)
                print("Deleted site.")
            else:
                print("Canceled.")
        else:
            print("No site in this directory.")
    elif action == "serve" or action == "s":
        run_server(args.port, args.site_dir, ctx)
    elif action == "":
        if is_in_nanosite_dir():  # default action: run server
            run_server(args.port, args.site_dir, ctx)
        else:
            setup_site_interactive(args.site_dir, ctx)
    else:
        print("Unrecognized action. " +
              "Valid actions: build, serve, clean, delete.")

if __name__ == "__main__":
    main()
    
