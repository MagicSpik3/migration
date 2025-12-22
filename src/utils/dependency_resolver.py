import os
import re
from collections import defaultdict, deque

class DependencyResolver:
    def __init__(self, repo_path):
        self.repo_path = os.path.abspath(repo_path)
        self.graph = defaultdict(list)
        self.in_degree = defaultdict(int)
        self.files = set()
        self.file_map = {} 

    def scan(self):
        print(f"🕵️  Scanning dependencies in {self.repo_path}...")
        
        # 1. Map all files
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                if file.lower().endswith('.sps'):
                    name = file.lower()
                    self.files.add(name)
                    self.file_map[name] = os.path.join(root, file)
                    if name not in self.in_degree: self.in_degree[name] = 0

        # 2. Parse content
        for name, path in self.file_map.items():
            with open(path, 'r', errors='ignore') as f:
                content = f.read().upper() # SPSS is case insensitive
            
            # Robust Regex: Handles "INSERT FILE = 'path'" (spaces, optional quotes)
            matches = re.findall(r"(?:INSERT|INCLUDE)\s+FILE\s*=\s*['\"]?([^'\"]+\.SPS)['\"]?", content)
            
            previous_sibling = None
            
            for match in matches:
                target = os.path.basename(match).lower()
                
                if target in self.files:
                    # Explicit Dependency: Master -> Target
                    # In Execution Order (Logic first), this means Target -> Master
                    self.graph[target].append(name) 
                    self.in_degree[name] += 1
                    print(f"   🔗 Parent-Child: {name} calls {target}")

                    # --- NEW: Sequential Sibling Dependency ---
                    # If Master calls A then B, assume A -> B
                    if previous_sibling:
                        self.graph[previous_sibling].append(target)
                        self.in_degree[target] += 1
                        print(f"   🔗 Sequential:   {previous_sibling} runs before {target}")
                    
                    previous_sibling = target

    def get_execution_order(self):
        # Topological Sort (Kahn's Algorithm)
        queue = deque([node for node in self.files if self.in_degree[node] == 0])
        sorted_files = []
        
        while queue:
            node = queue.popleft()
            sorted_files.append(node)
            
            for neighbor in self.graph[node]:
                self.in_degree[neighbor] -= 1
                if self.in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cyclic/unresolved dependencies
        if len(sorted_files) != len(self.files):
            print("⚠️  Warning: Cycles or Orphans detected. Graph may be incomplete.")
            
        return sorted_files

    def generate_architecture_doc(self, output_path="architecture.md"):
        order = self.get_execution_order()
        with open(output_path, 'w') as f:
            f.write("# 🏛️ System Architecture\n\n## Execution Chain\n")
            for i, file in enumerate(order):
                f.write(f"{i+1}. **{file}**\n")
            
            f.write("\n## Visual Graph\n```mermaid\ngraph TD;\n")
            for target, dependents in self.graph.items():
                for dep in dependents:
                    # Clean names for Mermaid
                    t_clean = target.replace(".", "_")
                    d_clean = dep.replace(".", "_")
                    f.write(f"    {t_clean} --> {d_clean};\n")
            f.write("```\n")

if __name__ == "__main__":
    REPO = os.path.expanduser("~/git/dummy_spss_repo/syntax")
    resolver = DependencyResolver(REPO)
    resolver.scan()
    print("Order:", resolver.get_execution_order())