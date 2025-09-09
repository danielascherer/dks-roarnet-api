from __future__ import annotations

import logging
import random
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from logging import getLogger
import time
from typing import Optional, Protocol, Self, TextIO, TypeVar, final

#from numpy import indices

from roar_net_api.operations import (
    SupportsApplyMove,
    SupportsConstructionNeighbourhood,
    SupportsCopySolution,
    SupportsEmptySolution,
    SupportsLocalNeighbourhood,
    SupportsLowerBound,
    SupportsLowerBoundIncrement,
    SupportsMoves,
    SupportsObjectiveValue,
    SupportsObjectiveValueIncrement,
    SupportsRandomMove,
    SupportsRandomMovesWithoutReplacement,
    #SupportsSubNeighbourhoods,
)


log = getLogger(__name__)

# ------------------------------ Solution --------------------------------------

@final
class Solution(SupportsCopySolution, 
               SupportsObjectiveValue, 
               SupportsLowerBound,
               ):
    def __init__(
            self, 
            problem: Problem, 
            used: list[int], 
            unused: list[int], 
            num_edges_in_used: int, 
            #num_missing_vertices: int, 
            num_neighbours_in_used: list[int], 
            lb: int,
    ):
        self.problem = problem
        self.used = used # set of used vertices 
        self.unused = unused # set of unused vertices
        #self.num_missing_vertices = num_missing_vertices # number of remaining vertices we still need to add to reach k
        self.num_edges_in_used = num_edges_in_used  # |E(S)|
        self.num_neighbours_in_used = num_neighbours_in_used  # neighbours of u already inside used (u \in unused)
        self.lb = lb # lower bound

    def __str__(self) -> str:
        '''
        Return the vertices in "used" as a space-separated string, sorted and converted to 1-based ids
        '''
        return " ".join(str(v+1) for v in sorted(self.used))

    
    def to_textio(self, f: TextIO) -> None:
        # According to the DKS solution format (output.mtx)
        k = self.problem.k
        f.write(f"{k}\n{self.num_edges_in_used}\n")
        f.write(str(self)) # print solution
        f.write("\n")

    

# ------------------------------ Moves ------------------------

'''@final
class AddMove(
    SupportsApplyMove[Solution], 
    SupportsLowerBoundIncrement[Solution],
    SupportsObjectiveValueIncrement[Solution],
    ):
    def _init__():
'''

# ------------------------------- Neighbourhood ------------------------------


# ------------------------------ Problem --------------------------------------

@final
class Problem(
    #SupportsLocalNeighbourhood[LocalNeighbourhood],
    SupportsEmptySolution[Solution],
):
    def __init__(self, n: int, edges: list[tuple[int, int]], k: int, name: str = "dks"):
        self.name = name
        self.n = n
        self.k = k
        # adjacency as 0..n-1
        adj = [set() for _ in range(n)] # list of n empty sets
        for u, v in edges:
            if u == v:
                continue
            # convert vertices from 1-based to 0-based indexing
            u -= 1
            v -= 1
            adj[u].add(v)
            adj[v].add(u)
        self.adj: list[set[int]] = adj

         


    @classmethod
    def from_textio(cls, f: TextIO, k: int | None = None, name: str = "dks") -> "Problem":
        # Skip initial comment lines (starting with %)
        def _next_data_line() -> str:
            while True:
                line = f.readline()
                if not line:
                    raise ValueError("unexpected EOF before header")
                s = line.strip()
                if s and not s.startswith("%"):
                    return s
        # get the header line
        header = _next_data_line()
        parts = header.split()
        k, n, _m = map(int, parts)        
    
        # Read edges (1-based ids)
        edges_1based: list[tuple[int, int]] = []
        for line in f:
            s = line.strip() # Removes whitespace from the line.
            if not s or s.startswith("%"):
                continue
            a, b = s.split()
            u, v = int(a), int(b)
            if u == v: # skip self-loops                
                continue            
            edges_1based.append((u, v))
    
        return cls(n=n, edges=edges_1based, k=k, name=name) #return a new instance of Problem




# ============================== Testing ===================================

if __name__ == "__main__":
    import roar_net_api.algorithms as alg
    logging.basicConfig(stream=sys.stderr, level="INFO", format="%(levelname)s;%(asctime)s;%(message)s")
    prob = Problem.from_textio(sys.stdin)     
        
    log.info(f"Instance: name={prob.name}, n={prob.n}, k={prob.k}")
    log.info(f"Adjacency: {prob.adj}")
    
    

    
    
    