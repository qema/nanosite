import nanosite.util as util
import nanosite.build as build
import nanosite.server as server

import os
import json
import shutil
import argparse

def is_in_nanosite_dir(path="."):
    if os.path.isfile(os.path.join(path, ".nanosite")):
        return True
    else:
        up = os.path.join("..", path)
        if util.same_path(up, path):  # reached root
            return False
        else:
            return is_in_nanosite_dir(up)
 
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
        f.write("{{{content}}}")
    with open(os.path.join(meta_dir, "macros.py"), "w") as f:
        f.write('# macro("example", lambda ctx: ctx_fetch(ctx, "site.title"))\n')
    with open(os.path.join(meta_dir, "meta.json"), "w") as f:
        json.dump(meta, f, sort_keys=True, indent=2)

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
                         "author": author, "url": ""}}
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
        if is_in_nanosite_dir():
            build.make_site(args.site_dir, ctx)
            print("Built site.")
        else:
            print("No site in this directory.")
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
        server.run_server(args.port, args.site_dir, ctx)
    elif action == "":
        if is_in_nanosite_dir():  # default action: run server
            server.run_server(args.port, args.site_dir, ctx)
        else:
            setup_site_interactive(args.site_dir, ctx)
    else:
        print("Unrecognized action. " +
              "Valid actions: build, serve, clean, delete.")

if __name__ == "__main__":
    main()
    
