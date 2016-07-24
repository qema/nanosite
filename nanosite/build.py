import nanosite.templates as templates
import nanosite.util as util

import os
from shutil import copyfile
from time import localtime
import json

def build_file(top, node, ctx):
    assert(node["is_file"])
    
    path = os.path.join(top, node["input_path"])
    root, ext = os.path.splitext(path)

    modified_files = []
    if ext.lower() in {".md", ".md+", ".html+"}:  # compile against templates
        # copy all node properties
        for k in node:
            ctx[k] = node[k]

        # fill local template
        template_path = node["template_path"]
        if template_path is not None:
            local_tmpl = templates.get_template(template_path)
            local_out_html = templates.fill_template(local_tmpl, ctx)
        else:
            local_out_html = node["content"]

        # get master template
        master_tmpl_path = os.path.join(top, ctx["MetaDir"], "master.tmpl")
        master_tmpl = templates.get_template(master_tmpl_path)

        # fill master template
        ctx["content"] = local_out_html
        out_html = templates.fill_template(master_tmpl, ctx)

        # remove escape symbols on delimiters
        out_html = templates.unescape_delimiters(out_html)

        relpath = os.path.relpath(root + ".html", top)
        out_path = os.path.join(top, ctx["OutputDir"], relpath)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        # create output file in output folder
        with open(out_path, "w") as f:
            # get/create output path
            f.write(out_html)
        modified_files = [os.path.abspath(out_path)]
    elif ext.lower() == ".tmpl":  # no action
        pass
    elif ext.lower() == ".xml+":
        tmpl = templates.get_template(path)
        out_html = templates.fill_template(tmpl, ctx)
        
        # remove escape symbols on delimiters
        out_html = templates.unescape_delimiters(out_html)
        
        relpath = os.path.relpath(root + ".xml", top)
        out_path = os.path.join(top, ctx["OutputDir"], relpath)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        
        with open(out_path, "w") as f:
            f.write(out_html)
        modified_files = [os.path.abspath(out_path)]
    else:   # copy file (make hard link on unix)
        relpath = os.path.relpath(path, top)
        out_path = os.path.join(top, ctx["OutputDir"], relpath)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        # copy if src and dest are different (i.e. OutputDir != ".")
        if not util.same_path(path, out_path):
            if os.name == "nt":
                copyfile(path, out_path)
            else:
                # only copy file if it's new or newly modified 
                if not os.path.lexists(out_path) or \
                   os.path.getmtime(path) > os.path.getmtime(out_path):
                    #print("copying", path, "->", out_path)
                    copyfile(path, out_path)
            modified_files = [os.path.abspath(out_path)]
    return modified_files
    
def add_dirtree_file(top, path, ctx, template_path):
    root, ext = os.path.splitext(path)

    out_dict = {}
    new_ext = ext
    if ext.lower() == ".md" or ext.lower() == ".md+":
        html, meta = util.compile_markdown(open(path, "r").read())
        if ext.lower() == ".md":  # don't template plain .md files
            html = templates.escape_delimiters(html)
        out_dict = {"content": html}
        for k in meta:
            out_dict[k] = meta[k]
        new_ext = ".html"
        
        #ctx["content"] = html
        #ctx["meta"] = meta
    elif ext.lower() == ".html+" or ext.lower() == ".xml+":
        contents = open(path, "r").read()
        #local_out_html = fill_template(contents, ctx)
        out_dict = {"content": contents}#local_out_html}
 
        new_ext = new_ext[:-1]#".html"
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
    out_dict["date"] = localtime(os.path.getmtime(path))
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
                if not (util.same_path(rp, md) or util.same_path(rp, od)):
                    dirs.append((subdir, subpath))

    for short_path, full_path in dirs:
        path_name = short_path.lower()
        tree[path_name] = make_dirtree(top, full_path, ctx, template_path)
        
    for short_path, full_path in files:
        name = short_path.replace(".", "_")
        if name in tree: name = name.replace("_", "__")
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
        modified_files += mf
    return modified_files
            
def load_meta(top, ctx):
    meta_path = os.path.join(top, ctx["MetaDir"], "meta.json")
    if os.path.isfile(meta_path):
        with open(meta_path, "r") as f:
            meta = json.loads(f.read())
        for key in meta:
            ctx[key] = meta[key]
    return ctx
    
def register_macros(top, ctx):
    # functions to be exposed to macros.py
    def macro(s, fun):
        ctx[s] = fun
    def fetch(ctx, key):
        return util.ctx_fetch(ctx, key)
    pgm_path = os.path.join(top, ctx["MetaDir"], "macros.py")
    if os.path.isfile(pgm_path):
        with open(pgm_path, "r") as f:
            pgm = f.read()
        exec(pgm, dict(list(globals().items()) + list(locals().items())))
    return ctx

# returns array of absolute paths of the files modified
def make_site(top, ctx):
    templates.clear_template_cache()

    # load meta variables
    ctx = load_meta(top, ctx)

    # register macros
    ctx = register_macros(top, ctx)

    # create dirtree
    tree = make_dirtree(top, top, ctx)
    
    # copy dirtree to context
    for k in tree:
        ctx[k] = tree[k]
        
    # fill master template in order to register global macros
    master_tmpl_path = os.path.join(top, ctx["MetaDir"], "master.tmpl")
    templates.fill_template(templates.get_template(master_tmpl_path), ctx)

    # compile dirtree
    mf = compile_dirtree(top, tree, ctx)
    return mf
