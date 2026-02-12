import random
from sympy import symbols, latex, Eq

x = symbols('x')

# -----------------------------
# Expression generators
# -----------------------------

def linear():
    a = random.randint(-500, 500)
    b = random.randint(-500, 500) 
    c = random.randint(-500, 500)
    return Eq(a*x + b, c)  

def polynomial():
    degree = random.randint(2, 5)
    expr = 0
    for d in range(degree, -1, -1):
        coef = random.randint(-500, 500)
        if coef != 0:
            expr += coef * x**d
    rhs = random.randint(-20, 20)
    return Eq(expr, rhs)

def factored():
    a = random.randint(-500, 500)
    b = random.randint(-500, 500)
    c = random.randint(-500, 500)
    return Eq((x + a) * (x + b), c) 

def power():
    a = random.randint(-5, 5)
    n = random.randint(2, 4)
    return (x + a)**n

def rational():
    num = polynomial()
    den = x + random.randint(1, 5)
    return num / den

def nested():
    a = random.randint(1, 4)
    b = random.randint(-5, 5)
    c = random.randint(-5, 5)
    return a * (x + b)**2 - (x + c)



def Radical_equation():
    # choose coefficient (non-zero)
    a = random.choice([i for i in range(-50, 51) if i != 0])
    
    # choose a solution
    x0 = random.randint(-20, 20)
    
    # choose non-negative RHS
    c = random.randint(0, 20)
    
    # compute b to guarantee solvability
    b = c**2 - a * x0
    
    return Eq((a*x + b)**0.5, c)


# -----------------------------
# Expression chooser
# -----------------------------

GENERATORS = [
    Radical_equation
]

def generate_expression():
    generator = random.choice(GENERATORS)
    return generator()

# -----------------------------
# Dataset writer
# -----------------------------

def generate_dataset(n=10000, filename="Radical_equations.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        for _ in range(n):
            expr = generate_expression()
            #expr_latex = latex(expr)
            f.write(f"{expr.lhs} = {expr.rhs}\n") 

    print(f"Saved {n} expressions to {filename}")

# -----------------------------
# Run
# -----------------------------

if __name__ == "__main__":
    generate_dataset(8000)
