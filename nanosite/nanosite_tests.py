from templates import fill_template

# fill template
assert fill_template("hello {{key}}!", {"key": "world"}) == "hello world!"
assert(fill_template("{{a.b.c}}", {"a": {"b": {"c": 3}}}) == "3")
assert(fill_template("{{#macro test a}}{{#if a}}A{{#else}}B{{#endif}}{{#endmacro}}{{test 1}}{{test 0}}", {}) == "AB")
assert(fill_template("{{#macro echo a}}{{a}}{{#endmacro}}{{#define x echo \"hello\"}}{{x}}", {}) == "hello")
assert(fill_template("{{#define x \"hello world\"}}{{x}}", {}) == "hello world")
assert(fill_template("{{#for x in items}}{{x}}.{{#endfor}}", {"items": [1, 2, 3]}) == "1.2.3.")
assert(fill_template("{{#define x \"hello world\"}}{{x}}", {}) == "hello world")
assert(fill_template("{{#if no}}nope{{#else}}{{#for x in items}}{{x}}.{{#endfor}}{{#endif}}", {"no": False, "items": [1, 2, 3]}) == "1.2.3.")
assert(fill_template("{{#if a}}A{{#if b}}B{{#elif c}}C{{#else}}(!B!C){{#endif}}(Y){{#else}}(!A){{#endif}}", {"a": True, "b": True, "c": True}) == "AB(Y)")
assert(fill_template("{{#if a}}A{{#if b}}B{{#elif c}}C{{#else}}(!B!C){{#endif}}(Y){{#else}}(!A){{#endif}}", {"a": True, "b": True, "c": False}) == "AB(Y)")
assert(fill_template("{{#if a}}A{{#if b}}B{{#elif c}}C{{#else}}(!B!C){{#endif}}(Y){{#else}}(!A){{#endif}}", {"a": True, "b": False, "c": True}) == "AC(Y)")
assert(fill_template("{{#if a}}A{{#if b}}B{{#elif c}}C{{#else}}(!B!C){{#endif}}(Y){{#else}}(!A){{#endif}}", {"a": True, "b": False, "c": False}) == "A(!B!C)(Y)")
assert(fill_template("{{#if a}}A{{#if b}}B{{#elif c}}C{{#else}}(!B!C){{#endif}}(Y){{#else}}(!A){{#endif}}", {"a": False, "b": True, "c": True}) == "(!A)")
assert(fill_template("{{#if a}}A{{#if b}}B{{#elif c}}C{{#else}}(!B!C){{#endif}}(Y){{#else}}(!A){{#endif}}", {"a": False, "b": True, "c": False}) == "(!A)")
assert(fill_template("{{#if a}}A{{#if b}}B{{#elif c}}C{{#else}}(!B!C){{#endif}}(Y){{#else}}(!A){{#endif}}", {"a": False, "b": False, "c": True}) == "(!A)")
assert(fill_template("{{#if a}}A{{#if b}}B{{#elif c}}C{{#else}}(!B!C){{#endif}}(Y){{#else}}(!A){{#endif}}", {"a": False, "b": False, "c": False}) == "(!A)")
