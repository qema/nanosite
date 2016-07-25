import re
from html import escape as escape_HTML

# escape templating delimiters
def escape_delimiters(s):
    return s.replace("{{", "\\{{").replace("}}", "\\}}")

def unescape_delimiters(s):
    return s.replace("\\{{", "{{").replace("\\}}", "}}")

# fetch key, possibly nested thru dot notation
def ctx_fetch(ctx, line):
    key, params = (line.split(" ", 1) + [""])[:2]
    parts = key.split(".", 1)
    is_attr = hasattr(ctx, parts[0])
    if parts[0] in ctx or is_attr:
        if len(parts) == 1:
            value = None
            try:  # try getting it as a dictionary entry first
                value = ctx[parts[0]]
            except:  # otherwise try getting it as an attribute
                value = getattr(ctx, parts[0])
            # if it's a macro, call it with parameter [ctx]
            if callable(value):
                value = value(ctx, *tokenize_params(ctx, params))
            return value
        else:
            return ctx_fetch(ctx[parts[0]], parts[1])
    else:
        return None

# get params from space-separated parameter list
# if greedy, then context grabs consume all of the remaining parameters
#   (this is for macro calls with parameters)
def tokenize_params(ctx, params, greedy=False):
    out = []
    in_string = False
    tokens = params.split(" ")
    for i, token in enumerate(tokens):
        if token != "":
            if token[0] == '"':  # begin string
                in_string = True
                token = token[1:]
                out.append("")
            if in_string:  # continue string
                if token[-1] == '"': 
                    token = token[:-1]
                    in_string = False
                out[-1] += token + (" " if in_string else "")
            else:
                try:  # int 
                    out.append(int(token))
                except ValueError:  # float
                    try:
                        out.append(float(token))
                    except ValueError:  # identifier (so get object from ctx)
                        if greedy: token = " ".join(tokens[i:])
                        out.append(ctx_fetch(ctx, token))
                        if greedy: break
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
# ctx is modified according to new variable bindings
def fill_template(tmpl, ctx):
    def make_define(ctx, cmd):
        ctx[cmd[1]] = tokenize_params(ctx, " ".join(cmd[2:]), greedy=True)[0]
                
    # get part before delim and part after
    def get_chunk(s, delim):
        #a = s.split(delim, 1)
        a = re.split(delim, s, 1)
        return (a[0], "") if len(a) <= 1 else a
    rest = tmpl
    out = ""
    seeking = None
    seek_depth = 0
    depth_if = 0
    depth_for = 0
    block_accum = ""
    for_variable = ""
    for_collection = None
    macro_name = ""
    macro_param_names = []
    while len(rest) > 0:
        # match {{, not \{{, \{{{
        cur, rest = get_chunk(rest, "(?<!\\\\)(?<!{){{")
        #print("}}", cur, "{{", rest, seeking, seek_depth, depth_if)
        #print()
        if seeking is None:
            out += cur
        else:
            block_accum += cur
        key, rest = get_chunk(rest, "(?<!\\\\)(?<!})}}")
        key = key.strip()
        cmd = key.split()
        if cmd: cmd[0] = cmd[0].lower()

        #print("{{", key, "}}", rest, seeking, seek_depth, depth_if)
        #print()
        #print()

        if seeking is not None:
            run_for_block = False
            create_macro = False
            if cmd[0] == "#if":
                depth_if += 1
            elif cmd[0] == "#else":
                if "#else" in seeking and seek_depth == depth_if:
                    #print("FOUND MATCHING ELSE", seek_depth, depth_if)
                    seeking = None
            elif cmd[0] == "#elif":
                if "#elif" in seeking and seek_depth == depth_if:
                    if ctx_fetch(ctx, " ".join(cmd[1:])):
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
            elif cmd[0] == "#macro":
                raise Exception("#macro declared inside of another block")
            elif cmd[0] == "#endmacro":
                seeking = None
                create_macro = True
            elif cmd[0] == "#define":
                make_define(ctx, cmd)
            if run_for_block:
                orig = None  # save original context binding
                if for_variable in ctx:
                    orig = ctx["for_variable"]

                for item in for_collection:
                    ctx[for_variable] = item
                    out += fill_template(block_accum, ctx)
                if orig is None:  # restore original context binding
                    if for_variable in ctx:
                        ctx.pop(for_variable)
                else:
                    ctx[for_variable] = orig
            elif create_macro:
                def macro_func(ctx, *params):
                    origs = {}  # saves original bindings
                    for name, value in zip(macro_param_names, params):
                        if name in ctx: origs[name] = ctx[name]
                        ctx[name] = value
                    out = fill_template(block_accum, ctx)
                    for key in origs:  # restore bindings
                        ctx[key] = origs[key]
                    return out
                ctx[macro_name] = macro_func
            else:
                block_accum += "{{" + key + "}}"
        else:
            if cmd == [] or cmd[0] == "":
                pass
            elif cmd[0] == "#if":
                depth_if += 1
                if not ctx_fetch(ctx, " ".join(cmd[1:])):  # if ctx[key] evaluates to True
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
                block_accum = ""
                seeking = {"#endfor"}
                seek_depth = depth_for
                for_variable = cmd[1]
                for_collection = ctx_fetch(ctx, " ".join(cmd[3:]))
            elif cmd[0] == "#endfor":
                depth_for -= 1
            elif cmd[0] == "#macro":
                block_accum = ""
                seeking = {"#endmacro"}
                macro_name = cmd[1]
                macro_param_names = cmd[2:]
            elif cmd[0] == "#define":
                make_define(ctx, cmd)
            else:
                if key[0] == "{":
                    val = str(ctx_fetch(ctx, key[1:].strip()))
                    _, rest = get_chunk(rest, "}") # get matching close brace
                else:
                   val = escape_HTML(str(ctx_fetch(ctx, key.strip())))
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
