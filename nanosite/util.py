import os
import markdown
from shutil import rmtree
from subprocess import call as subprocess_call

def forward_slash_path(path):
    return path.replace("\\", "/") if os.name == "nt" else path

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

def clean_output_dir(site_dir, output_dir):
    path = os.path.join(site_dir, output_dir)
    if os.path.isdir(path):
        rmtree(path)
        print("Cleaned output directory.")
    else:
        print("Nothing to clean.")
        
def delete_site_dir(top):
    for f in os.listdir(top):
        path = os.path.join(top, f)
        if os.path.isfile(path):
            os.unlink(path)
        elif os.path.isdir(path):
            rmtree(path)
    
def publish_site(top, meta_dir):
    cur_dir = os.getcwd()
    os.chdir(top)
    # run publish script from site top directory
    subprocess_call(os.path.join(top, meta_dir, "publish"))
    os.chdir(cur_dir)
    print("Finished running publish script.")

def prompt_YN(prompt):
    full_prompt = prompt + " [y/n] "
    print(full_prompt, end="")
    x = input()
    while x[0].lower() != "y" and x[0].lower() != "n":
        print("Invalid option. Type 'y' for yes and 'n' for no.")
        print(full_prompt, end="")
        x = input()
    return x[0].lower() == "y"
