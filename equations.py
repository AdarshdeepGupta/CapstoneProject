import random
from sympy import symbols, latex, Eq , log , sqrt , StrictGreaterThan, StrictLessThan, GreaterThan, LessThan , Function , Piecewise, Ge, Lt

x = symbols('x')
f = Function('f')

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
    a = random.randint(-20, 20)
    b = random.randint(-20, 20)
    c = random.randint(1, 20)
    d = random.randint(-20, 20)
    return (a*x + b)/(c*x + d)


def nested():
    a = random.randint(1, 4)
    b = random.randint(-5, 5)
    c = random.randint(-5, 5)
    return a * (x + b)**2 - (x + c)



def Piecewise_function():
    a = random.randint(-10, 10)
    b = random.randint(-20, 20)
    c = random.randint(-10, 10)
    d = random.randint(-20, 20)

    return a, b, c, d

   

# -----------------------------
# Expression chooser
# -----------------------------

GENERATORS = [
     Piecewise_function
]

def generate_expression():
    generator = random.choice(GENERATORS)
    return generator()

# -----------------------------
# Dataset writer
# -----------------------------

def generate_dataset(n=10000, filename="Piecewise_functions.txt"):
    with open(filename, "w", encoding="utf-8") as f_out:
        for _ in range(n):
            a, b, c, d = generate_expression()

            line = f"f(x) = {{ {a}x + {b} , x >= 0 ; {c}x + {d} , x < 0 }}"
            f_out.write(line + "\n")

    print(f"Saved {n} piecewise functions to {filename}")

# -----------------------------
# Run
# -----------------------------

if __name__ == "__main__":
    generate_dataset(8000)
