import os

class MermaidBuilder:
    """
    A helper class to construct Mermaid.js diagrams programmatically.
    Ensures syntax correctness and consistent styling.
    """
    def __init__(self, title="Process Flow"):
        self.title = title
        self.nodes = {}  # id -> label
        self.edges = []  # (from, to, text)
        self.classes = {} # id -> class_name
        self.styles = {
            "script": "fill:#f9f,stroke:#333,stroke-width:2px;",
            "data": "fill:#bbf,stroke:#333,stroke-width:2px;",
            "logic": "fill:#dfd,stroke:#333,stroke-width:2px;"
        }

    def add_node(self, node_id, label, shape="rect", style_class=None):
        """
        Shapes: rect [], round (), db [()]
        """
        clean_id = node_id.replace(" ", "_").replace(".", "_")
        clean_label = label.replace('"', "'")
        
        shapes = {
            "rect": ["[", "]"],
            "round": ["(", ")"],
            "db": ["[(", ")]"]
        }
        l, r = shapes.get(shape, ["[", "]"])
        
        self.nodes[clean_id] = f'{clean_id}{l}"{clean_label}"{r}'
        if style_class and style_class in self.styles:
            self.classes[clean_id] = style_class
        return clean_id

    def add_edge(self, from_id, to_id, label=None):
        clean_from = from_id.replace(" ", "_").replace(".", "_")
        clean_to = to_id.replace(" ", "_").replace(".", "_")
        
        arrow = "-->"
        if label:
            arrow = f"-- {label} -->"
            
        self.edges.append(f"    {clean_from} {arrow} {clean_to}")

    def generate_script(self):
        lines = ["graph TD;"]
        
        # Add Styles
        for name, style in self.styles.items():
            lines.append(f"    classDef {name} {style}")
            
        # Add Nodes
        for n_def in self.nodes.values():
            lines.append(f"    {n_def};")
            
        # Add Edges
        lines.extend(self.edges)
        
        # Apply Classes
        for node_id, cls in self.classes.items():
            lines.append(f"    class {node_id} {cls};")
            
        return "\n".join(lines)

    def save(self, output_path):
        content = f"```mermaid\n{self.generate_script()}\n```"
        with open(output_path, 'w') as f:
            f.write(content)
        return content