from src.main import process_query
import json

# Test query that should produce visualizations
test_query = "Compare the financial performance of Tesla and Ford over the last 4 quarters, including revenue, profits, and key ratios."

# Process the query
result = process_query(test_query)

# Print full result
print("\n===== FULL RESPONSE =====")
print(json.dumps(result, indent=2))
print("\n")

# Print regular response text
print("\n===== TEXT RESPONSE =====")
print(result["response"])
print("\n")

# Print visualization information
print("\n===== TABLES =====")
print(f"Number of tables: {len(result['tables'])}")
for i, table in enumerate(result['tables']):
    print(f"\nTable {i+1}: {table.get('title', 'Untitled')}")
    print(f"Description: {table.get('description', 'No description')}")
    print("Data sample: ", table.get('data', [])[:2])  # Print first 2 rows

print("\n===== GRAPHS =====")
print(f"Number of graphs: {len(result['graphs'])}")
for i, graph in enumerate(result['graphs']):
    print(f"\nGraph {i+1}: {graph.get('title', 'Untitled')}")
    print(f"Type: {graph.get('type', 'Unknown')}")
    print(f"Description: {graph.get('description', 'No description')}")
    print(f"X-Axis: {graph.get('xAxis', 'Not specified')}")
    print(f"Y-Axis: {graph.get('yAxis', 'Not specified')}")
    if 'datasets' in graph:
        print(f"Datasets: {len(graph['datasets'])}")