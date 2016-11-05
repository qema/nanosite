import nanosite.util as util
import nanosite.build as build
import nanosite.server as server
import nanosite.packages as packages

import os
import json
import argparse

# get root dir of site, or None if no site exists
def get_site_root_dir(path="."):
    if os.path.isfile(os.path.join(path, ".nanosite")):
        return path
    else:
        up = os.path.join(path, "..")
        if util.same_path(up, path):  # reached root
            return None
        else:
            return get_site_root_dir(up)

def get_cmdline_args():
    parser = argparse.ArgumentParser(prog="nanosite")
    parser.add_argument("action", nargs="?", default="",
                        help="options: build, serve, publish, " + \
                             "import, clean, delete")
    parser.add_argument("parameter", nargs="?", default="")
    parser.add_argument("--port", "-p", action="store", dest="port",
                        default="8000", type=int, help="set server port")
    parser.add_argument("-s", action="store", dest="site_dir",
                        default=os.getcwd(), help="specify site directory")
    parser.add_argument("-o", action="store", dest="output_dir",
                        default="output/", help="set output directory")
    parser.add_argument("-m", action="store", dest="meta_dir",
                        default="meta/", help="set meta directory")
    parser.add_argument("--set-package-url", action="store",
                        dest="package_url",
                        default=None, help="set package repository URL")
    parser.add_argument("--force", "-f", action="store_true", dest="force",
                        help="force actions")
    return parser.parse_args()

def setup_blank_site(top, ctx, meta):
    with open(".nanosite", "w") as f:
        json.dump({}, f)
    open("index.html+", "w").close()
    meta_dir = os.path.join(top, ctx["MetaDir"])
    os.makedirs(meta_dir, exist_ok=True)
    with open(os.path.join(meta_dir, "master.tmpl"), "w") as f:
        f.write("{{{content}}}")
    with open(os.path.join(meta_dir, "macros.py"), "w") as f:
        f.write('# macro("example", lambda ctx: fetch(ctx, "site.title"))\n')
    with open(os.path.join(meta_dir, "meta.json"), "w") as f:
        json.dump(meta, f, sort_keys=True, indent=2)
    if os.name == "nt":
        with open(os.path.join(meta_dir, "publish.bat"), "w") as f:
            f.write("rem This script is run during `nanosite publish`\n")
    else:
        publish_script_path = os.path.join(meta_dir, "publish")
        with open(publish_script_path, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("# This script is run during `nanosite publish`\n")
        os.chmod(publish_script_path, 0o744)  # make executable

def setup_site_interactive(top, ctx):
    if util.prompt_YN("Would you like to set up a site in this directory?"):
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

def main():
    args = get_cmdline_args()
    action = args.action.lower()
    param = args.parameter

    args.site_dir = get_site_root_dir(args.site_dir)

    ctx = {"OutputDir": args.output_dir, "MetaDir": args.meta_dir}
    if action == "":
        if args.package_url:  # trying to set package url
            packages.set_package_url(args.package_url, args.site_dir)
            print("Updated package URL.")
        else:
            if args.site_dir is not None:  # default action: run server
                server.run_server(args.port, args.site_dir, ctx)
            else:
                setup_site_interactive(args.site_dir, ctx)
    elif args.site_dir is None:
        print("No site in this directory.")
    elif action == "build" or action == "b":
        build.make_site(args.site_dir, ctx)
        print("Built site.")
    elif action == "clean" or action == "c":
        util.clean_output_dir(args.site_dir, args.output_dir)
    elif action == "delete" or action == "d":
        if util.prompt_YN("Are you sure you want to delete the site " +
                          "in this directory?"):
            util.delete_site_dir(args.site_dir)
            print("Deleted site.")
        else:
            print("Canceled.")
    elif action == "publish" or action == "p":
        util.publish_site(args.site_dir, args.meta_dir)
    elif action == "serve" or action == "s":
        server.run_server(args.port, args.site_dir, ctx)
    elif action == "import" or action == "i":
        if param:
            print("Installing package", param.lower())
            success, msg = packages.import_package(param, args.site_dir, ctx,
                                                   force=args.force)
            if success:
                print("Successfully installed package.")
            else:
                print(msg)
                print("Import failed.")
        else:
            print("Usage: nanosite import [package-name]")
    else:
        print("Unrecognized action. " +
              "Valid actions: build, serve, publish, import, clean, delete.")

if __name__ == "__main__":
    main()
    
