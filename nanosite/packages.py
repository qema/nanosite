import nanosite.templates as templates
import nanosite.util as util

import os
from zipfile import ZipFile
import json
from urllib.request import urlopen
from urllib.parse import urljoin
from distutils.version import LooseVersion

DefaultPackageURL = "http://wanganzhou.com/nanosite/packages/"

def set_package_url(url, top):
    if url and url[-1] != "/": url += "/"  # add trailing slash if necessary
    dot_nanosite = None
    with open(os.path.join(top, ".nanosite"), "r") as f:
        dot_nanosite = json.loads(f.read())
        dot_nanosite["package-url"] = url
    if dot_nanosite:
        with open(os.path.join(top, ".nanosite"), "w") as dnf:
            json.dump(dot_nanosite, dnf, indent=2)

# name: package name
# package_url: package repo URL
# returns whether download succeeded
def download_package(name, package_url, dest):
    filename = name + ".zip"
    url = urljoin(package_url, filename)
    print("Downloading package", name, "from", url)
    try:
        with urlopen(url) as response, \
         open(filename, "wb") as out_file:
            out_file.write(response.read())
        return True
    except:
        return False

# f: ZipFile object of package file
# dot_nanosite: contents of .nanosite file (loaded from JSON)
# force: whether to force override
# returns (success (bool), status (string))
def install_package(name, f, dot_nanosite, top, ctx, force=False):
    with f.open("rules.json", "r") as rules_file:
        rules = json.loads(rules_file.read().decode("utf-8"))
        files = rules["files"] if "files" in rules else {}
        dependencies = rules["dependencies"] if "dependencies" in rules else []
        version = rules["version"] if "version" in rules else "0.0.0"

        # check if package already installed
        installed_packages = dot_nanosite["installed-packages"]
        if name in installed_packages and \
           LooseVersion(installed_packages[name]["version"]) >= \
           LooseVersion(version) and not force:
            return False, name + " already installed"
        
        # check dependencies
        for dependency in dependencies:
            if dependency not in installed_packages:
                print("Installing dependency", dependency)
                success, msg = import_package(dependency, top, ctx)
                if not success:
                    return False, "Unable to install dependency " + dependency

        # preliminarily go through files, prompt user to overwrite if needed
        overwritten_files = []
        for filename in files:
            rule = files[filename]
            dest = os.path.join(top, templates.fill_template(rule["dest"],
                                                             ctx))
            # an overwrite will occur
            if os.path.isfile(dest) and "w" in rule["action"].lower():
                overwritten_files.append(dest)
        if overwritten_files:
            print("The following files will be overwritten:")
            for fn in overwritten_files:
                print(" -", fn)
            if not util.prompt_YN("Are you sure you want to continue?"):
                return False, "Canceled."
            
        # go through files
        for filename in files:
            rule = files[filename]
            dest = os.path.join(top, templates.fill_template(rule["dest"],
                                                             ctx))
            action = rule["action"]
            
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with f.open(filename, "r") as src_file:
                with open(dest, action) as dest_file:
                    dest_file.write(src_file.read().decode("utf-8"))

        # add to list of installed packages
        if name not in installed_packages:
            installed_packages[name] = {"version": version}
        dot_nanosite["installed-packages"] = installed_packages
        with open(os.path.join(top, ".nanosite"), "w") as dnf:
            json.dump(dot_nanosite, dnf, indent=2)
    return True, ""
    
# force: whether to force override
# returns (success (bool), status (string))
def import_package(name, top, ctx, force=False):
    name = name.lower()
    
    # setup package info in .nanosite file if first time
    with open(os.path.join(top, ".nanosite"), "r") as f:
        dot_nanosite = json.loads(f.read())
        if "installed-packages" not in dot_nanosite:
            dot_nanosite["installed-packages"] = {}
        if "package-url" not in dot_nanosite:
            dot_nanosite["package-url"] = DefaultPackageURL
        package_url = dot_nanosite["package-url"]

        # remove trailing slashes in MetaDir and OutputDir if needed
        if "MetaDir" in ctx and ctx["MetaDir"][-1] == "/":
            ctx["MetaDir"] = ctx["MetaDir"][:-1]
        if "OutputDir" in ctx and ctx["OutputDir"][-1] == "/":
            ctx["OutputDir"] = ctx["OutputDir"][:-1]

        # check if package file is in site top. If not, download it
        filename = name + ".zip"
        path = os.path.join(top, filename)
        downloaded_package = False
        if not os.path.isfile(path):
            downloaded_package = True
            success = download_package(name, package_url, path)
            if not success: return False, "Could not find package"

        # install package
        with ZipFile(path, "r") as f:
            success, msg = install_package(name, f, dot_nanosite, top, ctx,
                                           force=force)

        # delete package if downloaded
        if downloaded_package:
            os.remove(path)

        return success, msg
