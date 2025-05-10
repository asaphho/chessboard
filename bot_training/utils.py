import random
from typing import Dict, List, Tuple


def breed(config1: Dict[int, float], config2: Dict[int, float]) -> Dict[int, float]:
    offspring: Dict[int, float] = {}
    for i in config1:
        parent = random.choice([1, 2])
        if parent == 1:
            offspring[i] = config1[i]
        else:
            offspring[i] = config2.get(i, 0)
    return offspring


def mutate(config: Dict[int, float], mutation_prob: float, mutation_strength: float) -> Dict[int, float]:
    new_config: Dict[int, float] = {}
    for i in config:
        if random.random() < mutation_prob:
            new_config[i] = config[i] + random.gauss(0, mutation_strength)
        else:
            new_config[i] = config[i]
    return new_config


def breed_offspring_from_pool(parents: List[Dict[int, float]], n_offspring: int, mutation_prob: float,
                              mutation_strength: float) -> List[Dict[int, float]]:
    offsprings: List[Dict[int, float]] = []
    pairings: List[Tuple[int, int]] = []
    for i in range(len(parents) - 1):
        for j in range(i + 1, len(parents)):
            pairings.append((i, j))
    selected_pairings: List[Tuple[int, int]] = random.sample(pairings, min(n_offspring, len(pairings)))
    for pairing in selected_pairings:
        parent1 = parents[pairing[0]]
        parent2 = parents[pairing[1]]
        offspring = mutate(breed(parent1, parent2), mutation_prob=mutation_prob, mutation_strength=mutation_strength)
        offsprings.append(offspring)
    return offsprings
