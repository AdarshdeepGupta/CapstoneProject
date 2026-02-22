"""
Algebraic equation parser: reads equations from a .txt file (one per line)
and writes a .json file where each line has a separate JSON structure
following the same schema rules.
"""

import json
import re
from pathlib import Path
from typing import Any

from sympy import sympify
from sympy.core import Add, Mul, Pow
from sympy.core.numbers import Integer, Rational, Float
from sympy.core.symbol import Symbol as SymSymbol
from sympy.core.relational import Relational
from sympy.core.function import Function
from sympy.functions.elementary.exponential import log
from sympy.core.expr import Expr


# ---------------------------------------------------------------------------
# JSON schema (same rules for every equation line)
# ---------------------------------------------------------------------------
# Each equation: { "id", "raw", "variables", "equation_type", "relation", "lhs", "rhs" }
# Optional: "branches" for piecewise.
# Expression nodes: "constant" | "variable" | "sum" | "product" | "power" | "quotient" | "absolute_value" | "function_call"


def _normalize_line(line: str) -> str:
    """Normalize notation for parsing: unicode, ^n, implicit multiplication, | | -> Abs()."""
    line = line.strip()
    if not line:
        return ""

    # Unicode relations
    line = line.replace("≤", "<=").replace("≥", ">=")
    # Unicode superscripts (² ³ etc.)
    line = line.replace("²", "**2").replace("³", "**3")
    # Caret powers: x^2 -> x**2, x^n -> x**n (be careful with 10^2)
    line = re.sub(r"\^(\d+)", r"**\1", line)
    line = re.sub(r"\^([a-zA-Z]+)", r"**\1", line)

    # Insert * between number and letter/paren: "232 x" -> "232*x", "2(x+1)" -> "2*(x+1)"
    line = re.sub(r"(\d)\s*([a-zA-Z\(])", r"\1*\2", line)
    # Between ) and ( for factored: "(x-1)(x+2)" -> "(x-1)*(x+2)"
    line = re.sub(r"\)\s*\(", r")*(", line)

    # Absolute value: |expr| -> Abs(expr). Match innermost |...| first.
    while "|" in line:
        match = re.search(r"\|\s*([^|]+)\s*\|", line)
        if not match:
            break
        inner = match.group(1).strip()
        line = line[: match.start()] + f"Abs({inner})" + line[match.end() :]

    return line


def _parse_piecewise(line: str) -> dict[str, Any] | None:
    """Parse piecewise line: f(x) = { 9x + 10 , x >= 0 ; 6x + -14 , x < 0 }"""
    m = re.match(
        r"f\s*\(\s*x\s*\)\s*=\s*\{\s*(.+)\s*\}\s*$",
        line.strip(),
        re.IGNORECASE,
    )
    if not m:
        return None
    content = m.group(1).strip()
    # Split by ";" to get branches; each branch is "expr , condition"
    branches = []
    for part in content.split(";"):
        part = part.strip()
        if not part:
            continue
        # Last comma separates expression from condition
        idx = part.rfind(",")
        if idx == -1:
            continue
        expr_str = _normalize_line(part[:idx])
        cond_str = _normalize_line(part[idx + 1 :])
        try:
            expr = sympify(expr_str)
            cond = sympify(cond_str)
            branches.append({
                "condition": _expr_to_json(cond),
                "expression": _expr_to_json(expr),
            })
        except Exception:
            branches.append({
                "condition": {"type": "constant", "value": str(cond_str)},
                "expression": {"type": "constant", "value": str(expr_str)},
            })
    if not branches:
        return None
    return {
        "id": 0,  # set by caller
        "raw": line.strip(),
        "variables": ["x"],
        "equation_type": "piecewise",
        "relation": "=",
        "lhs": {"type": "function_def", "name": "f", "variable": "x"},
        "rhs": {"type": "piecewise", "branches": branches},
    }


def _detect_relation(normalized: str) -> tuple[str, str, str]:
    """Return (relation, lhs_str, rhs_str). relation one of '=', '>', '<', '>=', '<='."""
    for rel in [">=", "<=", "=", ">", "<"]:
        if rel in normalized:
            parts = normalized.split(rel, 1)
            if len(parts) == 2:
                return (rel, parts[0].strip(), parts[1].strip())
    return ("", normalized, "")


