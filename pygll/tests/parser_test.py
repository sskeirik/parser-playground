import sys
from ..grammar import *
from ..parser import *

def test_parser():
    g = Grammar(NonTerm("A"),
               { NonTerm("A") : { (Term("P")   ,) },
                 NonTerm("B") : { (NonTerm("Q"),) },
                 NonTerm("C") : { (Term("R"),),
                                  (NonTerm("B"),) }
               })
    print(g)

    r1 = Rule(NonTerm("A"), (Term("P"), NonTerm("R"), Term("Q")))
    r2 = Rule(NonTerm("A"), (NonTerm("P"), NonTerm("Q")))
    print(r1)
    print(r2)

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

    p = productive(g)
    print(p)

    g_1 = shrink(g, p)
    print(g_1)

    r = reachable(g_1)
    print(r)

    g_2 = shrink(g_1, r)
    print(g_2)

    f_1 = buildFirst(g_2)
    print(f_1)

    flw_1 = buildFollow(g_2, f_1)
    print(flw_1)

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

    f_2 = buildFirst(g_s)
    print(f_2)

    flw_2 = buildFollow(g_s, f_2)
    print(flw_2)
