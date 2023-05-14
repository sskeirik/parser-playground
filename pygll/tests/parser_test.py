import sys
from ..grammar import *
from ..parser import *

def test_grammar_format():
    r1 = Rule(NonTerm("A"), (Term("P"), NonTerm("R"), Term("Q")))
    r2 = Rule(NonTerm("A"), (NonTerm("P"), NonTerm("Q")))
    print(r1)
    print(r2)

    g = Grammar(NonTerm("A"),
               { NonTerm("A") : { (Term("P")   ,) },
                 NonTerm("B") : { (NonTerm("Q"),) },
                 NonTerm("C") : { (Term("R"),),
                                  (NonTerm("B"),) }
               })
    print(g)

    g_s = Grammar(NonTerm("S"),
                  { NonTerm("S") : { (NonTerm("S"), NonTerm("S")),
                                     (),
                                     (NonTerm("A"), NonTerm("B")),
                                     (Term("a"),) },
                    NonTerm("A") : { (Term("a"), NonTerm("A")) },
                    NonTerm("B") : { (Term("b"),) }
                  })
    print(g_s)

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
    g = Grammar(NonTerm("A"),
               { NonTerm("A") : { (Term("P")   ,) },
                 NonTerm("B") : { (NonTerm("Q"),) },
                 NonTerm("C") : { (Term("R"),),
                                  (NonTerm("B"),) }
               })

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

    g = Grammar(NonTerm("S"),
               { NonTerm("S") : { (NonTerm("S"), NonTerm("S")),
                                  (),
                                  (NonTerm("A"), NonTerm("B")),
                                  (Term("a"),) },
                 NonTerm("A") : { (Term("a"), NonTerm("A")) },
                 NonTerm("B") : { (Term("b"),) }
               })

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
