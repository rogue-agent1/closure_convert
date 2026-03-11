#!/usr/bin/env python3
"""closure_convert - Closure conversion pass for a functional language compiler.

Converts lambda expressions with free variables into closure-passing style.

Usage: python closure_convert.py [--demo]
"""
import sys

# AST nodes
class Var:
    def __init__(self, name): self.name = name
    def __repr__(self): return self.name
    def free_vars(self): return {self.name}

class Lam:
    def __init__(self, param, body): self.param = param; self.body = body
    def __repr__(self): return f"(λ{self.param}. {self.body})"
    def free_vars(self): return self.body.free_vars() - {self.param}

class App:
    def __init__(self, fn, arg): self.fn = fn; self.arg = arg
    def __repr__(self): return f"({self.fn} {self.arg})"
    def free_vars(self): return self.fn.free_vars() | self.arg.free_vars()

class Let:
    def __init__(self, name, val, body): self.name = name; self.val = val; self.body = body
    def __repr__(self): return f"(let {self.name} = {self.val} in {self.body})"
    def free_vars(self): return self.val.free_vars() | (self.body.free_vars() - {self.name})

class Num:
    def __init__(self, n): self.n = n
    def __repr__(self): return str(self.n)
    def free_vars(self): return set()

class BinOp:
    def __init__(self, op, l, r): self.op = op; self.l = l; self.r = r
    def __repr__(self): return f"({self.l} {self.op} {self.r})"
    def free_vars(self): return self.l.free_vars() | self.r.free_vars()

# Closure-converted AST
class MakeClosure:
    def __init__(self, fn_name, env_vars): self.fn_name = fn_name; self.env_vars = env_vars
    def __repr__(self): return f"MkClosure({self.fn_name}, [{', '.join(self.env_vars)}])"

class ClosureApp:
    def __init__(self, closure, arg): self.closure = closure; self.arg = arg
    def __repr__(self): return f"ClosureCall({self.closure}, {self.arg})"

class EnvRef:
    def __init__(self, idx, name): self.idx = idx; self.name = name
    def __repr__(self): return f"env[{self.idx}]/*{self.name}*/"

class TopFn:
    def __init__(self, name, env_param, param, body):
        self.name = name; self.env_param = env_param; self.param = param; self.body = body
    def __repr__(self): return f"fn {self.name}({self.env_param}, {self.param}) = {self.body}"

class ClosureConverter:
    def __init__(self):
        self.counter = 0
        self.top_fns = []

    def fresh(self):
        self.counter += 1
        return f"__fn_{self.counter}"

    def convert(self, expr, env_map=None):
        if env_map is None: env_map = {}
        if isinstance(expr, Num):
            return expr
        elif isinstance(expr, Var):
            if expr.name in env_map:
                return EnvRef(env_map[expr.name], expr.name)
            return expr
        elif isinstance(expr, BinOp):
            return BinOp(expr.op, self.convert(expr.l, env_map), self.convert(expr.r, env_map))
        elif isinstance(expr, Lam):
            fv = sorted(expr.free_vars())
            fn_name = self.fresh()
            inner_env = {v: i for i, v in enumerate(fv)}
            body = self.convert(expr.body, inner_env)
            self.top_fns.append(TopFn(fn_name, "__env", expr.param, body))
            return MakeClosure(fn_name, fv)
        elif isinstance(expr, App):
            fn = self.convert(expr.fn, env_map)
            arg = self.convert(expr.arg, env_map)
            return ClosureApp(fn, arg)
        elif isinstance(expr, Let):
            val = self.convert(expr.val, env_map)
            body = self.convert(expr.body, env_map)
            return Let(expr.name, val, body)
        return expr

def main():
    print("=== Closure Conversion Demo ===\n")
    # Example: let adder = λx. λy. x + y in (adder 3) 4
    expr = Let("adder",
        Lam("x", Lam("y", BinOp("+", Var("x"), Var("y")))),
        App(App(Var("adder"), Num(3)), Num(4)))
    print(f"Source:  {expr}")
    print(f"Free vars: {expr.free_vars()}\n")
    cc = ClosureConverter()
    converted = cc.convert(expr)
    print("Hoisted top-level functions:")
    for fn in cc.top_fns:
        print(f"  {fn}")
    print(f"\nConverted main: {converted}")

    # Example 2: counter = λinit. λ_. init + 1
    print("\n--- Example 2: counter ---")
    expr2 = Lam("init", Lam("_", BinOp("+", Var("init"), Num(1))))
    print(f"Source: {expr2}")
    cc2 = ClosureConverter()
    conv2 = cc2.convert(expr2)
    print("Hoisted:")
    for fn in cc2.top_fns:
        print(f"  {fn}")
    print(f"Converted: {conv2}")

if __name__ == "__main__":
    main()
