import markdown
import os
import json
import shutil
import argparse
import time
from html import escape as escape_HTML

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
    elif ext.lower() == ".tmpl":
        pass
    else:   # copy file
        relpath = os.path.relpath(path, top)
        out_path = os.path.join(top, ctx["OutputDir"], relpath)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        shutil.copyfile(path, out_path)
    
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
                rp = os.path.realpath(subpath)
                md = os.path.join(top, ctx["MetaDir"])
                od = os.path.join(top, ctx["OutputDir"])
                if rp != os.path.realpath(md) and rp != os.path.realpath(od):
                    dirs.append((subdir, subpath))

    for short_path, full_path in dirs:
        path_name = short_path.lower()
        tree[path_name] = make_dirtree(top, full_path, ctx, template_path)
        
    for short_path, full_path in files:
        name = os.path.splitext(short_path)[0].lower()  # remove extension
        tree[name] = add_dirtree_file(top, full_path, dict(ctx), template_path)

    return tree

# traverse tree to build all site files
def build_dirtree(top, tree, ctx):
    for k, node in tree.items():
        if "is_file" in node and node["is_file"]:
            build_file(top, node, dict(ctx))
        else:
            build_dirtree(top, node, ctx)
            
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
    
def make_site(top, ctx):
    ctx = load_meta(top, ctx)
    ctx = register_macros(top, ctx)
    tree = make_dirtree(top, top, ctx)
    
    # copy dirtree to context
    for k in tree:
        ctx[k] = tree[k]
        
    build_dirtree(top, tree, ctx)

def is_in_nanosite_dir(path="."):
    if os.path.isfile(os.path.join(path, ".nanosite")):
        return True
    else:
        up = os.path.join("..", path)
        if os.path.realpath(up) == os.path.realpath(path):  # reached root
            return False
        else:
            return is_in_nanosite_dir(up)

parser = argparse.ArgumentParser(prog="nanosite")
parser.add_argument("dir", nargs="?", default=os.getcwd())
args = parser.parse_args()

default_ctx = {"OutputDir": "output/", "MetaDir": "meta/"}
make_site(args.dir, default_ctx)
print("Built site.")
