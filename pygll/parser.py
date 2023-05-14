#!/usr/bin/env python3

from collections import defaultdict
from dataclasses import dataclass
from .grammar import Term, NonTerm, isTerm, isNonTerm, Rule, GrammarPredictor

MDOT = " · "

# Utility Functions
# #################

def setAdd(st, elem):
    i = len(st)
    st.add(elem)
    return len(st) != i

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
    def prevNonTerm(self):
        if self.ruleIndex == 0: raise ValueError("GrammarSlot prevNonTerm() cannot be called when index is 0")
        sym = self.rule.rhs[self.ruleIndex - 1]
        if not isNonTerm(sym ): raise ValueError("GrammarSlot prevNonTerm() cannot be called when previous symbol is not a non-terminal")
        return sym

@dataclass(frozen=True)
class Descriptor:
    slot: GrammarSlot
    returnIndex: int
    index: int

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
        if self.returnIndex < 0:
            raise ValueError("CallReturn index must be non-negative")

class GLLParser:
    grammar: GrammarPredictor
    parseInput: list[Term]
    workingSet: set[Descriptor]
    totalSet: set[Descriptor]
    callReturnForest: dict[CallLocation, set[CallReturn]]
    contingentReturnSet: dict[CallLocation, set[int]]

    def __init__(self, grammar):
        self.grammar = grammar

    def ntAdd(self, nonterm, index):
        for rule in grammar[nonterm]:
            if self.grammar.testSelect(self.parseInput[index], nonterm, rule.rhs):
                self.addDesc(Descriptor(GrammarSlot(rule, 0), index, index))

    def addDesc(self, desc):
        if desc not in self.totalSet:
            self.workingSet.add(desc)
            self.totalSet.add(desc)

    def call(self, slot, returnIndex, index):
        sym  = slot.prevNonTerm()
        loc  = CallLocation(sym, index)
        ret  = CallReturn(slot, returnIndex)
        rets = self.callReturnForest[loc]
        if len(rets) == 0:
            rets.add(ret)
            self.ntAdd(sym, index)
        else:
            added = setAdd(rets, ret)
            if added:
                for contingentRet in self.contingentReturnSet[loc]:
                    self.addDesc(Descriptor(slot, returnIndex, contingentRet))
                    self.bsrAdd(slot, returnIndex, index, contingentRet )

    def rtn(self, sym, returnIndex, index):
        loc = CallLocation(sym, returnIndex)
        contingentRet = self.contingentReturnSet[loc]
        added = setAdd(contingentRet, index)
        if added:
            for callRet in self.callReturnForest[loc]:
                self.addDesc(Descriptor(callRet.slot, callRet.returnIndex, index))
                self.bsrAdd(callRet.slot, callRet.returnIndex, returnIndex, index)

    def bsrAdd(self, slot, startIndex, index, endIndex):
        pass

    def initParse(self, parseInput):
        self.parseInput = parseInput
        self.workingSet = {}
        self.totalSet   = {}
        self.callReturnForest = defaultdict(set())
        self.contingentReturnSet = defaultdict(set())
        self.ntAdd(grammar.start)

    def continueParse(self, steps):
        while steps > 0 and len(self.workingSet) > 0:
            steps -= 1
            desc = self.workingSet.pop()
            raise RuntimeError("Unimplemented")

    def workRemaining(self):
        return len(self.workingSet)
