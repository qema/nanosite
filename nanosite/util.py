import os
import markdown

def same_path(a, b):
    return os.path.abspath(a).lower() == os.path.abspath(b).lower()

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
