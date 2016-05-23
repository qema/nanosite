import markdown
import os
from html import escape as escape_HTML

# compile markdown to HTML, returning (html, meta_info) tuple
def compile_markdown(md_text):
    md = markdown.Markdown(extensions = ["markdown.extensions.meta"])
    html = md.convert(md_text)
    meta = {k: "".join(v) for k, v in md.Meta.items()} \
           if md.Meta is not None else {}
    return (html, meta)
        
# fetch key, possibly nested thru dot notation
def ctx_fetch(ctx, key):
    parts = key.split(".", 1)
    if len(parts) == 1:
        return ctx[parts[0]]
    else:
        return ctx_fetch(ctx[parts[0]], parts[1])

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
        cmd = key.lower().strip().split()

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
                for_collection = ctx_fetch(ctx, cmd[3])
            else:
                if key[0] == "{":
                    out += str(ctx_fetch(ctx, key[1:]))
                    _, rest = get_chunk(rest, "}") # get matching close brace
                else:
                    out += escape_HTML(str(ctx_fetch(ctx, key)))
    if depth_if > 0:
        raise Exception("#if without #endif")
    elif depth_if < 0:
        raise Exception("#endif without #if")
    return out

def build_file(top, path, ctx, template_path):
    root, ext = os.path.splitext(path)
    if ext.lower() == ".md":
        html, meta = compile_markdown(open(path, "r").read())

        tmpl = open(template_path, "r").read()
        ctx["Content"] = html
        ctx["Meta"] = meta
        out_html = fill_template(tmpl, ctx)

        relpath = os.path.relpath(root + ".html", top)
        out_path = os.path.join(ctx["OutputDir"], relpath)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            f.write(out_html)  # TODO
    elif ext.lower() == ".html+":
        pass
    return "I'M A FILE"

def build_dir(top, path, ctx, template_path=None):
    files = []
    dirs = []
    tree = {}
    for subdir in os.listdir(path):
        subpath = os.path.join(path, subdir)
        if os.path.isfile(subpath):
            files.append((subdir, subpath))
            # update template path if there is a template in this folder
            root, ext = os.path.splitext(os.path.basename(subpath))
            if root.lower() == "template" and ext.lower() == ".tmpl":
                template_path = subpath
        elif os.path.isdir(subpath):
            dirs.append((subdir, subpath))

    aug_ctx = dict(ctx)
    for short_path, full_path in dirs:
        path_name = short_path.capitalize()
        tree[path_name] = build_dir(top, full_path, ctx, template_path)
        aug_ctx[path_name] = tree[path_name]
        
    for short_path, full_path in files:
        tree[short_path] = build_file(top, full_path, aug_ctx, template_path)

    return tree

def build_site(top, ctx):
    build_dir(top, top, ctx)

default_meta = {"OutputDir": "testsite/output/", "TemplateDir": "templates/"}
build_site("testsite/", default_meta)
