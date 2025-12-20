import pandas as pd
import numpy as np
import random
import json

class UniversalDataGenerator:
    def __init__(self, schema_json):
        """
        schema_json: The dictionary returned by the LLM describing inputs.
        """
        self.schema = schema_json if isinstance(schema_json, dict) else json.loads(schema_json)

    def generate_inputs(self, rows=50):
        """
        Returns a dictionary of argument_name -> value (or CSV path)
        """
        generated_args = {}
        
        if "arguments" not in self.schema:
            return generated_args

        for arg_name, details in self.schema["arguments"].items():
            arg_type = details.get("type", "string")
            
            if arg_type == "dataframe":
                generated_args[arg_name] = self._create_dataframe(details.get("columns", {}), rows)
            elif arg_type == "string":
                generated_args[arg_name] = details.get("default", "test_string")
            elif arg_type == "numeric":
                generated_args[arg_name] = details.get("default", 1)
                
        return generated_args

    def _create_dataframe(self, columns_schema, rows):
        data = {}
        for col, rules in columns_schema.items():
            dtype = rules.get("type", "string")
            
            if dtype == "string":
                # Use allowed values if present, else generic strings
                allowed = rules.get("allowed_values", [])
                if allowed:
                    data[col] = [random.choice(allowed) for _ in range(rows)]
                else:
                    data[col] = [f"val_{i}" for i in range(rows)]
                    
            elif dtype == "numeric":
                min_val = rules.get("min", 0)
                max_val = rules.get("max", 100)
                # Decide between int or float? Default to int for simplicity
                data[col] = np.random.randint(min_val, max_val, size=rows)
                
            elif dtype == "date":
                # Generate random dates
                start_date = pd.to_datetime('2020-01-01')
                random_days = np.random.randint(0, 365*3, size=rows)
                data[col] = [start_date + pd.Timedelta(days=int(d)) for d in random_days]

        return pd.DataFrame(data)