# -- begin date --
#
# {{ formatDate [date] }} formats a date object into a readable string, e.g.
#   "7 Jun 2016".
def format_date(ctx, date):
    mo = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][date.tm_mon - 1]
    return str(date.tm_mday) + " " + mo + " " + str(date.tm_year)
macro("formatDate", format_date)

#
# {{ newest [count] [folder] }} returns the newest [count] pages in directory
#   [folder], sorted by modification date. Set count to the string "unlimited"
#   to retrieve all pages.
#
# You will typically want to iterate over
#   the result, as in: {{ #for post in newest 5 posts }} ... {{ #endfor }}
def newest(ctx, count, folder):
    unlimited = type(count) == str and count.lower() == "unlimited"
    s = sorted([x for x in folder.values() if "is_file" in x],
               key=lambda x: x["date"],
               reverse=True)
    return s if unlimited else s[:count]
macro("newest", newest)

# -- end date --

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
        if "is_file" in ctx[item]:
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

