# A Parser Playground

This repository contains the following runtime[^1] parser-generator implementations:

| Name   | Parser Algorithm | Language        | Notes                                |
| ----   | ---------------- | --------        | -----                                |
| pygll  | _GLL-BSR_[^2]    | Python (>= 3.7) | 100% complete but with minimal tests |
| hsgll  | _GLL-BSR_        | Haskell         | Approx. 40% complete                 |

The parser implementations are contained in subfolders with their respective names.

[^1]: As opposed to the more commonly seen compile-time parser generators (which typically consume a grammar input file and generate grammar-specific parser code as output), runtime parser generators consume a grammar data structure at runtime and generate a parser object.

[^2]: This parsing algorithm is called _CNP_ by its creators, but I think the name _GLL-BSR_ (i.e., a _GLL_ parser that emits a binary subtree representation encoding of its parse forest) as opposed to plain ol' _GLL_ (i.e., _GLL-SPPF_, a _GLL_ parser that emits a shared packed parse forest) provides a better intuition about what the algorithm does.
For more details, see their paper: [_Elizabeth Scott, Adrian Johnstone, L. Thomas van Binsbergen: Derivation representation using binary subtree sets. Sci. Comput. Program. 175: 63-84 (2019)_](https://doi.org/10.1016/j.scico.2019.01.008).
