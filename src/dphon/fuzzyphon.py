#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phonological equivalence classes for fuzzy *seeding* in dphon.

Two orthogonal, opt-in relaxations of the exact-phoneme seed key. Neither
touches the verbatim phonemes used for extension, alignment, display, or
scoring -- they only change which n-grams seed together.

1. INITIAL place classes (``build_initial_classes``).
   * A "core" is a set of OBSTRUENTS at one place of articulation that differ
     only in voicing/aspiration (e.g. *b- / *p- / *pʰ-). Cores are derived from
     the ``oc-consonants.txt`` substitution matrix by connected components,
     **restricted to obstruent nodes** so that sonorants can never act as
     bridges. ``threshold`` is the single knob for core coarseness (>=7 keeps
     clean place triples).
   * Optionally (``fold_homorganic_nasals=True``) each NASAL is attached to the
     single core it is most similar to (argmax over per-core max edge, gated by
     ``nasal_threshold``). A nasal is a *leaf*: it joins a core but is never used
     as a bridge, so liquids/glides/fricatives (l, r, j, s, ...) are never pulled
     in. 

2. RHYME classes (``load_rhyme_classes``).
   * (nucleus, coda) pairs in the same traditional rhyme category (韻部) map to a
     single label, so e.g. *-in / *-iŋ (真) seed together. Membership is read
     from the curated Yunelizer-syntax file by PARSING it with ``ast`` -- never
     by executing it. Only ``rhgroup_*`` (the 部 partition) is consumed; pairwise
     ``crgroup_*`` cross-rhymes are intentionally ignored (a single-label
     partition cannot represent cross-rhyme links without over-merging, 
     so cross-rhymes are currently out of scope ).
