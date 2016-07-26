# -- begin menu --
#
# {{{ menu [folder] }}} creates a navigation menu, in the form of an unordered
#   list, for the pages in directory [folder].
#
# It titles them by their [title] attribute. So for a Markdown file, writing
#       title: [my title]
#   at the beginning of the file, and putting the file in directory [folder],
#   will cause it to show up in the menu.

def make_menu(ctx, folder, start=True, site_url=None):
    out = "<ul>"
    if start:
        site_url = ctx["site"]["url"]
        ctx = folder
        out += "<li><a href='" + site_url + "/'>Home</a></li>"
    for item in sorted(ctx):
        if "isFile" in ctx[item]:
            if "title" in ctx[item]:
                out += "<li><a href='" + site_url + "/" + \
                       ctx[item]["path"] + "'>"
                out += ctx[item]["title"] + "</a></li>"
        else:
            out += "<li>" + item.capitalize() + \
                   make_menu(ctx[item], False, site_url)
            out += "</li>"
    out += "</ul>"
    return out
macro("menu", make_menu)

# -- end menu --

