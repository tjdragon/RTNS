import numpy as np
from rtns import net_bilateral_payments, simplify_settlement_graph

def print_matrix(matrix, labels):
    header = "      " + " ".join([f"{label:<5}" for label in labels])
    print(header)
    print("    -" + "-" * len(header))
    for i, row in enumerate(matrix):
        row_str = f"{labels[i]:<5} |" + " ".join([f"{val:<5.1f}" for val in row])
        print(row_str)

if __name__ == '__main__':

    entity_labels = ["Alice", "Bob", "Carol", "David"]
    num_entities = len(entity_labels)

    initial_payments = np.array([
        #      To: Alice,   Bob, Carol, David
        [  0.0, 100.0,  50.0,   0.0], # From Alice
        [ 20.0,   0.0,  30.0,  80.0], # From Bob
        [ 40.0,   0.0,   0.0,  20.0], # From Carol
        [ 10.0,  10.0,   0.0,   0.0]  # From David
    ])
    
    # Let's add a payment cycle:
    # Alice owes Bob (already has 100)
    # Bob owes Carol (already has 30)
    # Carol owes Alice (already has 40)
    # This creates a cycle A -> B -> C -> A

    print("--- 1. Initial Debt Matrix ---")
    print("Represents who owes whom before any simplification.")
    print_matrix(initial_payments, entity_labels)
    print("\n" + "="*50 + "\n")

    # Step 1: Net out bilateral debts
    net_debts = net_bilateral_payments(initial_payments)
    print("--- 2. Net Bilateral Debts Matrix ---")
    print("Debts between any two people are netted out.")
    print_matrix(net_debts, entity_labels)
    print("\n" + "="*50 + "\n")


    # Step 2: Simplify settlement graph by resolving cycles
    final_settlement = simplify_settlement_graph(net_debts)
    print("--- 3. Final Simplified Settlement Plan ---")
    print("Cycles are removed. This is the most efficient payment plan.")
    print_matrix(final_settlement, entity_labels)

    print("\n--- Summary of Final Payments ---")
    for i in range(num_entities):
        for j in range(num_entities):
            if final_settlement[i, j] > 0.01: # Check for non-trivial amounts
                print(f"{entity_labels[i]} pays {entity_labels[j]}: {final_settlement[i,j]:.2f}")