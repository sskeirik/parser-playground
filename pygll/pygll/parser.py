#!/usr/bin/env python3

from collections import defaultdict
from dataclasses import dataclass, astuple, asdict
from .grammar import Symbol, Term, NonTerm, isTerm, isNonTerm, Rule, GrammarPredictor

MDOT = " . "

# Utility Functions
# #################

def setAdd(st, elem):
    i = len(st)
    st.add(elem)
    return len(st) != i

def dictAdd(dct, key, default):
    i = len(dct)
    val = dct.setdefault(key, default)
    return len(dct) != i, val

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
            if term: res += f"{sep}'{s.name}'"
            else:    res += f'{sep}{s.name}'
        if self.index == len(self.rule.rhs): res += MDOT
        return res.strip()
    def __len__(self):
        return len(self.rule)
    def __getitem__(self, idx):
        return self.rule[idx]
    def pred(self):
        sym = self.rule.rhs[self.index - 1] if self.index else None
        if sym == None:        raise ValueError("GrammarSlot.pred() requires index > 0")
        if not isNonTerm(sym): raise ValueError("GrammarSlot.pred() requires symbol at index-1 is NonTerm")
        return sym
    def subject(self):
        return self.rule.rhs[self.index] if self.index < len(self) - 1 else None
    def prefix(self):
        return self.rule.rhs[:self.index]
    def suffix(self):
        return self.rule.rhs[self.index:]
    def update(self, offset=0):
        if offset == 0: return self
        return GrammarSlot(self.rule, self.index + offset) if self.index + offset <= len(self) else None

@dataclass(frozen=True)
class Descriptor:
    slot: GrammarSlot
    callIndex: int
    index: int

    def __post_init__(self):
        if self.index < 0 or self.callIndex < 0:
            raise ValueError("Descriptor indices must be non-negative")

@dataclass(frozen=True)
class CallRecord:
    symbol: NonTerm
    index: int

    def __post_init__(self):
        if self.index < 0:
            raise ValueError("CallRecord index must be non-negative")

@dataclass(frozen=True)
class CallContinuation:
    slot: GrammarSlot
    callIndex: int

    def __post_init__(self):
        if self.callIndex < 0:
            raise ValueError("CallContinuation callIndex must be non-negative")

def validateBSRNode(isTreeNode, node):
    if not (node.lext <= node.pivot and node.pivot <= node.rext):
        raise ValueError("BSRNode extents invalid")
    if isTerm(node.label[-1]) and not (node.pivot + 1 == node.rext):
        raise ValueError("BSRNode extents are invalid for term-final label")
    if isTreeNode and len(node.label) < 2:
        raise ValueError("BSRTreeNode label must have length >= 2")
    if len(node.label) == 0 and not (node.lext == node.pivot and node.pivot == node.rext):
        raise ValueError("BSRNode extents are invalid for an empty rule")
    if len(node.label) == 1 and not (node.lext == node.pivot):
        raise ValueError("BSRNode extents are invalid for singleton rule")

@dataclass(frozen=True)
class BSRNode: pass

@dataclass(frozen=True)
class BSRAltNode(BSRNode):
    label: Rule
    lext: int
    pivot: int
    rext: int

    def __post_init__(self):
        validateBSRNode(False, self)

@dataclass(frozen=True)
class BSRTreeNode(BSRNode):
    label: list[Symbol]
    lext: int
    pivot: int
    rext: int

    def __post_init__(self):
        validateBSRNode(True, self)

# GLL Parser
# ##########

