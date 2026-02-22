# Equation Parser — TXT to JSON

Reads a **.txt** file (one equation per line), parses each line, and writes a **.json** file. **Each line produces one JSON structure; the same schema rules apply to every equation.**

## Usage

```bash
# Using venv Python
e:\Capstone\venv\Scripts\python.exe equation_parser.py input.txt -o output.json

# Or use run_parser.py (default: sample_equations.txt → sample_equations.json)
python run_parser.py
python run_parser.py linear_equations.txt
python run_parser.py linear_equations.txt my_output.json
```

From Python:

```python
from equation_parser import parse_equations_file, parse_equation

# Parse entire file → one JSON structure per line in result["equations"]
result = parse_equations_file("equations.txt", output_path="equations.json")

# Parse a single line
one = parse_equation("2*x + 3 = 7", equation_id=1)
```

## Input

- **Format:** One equation per line in a `.txt` file.
- **Supported:** Linear, quadratic, polynomial, rational, power, radical, exponential, logarithmic, inequalities (≤ ≥ < >), absolute value, piecewise (`f(x) = { ... ; ... }`), parametric, functional, identities.
- **Notation:** `x²` or `x^2`, `≤`/`≥`, `|expr|`, implicit multiplication like `2x` or `(x-1)(x+2)`.

## Output JSON (same rules for every line)

**File level:**
```json
{
  "source_file": "equations.txt",
  "count": 10,
  "equations": [ ... ]
}
```

**Each element of `equations` (one per line):**

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | 1-based line number |
| `raw` | string | Original line |
| `variables` | string[] | Sorted variable names |
| `equation_type` | string | `linear`, `quadratic`, `polynomial`, `rational`, `power`, `radical`, `exponential`, `logarithmic`, `inequality_linear`, `inequality_polynomial`, `piecewise`, `absolute`, `parametric`, `functional`, `identity`, `constant`, `other` |
| `relation` | string | `=`, `>`, `<`, `>=`, `<=` |
| `lhs` | object | Left-hand side expression tree |
| `rhs` | object | Right-hand side expression tree |

**Expression tree (same for `lhs`/`rhs`):**

- `{"type": "constant", "value": number}`
- `{"type": "variable", "name": "x"}`
- `{"type": "sum", "terms": [expr, ...]}`
- `{"type": "product", "factors": [expr, ...]}`
- `{"type": "power", "base": expr, "exponent": expr}`
- `{"type": "absolute_value", "operand": expr}`
- `{"type": "function_call", "name": "log", "arguments": [expr, ...]}`
- `{"type": "relational", "relation": ">=", "lhs": expr, "rhs": expr}` (e.g. in piecewise conditions)
- **Piecewise only:** `lhs`: `{"type": "function_def", "name": "f", "variable": "x"}`, `rhs`: `{"type": "piecewise", "branches": [{"condition": expr, "expression": expr}, ...]}`
