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
            curr_degree: int,
    ):
        self.problem = problem
        self.used    = used   # set of used vertices 
        self.unused  = unused # set of unused vertices
        self.lb      = lb     # lower bound
        self.curr_degree = curr_degree

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
        return self.__class__(self.problem, self.used.copy(), self.unused.copy(), self.lb, self.curr_degree)

    def objective_value(self) -> Optional[int]:
        if self.is_feasible:
            obj = 0
            for u in self.used:
                for v in self.used:
                    if u[0] in self.problem.adj[v[0]]:
                        obj += 1
            return - obj // 2
        return None

    def lower_bound(self) -> int:
        return self.lb


# ------------------------------ Moves ------------------------
@final
class AddMove(SupportsApplyMove[Solution], SupportsLowerBoundIncrement[Solution]):
    def __init__(self, neighbourhood: AddNeighbourhood, v: tuple[int, int]):
        self.neighbourhood = neighbourhood
        self.v = v 

    def __str__(self) -> str:
        return str(self.v)

    def apply_move(self, solution: Solution) -> Solution:
        solution.lb += self.lower_bound_increment(solution)
        solution.curr_degree += len(solution.problem.adj[self.v[0]])
        solution.used.add(self.v)
        solution.unused.remove(self.v)
        return solution

    def lower_bound_increment(self, solution: Solution) -> float:
        lb = 0
        best_k = solution.unused[:(solution.problem.k - len(solution.used))]

        if not self.v in best_k:
            best_k = best_k[:-1]
            lb += self.v[1]
        else:
            lb += sum([u[1] for u in best_k])
        lb += solution.curr_degree 

        return (lb/2) - solution.lb 
        return solution.lb - (lb/2)


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
    
        # Read edges (1-based ids)    solution = alg.beam_search(prob)
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
        degrees = [(i, min(len(self.adj[i]), self.k-1)) for i in range(len(self.adj))]
        degrees.sort(key=lambda i: i[1], reverse=True)

        return Solution(self, used=set(), unused=degrees, lb=-sum([u[1] for u in degrees[:self.k]]) / 2, curr_degree=0)

    # def random_solution(self) -> Solution:
    #     lb = 0
    #     c = list(range(self.n))
    #     random.shuffle(c)
    #     used = c[:self.k]
    #     unused = c[self.k:]

    #     for u in used:
    #         for v in used:
    #             if u in self.adj[v]:
    #                 lb += 1
    #     print("lb: ", -lb//2)
    #     return Solution(self, used=used, unused=unused, lb=-lb//2, curr_degree=self.k)


# ============================== Testing ===================================
if __name__ == "__main__":
    import roar_net_api.algorithms as alg
    logging.basicConfig(stream=sys.stderr, level="INFO", format="%(levelname)s;%(asctime)s;%(message)s")

    prob = Problem.from_textio(sys.stdin)     
        
    log.info(f"Instance: name={prob.name}, n={prob.n}, k={prob.k}")
    log.info(f"Adjacency: {prob.adj}")

    # sol = prob.empty_solution()
    # print(sol.lb)
    
    print("\nRunning GREEDY...\n")
    solution = alg.greedy_construction(prob)
    log.info(f"Objective value after constructive search: {-solution.objective_value()}")

    print("\nRunning BEAM search...\n")
    solution = alg.beam_search(prob)
    # print(solution)
    log.info(f"Objective value after constructive search: {-solution.objective_value()}")

    print("\nRunning GRASP...\n")
    solution = alg.grasp(prob, 10)
    # print(solution)
    log.info(f"Objective value after constructive search: {-solution.objective_value()}")


    # s = prob.empty_solution()
    # print(s)

    # neigh = prob.construction_neighbourhood()
    # for n in neigh.moves(s):
    #     print(n)
    
    

    
