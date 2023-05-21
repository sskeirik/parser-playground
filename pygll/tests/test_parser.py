from copy import deepcopy
from pathlib import Path
import pickle
import sys
from pygll.grammar import *
from pygll.parser import *

try:
    import pytest
    from deepdiff import DeepDiff
except:
    print("Package(s) pytest, deepdiff required; try\n$ pip install pytest deepdiff", file=sys.stderr)
    sys.exit(1)

G1 = Grammar(NonTerm("A"),
            { NonTerm("A") : { (Term("P")   ,) },
              NonTerm("B") : { (NonTerm("Q"),) },
              NonTerm("C") : { (Term("R"),),
                               (NonTerm("B"),) }
            })

G2 = Grammar(NonTerm("S"),
            { NonTerm("S") : { (NonTerm("S"), NonTerm("S")),
                               (),
                               (NonTerm("A"), NonTerm("B")),
                               (Term("a"),) },
              NonTerm("A") : { (Term("a"), NonTerm("A")) },
              NonTerm("B") : { (Term("b"),) }
            })

G3 = Grammar(NonTerm("S"),
            { NonTerm("S") : { (NonTerm("A"), NonTerm("C"), Term("a"), NonTerm("B")),
                               (NonTerm("A"), NonTerm("B"), Term("a"), Term("a")),
                             },
              NonTerm("A") : { (Term("a"), NonTerm("A")),
                               (Term("a"),),
                             },
              NonTerm("B") : { (Term("b"), NonTerm("B")),
                               (Term("b"),),
                             },
              NonTerm("C") : { (Term("b"), NonTerm("C")),
                               (Term("b"),),
                             },
            })

G4 = Grammar(NonTerm("E"),
            { NonTerm("E") : { (NonTerm("E"), Term("+"), NonTerm("E")),
                               (Term("1"),),
                             },
            })

def test_grammar_format():
    r1 = Rule(NonTerm("A"), (Term("P"), NonTerm("R"), Term("Q")))
    r2 = Rule(NonTerm("A"), (NonTerm("P"), NonTerm("Q")))
    print(r1)
    print(r2)

    print(G1)
    print(G2)

    print(GrammarSlot(r1,0))
    print(GrammarSlot(r1,1))
    print(GrammarSlot(r1,2))
    print(GrammarSlot(r1,3))
    print(GrammarSlot(r2,0))
    print(GrammarSlot(r2,1))
    print(GrammarSlot(r2,2))

    try:
        GrammarSlot(r2,3)
        raise Exception("A ValueError should have been raised")
    except ValueError:
        pass

def test_grammar_build():
    g     = deepcopy(G1)
    p     = productive(g)
    g_1   = shrink(g, p)
    r     = reachable(g_1)
    g_2   = shrink(g_1, r)
    f_1   = buildFirst(g_2)
    flw_1 = buildFollow(g_2, f_1)
    print(g)
    print(p)
    print(g_1)
    print(r)
    print(g_2)
    print(f_1)
    print(flw_1)

    g     = deepcopy(G2)
    p     = productive(g)
    g_1   = shrink(g, p)
    r     = reachable(g_1)
    g_2   = shrink(g_1, r)
    f_1   = buildFirst(g_2)
    flw_1 = buildFollow(g_2, f_1)
    print(g)
    print(p)
    print(g_1)
    print(r)
    print(g_2)
    print(f_1)
    print(flw_1)

PARSER_TESTS = [
                 (G3, "abaa", "./inputs/simple_01.pickle"),
                 (G4, "1+1+1", "./inputs/ambexp_01.pickle")
               ]

def dump_parser_state():
    script_dir = Path(__file__).parent.resolve()
    for grammar, inputstr, json_state_file in PARSER_TESTS:
        p = init_parser(grammar, inputstr, -1)
        with open(script_dir / json_state_file, 'wb') as f:
            pickle.dump(p.todict(), f)

def load_parser_state(json_state_file):
    script_dir = Path(__file__).parent.resolve()
    with open(script_dir / json_state_file,'rb') as f:
        st = pickle.load(f)
    return st

def validate_parser_state(json_state_file, parser):
    expected_state = load_parser_state(json_state_file)
    actual_state = parser.todict()
    diff = DeepDiff(expected_state, actual_state)
    if len(diff) != 0:
        raise ValueError(f"Parser state does not match expected state:\n{expected_state}\n{actual_state}\n{diff.pretty()}")

def init_parser(grammar, rawInput, steps=0):
    parseInput = [Term(c) for c in rawInput]
    grammarPredictor = GrammarPredictor(deepcopy(grammar))
    gllParser = GLLParser(grammarPredictor)
    gllParser.parse(parseInput, steps)
    return gllParser

@pytest.mark.parametrize("grammar,rawInput,state_file", PARSER_TESTS)
def test_parser(grammar, rawInput, state_file):
    p = init_parser(grammar, rawInput)
    p.continueParse()
    validate_parser_state(state_file, p)
