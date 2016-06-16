def format_date(ctx, date):
    mo = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][date.tm_mon - 1]
    return str(date.tm_mday) + " " + mo + " " + str(date.tm_year)
macro("format_date", format_date)

def newest(ctx, count, folder):
    unlimited = type(count) == str and count.lower() == "unlimited"
    s = sorted([x for x in folder.values() if "is_file" in x],
               key=lambda x: x["date"],
               reverse=True)
    return s if unlimited else s[:count]
macro("newest", newest)

def make_menu(ctx, start=True, site_url=None):
    out = "<ul>"
    if start:
        site_url = ctx["site"]["url"]
        ctx = ctx["pages"]
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
macro("nav", make_menu)
