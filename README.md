# Roar-Net Code Fest 2025 – Densest k-Subgraph Problem

This repository contains our implementation for the **Densest k-Subgraph (DkS) problem** using the [Roar-Net API](https://github.com/roar-net).  
It was developed during the **ROAR-NET Problem Modelling Code Fest** (9-11 September 2025).

---

## Problem Statement

The **Densest k-Subgraph (DkS)** problem can be described as follows:

> Given an undirected graph $G = (V,E)$ and an integer $k$, find a subset of exactly $k$ vertices that induces a subgraph with the maximum number of edges.

For a more detailed explanation about the problem, please check [`problem-statement/dks.md`](./problem-statement/dks.md).

---

## Repository Organization

```text
roar-net-api/
├── data/                     # Input graphs + output solutions
│
├── problem-statement/        # Problem definition
│   ├── dks.md                
│   └── images/               
│
├── src/                      # Implementation of the DkS model using Roar-Net API
│
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## How to Run

1. Clone this repository:
   ```bash
   git clone https://github.com/danielascherer/dks-roarnet-api.git
   cd roar-net-api/src
   ```
    
2. Install dependencies (requires Python ≥ 3.11):
    ```bash
    pip install -r requirements.txt
    ```
3. Run an example:
   ```bash
   python dks.py < ../data/input.mtx >> output.mtx
   ```
---

## Upper Bound on the Number of Edges

Given an undirected graph $G=(V,E)$, where $V$ is the set of vertices and $E$ is the set of edges, let $S=(V_S, E_S)$ be a subgraph of $G$, with $V_S \subseteq V$ and $E_S \subseteq E$.
Our implementation applies a degree-based upper bound calculated as follows. 

```math
ub = \frac{1}{2}\left(\sum_{v \in S} d_b(v) \;\;+\; \sum_{i=1}^{k - |V_S|} D_i\right)
```

where $d_b$ is a **bounded degree** calculated for each vertex $v \in V$ such that

```math
d_b(v) = 
\begin{cases} \min \Big( d_G(v)\,,\; d_S(v) \,+\, k \,-\, |V_S| \,-\, 1 \Big) & v \notin S \\ 
\min \Big( d_G(v)\,,\; d_S(v) \,+\, k \,-\, |V_S| \Big) & v \in S \end{cases}
```

Where:  
- $`d_G(v)=\lvert\{u \in V\,:\; \{u,v\} \in E\;\}\lvert`$, that is the degree of $v$ in the original graph $G$ 
- $`d_S(v)=\lvert\{u \in V_S\,:\; \{u,v\} \in E_S\;\}\lvert`$, that is the degree of $v$ w.r.t. the solution subgraph $S$.
- $|V_S|$ = number of vertices currently in $S$  
- $k$ = target subgraph size  


$D$ is the list of $d_b(v)$ with $v \notin S$. This list is sorted by non-increasing values.

The upper bound captures how many edges can still contribute to a solution of size $k$, considering both the original graph structure and the current partial solution $S$.

---

## Team 42

- Daniela Scherer dos Santos  
- Felipe Mota  
- João Moreira  
- Miguel Rabuge  

---

## License

This project is licensed under the CC-BY 4.0 license.

---

## Acknowledgements

This problem statement is based upon work from COST Action Randomised
Optimisation Algorithms Research Network (ROAR-NET), CA22137, is supported by
COST (European Cooperation in Science and Technology).

This work is funded by national funds through FCT – Foundation for Science and Technology, I.P., within the scope of the research unit UID/00326 - Centre for Informatics and Systems of the University of Coimbra.



