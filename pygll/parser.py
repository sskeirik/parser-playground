#!/usr/bin/env python3

from collections import defaultdict
from dataclasses import dataclass
from typing import TypeVar, Callable, Any
from copy import deepcopy

T = TypeVar('T')
G = TypeVar('G')

MDOT = " · "

# Grammar Representation
# ######################

@dataclass(frozen=True)
class Symbol: pass

@dataclass(frozen=True)
class NonTerm(Symbol):
    name: str
    def __repr__(self): return self.name

@dataclass(frozen=True)
class PseudoTerm(Symbol): pass

@dataclass(frozen=True)
class Term(PseudoTerm):
    name: str
    def __repr__(self): return f'"{self.name}"'

@dataclass(frozen=True)
class Epsilon(PseudoTerm): pass

@dataclass(frozen=True)
class Rule:
    lhs: NonTerm
    rhs: tuple[Symbol, ...]

    def __repr__(self):
        res = self.lhs.name + " :="
        for s in self.rhs:
            term = isTerm(s)
            if term: res += f' "{s.name}"'
            else:    res += f' {s.name}'
        return res

@dataclass
class Grammar:
    start: NonTerm
    ruleDict: dict[NonTerm, set[tuple[Symbol, ...]]]

    def __repr__(self):
        res = f"Grammar(\n  start = {self.start},\n"
        for n, rules in self.ruleDict.items():
            for rule in rules:
                res += "  " + repr(Rule(n, rule)) + "\n"
        res += ")"
        return res

    def keys(self):
        return self.ruleDict.keys()

    def items(self):
        return self.ruleDict.items()

    def rules(self):
        return self.ruleDict.items()

    def __getitem__(self, nonterm):
        if not isinstance(nonterm, NonTerm):
            raise ValueError("Grammar rule lookup must use valid non-terminal")
        return self.ruleDict.get(nonterm, set())

# GLL Data Structure
# ##################

@dataclass(frozen=True)
class GrammarSlot:
    rule: Rule
    ruleIndex: int
    def __post_init__(self):
        if self.ruleIndex < 0:                  raise ValueError("GrammarSlot ruleIndex must be non-negative")
        if self.ruleIndex > len(self.rule.rhs): raise ValueError("GrammarSlot ruleIndex must be less than or equal to the rule RHS symbols")
    def __repr__(self):
        res = self.rule.lhs.name + " :="
        for i,s in enumerate(self.rule.rhs):
            term = isTerm(s)
            sep = ' '
            if i == self.ruleIndex: sep = MDOT
            if term: res += f'{sep}"{s.name}"'
            else:    res += f'{sep}{s.name}'
        if self.ruleIndex == len(self.rule.rhs): res += MDOT
        return res.strip()

@dataclass(frozen=True)
class Descriptor:
    slot: GrammarSlot
    index: int
    returnIndex: int

    def __post_init__(self):
        if self.index < 0 or self.returnIndex < 0:
            raise ValueError("Descriptor indices must be non-negative")

@dataclass(frozen=True)
class CallLocation:
    symbol: NonTerm
    index: int

    def __post_init__(self):
        if self.index < 0:
            raise ValueError("CallLocation index must be non-negative")

@dataclass(frozen=True)
class CallReturn:
    slot: GrammarSlot
    returnIndex: int

    def __post_init__(self):
        if self.index < 0:
            raise ValueError("CallReturn index must be non-negative")

@dataclass
class GLLParser:
    grammar: Grammar
    parseInput: str
    workingSet: set[Descriptor]
    totalSet: set[Descriptor]
    callReturnForest: dict[CallLocation, CallReturn]

    def __init__(self, grammar, parseInput):
        self.grammar    = grammar
        self.parseInput = parseInput
        self.workingSet = {}
        self.totalSet   = {}
        self.callReturnForest = dict()
        for rule in grammar[grammar.start]:
          addDesc(Descriptor(GrammarSlot(rule, 0), 0, 0))

    def addDesc(desc):
        if desc not in self.totalSet:
            self.workingSet.add(desc)
            self.totalSet.add(desc)

