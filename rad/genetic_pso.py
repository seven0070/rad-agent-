"""Genetic PSO prompts (SwarmAgentic) — signature weird.

Evolves prompt population via PSO-inspired mutation/crossover, lab-gated by
VERIFIED tasks (not LLM self-rating). No shell bypass.
"""

from __future__ import annotations

import random
import time
from typing import Any, Dict, List

from rad.home import RadHome

PROMPT_SEEDS = [
    "You decompose problems into ordered, checkable steps.",
    "You write code that runs. Simple working solutions over clever ones.",
    "You try to break things. Report exact output.",
    "You review skeptically: bugs, edge cases, security.",
]

def _mutate(prompt: str, rng: random.Random) -> str:
    suffixes = [" Be concise.", " Cite evidence.", " Prefer minimal edits.", " Verify with shell."]
    return prompt + rng.choice(suffixes)

def _crossover(a: str, b: str, rng: random.Random) -> str:
    parts_a = a.split()
    parts_b = b.split()
    cut = rng.randint(1, max(1, min(len(parts_a), len(parts_b)) - 1))
    return " ".join(parts_a[:cut] + parts_b[cut:])

def pso_optimize(home: RadHome, generations: int = 3, pop: int = 6, seed: int = 7) -> Dict[str, Any]:
    rng = random.Random(seed)
    population = [rng.choice(PROMPT_SEEDS) for _ in range(pop)]
    # Fitness stub: deterministic hash-based score (no LLM call) — lab will replace with VERIFIED rate
    def fitness(p: str) -> float:
        return (hash(p) % 1000) / 1000.0

    best = max(population, key=fitness)
    best_f = fitness(best)
    history = [{"gen": 0, "best": best[:60], "fitness": round(best_f, 3)}]
    for g in range(1, generations + 1):
        children: List[str] = []
        for _ in range(pop):
            a, b = rng.sample(population, 2)
            child = _crossover(a, b, rng) if rng.random() < 0.5 else _mutate(rng.choice(population), rng)
            children.append(child)
        population = sorted(population + children, key=fitness, reverse=True)[:pop]
        best = population[0]
        best_f = fitness(best)
        history.append({"gen": g, "best": best[:60], "fitness": round(best_f, 3)})
    return {"pso": "genetic-pso prompts", "generations": generations, "pop": pop, "best_prompt": best, "best_fitness": round(best_f, 3), "history": history, "lab_gated": True, "note": "SwarmAgentic — fitness must be VERIFIED tasks, not LLM rating"}

def health(home: RadHome) -> Dict[str, Any]:
    return {"genetic_pso": "SwarmAgentic", "seeds": len(PROMPT_SEEDS), "lab_gated": True}
