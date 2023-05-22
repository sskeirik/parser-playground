module FunPar where

import qualified Data.Map as Map
import qualified Data.Set as Set

-- NOTE: it would be interesting to make hsgll parsers able to emit cbor-encoded state
--       so that we could compare the pygll and hsgll implementations against each other.

type Set = Set.Set
type Map = Map.Map

type Id = String

data Symbol = NT Id
            | T Id
  deriving (Show, Eq, Ord)

type Rule = [ Symbol ]

data Grammar = Grammar { start :: Id,
                         rules :: Map Id [Rule] }
  deriving Show

isTerm    (T  _ ) = True
isTerm    (NT _ ) = False
isNonTerm (T  _ ) = False
isNonTerm (NT _ ) = True
name      (T  id) = id
name      (NT id) = id

nonTerms = filter isNonTerm

runG f g = f (rules g)
mapG f g = Grammar { start = start g, rules = f (rules g) }

nai p c = isNonTerm(c) && Set.member (name c) p
toi p c = isTerm(c)    || Set.member (name c) p

trans_closure :: (Set a -> b -> Set a) -> (Set a -> b -> Set a)
trans_closure f = recf (-1) where
  recf n s d
    | n >= Set.size(s) = s
    | otherwise = recf (Set.size s) (f s d) d

filterNTs' syms = Map.foldlWithKey f Map.empty
  where f acc nt rs =
          if Set.member nt syms
             then Map.insert nt (filter (all (toi syms)) rs) acc
             else acc

filterNTs syms g = Grammar (start g) $ runG (filterNTs' syms) g

prod1 :: Set Id -> Map Id [Rule] -> Set Id
prod1 = Map.foldlWithKey f
  where f acc nt rs =
          if Set.member nt acc || ( not $ (any . all) (toi acc) rs )
             then acc
             else Set.insert nt acc

reach1 :: Set Id -> Map Id [Rule] -> Set Id
reach1 = Map.foldlWithKey f
  where f acc nt rs =
          if Set.member nt acc
             then foldl (\acc r -> Set.union acc (Set.fromList $ map name $ nonTerms r)) acc rs
             else acc

null1 :: Set Id -> Map Id [Rule] -> Set Id
null1 = Map.foldlWithKey f
  where f acc nt rs =
          if Set.member nt acc || ( not $ (any . all) (nai acc) rs )
             then acc
             else Set.insert nt acc



prod  g = trans_closure prod1   Set.empty                (rules g)
reach g = trans_closure reach1 (Set.singleton $ start g) (rules g)
null  g = trans_closure null1   Set.empty                (rules g)

ex = Grammar { start = "A",
               rules = Map.fromList [("A", [ [T  "P"] ]),
                                     ("B", [ [NT "Q"] ]),
                                     ("C", [ [T  "R"],
                                             [NT "B"] ])] }

ex2 = Grammar { start = "S",
                rules = Map.fromList [("S", [ [NT "S", NT "S"],
                                              [],
                                              [NT "A", NT "B"],
                                              [T "a"]
                                            ]),
                                      ("A", [[T "a", NT "A"]]),
                                      ("B", [[T "b"]])
                                     ]}
