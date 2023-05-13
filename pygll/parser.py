#!/usr/bin/env python3

from .grammar import *

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
        if self.returnIndex < 0:
            raise ValueError("CallReturn index must be non-negative")

@dataclass(frozen=True)
class CallReturnAction:
    symbol: NonTerm
    index: int
    returnIndex: int

    def __post_init__(self):
        if self.index < 0 or self.returnIndex < 0:
            raise ValueError("CallReturnAction indices must be non-negative")

@dataclass
class GLLParser:
    grammar: GrammarPredictor
    parseInput: str
    workingSet: set[Descriptor]
    totalSet: set[Descriptor]
    callReturnForest: dict[CallLocation, set[CallReturn]]
    contingentReturnSet: set[CallReturnAction]

    def __init__(self, grammar, parseInput, processGrammar=False):
        self.grammar    = grammar
        self.parseInput = parseInput
        self.workingSet = {}
        self.totalSet   = {}
        self.callReturnForest = dict()
        self.ntAdd(grammar.start)

    def ntAdd(nonterm):
        for rule in grammar[nonterm]:
          addDesc(Descriptor(GrammarSlot(rule, 0), 0, 0))

    def addDesc(desc):
        if desc not in self.totalSet:
            self.workingSet.add(desc)
            self.totalSet.add(desc)
