# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L56903-L57196 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #147  lines=293  compile=OK
# kind: fragment  ident: frag_L56903.py
# edits: none. Header comment is the only addition.
# ======================
"""
CMAWSE v1.0.2 Reference Benchmark Runner
Core Engine & Hmid-3 Deterministic Program Synthesizer
Standard Library Only (Zero Third-Party Dependencies)
"""
from __future__ import annotations
import json
import heapq
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# ============================================================================
# 1. GRAMMAR & CONSTANTS DEFINITIONS
# ============================================================================

MAX_NODES: int = 12
MAX_EXPANDED_NODES: int = 1000
FALLBACK_PROGRAM: str = "IF X == A THEN q0 ELSE q0"

STATES: Tuple[str, ...] = ("q0", "q1", "q2", "q3")
TARGET_STATES: Tuple[str, ...] = ("q1", "q2", "q3")
VARS: Tuple[str, ...] = ("X", "K", "act")

OBJECT_CONSTS: Tuple[str, ...] = ("A", "B", "C")
CONTEXT_CONSTS: Tuple[str, ...] = ("K_ctx", "L_ctx", "M_ctx")
ACTION_CONSTS: Tuple[str, ...] = (
    "act_alpha", "act_beta", "act_gamma",
    "act_delta", "act_epsilon", "act_zeta"
)

VAR_DOMAINS: Dict[str, Tuple[str, ...]] = {
    "X": OBJECT_CONSTS,
    "K": CONTEXT_CONSTS,
    "act": ACTION_CONSTS,
}

# ============================================================================
# 2. AST REPRESENTATION & CANONICAL SERIALIZATION
# ============================================================================

class ASTNode:
    """Immutable Abstract Syntax Tree Node for Hmid-3 DSL."""
    __slots__ = ("symbol", "children", "_canon_cache", "_node_count_cache")

    def __init__(self, symbol: str, children: Optional[Tuple[ASTNode, ...]] = None):
        self.symbol: str = symbol
        self.children: Tuple[ASTNode, ...] = children or ()
        self._canon_cache: Optional[str] = None
        self._node_count_cache: Optional[int] = None

    @property
    def is_terminal(self) -> bool:
        return len(self.children) == 0 and not self.symbol.startswith("<")

    def node_count(self) -> int:
        if self._node_count_cache is None:
            self._node_count_cache = 1 + sum(c.node_count() for c in self.children)
        return self._node_count_cache

    def to_canon_string(self) -> str:
        if self._canon_cache is not None:
            return self._canon_cache

        if not self.children:
            self._canon_cache = self.symbol
            return self._canon_cache

        sym = self.symbol
        if sym == "<Program>":
            cond = self.children[0].to_canon_string()
            target = self.children[1].to_canon_string()
            res = f"IF {cond} THEN {target} ELSE q0"
        elif sym == "<Condition>":
            if len(self.children) == 1:
                res = self.children[0].to_canon_string()
            else:
                # Canonicalize AND ordering: X < K < act
                c1 = self.children[0]
                c2 = self.children[1]
                s1 = c1.to_canon_string()
                s2 = c2.to_canon_string()
                v1 = c1.children[0].symbol if c1.children else ""
                v2 = c2.children[0].symbol if c2.children else ""
                order = {"X": 0, "K": 1, "act": 2}
                if order.get(v1, 99) <= order.get(v2, 99):
                    res = f"{s1} AND {s2}"
                else:
                    res = f"{s2} AND {s1}"
        elif sym == "<SimpleCond>":
            var = self.children[0].to_canon_string()
            op = self.children[1].to_canon_string()
            val = self.children[2].to_canon_string()
            res = f"{var} {op} {val}"
        elif sym == "<ConstSet>":
            elems = sorted([c.to_canon_string() for c in self.children])
            res = "{" + ", ".join(elems) + "}"
        else:
            res = f"{sym}(" + ", ".join(c.to_canon_string() for c in self.children) + ")"

        self._canon_cache = res
        return self._canon_cache

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ASTNode):
            return False
        return self.to_canon_string() == other.to_canon_string()

    def __lt__(self, other: ASTNode) -> bool:
        return self.to_canon_string() < other.to_canon_string()

# ============================================================================
# 3. PARSER & EVALUATOR FOR HMID-3 AST
# ============================================================================

def evaluate_ast(program_ast: ASTNode, observation: Dict[str, str]) -> str:
    """Executes a completed AST against a single transition input."""
    if program_ast.symbol != "<Program>" or len(program_ast.children) < 2:
        return "q0"

    cond_node = program_ast.children[0]
    target_state = program_ast.children[1].symbol

    def eval_simple_cond(node: ASTNode) -> bool:
        var_name = node.children[0].symbol
        op = node.children[1].symbol
        obs_val = observation.get(var_name, "")

        if op == "==":
            const_val = node.children[2].symbol
            return obs_val == const_val
        elif op == "IN":
            const_set_node = node.children[2]
            const_vals = {c.symbol for c in const_set_node.children}
            return obs_val in const_vals
        return False

    def eval_cond(node: ASTNode) -> bool:
        if node.symbol == "<SimpleCond>":
            return eval_simple_cond(node)
        if len(node.children) == 1:
            return eval_simple_cond(node.children[0])
        elif len(node.children) == 2:
            return eval_simple_cond(node.children[0]) and eval_simple_cond(node.children[1])
        return False

    if eval_cond(cond_node):
        return target_state
    return "q0"


