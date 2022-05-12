import math
import random
from typing import TypeVar, Generic

from src.common.math import normalize_array
from src.modules.workbench.neural_network.network import NeuralNetwork

GenomeType = TypeVar('GenomeType')  # TypeVar('GenomeType', NeuralNetwork, OtherCrossover-ableClass)


class EvolutionConfig:
    def __init__(self,
                 elitism=0.,
                 crossover_segmentation=16,
                 crossover_chance=0.5,
                 mutation_chance=0.1,
                 mutation_scale=0.1):
        """
        Args:
            elitism: a factor between 0 and 1, representing the percentage of the best genomes to be copied to the next generation
            crossover_segmentation: the number of dna segments to split the genome into when performing crossover
            crossover_chance: the chance of passing other parent's dna segment into the child's dna (should be around 0.5 for even crossover)
            mutation_chance: the chance of performing mutation
            mutation_scale: the scale of the mutation
        """

        if crossover_segmentation < 2:
            raise ValueError("crossover_segmentation must be greater than 1")

        self.elitism = elitism
        self.crossover_segmentation = crossover_segmentation
        self.crossover_chance = crossover_chance
        self.mutation_chance = mutation_chance
        self.mutation_scale = mutation_scale


class Evolution(Generic[GenomeType]):
    class _Individual(Generic[GenomeType]):
        def __init__(self, species_id: int, genome: GenomeType):
            self.species_id = species_id
            self.genome = genome  # Object to crossover
            self.fitness = 0.0  # NOTE: This value is probably normalized across the population

    class _Species:
        def __init__(self):
            self.generation = 0  # Works as species age; #TODO: utilize this

    """ 
        TODO: species creation and removal chances; 
        creating species by splitting existing species in two; 
        removing species by either merging two species (tricky) or by killing all individuals in a species
    """

    def __init__(self, genomes: list[GenomeType], evolution_config: EvolutionConfig):
        if len(genomes) < 2:
            raise ValueError("There must be at least 2 genomes to evolve")
        self.__genomes_type = type(genomes[0])
        self.__config = evolution_config
        self.__generation = 0
        self.__best_score = 0.0
        self.__average_score = 0.0

        self.__species_counter = 0
        self.__species: dict[int, Evolution._Species] = {
            self.__species_counter: Evolution._Species()
        }
        self.__individuals: list[Evolution._Individual[GenomeType]] = list(
            map(lambda genome: Evolution._Individual[GenomeType](self.__species_counter, genome), genomes))

        self.__species_counter += 1

        # Initialize first species
        # self.__add_species(genomes)

    # def __add_species(self, genomes: list[GenomeType]):
    #     self.__species[self.__species_counter] = Evolution._Species()
    #
    #     species_population = list(
    #         map(lambda genome: Evolution._Individual[GenomeType](self.__species_counter, genome), genomes))
    #     self.individuals.extend(species_population)
    #
    #     self.__species_counter += 1

    @property
    def individuals(self):
        return self.__individuals

    @property
    def population_size(self):
        return len(self.__individuals)

    # @property
    # def generation(self):
    #     return self.__generation

    def print_stats(self):
        # TODO: population of each species
        print(f'''--- EVOLUTION STATISTICS ---
            Generation: {self.__generation}
            Best score: {self.__best_score}
            Average score: {self.__average_score}
            Number of species: {len(self.__species)}
        ''')

    @staticmethod
    def __distribution(max_value: float):
        value = abs(random.gauss(0, 0.4))
        while value > max_value:
            value = abs(random.gauss(0, 0.4))
        return value

    def __crossover(self, parent_a: _Individual[GenomeType], parent_b: _Individual[GenomeType]):
        if parent_a.species_id != parent_b.species_id:
            raise ValueError("Cannot crossover individuals from different species")

        if self.__genomes_type == NeuralNetwork:
            network_a: NeuralNetwork = parent_a.genome
            network_b: NeuralNetwork = parent_b.genome

            if not NeuralNetwork.compare_structure(network_a, network_b):
                raise ValueError("Cannot crossover networks with different structure")

            layers_structure = list(map(lambda layer: len(layer), network_a.get_layers()))
            evolved_genome = NeuralNetwork(layers_structure, randomize_weights=False)

            weights_a = network_a.get_weights()
            weights_b = network_b.get_weights()

            evolved_weights: list[float] = []

            # Randomly split weights array into n segments where n is self.__config.crossover_segmentation
            weights_count = len(weights_a)
            segment_sizes = list(map(lambda _: int(random.random() * weights_count),
                                     range(self.__config.crossover_segmentation - 1)
                                     ))
            segment_sizes.extend((0, weights_count))
            segment_sizes = list(dict.fromkeys(segment_sizes))
            segment_sizes.sort()
            # print(weights_count, segment_sizes)

            for i in range(len(segment_sizes) - 1):
                index_start: int = segment_sizes[i]
                index_end: int = segment_sizes[i + 1]

                parent_weights = weights_a if random.random() < self.__config.crossover_chance else weights_b
                segment = parent_weights[index_start:index_end]
                # print(len(segment))

                # Mutation
                for j in range(len(segment)):
                    if random.random() < self.__config.mutation_chance:
                        segment[j] += random.uniform(-self.__config.mutation_scale, self.__config.mutation_scale)
                evolved_weights.extend(segment)

            evolved_genome.set_weights(evolved_weights)

        else:
            raise ValueError("Unsupported genome type. Cannot crossover.")

        child = Evolution._Individual[GenomeType](species_id=parent_a.species_id, genome=evolved_genome)

        # Estimate child fitness by averaging both parent fitness values (this is mostly for debugging purposes)
        child.fitness = (parent_a.fitness + parent_b.fitness) / 2.0
        return child

    def __crossover_species(self, species_individuals: list[tuple[_Individual[GenomeType], int]]):
        """
        Crossover individuals in a species

        Args:
            species_individuals: sorted by fitness list of _Individual objects of same species

        Returns:
            List of evolved individuals within given species into new generation
        """
        species_size = len(species_individuals)
        elite_count = math.ceil(species_size * self.__config.elitism)

        new_species_generation: list[tuple[Evolution._Individual[GenomeType], int]] = species_individuals[:elite_count]

        def get_partner_index():
            distribution_value = self.__distribution(0.999999)
            return math.floor(distribution_value * len(species_individuals))

        for i in range(elite_count, species_size):
            individual, index = species_individuals[i]

            other_parent_index = get_partner_index()
            while other_parent_index >= len(species_individuals) or other_parent_index == index:
                other_parent_index = get_partner_index()

            child = self.__crossover(individual, species_individuals[other_parent_index][0])
            new_species_generation.append((child, index))

        return new_species_generation

    def evolve(self, scores: list[float]):
        if len(scores) != self.population_size:
            raise ValueError("Scores size does not match population size")

        self.__best_score = max(scores)
        self.__average_score = sum(scores) / len(scores)
        scores = normalize_array(scores)

        # Assign scores to individuals
        for i, individual in enumerate(self.individuals):
            # TODO: store fitness values of parents for better overall fitness calculation during crossover;
            #  parent fitness values can be averaged with linear weights for better selection;
            #  individuals with little score in current generation can still carry good genes from ancestors therefore
            #  those individuals with more successful ancestors should be more likely to be selected
            individual.fitness = scores[i]

        # Sort individuals by fitness
        self.individuals.sort(key=lambda individual_: individual_.fitness, reverse=True)

        # Keys are species id; values are list of _Individual and its original index pairs
        species_groups: dict[int, list[tuple[Evolution._Individual[GenomeType], int]]] = {}
        for i, individual in enumerate(self.individuals):
            species_id = individual.species_id
            if species_id not in species_groups:
                species_groups[species_id] = []
            species_groups[species_id].append((individual, i))

        evolved_individuals: list[tuple[Evolution._Individual[GenomeType], int]] = []

        # Evolve each species
        for species_group in species_groups.values():
            new_generation = self.__crossover_species(species_group)
            evolved_individuals.extend(new_generation)

        # Update generation with newly evolved individuals
        if len(evolved_individuals) != self.population_size:
            raise ValueError(
                "Evolved individuals size does not match population size. There must have been a problem with crossover")
        for evolved, index in evolved_individuals:
            self.individuals[index] = evolved

        for species_id in self.__species:
            self.__species[species_id].generation += 1
        self.__generation += 1
