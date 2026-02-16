
"""
Problem Description:
Given a list of spans in the format of a map of the metadata and its values
(including start timestamp, span_id, parent_id etc), and the list is not in any order.
If the parent id is None, the span will be considered as root span;
if span_id in parent_span id is named but can't be found, the span will be considered as orphan span
and will become the root span.
The output should be the list of tree structure trace built with spans.
Also the child spans should be sorted by start timestamp.

Example:
Input:
[{"span_id":"span_1", "parent_id":None,"start_time":300},
 {"span_id":"span_2", "parent_id":"span_1","start_time":500},
 {"span_id":"span_3", "parent_id":"span_1","start_time":300},
 {"span_id":"span_4", "parent_id":"span_2","start_time":500},
 {"span_id":"span_5", "parent_id":"span_6","start_time":600},
 {"span_id":"span_7", "parent_id":None,"start_time":1000}]

Output:
[{"span_id":"span_1", "parent_id":None,"start_time":300, children: [{
        "span_id":"span_3", "parent_id":"span_1","start_time":300
        },
        {"span_id":"span_2", "parent_id":"span_1","start_time":500, children: [{
                "span_id":"span_4", "parent_id":"span_2","start_time":500
        }]}]},
{"span_id":"span_5", "parent_id":"span_6","start_time":600},
{"span_id":"span_7", "parent_id":None,"start_time":1000}
        ]
"""

from typing import List, Dict, Optional

def build_span_tree(spans: List[Dict]) -> List[Dict]:
    """
    Builds a list of tree structure traces from a list of spans.
    
    Args:
        spans: A list of dictionaries representing spans. 
               Each span must have 'span_id', 'parent_id', and 'start_time'.

    Returns:
        A list of root spans, where each span may have a 'children' key 
        containing a list of its child spans, sorted by start_time.
    """
    if not spans:
        return []

    # 1. Create a lookup map and initialize children for each span
    span_map = {}
    for span in spans:
        # Create a shallow copy to avoid mutating the original input dicts
        new_span = span.copy()
        new_span['children'] = []
        span_map[new_span['span_id']] = new_span

    roots = []

    # 2. Build the tree structure
    for span_id, span in span_map.items():
        parent_id = span.get('parent_id')
        
        if parent_id is None:
            # Root span
            roots.append(span)
        elif parent_id not in span_map:
            # Orphan span (treat as root)
            roots.append(span)
        else:
            # Child span
            parent = span_map[parent_id]
            parent['children'].append(span)

    # 3. Sort roots by start_time
    roots.sort(key=lambda x: x['start_time'])

    # 4. Process all spans to sort children and remove empty children lists
    for span in span_map.values():
        if span['children']:
            # Sort children by start_time
            span['children'].sort(key=lambda x: x['start_time'])
        else:
            # Remove 'children' key if empty to match the clean output format
            del span['children']

    return roots

if __name__ == "__main__":
    example_input = [
        {"span_id": "span_1", "parent_id": None, "start_time": 300},
        {"span_id": "span_2", "parent_id": "span_1", "start_time": 500},
        {"span_id": "span_3", "parent_id": "span_1", "start_time": 300},
        {"span_id": "span_4", "parent_id": "span_2", "start_time": 500},
        {"span_id": "span_5", "parent_id": "span_6", "start_time": 600},
        {"span_id": "span_7", "parent_id": None, "start_time": 1000}
    ]

    import json
    result = build_span_tree(example_input)
    print(json.dumps(result, indent=4))