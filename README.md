# CompSocialScience_Erasmus

This project analyzes Erasmus+ KA2 mobility data, creating network graphs to study student exchange patterns across European countries.

## KA2 Graphs Structure

The KA2 graphs are stored as JSON files in [`data/ka2_graphs/`](data/ka2_graphs/) and represent directed networks of Erasmus+ mobility flows:

- **Nodes**: Countries, each with attributes:
  - `language_family`: Comma-separated list of language family IDs (e.g., "1,3,4"). More info in [this file](data/languages.txt)
  - `economic_family`: Economic classification. More info in [this file](data/economy.txt) 
  
    - "Advanced_Economy", 
    - "Emerging_Market", 
    - "Developing_Economy"
  - `geographical_cultural_region`: Regional classification. More info in [this file](data/geographical_cultural.txt)
    - West
    - North
    - Central/Eastern
    - South
    - Other 
  - `lat`, `lon`: Geographic coordinates

- **Edges**: Directed flows from sending to receiving countries with:
  - `weight`: Number of participants in the mobility flow
  - `metadata`: Aggregated details about the exchanges (sending/receiving organizations, activity types, special needs info)

  examples node: 
  ```json
    'LI - Liechtenstein':
        {'language_family': '1,3',
         'economic_family': 'Advanced_Economy',
          'geographical_cultural_region': 'West', 
          'lat': 47.166, 
          'lon': 9.5554
        }
          
    ```
    examples edge: Edge from LI - Liechtenstein to NL - Netherlands:
    ```json
     {'weight': 1, 
     'metadata': 
        {'sender_org': 
            {'istituto statale di istruzione secondaria superiore "p.gobetti a.volta"': 1}, 
        'receiver_org': 
            {"'t atrium": 1},
        'start_months': 
            {2: 1}, 
        'activity': 
            {'Short-term exchanges of groups of pupils': 1},
        'special_needs': {'N': 1},
        'fewer_opportunities': {'N': 1}, 
        'disadvantaged_background': {'N': 1}
        }
    }
  ```

- **Files**: One graph per year (2014-2023) plus an aggregated `ka2_mobility_network_all.json`

## Loading KA2 Graphs

Load graphs using NetworkX and the json_graph utility:

```python
import networkx as nx
from networkx.readwrite import json_graph
import json

year = 2014
with open(f'../data/ka2_graphs/ka2_mobility_network_{year}.json', 'r') as f:
        data = json.load(f)
        G = json_graph.node_link_graph(data)
```

## Language Similarity

Language similarity quantifies how many language families two countries share:

- **Score 0**: No language families in common
- **Score 1**: Some (but not all) language families in common
- **Score 2**: All language families in common (identical language profiles)

Each country's `language_family` attribute contains IDs (1-14) representing different language families. The similarity is computed by comparing these sets.

## Data Files

- `country_extra_data.csv`: Country attributes (language, economic, geographical data)
- `languages.txt`, `economy.txt`, `geographical_cultural.txt`: Reference mappings for attribute IDs

## Scripts

- `creating_nets.ipynb`: Network creation from raw data
- `language_similarity_ex.ipynb`: Language similarity examples