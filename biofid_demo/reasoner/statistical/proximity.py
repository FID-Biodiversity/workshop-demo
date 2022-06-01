from dataclasses import dataclass
from functools import partial
from itertools import combinations, product
from typing import List, Tuple, Iterator

import numpy as np

from biofid_demo.reader import NamedEntity


@dataclass
class ProximityResult:
    """ Holds two NamedEntity objects and a value to express their proximity. """
    annotations: List[NamedEntity]
    proximity_rate: float

    def __hash__(self):
        sorted_frozen_annotations = tuple(sorted(self.annotations, key=lambda ann: ann.begin))
        return hash(sorted_frozen_annotations)


class ProximityReasoner:
    """ Evaluates the co-occurrence of NamedEntity objects by their proximity.
        Currently, it only applies a parameterizable Gamma distribution model
    """

    def __init__(self, mean: float = 0.0, sd: float = 200.0):
        self.mean = mean
        self.sd = sd

    def evaluate(self, named_entities: List[NamedEntity], comparison_named_entities: List[NamedEntity] = None
                 ) -> List[ProximityResult]:
        """ Calculates the proximity of NamedEntities in a text.
            If only `named_entities` is given, all entities within this list will be compared with each other.
            However, if both `named_entities` and `comparison_named_entities` is given, the entities between these
            two lists will be compares. There will be NO comparison within each list.
        """
        proximity_function = partial(calculate_normal_distribution, mean=self.mean, sd=self.sd)

        return [create_proximity_result(proximity_function, nes_to_compare)
                for nes_to_compare in get_combinations(named_entities, comparison_named_entities)]


def get_combinations(list1: list, list2: list) -> Iterator:
    if list1 is None or not list1:
        raise StopIteration()

    if list2 is not None and not list2:
        raise ValueError('The given comparison list is empty!')

    if list2 is None:
        return combinations(list1, 2)
    else:
        return product(list1, list2)


def create_proximity_result(proximity_func, named_entities: Tuple[NamedEntity]) -> ProximityResult:
    first_ne, second_ne = list(sorted(named_entities, key=lambda x: x.begin))
    named_entity_proximity = second_ne.begin - first_ne.end

    proximity_rate = proximity_func(named_entity_proximity)
    scaled_proximity_rate = proximity_rate * 500

    return ProximityResult(annotations=[first_ne, second_ne], proximity_rate=scaled_proximity_rate)


def calculate_normal_distribution(x, mean: float, sd: float):
    return 1 / (sd * np.sqrt(2 * np.pi)) * np.exp(- (x - mean) ** 2 / (2 * sd ** 2))
