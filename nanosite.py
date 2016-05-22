# fetch key, possibly nested thru dot notation
def ctx_fetch(ctx, key):
    parts = key.split(".", 1)
    if len(parts) == 1:
        return ctx[parts[0]]
    else:
        return ctx_fetch(ctx[parts[0]], parts[1])

# escape HTML braces
def escape_HTML(s):
    raise "TODO"
    return s

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
        cmd = key.lower().strip().split()

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
                    
            if run_for_block:
                orig = None
                if for_variable in ctx:
                    orig = ctx["for_variable"]
                    
                for item in for_collection:
                    ctx[for_variable] = item
                    out += fill_template(for_block_accum, ctx)
                if orig is None:
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
                for_collection = ctx_fetch(ctx, cmd[3])
            else:
                if key[0] == "{" and key[-1] == "}":
                    out += str(ctx_fetch(ctx, key[1:-1]))
                else:
                    out += escape_HTML(str(ctx_fetch(ctx, key)))
    if depth_if > 0:
        raise Exception("#if without #endif")
    elif depth_if < 0:
        raise Exception("#endif without #if")
    return out