def _expr_to_json(expr) -> dict[str, Any]:
    """Convert SymPy expression to canonical JSON."""
    if expr is None:
        return {"type": "constant", "value": None}

    if isinstance(expr, (Integer, Rational, Float)):
        try:
            val = int(expr) if expr == int(expr) else float(expr)
        except (TypeError, ValueError):
            val = float(expr)
        return {"type": "constant", "value": val}

    if isinstance(expr, SymSymbol):
        return {"type": "variable", "name": str(expr.name)}

    if isinstance(expr, Add):
        return {"type": "sum", "terms": [_expr_to_json(t) for t in expr.args]}

    if isinstance(expr, Mul):
        return {"type": "product", "factors": [_expr_to_json(a) for a in expr.args]}

    if isinstance(expr, Pow):
        return {
            "type": "power",
            "base": _expr_to_json(expr.base),
            "exponent": _expr_to_json(expr.exp),
        }

    # Relational (for piecewise conditions: x >= 0, x < 0)
    if isinstance(expr, Relational):
        rel_map = {
            "Equality": "=", "Eq": "=", "Ne": "!=",
            "GreaterThan": ">=", "LessThan": "<=",
            "StrictGreaterThan": ">", "StrictLessThan": "<",
        }
        rel = rel_map.get(type(expr).__name__, "=")
        return {
            "type": "relational",
            "relation": rel,
            "lhs": _expr_to_json(expr.lhs),
            "rhs": _expr_to_json(expr.rhs),
        }

    # Abs
    if type(expr).__name__ == "Abs" or (hasattr(expr, "func") and getattr(expr.func, "__name__", None) == "Abs"):
        arg = expr.args[0] if expr.args else expr
        return {"type": "absolute_value", "operand": _expr_to_json(arg)}

    # log
    if hasattr(expr, "func") and getattr(expr.func, "__name__", None) == "log":
        args = expr.args
        if len(args) >= 1:
            return {
                "type": "function_call",
                "name": "log",
                "arguments": [_expr_to_json(args[0])],
            }
        return {"type": "function_call", "name": "log", "arguments": []}

    # Other functions (f(x), etc.)
    if isinstance(expr, Function) or (hasattr(expr, "func") and hasattr(expr.func, "__name__")):
        name = getattr(expr.func, "__name__", "unknown")
        return {
            "type": "function_call",
            "name": name,
            "arguments": [_expr_to_json(a) for a in expr.args],
        }

    if isinstance(expr, Expr):
        if expr.is_Add:
            return {"type": "sum", "terms": [_expr_to_json(t) for t in expr.args]}
        if expr.is_Mul:
            return {"type": "product", "factors": [_expr_to_json(a) for a in expr.args]}
        if expr.is_Pow:
            return {"type": "power", "base": _expr_to_json(expr.base), "exponent": _expr_to_json(expr.exp)}
        try:
            if expr.is_number:
                return {"type": "constant", "value": float(expr)}
        except Exception:
            pass
        return {"type": "constant", "value": str(expr)}

    return {"type": "constant", "value": str(expr)}


def _collect_variables(expr) -> set:
    """Collect symbol names from SymPy expression."""
    if expr is None:
        return set()
    if isinstance(expr, SymSymbol):
        return {str(expr.name)}
    if isinstance(expr, (Integer, Rational, Float)):
        return set()
    if hasattr(expr, "free_symbols"):
        return {str(s.name) for s in expr.free_symbols}
    return set()


