#!/usr/bin/env python3

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field, astuple
from typing import TypeVar, Callable, Any
from copy import deepcopy

T = TypeVar('T')
G = TypeVar('G')

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
    def __repr__(self): return f"'{self.name}'"

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
            if term: res += f" '{s.name}'"
            else:    res += f' {s.name}'
        return res

    def __len__(self):
        return len(self.rhs)

    def __getitem__(self, idx):
        if not isinstance(idx, int):
            raise ValueError("Rule.__getitem__ requires int index")
        return self.rhs[idx]

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
            raise ValueError("Grammar.__getitem__ requires non-terminal")
        return self.ruleDict.get(nonterm, set())

    def todict(self):
        return { "start": self.start.name,
                 "ruleDict": { astuple(nt): { tuple(astuple(sym) for sym in rule) for rule in rules } for nt, rules in self.ruleDict.items() }
               }

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

def _productive_1(p: set[NonTerm], g: Grammar) -> set[NonTerm]:
    for n, rules in g.rules():
        if n in p: continue
        if any(productive_rule(rule, p) for rule in rules):
            p.add(n)
            continue
    return p

_productive_0 = closure(_productive_1, True)

def productive(g: Grammar) -> set[NonTerm]:
    return _productive_0(set(), g)

def _reachable_1(r: set[NonTerm], g: Grammar) -> set[NonTerm]:
    for n, rules in g.rules():
        if n not in r: continue
        for rule in rules:
            r.update({ s for s in rule if isNonTerm(s) })
    return r

_reachable_0 = closure(_reachable_1, True)

def reachable(g: Grammar) -> set[NonTerm]:
    return _reachable_0({ g.start }, g)

# grammar prediction
# ##################

def _nullable_1(null: set[NonTerm], g: Grammar) -> set[NonTerm]:
    for n, rules in g.rules():
        if n in null: continue
        for rule in rules:
            if all(isNonTerm(s) and s in null for s in rule):
                null.add(n)
                break
    return null

_nullable_0 = closure(_nullable_1, True)

def nullable(g: Grammar) -> set[NonTerm]:
    return _nullable_0(set(), g)

def first(firstMap: dict[NonTerm, set[PseudoTerm]], word: Iterable[Symbol]) -> set[PseudoTerm]:
    firstWord = set()
    for sym in word:
        if isTerm(sym):
            firstWord.add(sym)
            break
        firstSym = firstMap[sym]
        hasEpsilon = Epsilon() in firstSym
        firstWord.update(firstMap[sym] - { Epsilon() })
        if not hasEpsilon:
            break
    else:
        firstWord.add(Epsilon())
    return firstWord

def _buildFirst1(firstMap: defaultdict[NonTerm, set[PseudoTerm]], g: Grammar):
    for n, rules in g.rules():
        for rule in rules:
            firstMap[n] = first(firstMap, rule)
    return firstMap

_buildFirst0 = closure(_buildFirst1, True)

def buildFirst(g: Grammar) -> dict[NonTerm, set[PseudoTerm]]:
    return _buildFirst0(defaultdict(set), g)

def _buildFollow1(follow: defaultdict[NonTerm, set[PseudoTerm]], gfp: tuple[Grammar, set[PseudoTerm]]):
    g, firstMap = gfp
    for n, rules in g.rules():
        for rule in rules:
            if len(rule) == 0: continue
            for i in range(len(rule)-1):
                curr, nxt = rule[i], rule[i+1]
                if isTerm(curr): continue
                if isTerm(nxt): follow[curr].add(nxt)
                else:           follow[curr].update(firstMap[nxt] - { Epsilon() })
            last = rule[-1]
            if isNonTerm(last): follow[last].update(follow[n])
    return follow

_buildFollow0 = closure(_buildFollow1, True)

def buildFollow(g: Grammar, first: set[PseudoTerm], end=Term("$")):
    d = defaultdict(set)
    d[g.start].add(end)
    return _buildFollow0(d, (g, first))

# grammar initialization routines
# ###############################

def preprocess(g: Grammar) -> Grammar:
    p  = productive(g)
    g1 = shrink(g, p)
    r  = reachable(g1)
    g2 = shrink(g1, r)
    return g

class GrammarPredictor:
    grammar: Grammar
    firstMap: dict[NonTerm, set[PseudoTerm]]
    followMap: dict[NonTerm, set[PseudoTerm]]
    end: Term

    def __init__(self, grammar: Grammar, end=Term("$")):
        self.grammar   = preprocess(grammar)
        self.firstMap  = buildFirst(self.grammar)
        self.followMap = buildFollow(self.grammar, self.firstMap, end)
        self.end       = end

    def testSelect(self, term: Term, nonterm: NonTerm, word: Iterable[Symbol]):
        wordFirst = first(self.firstMap, word)
        return ( term in wordFirst ) \
            or ( Epsilon() in wordFirst and term in followMap[nonterm] )

    def todict(self):
        return { "grammar":   self.grammar.todict(),
                 "end":       self.end.name,
                 "firstMap":  { astuple(nt) : { astuple(v) for v in vs } for nt,vs in self.firstMap.items()  },
                 "followMap": { astuple(nt) : { astuple(v) for v in vs } for nt,vs in self.followMap.items() },
               }
