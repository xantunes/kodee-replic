"""Data analysis helper functions for the DataAgent.

These are NOT MCP tools; they are internal helpers the DataAgent can call
directly when processing data-related user messages.
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Union


def parse_csv(file_path: str) -> List[Dict[str, Any]]:
    """Parse a CSV file into a list of dictionaries.

    Args:
        file_path: Path to the CSV file.

    Returns:
        List of rows, where each row is a dictionary mapping column names to values.
    """
    path = Path(file_path)
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def summarize_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute basic statistics over a list of dictionary rows.

    Stats include row count and, for each column that contains numeric values,
    the mean, min, max, and sum.

    Args:
        data: List of row dictionaries (e.g. from ``parse_csv``).

    Returns:
        Dictionary with ``count`` and per-column numeric summaries.
    """
    if not data:
        return {"count": 0, "columns": {}}

    count = len(data)
    columns: Dict[str, Any] = {}

    # Gather all column names from the first row
    first_row = data[0]
    for col in first_row.keys():
        numeric_values: List[float] = []
        for row in data:
            val = row.get(col)
            if val is None:
                continue
            try:
                numeric_values.append(float(val))
            except (ValueError, TypeError):
                continue

        if numeric_values:
            columns[col] = {
                "type": "numeric",
                "mean": round(sum(numeric_values) / len(numeric_values), 4),
                "min": round(min(numeric_values), 4),
                "max": round(max(numeric_values), 4),
                "sum": round(sum(numeric_values), 4),
                "non_null_count": len(numeric_values),
            }
        else:
            # Non-numeric column: just count non-null entries
            non_null = sum(
                1 for row in data if row.get(col) is not None and str(row.get(col)) != ""
            )
            columns[col] = {
                "type": "text",
                "non_null_count": non_null,
            }

    return {"count": count, "columns": columns}


def parse_json(file_path: str) -> Union[List[Any], Dict[str, Any]]:
    """Parse a JSON file into Python objects.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON object (list or dict), or an empty dict on error.
    """
    path = Path(file_path)
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
