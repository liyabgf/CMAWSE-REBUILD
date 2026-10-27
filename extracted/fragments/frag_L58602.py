# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L58602-L58918 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #156  lines=316  compile=OK
# kind: fragment  ident: frag_L58602.py
# edits: none. Header comment is the only addition.
# ======================
"""
CMAWSE v1.0.3 Reference Benchmark Runner
Core Engine & Hmid-3 Deterministic Program Synthesizer
Standard Library Only (Zero External Dependencies)
"""
from __future__ import annotations
import itertools
import heapq
from typing import Any, Dict, List, Optional, Set, Tuple

# ============================================================================
# 1. GRAMMAR & SYSTEM CONSTANTS
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

VAR_PRECEDENCE: Dict[str, int] = {"X": 0, "K": 1, "act": 2}

# ============================================================================
# 2. IMMUTABLE AST NODE & CANONICAL SERIALIZATION
# ============================================================================

class ASTNode:
    """Canonical Abstract Syntax Tree Node for Hmid-3 DSL."""
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
                c1, c2 = self.children[0], self.children[1]
                s1, s2 = c1.to_canon_string(), c2.to_canon_string()
                v1 = c1.children[0].symbol if c1.children else ""
                v2 = c2.children[0].symbol if c2.children else ""
                p1 = VAR_PRECEDENCE.get(v1, 99)
                p2 = VAR_PRECEDENCE.get(v2, 99)
                # Strict tie-break on secondary ASCII serialization
                if (p1, s1) <= (p2, s2):
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
# 3. GRAMMAR-STRICT PARSER & EVALUATOR
# ============================================================================

def evaluate_ast(program_ast: ASTNode, observation: Dict[str, str]) -> str:
    """Evaluates a complete AST against an observation slice."""
    if program_ast.symbol != "<Program>" or len(program_ast.children) < 2:
        return "q0"

    cond_node = program_ast.children[0]
    target_state = program_ast.children[1].symbol

    def eval_simple_cond(node: ASTNode) -> bool:
        var_name = node.children[0].symbol
        op = node.children[1].symbol
        obs_val = observation.get(var_name, "")

        if op == "==":
            return obs_val == node.children[2].symbol
        elif op == "IN":
            const_vals = {c.symbol for c in node.children[2].children}
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

    return target_state if eval_cond(cond_node) else "q0"


def parse_canonical_string(text: str) -> ASTNode:
    """
    Normative Grammar-Strict Parser.
    Reconstructs an AST from CanonString and validates grammar compliance.
    Rejects malformed syntax, invalid operators, or domain violations.
    """
    text = text.strip()
    if not (text.startswith("IF ") and " THEN " in text and text.endswith(" ELSE q0")):
        raise ValueError(f"Malformed Program Header/Trailer: {text}")

    then_idx = text.index(" THEN ")
    cond_str = text[3:then_idx].strip()
    target_str = text[then_idx + 6 : -8].strip()

    if target_str not in TARGET_STATES:
        raise ValueError(f"Invalid Target State: {target_str}")

    cond_parts = cond_str.split(" AND ") if " AND " in cond_str else [cond_str]
    if len(cond_parts) > 2:
        raise ValueError(f"Condition exceeds maximum of 2 conjuncts: {cond_str}")

    simple_cond_nodes: List[ASTNode] = []
    seen_vars: List[Tuple[int, str]] = []

    for cp in cond_parts:
        tokens = cp.split(" ", 2)
        if len(tokens) != 3:
            raise ValueError(f"Malformed SimpleCond: '{cp}'")
        var_name, op, right = tokens[0], tokens[1], tokens[2]

        if var_name not in VARS:
            raise ValueError(f"Invalid Variable: {var_name}")
        if op not in ("==", "IN"):
            raise ValueError(f"Invalid Operator: {op}")

        var_node = ASTNode(var_name)
        op_node = ASTNode(op)
        valid_domain = VAR_DOMAINS[var_name]

        if op == "==":
            if right not in valid_domain:
                raise ValueError(f"Constant '{right}' not in domain of {var_name}")
            val_node = ASTNode(right)
            simple_cond_nodes.append(ASTNode("<SimpleCond>", (var_node, op_node, val_node)))
        else:  # IN
            if not (right.startswith("{") and right.endswith("}")):
                raise ValueError(f"Malformed Set Literal: {right}")
            raw_elements = [e.strip() for e in right[1:-1].split(",") if e.strip()]
            if len(raw_elements) < 2 or len(raw_elements) > len(valid_domain):
                raise ValueError(f"Invalid Set Cardinality {len(raw_elements)} for {var_name}")
            if raw_elements != sorted(list(set(raw_elements))):
                raise ValueError(f"Set elements not strictly sorted or contain duplicates: {right}")
            for elem in raw_elements:
                if elem not in valid_domain:
                    raise ValueError(f"Set element '{elem}' not in domain of {var_name}")
            val_node = ASTNode("<ConstSet>", tuple(ASTNode(e) for e in raw_elements))
            simple_cond_nodes.append(ASTNode("<SimpleCond>", (var_node, op_node, val_node)))

        seen_vars.append((VAR_PRECEDENCE[var_name], cp))

    # Verify canonical variable ordering
    if len(seen_vars) == 2 and seen_vars[0] > seen_vars[1]:
        raise ValueError(f"Condition variables violated canonical ordering: {cond_str}")

    cond_node = ASTNode("<Condition>", tuple(simple_cond_nodes))
    target_node = ASTNode(target_str)
    return ASTNode("<Program>", (cond_node, target_node))