def _classify_equation(lhs, rhs, relation: str, variables: set) -> str:
    """Classify equation type."""
    if relation != "=":
        # Inequality
        try:
            expr = lhs - rhs
            if hasattr(expr, "as_poly") and variables:
                syms = getattr(lhs, "free_symbols", set()) | getattr(rhs, "free_symbols", set())
                poly = expr.as_poly(*syms)
                if poly and poly.degree() <= 1:
                    return "inequality_linear"
                if poly:
                    return "inequality_polynomial"
        except Exception:
            pass
        return "inequality"

    if not variables:
        return "constant"

    syms = getattr(lhs, "free_symbols", set()) | getattr(rhs, "free_symbols", set())
    expr = lhs - rhs

    try:
        poly = expr.as_poly(*syms) if syms else None
    except Exception:
        poly = None

    if poly is not None:
        if poly.degree() <= 1:
            return "linear"
        if poly.degree() == 2:
            return "quadratic"
        return "polynomial"

    # Exponential: base**var = const
    if isinstance(lhs, Pow) and isinstance(lhs.base, (Integer, Float, Rational)):
        if lhs.exp in syms or (hasattr(lhs.exp, "free_symbols") and lhs.exp.free_symbols):
            return "exponential"
    # Logarithmic (log in lhs or numerator of lhs)
    try:
        if hasattr(lhs, "func") and getattr(lhs.func, "__name__", None) == "log":
            return "logarithmic"
        if isinstance(lhs, Mul) and any(
            getattr(a, "func", None) and getattr(a.func, "__name__", None) == "log"
            for a in lhs.args
        ):
            return "logarithmic"
    except Exception:
        pass
    # Radical (power with exponent 0.5 or 1/2)
    if isinstance(lhs, Pow):
        try:
            if lhs.exp == 0.5 or lhs.exp == sympify("1/2"):
                return "radical"
        except Exception:
            pass
    # Power equation (polynomial in power form)
    if isinstance(lhs, Pow) and lhs.exp.is_Integer:
        return "power"
    # Rational
    try:
        num, den = expr.as_numer_denom()
        if den.has(*syms) and den != 1:
            return "rational"
    except Exception:
        pass
    # Absolute value
    if type(lhs).__name__ == "Abs" or (hasattr(lhs, "func") and getattr(lhs.func, "__name__", None) == "Abs"):
        return "absolute"
    # Parametric / multi-var linear
    if len(syms) >= 2:
        try:
            if expr.as_poly(*syms).degree() <= 1:
                return "parametric"
        except Exception:
            pass
    # Functional
    if hasattr(lhs, "func") and hasattr(lhs.func, "__name__") and lhs.func.__name__ == "f":
        return "functional"
    # Identity (lhs and rhs both non-constant expressions)
    if not lhs.is_number and not rhs.is_number:
        return "identity"

    return "other"


def parse_equation(line: str, equation_id: int = 1) -> dict[str, Any] | None:
    """
    Parse one equation line into the canonical JSON structure.
    Returns one JSON object per line (same schema rules for all).
    """
    raw = line.strip()
    if not raw:
        return None

    # Piecewise: special format
    pw = _parse_piecewise(raw)
    if pw is not None:
        pw["id"] = equation_id
        return pw

    normalized = _normalize_line(raw)
    relation, lhs_str, rhs_str = _detect_relation(normalized)
    if not relation or not lhs_str or not rhs_str:
        return None

    try:
        lhs = sympify(lhs_str)
        rhs = sympify(rhs_str)
    except Exception:
        return None

    variables = sorted(_collect_variables(lhs) | _collect_variables(rhs))
    equation_type = _classify_equation(lhs, rhs, relation, set(variables))

    return {
        "id": equation_id,
        "raw": raw,
        "variables": variables,
        "equation_type": equation_type,
        "relation": relation,
        "lhs": _expr_to_json(lhs),
        "rhs": _expr_to_json(rhs),
    }


def parse_equations_file(input_path: str | Path, output_path: str | Path | None = None) -> dict[str, Any]:
    """
    Read .txt file (one equation per line). Generate a separate JSON structure
    for each line following the same rules. Write to .json if output_path given.
    """
    input_path = Path(input_path)
    if input_path.suffix.lower() != ".txt":
        raise ValueError("Input file must be a .txt file")

    equations = []
    with open(input_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            parsed = parse_equation(line, equation_id=i)
            if parsed is not None:
                equations.append(parsed)

    result = {
        "source_file": input_path.name,
        "count": len(equations),
        "equations": equations,
    }

    if output_path is not None:
        output_path = Path(output_path)
        if output_path.suffix.lower() != ".json":
            output_path = output_path.with_suffix(".json")
        with open(output_path, "w", encoding="utf-8") as out:
            json.dump(result, out, indent=2)

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Parse equations from .txt to .json (one JSON structure per line)")
    parser.add_argument("input", type=Path, help="Input .txt file")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output .json file")
    args = parser.parse_args()
    out = args.output or args.input.with_suffix(".json")
    result = parse_equations_file(args.input, output_path=out)
    print(f"Parsed {result['count']} equations -> {out}")
