import re

class MermaidBuilder:
    def __init__(self, title="Flowchart"):
        self.title = title
        self.nodes = {}
        self.edges = []
        
    def sanitize_id(self, node_id):
        """Cleans a node ID to be Mermaid-safe (alphanumeric only)."""
        if not node_id: 
            return "node_unknown"
        # Replace non-alphanumeric chars with underscores
        clean = re.sub(r'[^a-zA-Z0-9_]', '_', node_id.strip())
        # Ensure it doesn't start with a number (Mermaid dislikes this sometimes)
        if clean and clean[0].isdigit():
            clean = "_" + clean
        return clean

    def add_node(self, node_id, label, shape="rect", style_class="script"):
        clean_id = self.sanitize_id(node_id)
        
        # Mermaid shape lookups
        shapes = {
            "rect": ('[', ']'),
            "round": ('(', ')'),
            "db": ('[(', ')]'),
            "rhombus": ('{', '}') 
        }
        
        open_b, close_b = shapes.get(shape, ('[', ']'))
        # Escape quotes in label
        clean_label = label.replace('"', "'")
        
        self.nodes[clean_id] = {
            "def": f'{clean_id}{open_b}"{clean_label}"{close_b}',
            "style": style_class
        }
        return clean_id

    def add_edge(self, from_id, to_id, label=None):
        clean_from = self.sanitize_id(from_id)
        clean_to = self.sanitize_id(to_id)
        
        arrow = "-->"
        if label:
            arrow = f'-- "{label}" -->'
            
        self.edges.append(f"    {clean_from} {arrow} {clean_to}")

    def generate_script(self):
        lines = ["graph TD;"]
        
        # 1. Definitions (Classes)
        lines.append("    classDef script fill:#f9f,stroke:#333,stroke-width:2px;")
        lines.append("    classDef data fill:#bbf,stroke:#333,stroke-width:2px;")
        lines.append("    classDef logic fill:#dfd,stroke:#333,stroke-width:2px;")
        
        # 2. Nodes
        for nid, data in self.nodes.items():
            lines.append(f"    {data['def']};")
            
        # 3. Edges
        for edge in self.edges:
            lines.append(edge)
            
        # 4. Styling assignment
        for nid, data in self.nodes.items():
            if data['style']:
                lines.append(f"    class {nid} {data['style']};")
                
        return "\n".join(lines)