# ============================================================================
# 4. DETERMINISTIC UNIFORM-COST SYNTHESIZER (UCS)
# ============================================================================

class Hmid3Synthesizer:
    """
    Hmid-3: Deterministic Uniform-Cost Search (UCS) over AST node count.
    Guarantees machine-independent, bit-level deterministic program synthesis.
    """

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
        new_children[curr_idx] = Hmid3Synthesizer._replace_at_path(
            root.children[curr_idx], path[1:], replacement
        )
        return ASTNode(root.symbol, tuple(new_children))

    def _get_productions(self, non_terminal: str) -> List[ASTNode]:
        prods: List[ASTNode] = []
        if non_terminal == "<Program>":
            for target in TARGET_STATES:
                prods.append(ASTNode("<Program>", (ASTNode("<Condition>"), ASTNode(target))))
        elif non_terminal == "<Condition>":
            prods.append(ASTNode("<Condition>", (ASTNode("<SimpleCond>"),)))
            prods.append(ASTNode("<Condition>", (ASTNode("<SimpleCond>"), ASTNode("<SimpleCond>"))))
        elif non_terminal == "<SimpleCond>":
            for var in VARS:
                prods.append(ASTNode("<SimpleCond>", (ASTNode(var), ASTNode("=="), ASTNode(f"<Const_{var}>"))))
                prods.append(ASTNode("<SimpleCond>", (ASTNode(var), ASTNode("IN"), ASTNode(f"<ConstSet_{var}>"))))
        elif non_terminal.startswith("<Const_"):
            var = non_terminal[7:-1]
            for val in VAR_DOMAINS[var]:
                prods.append(ASTNode(val))
        elif non_terminal.startswith("<ConstSet_"):
            var = non_terminal[10:-1]
            domain = sorted(VAR_DOMAINS[var])
            for r in range(2, len(domain) + 1):
                for combo in itertools.combinations(domain, r):
                    prods.append(ASTNode("<ConstSet>", tuple(ASTNode(c) for c in combo)))
        # Strictly sort productions by byte-level CanonString
        return sorted(prods, key=lambda p: p.to_canon_string())

    def synthesize(self, training_data: List[Dict[str, str]]) -> Tuple[str, int]:
        """
        Executes bounded deterministic UCS.
        Returns: (Canonical Program String, Node Expansions Count)
        """
        start_node = ASTNode("<Program>")
        queue: List[Tuple[int, str, ASTNode]] = []
        heapq.heappush(queue, (start_node.node_count(), start_node.to_canon_string(), start_node))

        closed_set: Set[str] = set()
        expanded_nodes: int = 0

        while queue:
            if expanded_nodes >= self.max_expansions:
                break

            cost, canon_str, current = heapq.heappop(queue)
            if canon_str in closed_set:
                continue

            closed_set.add(canon_str)
            expanded_nodes += 1

            target_info = self._find_leftmost_nonterminal(current)
            if target_info is None:
                # Complete AST reached: verify zero training error
                if all(evaluate_ast(current, row) == row["label"] for row in training_data):
                    return current.to_canon_string(), expanded_nodes
                continue

            nt_node, path = target_info
            productions = self._get_productions(nt_node.symbol)

            for prod in productions:
                child = self._replace_at_path(current, path, prod)
                if child.node_count() <= self.max_nodes:
                    c_str = child.to_canon_string()
                    if c_str not in closed_set:
                        heapq.heappush(queue, (child.node_count(), c_str, child))

        return FALLBACK_PROGRAM, expanded_nodes
