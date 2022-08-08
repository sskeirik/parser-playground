#!/usr/bin/env python3

from dataclasses import dataclass
from typing import TypeVar, Callable, Any
from copy import deepcopy

T = TypeVar('T')
G = TypeVar('G')

@dataclass(frozen=True)
class Symbol: pass

@dataclass(frozen=True)
class NonTerm(Symbol):
    name: str
    def __repr__(self): return self.name

@dataclass(frozen=True)
class Term(Symbol):
    name: str
    def __repr__(self): return f'"{self.name}"'

@dataclass(frozen=True)
class Rule:
    lhs: NonTerm
    rhs: tuple[Symbol, ...]

    def __repr__(self):
        res = self.lhs.name + " := "
        run = False
        for s in self.rhs:
            term = isTerm(s)
            if term and not run: res += '"'
            elif run: res += '" '
            else: res += ' '
            res += s.name
            run = term
        if run: res += '"'
        return res

@dataclass
class Grammar:
    start: NonTerm
    rules: dict[NonTerm, set[tuple[Symbol, ...]]]

    def __repr__(self):
        res = f"Grammar(\n  start = {self.start},\n"
        for n, rules in self.rules.items():
            for rule in rules:
                res += "  " + repr(Rule(n, rule)) + "\n"
        res += ")"
        return res

def isTerm(s: Symbol) -> bool:
    return isinstance(s, Term)

def isNonTerm(s: Symbol) -> bool:
    return isinstance(s, NonTerm)

def shrink_rules(rules: set[tuple[Symbol, ...]], p: set[NonTerm]) -> set[tuple[Symbol, ...]]:
    res = set()
    for rule in rules:
        if not any(isNonTerm(sym) and sym not in p for sym in rule):
            res.add(rule)
    return res

def shrink(g: Grammar, p: set[NonTerm]) -> Grammar:
    new_rules = { n : shrink_rules(rules, p) for n, rules in g.rules.items() if n in p }
    return Grammar(g.start, new_rules)

def closure(f: Callable[[set[T], G], set[T]], inc: bool) -> Callable[[set[T], G], set[T]]:

    if inc:
        init  = lambda s: (-1, len(s))
        check = lambda s1, s2: s1 < s2

    else:
        init  = lambda s: (len(s), len(s)+1)
        check = lambda s1, s2: s2 > s1

    def closure_f(s: set[T], g: G) -> set[T]:
       s = deepcopy(s)
       size, newsize = init(s)
       while check(size, newsize):
           size = newsize
           s = f(s,g)
           newsize = len(s)
       return s

    return closure_f

def productive_rule(rule: tuple[Symbol, ...], p: set[NonTerm]) -> bool:
    return all(isTerm(s) or s in p for s in rule)

def productive_1(p: set[NonTerm], g: Grammar) -> set[NonTerm]:
    for n, rules in g.rules.items():
        if n in p: continue
        if any(productive_rule(rule, p) for rule in rules):
            p.add(n)
            continue
    return p

productive_0 = closure(productive_1, True)

def productive(g: Grammar) -> set[NonTerm]:
    return productive_0(set(), g)

def reachable_1(r: set[NonTerm], g: Grammar) -> set[NonTerm]:
    for n, rules in g.rules.items():
        if n not in r: continue
        for rule in rules:
            r.update({ s for s in rule if isNonTerm(s) })
    return r

reachable_0 = closure(reachable_1, True)

def reachable(g: Grammar) -> set[NonTerm]:
    return reachable_0({ g.start }, g)

def nullable_1(null: set[NonTerm], g: Grammar) -> set[NonTerm]:
    for n, rules in g.rules.items():
        if n in null: continue
        for rule in rules:
            if all(isNonTerm(s) and s in null for s in rule):
                null.add(n)
                break
    return null

nullable_0 = closure(nullable_1, True)

def nullable(g: Grammar) -> set[NonTerm]:
    return nullable_0(set(), g)

if __name__ == "__main__":
    g = Grammar(NonTerm("A"),
               { NonTerm("A") : { (Term("P")   ,) },
                 NonTerm("B") : { (NonTerm("Q"),) },
                 NonTerm("C") : { (Term("R"),),
                                  (NonTerm("B"),) }
               })
    print(g)

    p = productive(g)
    print(p)

    g_1 = shrink(g, p)
    print(g_1)

    r = reachable(g_1)
    print(r)

    g_2 = shrink(g_1, r)
    print(g_2)

    g_s = Grammar(NonTerm("S"),
                  { NonTerm("S") : { (NonTerm("S"), NonTerm("S")),
                                     (),
                                     (NonTerm("A"), NonTerm("B")),
                                     (Term("a"),) },
                    NonTerm("A") : { (Term("a"), NonTerm("A")) },
                    NonTerm("B") : { (Term("b"),) }
                  })
    print(g_s)

    ts = productive(g_s)
    print(ts)
    g_s = shrink(g_s, ts)
    print(g_s)

    ts = reachable(g_s)
    print(ts)
    g_s = shrink(g_s, ts)
    print(g_s)

    print(nullable(g_s))