# utility functions
# #################

def isTerm(s: Symbol) -> bool:
    return isinstance(s, Term)

def isNonTerm(s: Symbol) -> bool:
    return isinstance(s, NonTerm)

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

# grammar preprocessing
# #####################

def shrink_rules(rules: set[tuple[Symbol, ...]], p: set[NonTerm]) -> set[tuple[Symbol, ...]]:
    res = set()
    for rule in rules:
        if not any(isNonTerm(sym) and sym not in p for sym in rule):
            res.add(rule)
    return res

def shrink(g: Grammar, p: set[NonTerm]) -> Grammar:
    new_rules = { n : shrink_rules(rules, p) for n, rules in g.rules() if n in p }
    return Grammar(g.start, new_rules)

def productive_rule(rule: tuple[Symbol, ...], p: set[NonTerm]) -> bool:
    return all(isTerm(s) or s in p for s in rule)

def productive_1(p: set[NonTerm], g: Grammar) -> set[NonTerm]:
    for n, rules in g.rules():
        if n in p: continue
        if any(productive_rule(rule, p) for rule in rules):
            p.add(n)
            continue
    return p

productive_0 = closure(productive_1, True)

def productive(g: Grammar) -> set[NonTerm]:
    return productive_0(set(), g)

def reachable_1(r: set[NonTerm], g: Grammar) -> set[NonTerm]:
    for n, rules in g.rules():
        if n not in r: continue
        for rule in rules:
            r.update({ s for s in rule if isNonTerm(s) })
    return r

reachable_0 = closure(reachable_1, True)

def reachable(g: Grammar) -> set[NonTerm]:
    return reachable_0({ g.start }, g)

def preprocess(g: Grammar) -> Grammar:
    p  = productive(g)
    g1 = shrink(g, p)
    r  = reachable(g1)
    g2 = shrink(g1, r)
    return g

# grammar prediction
# ##################

def nullable_1(null: set[NonTerm], g: Grammar) -> set[NonTerm]:
    for n, rules in g.rules():
        if n in null: continue
        for rule in rules:
            if all(isNonTerm(s) and s in null for s in rule):
                null.add(n)
                break
    return null

nullable_0 = closure(nullable_1, True)

def nullable(g: Grammar) -> set[NonTerm]:
    return nullable_0(set(), g)

def first_1(first: defaultdict[NonTerm, set[PseudoTerm]], g: Grammar):
    for n, rules in g.rules():
        for rule in rules:
            if len(rule) == 0:
                first[n].add(Epsilon())
            else:
                for sym in rule:
                    if isTerm(sym):
                        first[n].add(sym)
                        break
                    elif Epsilon() in first[sym]:
                        first[n].update(first[sym] - { Epsilon() })
                    else:
                        first[n].update(first[sym])
                        break
                else:
                    first[n].add(Epsilon())
    return first

first_0 = closure(first_1, True)

def first(g: Grammar) -> dict[NonTerm, set[PseudoTerm]]:
    return first_0(defaultdict(set), g)

def follow_1(follow: defaultdict[NonTerm, set[PseudoTerm]], gfp):
    g, first = gfp
    for n, rules in g.rules():
        for rule in rules:
            if len(rule) == 0: continue
            for i in range(len(rule)-1):
                curr, nxt = rule[i], rule[i+1]
                if isTerm(curr): continue
                if isTerm(nxt): follow[curr].add(nxt)
                else:           follow[curr].update(first[nxt] - { Epsilon() })
            last = rule[-1]
            if isNonTerm(last): follow[last].update(follow[n])
    return follow

follow_0 = closure(follow_1, True)

def follow(g: Grammar, first):
    d = defaultdict(set)
    d[g.start].add(Term("$"))
    return follow_0(d, (g, first))
