from html import escape as escape_HTML

# fetch key, possibly nested thru dot notation
def ctx_fetch(ctx, line):
    key, params = (line.split(" ", 1) + [""])[:2]
    parts = key.split(".", 1)
    is_attr = hasattr(ctx, parts[0])
    if parts[0] in ctx or is_attr:
        if len(parts) == 1:
            value = None
            if is_attr:  # try getting it as an attribute first
                value = getattr(ctx, parts[0])
            else:  # otherwise access dictionary entry
                value = ctx[parts[0]]
            # if it's a macro, call it with parameter [ctx]
            if callable(value):
                value = value(ctx, *tokenize_params(ctx, params))
            return value
        else:
            return ctx_fetch(ctx[parts[0]], parts[1])
    else:
        return None

# get params from space-separated parameter list
def tokenize_params(ctx, params):
    out = []
    in_string = False
    for token in params.split(" "):
        if token != "":
            if token[0] == '"':  # begin string
                in_string = True
                out.append(token[1:])
            elif in_string:  # continue string
                if token[-1] == '"': 
                    token = token[:-1]
                    in_string = False
                out[-1] += " " + token
            else:
                try:  # int 
                    out.append(int(token))
                except ValueError:  # float
                    try:
                        out.append(float(token))
                    except ValueError:  # identifier (so get object from ctx)
                        out.append(ctx_fetch(ctx, token))
    return out

template_cache = {}
def clear_template_cache():
    global template_cache
    template_cache = {}
    
# get template from path (cached)
def get_template(path):
    global template_cache
    if path in template_cache:
        return template_cache[path]
    else:
        tmpl = open(path, "r").read()
        template_cache[path] = tmpl
        return tmpl

# fill template according to rules in doc.txt
def fill_template(tmpl, ctx):
    #print("FILLING TEMPLATE ", tmpl, "WITH CONTEXT", ctx)
    
    # get part before delim and part after
    def get_chunk(s, delim):
        a = s.split(delim, 1)
        return (a[0], "") if len(a) <= 1 else a
    rest = tmpl
    out = ""
    seeking = None
    seek_depth = 0
    depth_if = 0
    depth_for = 0
    for_block_accum = ""
    for_variable = ""
    for_collection = None
    while len(rest) > 0:
        cur, rest = get_chunk(rest, "{{")
        #print("}}", cur, "{{", rest, seeking, seek_depth, depth_if)
        #print()
        if seeking is None:
            out += cur
        else:
            for_block_accum += cur
        key, rest = get_chunk(rest, "}}")
        key = key.strip()
        cmd = key.split()
        if cmd != []: cmd[0] = cmd[0].lower()

        #print("{{", key, "}}", rest, seeking, seek_depth, depth_if)
        #print()
        #print()

        if seeking is not None:
            run_for_block = False
            if cmd[0] == "#if":
                depth_if += 1
            elif cmd[0] == "#else":
                if "#else" in seeking and seek_depth == depth_if:
                    #print("FOUND MATCHING ELSE", seek_depth, depth_if)
                    seeking = None
            elif cmd[0] == "#elif":
                if "#elif" in seeking and seek_depth == depth_if:
                    if ctx_fetch(ctx, cmd[1]):
                        #print("FOUND MATCHING ELIF", seek_depth, depth_if)
                        seeking = None
            elif cmd[0] == "#endif":
                if "#endif" in seeking and seek_depth == depth_if:
                    #print("FOUND MATCHING ENDIF", seek_depth, depth_if)
                    seeking = None
                depth_if -= 1
            elif cmd[0] == "#for":
                depth_for += 1
            elif cmd[0] == "#endfor":
                if "#endfor" in seeking and seek_depth == depth_for:
                    seeking = None
                    run_for_block = True
                depth_for -= 1
                    
            if run_for_block:
                orig = None
                if for_variable in ctx:
                    orig = ctx["for_variable"]

                for item in for_collection:
                    ctx[for_variable] = item
                    out += fill_template(for_block_accum, ctx)
                if orig is None:
                    if for_variable in ctx:
                        ctx.pop(for_variable)
                else:
                    ctx[for_variable] = orig
            else:
                for_block_accum += "{{" + key + "}}"
        else:
            if cmd == [] or cmd[0] == "":
                pass
            elif cmd[0] == "#if":
                depth_if += 1
                if not ctx_fetch(ctx, cmd[1]):  # if ctx[key] evaluates to True
                    seeking = {"#elif", "#else", "#endif"}
                    seek_depth = depth_if
            elif cmd[0] == "#else" or cmd[0] == "#elif":
                if depth_if == 0:
                    raise Exception(cmd[0] + " without #if")
                seeking = {"#endif"}
                seek_depth = depth_if
            elif cmd[0] == "#endif":
                depth_if -= 1
            elif cmd[0] == "#for":
                depth_for += 1
                for_block_accum = ""
                seeking = {"#endfor"}
                seek_depth = depth_for
                for_variable = cmd[1]
                for_collection = ctx_fetch(ctx, " ".join(cmd[3:]))
            elif cmd[0] == "#endfor":
                depth_for -= 1
            else:
                if key[0] == "{":
                    val = str(ctx_fetch(ctx, key[1:]))
                    _, rest = get_chunk(rest, "}") # get matching close brace
                else:
                   val = escape_HTML(str(ctx_fetch(ctx, key)))
                out += fill_template(val, ctx)
    if depth_if > 0:
        raise Exception("#if without #endif")
    elif depth_if < 0:
        raise Exception("#endif without #if")
    if depth_for > 0:
        raise Exception("#for without #endfor")
    elif depth_for < 0:
        raise Exception("#endfor without #for")
    return out
