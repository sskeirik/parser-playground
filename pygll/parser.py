#!/usr/bin/env python3

from collections import defaultdict
from dataclasses import dataclass, astuple
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
    index: int
    def __post_init__(self):
        if self.index < 0:         raise ValueError("GrammarSlot index must be non-negative")
        if self.index > len(self): raise ValueError("GrammarSlot index must be less than or equal to the rule RHS symbols")
    def __repr__(self):
        res = self.rule.lhs.name + " :="
        for i,s in enumerate(self.rule.rhs):
            term = isTerm(s)
            sep = ' '
            if i == self.index: sep = MDOT
            if term: res += f'{sep}"{s.name}"'
            else:    res += f'{sep}{s.name}'
        if self.index == len(self.rule.rhs): res += MDOT
        return res.strip()
    def __len__(self):
        return len(self.rule)
    def callee(self):
        sym = self.rule.rhs[self.index - 1] if self.index else None
        if sym == None:        raise ValueError("GrammarSlot.callee() requires index > 0")
        if not isNonTerm(sym): raise ValueError("GrammarSlot.callee() requires symbol at index-1 is NonTerm")
        return sym
    def subject(self):
        return self.rule.rhs[self.index] if self.index < len(self) - 1 else None
    def suffix(self):
        return self.rule.rhs[self.index:]
    def update(self, offset=0):
        if offset == 0: return self
        return GrammarSlot(self.rule, self.index + offset) if self.index + offset <= len(self) else None

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

@dataclass(frozen=True)
class BSR:
    slot: GrammarSlot
    start: int
    pivot: int
    end: int

    def __post_init__(self):
        if not (self.start <= self.pivot and self.pivot <= self.end):
            raise ValueError("BSREndNode indices invalid")

# GLL Parser
# ##########

class GLLParser:
    grammar: GrammarPredictor
    parseInput: list[Term]
    workingSet: set[Descriptor]
    totalSet: set[Descriptor]
    callReturnForest: dict[CallLocation, set[CallReturn]]
    contingentReturnSet: dict[CallLocation, set[int]]
    bsrSet: set[BSR]

    def __init__(self, grammar):
        self.grammar = grammar

    def ntAdd(self, nonterm, index):
        for ruleRhs in self.grammar.grammar[nonterm]:
            if self.grammar.testSelect(self.parseInput[index], nonterm, ruleRhs):
                self.addDesc(Descriptor(GrammarSlot(Rule(nonterm, ruleRhs), 0), index, index))

    def addDesc(self, desc):
        if desc not in self.totalSet:
            self.workingSet.add(desc)
            self.totalSet.add(desc)

    def call(self, slot, returnIndex, index):
        sym  = slot.callee()
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

    def bsrAdd(self, slot, startIndex, middleIndex, endIndex):
        self.bsrSet.add(BSR(slot, startIndex, middleIndex, endIndex))

    def parse(self, parseInput, steps=-1):
        self.parseInput = parseInput
        self.workingSet = set()
        self.totalSet   = set()
        self.bsrSet     = set()
        self.callReturnForest = defaultdict(set)
        self.contingentReturnSet = defaultdict(set)
        self.ntAdd(self.grammar.grammar.start, 0)
        self.continueParse(steps)

    def continueParse(self, steps=-1):
        # while more work to do and steps remaining
        while len(self.workingSet) > 0 and steps != 0:
            if steps > 0: steps -= 1

            # grab descriptor
            desc = self.workingSet.pop()
            slot, returnIndex, index = desc.slot, desc.returnIndex, desc.index

            # skip epsilon slots (for now)
            if len(slot) == 0: continue

            # grab sym, suffix
            sym = slot.rule.lhs
            suffix = slot.suffix()

            # if slot is nonfinal
            offset = 0
            while len(suffix[offset:]) > 0:

                # grab slot subject and parse focus
                subject = suffix[offset]
                focus = self.parseInput[index + offset]

                # prune invalid descriptors
                needSelect = slot.index != 0
                if needSelect and not self.grammar.testSelect(focus, slot.rule.lhs, suffix[offset:]):
                    continue

                # if subject is nonterm, call it and finish processing descriptor
                if isNonTerm(subject):
                    self.call(slot.update(offset+1), returnIndex, index + offset)
                    break

                # if subject is a term, add bsr element
                if isTerm(subject):
                    self.bsrAdd(slot.update(offset+1), returnIndex, index + offset, index + offset + 1)

                # update offset
                offset += 1

            # if we didn't exit due to call
            else:
                # if slot is final and focus is in follow map
                if len(suffix[offset:]) == 0:
                    if self.parseInput[index + offset] in self.grammar.followMap[sym]:
                        self.rtn(sym, returnIndex, index)
                        continue

        # return new working set size
        return len(self.workingSet)

    def workRemaining(self):
        return len(self.workingSet)
