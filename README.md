# A Parser Playground

This repository contains the following runtime[^1] parser-generator implementations:

| Name   | Parser Algorithm  | Language        | Notes                                |
| ----   | ----------------  | --------        | -----                                |
| pygll  | _GLL-CRF-BSR_[^2] | Python (>= 3.7) | 100% complete but with minimal tests |
| hsgll  | _GLL-CRF-BSR_     | Haskell         | Approx. 40% complete                 |

The parser implementations are contained in subfolders with their respective names.

[^1]: As opposed to the more commonly seen compile-time parser generators (which typically consume a grammar input file and generate grammar-specific parser code as output), runtime parser generators consume a grammar data structure at runtime and generate a parser object.

[^2]: While this parsing algorithm is called _clustered nonterminal parsing_ (_CNP_) by its creators, I find the name _GLL-CRF-BSR_ (i.e., a _generalized, left-to-right, leftmost derivation_ _(GLL)_ parser which stores its intermediate state in a _call return forest_ (_CRF_) and emits a _binary subtree representation_ (_BSR_) encoding of its parse forest) as opposed to plain ol' _GLL_ (i.e., _GLL-GSS-SPPF_, a _GLL_ parser which stores its intermediate state in a graph-structured stack (_GSS_) and emits a shared packed parse forest _(SPPF_) encoding of its parse forest) provides a better intuition about what the algorithm does.
For more details, see their paper: [_Elizabeth Scott, Adrian Johnstone, L. Thomas van Binsbergen: Derivation representation using binary subtree sets. Sci. Comput. Program. 175: 63-84 (2019)_](https://doi.org/10.1016/j.scico.2019.01.008).