def parse_canonical_string(text: str) -> ASTNode:
    """Reconstructs an AST from a strict Canonical String."""
    text = text.strip()
    if not (text.startswith("IF ") and " THEN " in text and text.endswith(" ELSE q0")):
        raise ValueError(f"Invalid Program Canonical Form: {text}")

    then_idx = text.index(" THEN ")
    cond_str = text[3:then_idx]
    target_str = text[then_idx + 6 : -8]

    # Parse Condition
    if " AND " in cond_str:
        cond_parts = cond_str.split(" AND ")
    else:
        cond_parts = [cond_str]

    simple_cond_nodes = []
    for cp in cond_parts:
        tokens = cp.split(" ")
        var_name = tokens[0]
        op = tokens[1]
        var_node = ASTNode(var_name)
        op_node = ASTNode(op)
        if op == "==":
            val_node = ASTNode(tokens[2])
            simple_cond_nodes.append(ASTNode("<SimpleCond>", (var_node, op_node, val_node)))
        elif op == "IN":
            raw_set = cp[cp.index("{") + 1 : cp.index("}")]
            elements = sorted([e.strip() for e in raw_set.split(",")])
            set_children = tuple(ASTNode(e) for e in elements)
            val_node = ASTNode("<ConstSet>", set_children)
            simple_cond_nodes.append(ASTNode("<SimpleCond>", (var_node, op_node, val_node)))
        else:
            raise ValueError(f"Unknown Operator: {op}")

    cond_node = ASTNode("<Condition>", tuple(simple_cond_nodes))
    target_node = ASTNode(target_str)
    return ASTNode("<Program>", (cond_node, target_node))

# ============================================================================
# 4. DETERMINISTIC UNIFORM-COST PROGRAM SYNTHESIZER
# ============================================================================

class Hmid3Synthesizer:
    """Canonical Uniform-Cost / BFS AST search engine."""

    def __init__(self, max_nodes: int = MAX_NODES, max_expansions: int = MAX_EXPANDED_NODES):
        self.max_nodes: int = max_nodes
        self.max_expansions: int = max_expansions

    @staticmethod
    def _find_leftmost_nonterminal(node: ASTNode) -> Optional[Tuple[ASTNode, List[int]]]:
        stack = [(node, [])]
        while stack:
            curr, path = stack.pop()
            if curr.symbol.startswith("<") and not curr.children:
                return curr, path
            for idx in reversed(range(len(curr.children))):
                stack.append((curr.children[idx], path + [idx]))
        return None

    @staticmethod
    def _replace_at_path(root: ASTNode, path: List[int], replacement: ASTNode) -> ASTNode:
        if not path:
            return replacement
        curr_idx = path[0]
        new_children = list(root.children)
        new_children[curr_idx] = Hmid3Synthesizer._replace_at_path(root.children[curr_idx], path[1:], replacement)
        return ASTNode(root.symbol, tuple(new_children))

    def _get_productions(self, non_terminal: str) -> List[ASTNode]:
        prods: List[ASTNode] = []
        if non_terminal == "<Program>":
            for target in TARGET_STATES:
                prods.append(ASTNode("<Program>", (ASTNode("<Condition>"), ASTNode(target))))
        elif non_terminal == "<Condition>":
            # 1 SimpleCond
            prods.append(ASTNode("<Condition>", (ASTNode("<SimpleCond>"),)))
            # 2 SimpleConds (conjunction)
            prods.append(ASTNode("<Condition>", (ASTNode("<SimpleCond>"), ASTNode("<SimpleCond>"))))
        elif non_terminal == "<SimpleCond>":
            for var in VARS:
                # Equality branch
                prods.append(ASTNode("<SimpleCond>", (ASTNode(var), ASTNode("=="), ASTNode(f"<Const_{var}>"))))
                # Set inclusion branch
                prods.append(ASTNode("<SimpleCond>", (ASTNode(var), ASTNode("IN"), ASTNode(f"<ConstSet_{var}>"))))
        elif non_terminal.startswith("<Const_"):
            var = non_terminal[7:-1]
            for val in VAR_DOMAINS[var]:
                prods.append(ASTNode(val))
        elif non_terminal.startswith("<ConstSet_"):
            var = non_terminal[10:-1]
            domain = VAR_DOMAINS[var]
            # Enumerate size 2 subsets canonically
            n = len(domain)
            for i in range(n):
                for j in range(i + 1, n):
                    prods.append(ASTNode("<ConstSet>", (ASTNode(domain[i]), ASTNode(domain[j]))))
        return sorted(prods, key=lambda p: p.to_canon_string())

    def synthesize(self, training_data: List[Dict[str, str]]) -> Tuple[str, int]:
        """
        Executes bounded search over the grammar.
        Returns: (Canonical Program String, Node Expansions Count)
        """
        start_node = ASTNode("<Program>")
        start_key = (start_node.node_count(), start_node.to_canon_string())

        # Priority Queue: (cost, canon_str, node)
        queue: List[Tuple[int, str, ASTNode]] = []
        heapq.heappush(queue, (start_key[0], start_key[1], start_node))

        closed_set: Set[str] = set()
        expansions = 0

        while queue:
            cost, canon_str, current = heapq.heappop(queue)

            if canon_str in closed_set:
                continue
            closed_set.add(canon_str)

            expansions += 1
            if expansions > self.max_expansions:
                break

            target_info = self._find_leftmost_nonterminal(current)
            if target_info is None:
                # AST is fully terminal, evaluate on training data
                if all(evaluate_ast(current, row) == row["label"] for row in training_data):
                    return current.to_canon_string(), expansions
                continue

            nt_node, path = target_info
            productions = self._get_productions(nt_node.symbol)

            for prod in productions:
                child = self._replace_at_path(current, path, prod)
                if child.node_count() <= self.max_nodes:
                    c_str = child.to_canon_string()
                    if c_str not in closed_set:
                        heapq.heappush(queue, (child.node_count(), c_str, child))

        return FALLBACK_PROGRAM, expansions
