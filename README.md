# Centralised Realtime Net Settlement System

This project investigates a realtime net settlement system (RTNS), first in a centralised and then in a decentralised form.
The goal is to net out payments between n parties, eliminating issues related to non-payments due to cycles in the payment graph.

## Payment matrix

Assume an n-by-n matrix of an amount owed by entity i to entity j: `matrix[i][j]` represents that amount.
The matrix must be a square matrix.

### Bilateral Net Settlement Algorithm

The algorithm to net settle is straightforward (see code):

```python
import numpy as np

def net_bilateral_payments(payment_matrix):
    if payment_matrix.shape[0] != payment_matrix.shape[1]:
        raise ValueError("Payment matrix must be square.")

    n = payment_matrix.shape[0]
    # Create a copy to avoid modifying the original matrix
    net_matrix = payment_matrix.copy()

    for i in range(n):
        for j in range(i + 1, n):
            # The amount i owes j vs. what j owes i
            diff = net_matrix[i][j] - net_matrix[j][i]

            if diff > 0:
                # i owes j the net amount
                net_matrix[i][j] = diff
                net_matrix[j][i] = 0
            else:
                # j owes i the net amount
                net_matrix[j][i] = -diff
                net_matrix[i][j] = 0

    return net_matrix
```

### Cycles and Deadlock Algo

Another typical problem is the potential payment deadlock if there is a cycle in the payment graph.
For example:

- Alice owes Bob $10.
- Bob owes Carol $10.
- Carol owes Alice $10.

Alice can't pay Bob until she receives money from Carol, who can't pay until she gets it from Bob, who is waiting on Alice. This is a payment cycle.

The solution is to find and eliminate cycles by removing the minimum amount to all parties part of the cycle.

For example:

- Alice -owes> Bob ($100), Bob -owes> Carol ($80), Carol -owes> Alice ($120)
- Subtract 80 from the all parties
- The previous cycle becomes a non-cycle: 
    - from Alice -owes> Bob ($20), Bob -owes> Carol ($0), Carol -owes> Alice ($40)
    - to Alice -owes> Bob ($20) and Carol -owes> Alice ($40) - no cycles


Once we have been through the Bilateral Net Settlement Algo, we convert the remaining matrix into a DAG (Directed Acyclic Graph) where each vertice is an entity, and the edge represents what is owed. Once a cycle is removed via the Cycles and Deadlock Algo, remove the edge from the DAG, and repeat the process until no more cycle is found.

The final result is the optimized net settled payments. Some payments might still be required.

Find cycle:

```python
def find_cycle(graph, start_node, current_node, path, visited):
    path.append(current_node)
    visited.add(current_node)

    if current_node in graph:
        for neighbor, _ in graph[current_node]:
            if neighbor == start_node:
                # Cycle detected
                return path + [neighbor]
            if neighbor not in visited:
                result = find_cycle(graph, start_node, neighbor, path, visited)
                if result:
                    return result
    
    # Backtrack
    path.pop()
    visited.remove(current_node)
    return None
```

Cycles and Deadlock:

```python
def simplify_settlement_graph(net_matrix):
    n = net_matrix.shape[0]
    simplified_matrix = net_matrix.copy()

    while True:
        graph = {}
        for i in range(n):
            for j in range(n):
                if simplified_matrix[i][j] > 0:
                    if i not in graph:
                        graph[i] = []
                    graph[i].append((j, simplified_matrix[i][j]))

        if not graph: # No more payments to simplify
            break

        # Find a cycle in the graph
        cycle_path = None
        for start_node in graph:
            cycle_path = find_cycle(graph, start_node, start_node, [], set())
            if cycle_path:
                break
        
        # If no cycle is found, the settlement is already as simple as it can be.
        if not cycle_path:
            break
            
        # If a cycle is found, simplify it.
        min_debt_in_cycle = float('inf')
        for i in range(len(cycle_path) - 1):
            payer = cycle_path[i]
            receiver = cycle_path[i+1]
            debt = simplified_matrix[payer, receiver]
            if debt < min_debt_in_cycle:
                min_debt_in_cycle = debt

        # Subtract the minimum amount from every debt in the cycle
        for i in range(len(cycle_path) - 1):
            payer = cycle_path[i]
            receiver = cycle_path[i+1]
            simplified_matrix[payer, receiver] -= min_debt_in_cycle
            
    return simplified_matrix
```

### Centralised Test

See this [test](./code/rtns-test.py)


# Distributed Realtime Net Settlement System

In this scenario, there is no central system.

### Bilateral Net Settlement Algo

It is a very simple step of two nodes talk to each other and update their local ledgers accordingly.

- Alice node to Bob node: I owe you 10$
- Bob node to Alice node: I owe you 20$ - let's net it.

Local ledgers are updated: Alice: 0, Bob owes 10$ to Alice.

### Distributed Cycles and Deadlock Algo

The only way to detect cycles is by sending a message to your direct peers to see if it is part of a cycle:

- The *initiator* wants to know if it is part of a cycle.
    - The *initiator* creates a probe message containing:
        - A unique identifier for the current probe message
        - A unique identifier for the *initiator*
        - The path amended as the probe message goes through
        - The amount owed by the initiator to the next node

A cycle is detected if the probe message goes back to the *initiator*.
The logic then follows the Cycles and Deadlock Algo, find the minimum and send a settlement message to all the nodes in the path. 

Note the complexities with regards to atomicity, concurrency, network and trust.