"""

from __future__ import annotations

import ast
import csv
import logging
from importlib.resources.abc import Traversable
from typing import Dict, List, Tuple

# (nucleus, coda) -> rhyme-class label
RhymeClasses_T = Dict[Tuple[str, str], str]
# raw initial symbol -> place-class label
InitialClasses_T = Dict[str, str]
# raw nucleus -> normalized nucleus, applied to the seed key only
NucleusNorm_T = Dict[str, str]

# Symbols that may be *folded* into an obstruent core (only when requested).
NASALS = frozenset({"m", "n", "ŋ", "ŋʷ"})
# Sonorants that must never form, join, or bridge a core. They always remain
# their own seed class. (Add to this set if the matrix grows new approximants.)
NON_OBSTRUENT_APPROXIMANTS = frozenset({"l", "r", "j", "w"})


# --------------------------------------------------------------------------- #
# consonant matrix
# --------------------------------------------------------------------------- #
def load_consonant_matrix(path: Traversable) -> Dict[Tuple[str, str], int]:
    """Load ``oc-consonants.txt`` as a {(row_symbol, col_symbol): score} map.

    Fails fast on an empty file, a missing header, a blank row symbol, a short
    row, or a non-integer cell -- silent mis-parses here corrupt every class.
    """
    with path.open(encoding="utf8") as file:
        rows = list(csv.reader(file, delimiter="\t"))
    if not rows:
        raise ValueError(f"empty consonant matrix: {path}")

    header = [cell.strip() for cell in rows[0][1:] if cell.strip()]
    if not header:
        raise ValueError(f"missing consonant-matrix header: {path}")

    matrix: Dict[Tuple[str, str], int] = {}
    for line_no, row in enumerate(rows[1:], start=2):
        if not row or not any(cell.strip() for cell in row):
            continue
        sym = row[0].strip()
        if not sym:
            raise ValueError(f"blank row symbol at line {line_no}: {path}")
        vals = [cell.strip() for cell in row[1:1 + len(header)]]
        if len(vals) < len(header):
            raise ValueError(f"short row for {sym!r} at line {line_no}: {path}")
        for col, val in zip(header, vals):
            try:
                matrix[(sym, col)] = int(val)
            except ValueError as exc:
                raise ValueError(
                    f"non-integer cell ({sym!r},{col!r})={val!r} at line {line_no}: {path}"
                ) from exc
    return matrix


def _connected_components(
    nodes: List[str], edges: Dict[str, set]
) -> Dict[str, List[str]]:
    """Deterministic connected components via iterative DFS.

    Returns {component_label: sorted_members}, labelled by the
    lexicographically smallest member.
    """
    seen: set = set()
    comps: Dict[str, List[str]] = {}
    for node in nodes:
        if node in seen:
            continue
        stack, comp = [node], []
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            comp.append(cur)
            stack.extend(sorted(edges[cur] - seen))
        comp.sort()
        comps[comp[0]] = comp
    return comps


def build_initial_classes(
    path: Traversable,
    threshold: int = 7,
    fold_homorganic_nasals: bool = False,
    nasal_threshold: int = 5,
) -> InitialClasses_T:
    """Map each initial symbol to a place-class representative.

    Args:
        path: ``oc-consonants.txt``.
        threshold: minimum pairwise score for two OBSTRUENTS to share a core.
            >=7 yields clean voicing/aspiration triples per place.
        fold_homorganic_nasals: if True, attach each nasal to the single core it
            is most similar to. Off by default (nasals stay their own class).
        nasal_threshold: minimum nasal-to-core score required to fold a nasal.

    Only obstruents form cores, and only nasals may be folded in; liquids,
    glides, and fricatives outside a core always map to themselves.
    """
    matrix = load_consonant_matrix(path)
    symbols = sorted({a for a, _ in matrix} | {b for _, b in matrix})

    # 1. obstruent cores -- restrict the graph to obstruents so no sonorant can
    #    bridge two places or join a core.
    obstruents = [
        s for s in symbols
        if s not in NASALS and s not in NON_OBSTRUENT_APPROXIMANTS
    ]
    obstruent_set = set(obstruents)
    edges: Dict[str, set] = {s: set() for s in obstruents}
    for (a, b), score in matrix.items():
        if a != b and score >= threshold and a in obstruent_set and b in obstruent_set:
            edges[a].add(b)
            edges[b].add(a)

    cores = _connected_components(obstruents, edges)  # label -> [members]
    classes: InitialClasses_T = {}
    for label, members in cores.items():
        for member in members:
            classes[member] = label

    # 2. fold homorganic nasals as leaves (opt-in). Each nasal joins the core
    #    with which it has its single highest edge; it never bridges.
    if fold_homorganic_nasals:
        for nasal in sorted(NASALS):
            if nasal not in symbols:
                continue
            best_label, best_score = None, 0
            for label in sorted(cores):
                members = cores[label]
                score = max((matrix.get((nasal, m), 0) for m in members), default=0)
                if score > best_score:  # strict '>' => smallest label wins ties
                    best_score, best_label = score, label
            if best_label is not None and best_score >= nasal_threshold:
                classes[nasal] = best_label
            # else: no homorganic core -> nasal stays its own class

    # 3. every remaining symbol (l, r, j, s, lone obstruents, unfolded nasals)
    #    maps to itself: no relaxation.
    for s in symbols:
        classes.setdefault(s, s)

    n_classes = len(set(classes.values()))
    logging.info(
        "built %d initial classes (threshold=%d, fold_nasals=%s) from %s",
        n_classes, threshold, fold_homorganic_nasals,
        getattr(path, "name", path),
    )
    if fold_homorganic_nasals:
        folded = [n for n in sorted(NASALS) if n in classes and classes[n] != n]
        logging.info("folded homorganic nasals: %s", folded or "none")
    return classes


# --------------------------------------------------------------------------- #
# rhyme classes  (parse the Yunelizer file with ast; never exec it)
# --------------------------------------------------------------------------- #
# Yunelizer encodes a rime as "{nucleus}{coda}.." with these coda conventions;
# translate to the (nucleus, coda) shape used by dphon's sound table.
_YUNELIZER_CODA = {"0": "", "ꞣ": "wk"}


def _decode_rime(rime: str) -> Tuple[str, str]:
    """Decode a Yunelizer rime (e.g. 'iŋ..', 'ə0..') to (nucleus, coda).

    Assumes a single-codepoint nucleus and a single-codepoint coda marker; this
    holds for the entire current inventory. Multi-codepoint nuclei would need a
    revised encoding here.
    """
    nucleus, coda = rime[0], rime[1]
    return nucleus, _YUNELIZER_CODA.get(coda, coda)


class _RhymeGroupReader(ast.NodeVisitor):
    """Resolve a Yunelizer rhyme file into named groups WITHOUT executing it.

    Supports exactly the grammar the file uses:
        name = "literal"
        name = [a, b, ...]                 # list of names/literals
        name = a + b                       # list concatenation
        name = is_rhgroup([a, b, ...])     # flattened group
    Anything else raises, so a malformed/hostile file fails loudly instead of
    running code.
    """

    def __init__(self) -> None:
        self.env: Dict[str, Tuple[str, ...]] = {}
        self.rhgroups: Dict[str, List[str]] = {}

    def _resolve(self, node: ast.AST) -> Tuple[str, ...]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return (node.value,)
        if isinstance(node, ast.Name):
            return self.env[node.id]
        if isinstance(node, ast.List):
            out: Tuple[str, ...] = ()
            for elt in node.elts:
                out += self._resolve(elt)
            return out
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self._resolve(node.left) + self._resolve(node.right)
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "is_rhgroup":
            if len(node.args) != 1:
                raise ValueError("is_rhgroup expects exactly one argument")
            return self._resolve(node.args[0])
        raise ValueError(f"unsupported expression in rhyme file: {ast.dump(node)}")

    def visit_Assign(self, node: ast.Assign) -> None:
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            return
        name = node.targets[0].id
        value = self._resolve(node.value)
        self.env[name] = value
        # consume only the 部 partition; crgroup_* (cross-rhymes) are ignored.
        if name.startswith("rhgroup_"):
            self.rhgroups[name[len("rhgroup_"):]] = list(value)


def load_rhyme_classes(path: Traversable) -> RhymeClasses_T:
    """Build a (nucleus, coda) -> 部-label map from a Yunelizer-syntax file.

    The file is parsed with ``ast`` (no execution). Each ``rhgroup_X`` becomes a
    class labelled ``X`` whose members are its rimes decoded to (nucleus, coda).
    Combos absent from any rhgroup get no entry and fall back to exact identity.
    Pairwise ``crgroup_*`` cross-rhymes are deliberately not consumed.
    """
    reader = _RhymeGroupReader()
    with path.open(encoding="utf8") as file:
        tree = ast.parse(file.read())
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            reader.visit_Assign(stmt)

    classes: RhymeClasses_T = {}
    for label, rimes in reader.rhgroups.items():
        for rime in rimes:
            classes[_decode_rime(rime)] = label

    logging.info(
        "loaded %d rhyme-class assignments in %d classes from %s",
        len(classes), len(reader.rhgroups), getattr(path, "name", path),
    )
    return classes


# --------------------------------------------------------------------------- #
# validation against the live sound table  (warn, never raise on a superset)
# --------------------------------------------------------------------------- #
def _attested(sound_table, idx: int) -> set:
    return {r[idx] for r in sound_table.values() if len(r) > idx}


def warn_unattested_initials(sound_table, initial_classes, initial_idx: int = 3) -> None:
    """Log (do NOT raise) initials in the matrix that never occur as a token.

    The consonant matrix is a superset of any one table's initial inventory
     (e.g. 'j', 'wk'), so this is informational only.
    """
    unknown = sorted(set(initial_classes) - _attested(sound_table, initial_idx))
    if unknown:
        logging.warning("initial classes include unattested initials: %s", unknown[:20])


def warn_unattested_rhymes(
    sound_table,
    rhyme_classes,
    nucleus_idx: int = 6,
    coda_idx: int = 7,
    nucleus_norm: NucleusNorm_T | None = None,
) -> None:
    """Log (do NOT raise) rhyme keys that never occur in the table.

    ``nucleus_norm`` must match the normalization applied when the seed key is
    built (e.g. {'A': 'a'}); otherwise normalized keys spuriously look absent.
    """
    norm = nucleus_norm or {}
    attested = {
        (norm.get(r[nucleus_idx], r[nucleus_idx]), r[coda_idx])
        for r in sound_table.values()
        if len(r) > max(nucleus_idx, coda_idx)
    }
    unknown = sorted(set(rhyme_classes) - attested)
    if unknown:
        logging.warning("rhyme classes include unattested (nucleus,coda): %s", unknown[:20])
