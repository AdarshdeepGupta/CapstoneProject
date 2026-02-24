import random
import json

def generate_tree_example():
    a = random.randint(1, 10)
    b = random.randint(-20, 20)
    x = random.randint(-10, 10)

    c = a * x + b

    problem = f"{a}x + {b} = {c}"

    # Step 1
    new_rhs = c - b
    step1_result = f"{a}x = {new_rhs}"

    # Step 2
    step2_result = f"x = {x}"

    tree = {
        "node_type": "equation",
        "value": problem,
        "children": [
            {
                "operation": "subtract_constant",
                "description": f"Subtract {b} from both sides",
                "result": step1_result,
                "children": [
                    {
                        "operation": "divide_coefficient",
                        "description": f"Divide both sides by {a}",
                        "result": step2_result,
                        "children": []
                    }
                ]
            }
        ]
    }

    return {
        "problem": problem,
        "solution_tree": tree
    }

def generate_dataset(n=5000):
    dataset = [generate_tree_example() for _ in range(n)]

    with open("dataset.json", "w") as f:
        json.dump(dataset, f, indent=4)

    print(f"Generated {n} tree-structured examples.")

if __name__ == "__main__":
    generate_dataset(5000)