class GLLParser:
    grammar: GrammarPredictor
    parseInput: list[Term]
    workingSet: set[Descriptor]
    totalSet: set[Descriptor]
    callReturnForest: dict[CallRecord, set[CallContinuation]]
    contingentReturnSet: dict[CallRecord, set[int]]
    bsrSet: set[BSRNode]

    def __init__(self, grammar):
        self.grammar = grammar

    def todict(self):
        return { "grammar":             self.grammar.todict(),
                 "parseInput":          [ v.name for v in self.parseInput ],
                 "totalSet":            { astuple(v) for v in self.totalSet   },
                 "workingSet":          { astuple(v) for v in self.workingSet },
                 "callReturnForest":    { astuple(k): { astuple(v) for v in vs } for k,vs in self.callReturnForest.items() },
                 "contingentReturnSet": { astuple(k): vs for k,vs in self.contingentReturnSet.items() },
                 "bsrSet":              { astuple(v) for v in self.bsrSet }
               }

    def ntAdd(self, nonterm, index):
        for ruleRhs in self.grammar.grammar[nonterm]:
            if self.grammar.testSelect(self.parseInput[index], nonterm, ruleRhs):
                self.addDesc(Descriptor(GrammarSlot(Rule(nonterm, ruleRhs), 0), index, index))

    def addDesc(self, desc):
        if desc not in self.totalSet:
            self.workingSet.add(desc)
            self.totalSet.add(desc)

    def call(self, slot, callIndex, index):
        sym = slot.pred()
        record = CallRecord(sym, index)
        cont   = CallContinuation(slot, callIndex)
        addedCall, contSet = dictAdd(self.callReturnForest, record, set())
        if addedCall:
            contSet.add(cont)
            self.ntAdd(sym, index)
        else:
            addedCont = setAdd(contSet, cont)
            if addedCont:
                for retIndex in self.contingentReturnSet[record]:
                    self.addDesc(Descriptor(slot, callIndex, retIndex))
                    self.bsrAdd(slot, callIndex, index, retIndex )

    def rtn(self, sym, callIndex, retIndex):
        record = CallRecord(sym, callIndex)
        retIndices = self.contingentReturnSet[record]
        added = setAdd(retIndices, retIndex)
        if added:
            for retAddr in self.callReturnForest[record]:
                self.addDesc(Descriptor(retAddr.slot, retAddr.callIndex, retIndex))
                self.bsrAdd(retAddr.slot, retAddr.callIndex, callIndex, retIndex)

    def bsrAdd(self, slot, lext, pivot, rext):
        if len(slot.suffix()) == 0:
            self.bsrSet.add(BSRAltNode(slot.rule, lext, pivot, rext))
        elif len(slot.prefix()) > 1:
            self.bsrSet.add(BSRTreeNode(slot.prefix(), lext, pivot, rext))

    def getInput(self, index, allowEnd=True):
        if allowEnd and index == len(self.parseInput):
            return self.grammar.end
        elif index >= 0 and index < len(self.parseInput):
            return self.parseInput[index]
        else:
            raise ValueError(f"GLLParser.getInput() index invalid")

    def parse(self, parseInput, steps=-1):
        self.parseInput = parseInput + [self.grammar.end]
        self.workingSet = set()
        self.totalSet   = set()
        self.bsrSet     = set()
        self.callReturnForest = { CallRecord(self.grammar.grammar.start, 0): set() }
        self.contingentReturnSet = defaultdict(set)
        self.ntAdd(self.grammar.grammar.start, 0)
        self.continueParse(steps)

    def continueParse(self, steps=-1):
        # while more work to do and steps remaining
        while len(self.workingSet) > 0 and steps != 0:
            if steps > 0: steps -= 1

            # grab descriptor
            desc = self.workingSet.pop()
            slot, callIndex, index = desc.slot, desc.callIndex, desc.index

            # grab sym, suffix
            sym = slot.rule.lhs
            suffix = slot.suffix()

            # if slot is nonfinal
            offset = 0
            while len(suffix[offset:]) > 0:

                # grab slot subject and parse focus
                subject = suffix[offset]
                focus = self.getInput(index + offset)

                # prune invalid descriptors
                needSelect = slot.index + offset != 0
                if needSelect and not self.grammar.testSelect(focus, slot.rule.lhs, suffix[offset:]):
                    break

                # if subject is nonterm, call it and finish processing descriptor
                if isNonTerm(subject):
                    self.call(slot.update(offset+1), callIndex, index + offset)
                    break

                # if subject is a term, add bsr element
                if isTerm(subject):
                    self.bsrAdd(slot.update(offset+1), callIndex, index + offset, index + offset + 1)

                # update offset
                offset += 1

            # if we didn't exit due to prune/call
            else:
                # if slot is final and focus is in follow map
                if len(suffix[offset:]) == 0:
                    if self.getInput(index + offset) in self.grammar.followMap[sym]:
                        self.rtn(sym, callIndex, index + offset)
                        continue

        # return new working set size
        return len(self.workingSet)

    def workRemaining(self):
        return len(self.workingSet)
