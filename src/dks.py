from __future__ import annotations

import logging
import random
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from logging import getLogger
import time
from typing import Optional, Protocol, Self, TextIO, TypeVar, final


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
            used: set[int], 
            unused: set[int], 
            lb: int,
            inner_degree: list[int], 
            outter_degree: list[int],
    ):
        self.problem = problem
        self.used    = used # set of used vertices 
        self.unused  = unused # set of unused vertices
        self.lb      = lb # lower bound
        self.inner_degree = inner_degree
        self.outter_degree = outter_degree

    def __str__(self) -> str:
        '''
        Return the vertices in "used" as a space-separated string, sorted and converted to 1-based ids
        '''
        return "used: " + " ".join(str(v) for v in sorted(self.used)) + "\nunused: " + " ".join(str(v) for v in sorted(self.unused))
    
    def to_textio(self, f: TextIO) -> None:
        k = self.problem.k
        f.write(f"{k}\n{self.num_edges_in_used}\n")
        f.write(str(self))
        f.write("\n")

    @property
    def is_feasible(self) -> bool:
        return len(self.used) == self.problem.k

    def copy_solution(self) -> Self:
        return self.__class__(self.problem, self.used.copy(), self.unused.copy(), self.lb, self.inner_degree.copy(), self.outter_degree.copy())

    def objective_value(self) -> Optional[int]:
        if self.is_feasible:
            return self.lb
        return None

    def lower_bound(self) -> int:
        return self.lb


# ------------------------------ Moves ------------------------
@final
class AddMove(SupportsApplyMove[Solution], SupportsLowerBoundIncrement[Solution]):
    def __init__(self, neighbourhood: AddNeighbourhood, v: int):
        self.neighbourhood = neighbourhood
        self.v = v 

    def __str__(self) -> str:
        return str(self.v)

    def apply_move(self, solution: Solution) -> Solution:
        solution.lb += self.lower_bound_increment(solution)
        solution.used.add(self.v)
        solution.unused.remove(self.v)
        return solution

    def _degree_of_used_vertex(self, w, used, solution):
        Gi = 0
        for u in used:
            if u in solution.problem.adj[w]:
                Gi += 1
        Ge = len(solution.problem.adj[w]) - Gi
        k = solution.problem.k
        j = len(solution.used)
        return (min(Ge, k-j) + Gi)

    def _degree_of_unused_vertex(self, w, used, solution):
        Gi = 0
        for u in used:
            if u in solution.problem.adj[w]:
                Gi += 1
        Ge = len(solution.problem.adj[w]) - Gi
        k = solution.problem.k
        j = len(solution.used)
        return (min(Ge, k-j-1) + Gi)

    def lower_bound_increment(self, solution: Solution) -> float:

        used   = list(solution.used)
        used.append(self.v)
        unused = list(solution.unused)
        unused.remove(self.v)

        lb = 0
        for u in used:
            lb += self._degree_of_used_vertex(u, used, solution)

        aux = []
        for u in unused:
            aux.append(self._degree_of_unused_vertex(u, used, solution))

        aux.sort(reverse=True)
        total = solution.problem.k - len(used) # - 1
        # return (-solution.lb - ((sum(aux[:total]) + lb) // 2))
        return (sum(aux[:total]) + lb) // 2 - (-solution.lb)
            
            
        # Gi = 0
        # for u in solution.used:
        #     if u in solution.problem.adj[self.v]:
        #         Gi += 1
        # Ge = solution.outter_degree[self.v] - Gi
        # k = solution.problem.k
        # j = len(solution.used)
        # return (min(Ge, k-j-1) + Gi) // 2


# ------------------------------- Neighbourhood ------------------------------
@final
class AddNeighbourhood(SupportsMoves[Solution, AddMove]):
    def __init__(self, problem: Problem):
        self.problem = problem

    def moves(self, solution: Solution) -> Iterable[AddMove]:
        if len(solution.used) < self.problem.k:
            for i in solution.unused:
                yield AddMove(self, i)


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
        self.c_nbhood: Optional[AddNeighbourhood] = None

        adj = [set() for _ in range(n)]   # adjacency list
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
            s = line.strip()   # Removes whitespace from the line.
            if not s or s.startswith("%"):
                continue
            a, b = s.split()
            u, v = int(a), int(b)
            if u == v:         # skip self-loops                
                continue            
            edges_1based.append((u, v))
    
        return cls(n=n, edges=edges_1based, k=k, name=name)   # return a new instance of Problem

    def construction_neighbourhood(self) -> AddNeighbourhood:
        if self.c_nbhood is None:
            self.c_nbhood = AddNeighbourhood(self)
        return self.c_nbhood

    def empty_solution(self) -> Solution:
        outter_degree = [min(len(self.adj[i]), self.k-1) for i in range(len(self.adj))]
        inner_degree = [0 for _ in range(len(self.adj))]

        aux = list(outter_degree)
        aux.sort(reverse=True)
        lb = sum(aux[:self.k]) // 2

        return Solution(self, used=set(), unused=set(range(self.n)), lb=-lb, inner_degree=inner_degree, outter_degree=outter_degree)



# ============================== Testing ===================================
if __name__ == "__main__":
    import roar_net_api.algorithms as alg
    logging.basicConfig(stream=sys.stderr, level="INFO", format="%(levelname)s;%(asctime)s;%(message)s")

    prob = Problem.from_textio(sys.stdin)     
        
    # log.info(f"Instance: name={prob.name}, n={prob.n}, k={prob.k}")
    # log.info(f"Adjacency: {prob.adj}")

    
    print("\nRunning GREEDY...\n")
    solution = alg.greedy_construction(prob)
    log.info(f"Objective value after constructive search: {-solution.objective_value()}")

    print("\nRunning BEAM search...\n")
    solution = alg.beam_search(prob)
    log.info(f"Objective value after constructive search: {-solution.objective_value()}")

    print("\nRunning GRASP...\n")
    solution = alg.grasp(prob, 10)
    log.info(f"Objective value after constructive search: {-solution.objective_value()}")
