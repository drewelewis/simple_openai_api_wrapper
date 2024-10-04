import json

def generate_html_table(json_data):
    # Convert JSON data to Python dictionary
    data = json.loads(json_data)

    # Get the keys from the first item in the JSON data
    keys = list(data[0].keys())

    # Generate the table header
    table_header = "<tr>"
    for key in keys:
        table_header += f"<th>{key}</th>"
    table_header += "</tr>"

    # Generate the table rows
    table_rows = ""
    for item in data:
        table_row = "<tr>"
        for key in keys:
            table_row += f"<td>{item.get(key, '')}</td>"
        table_row += "</tr>"
        table_rows += table_row

    # Generate the complete HTML table
    html_table = f"<table>{table_header}{table_rows}</table>"

    return html_table

# Example usage
json_data = '[{"name": "John", "age": 30, "city": "New York"}, {"name": "Jane", "age": 25, "city": "London"}]'
html_table = generate_html_table(json_data)
print(html_table)
