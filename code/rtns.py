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