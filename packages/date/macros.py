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
    s = sorted([x for x in folder.values() if "isFile" in x],
               key=lambda x: x["date"],
               reverse=True)
    return s if unlimited else s[:count]
macro("newest", newest)

# -- end date --

