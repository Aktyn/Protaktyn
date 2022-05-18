import json
import math
import random
from typing import TypeVar, Generic, Iterable

from src.common.math import normalize_array, mix, linearly_weighted_average
from src.modules.workbench.neural_network.network import NeuralNetwork

GenomeType = TypeVar('GenomeType')  # TypeVar('GenomeType', NeuralNetwork, OtherCrossover-ableClass)


class EvolutionConfig:
    def __init__(self,
                 elitism=0.,
                 crossover_segmentation=16,
                 crossover_chance=0.5,
                 mutation_chance=0.1,
                 mutation_scale=0.1,
                 species_maturation_generations=32,
                 maximum_species=16,
                 species_creation_chance=0.05,
                 species_extinction_chance=0.05
                 ):
        """
        Args:
            elitism: a factor between 0 and 1, representing the percentage of the best genomes to be copied to the next generation
            crossover_segmentation: the number of dna segments to split the genome into when performing crossover
            crossover_chance: the chance of passing other parent's dna segment into the child's dna (should be around 0.5 for even crossover)
            mutation_chance: the chance of performing mutation
            mutation_scale: the scale of the mutation
            species_maturation_generations: minimum number of generations a species must achieve before it can be considered mature enough to extinct
            maximum_species: maximum number of species that can exist at the same time
            species_creation_chance: chance of splitting biggest species into two smaller ones during evolution process
            species_extinction_chance: chance of extinction of the worst fitting species
        """

        if crossover_segmentation < 2:
            raise ValueError("crossover_segmentation must be greater than 1")

        self.elitism = elitism
        self.crossover_segmentation = crossover_segmentation
        self.crossover_chance = crossover_chance
        self.mutation_chance = mutation_chance
        self.mutation_scale = mutation_scale
        self.species_maturation_generations = species_maturation_generations
        self.maximum_species = maximum_species
        self.species_creation_chance = species_creation_chance
        self.species_extinction_chance = species_extinction_chance

    def to_dict(self):
        return {
            "elitism": self.elitism,
            "crossover_segmentation": self.crossover_segmentation,
            "crossover_chance": self.crossover_chance,
            "mutation_chance": self.mutation_chance,
            "mutation_scale": self.mutation_scale,
            "species_maturation_generations": self.species_maturation_generations,
            "maximum_species": self.maximum_species,
            "species_creation_chance": self.species_creation_chance,
            "species_extinction_chance": self.species_extinction_chance
        }


class Evolution(Generic[GenomeType]):
    _FITNESS_HISTORY_SIZE = 4
    _ANCESTOR_FITNESS_SCALE = 0.125  # TODO: move it to EvolutionConfig

    class _Individual(Generic[GenomeType]):
        def __init__(self, species_id: int, genome: GenomeType):
            self.species_id = species_id
            self.genome = genome  # Object to crossover
            self.__fitness = 0.0  # NOTE: This value is probably normalized across the population
            self.__computed_overall_fitness = 0.0
            self.ancestors_fitness: list[float] = []

        @property
        def fitness(self):
            return self.__fitness

        @fitness.setter
        def fitness(self, value: float):
            self.__fitness = value
            self.__update_overall_fitness()

        @property
        def overall_fitness(self) -> float:
            """
            Note that returned value may be larger than 1 since ancestors fitness values are added to current fitness
            Returns:
                Fitness value calculated according to ancestors fitness values and current fitness
            """
            return self.__computed_overall_fitness

        def to_dict(self):
            if type(self.genome) == NeuralNetwork:
                genome_dict = self.genome.to_dict()
            else:
                genome_dict = None

            return {
                "species_id": self.species_id,
                "genome": genome_dict,
                "fitness": self.__fitness,
                "ancestors_fitness": self.ancestors_fitness
            }

        def __update_overall_fitness(self):
            self.__computed_overall_fitness = self.__fitness + \
                                              linearly_weighted_average(
                                                  self.ancestors_fitness, reverse=True
                                              ) * Evolution._ANCESTOR_FITNESS_SCALE

        def crossover_fitness(self, parent_a: 'Evolution._Individual', parent_b: 'Evolution._Individual',
                              crossover_chance: float):
            parents_average_fitness = mix(parent_a.fitness, parent_b.fitness, crossover_chance)
            self.fitness = parents_average_fitness
            self.ancestors_fitness = [parents_average_fitness]

            for i in range(max(len(parent_a.ancestors_fitness), len(parent_b.ancestors_fitness))):
                if len(self.ancestors_fitness) >= Evolution._FITNESS_HISTORY_SIZE:
                    break

                parent_a_fitness = parent_a.ancestors_fitness[i] if i < len(parent_a.ancestors_fitness) else None
                parent_b_fitness = parent_b.ancestors_fitness[i] if i < len(parent_b.ancestors_fitness) else None

                if parent_a_fitness is not None and parent_b_fitness is not None:
                    self.ancestors_fitness.append(mix(parent_a_fitness, parent_b_fitness, crossover_chance))
                elif parent_a_fitness is not None:
                    self.ancestors_fitness.append(parent_a_fitness)
                elif parent_b_fitness is not None:
                    self.ancestors_fitness.append(parent_b_fitness)

            self.__update_overall_fitness()

    class _Species:
        def __init__(self, species_id: int, population_size: int):
            self.__id = species_id
            self.population_size = population_size
            self.generation = 0  # Works as species age. Only mature enough species can extinct.

        @property
        def id(self):
            return self.__id

        def to_dict(self):
            return {
                'id': self.__id,
                'population_size': self.population_size,
                'generation': self.generation
            }

    def __init__(self, genomes: list[GenomeType], evolution_config: EvolutionConfig):
        if len(genomes) < 2:
            raise ValueError("There must be at least 2 genomes to evolve")
        self.__genomes_type = type(genomes[0])
        self.__config = evolution_config
        self.__generation = 0
        self.__best_generation_score = 0.0
        self.__average_generation_score = 0.0

        self.__species_counter = 0
        self.__species: dict[int, Evolution._Species] = {
            self.__species_counter: Evolution._Species(self.__species_counter, len(genomes))
        }
        self.__individuals: list[Evolution._Individual[GenomeType]] = list(
            map(lambda genome: Evolution._Individual[GenomeType](self.__species_counter, genome), genomes))

        if self.__minimum_species_population < 2:
            raise ValueError("There must be at least 2 individuals in a minimum species. Adjust EvolutionConfig.")

        self.__species_counter += 1

    def __create_species(self):
        species_able_to_split = list(
            filter(lambda s: s.population_size >= self.__minimum_species_population * 2, self.__species.values())
        )

        # Skip species creation if there are no species population large enough to split
        if len(species_able_to_split) == 0:
            return

        chosen_species = random.choice(species_able_to_split)
        chosen_species_individuals = list(
            filter(lambda individual: individual.species_id == chosen_species.id, self.__individuals)
        )
        random.shuffle(chosen_species_individuals)

        if len(chosen_species_individuals) != chosen_species.population_size:
            raise ValueError("Chosen species population size does not match number of individuals with that species id")

        new_species_population_count = random.choice(range(
            self.__minimum_species_population,
            chosen_species.population_size - self.__minimum_species_population + 1
        ))
        chosen_species_individuals = chosen_species_individuals[:new_species_population_count]

        # Increase original species population size
        chosen_species.population_size -= len(chosen_species_individuals)

        # Create new species with chosen individuals
        self.__species[self.__species_counter] = Evolution._Species(
            self.__species_counter, len(chosen_species_individuals)
        )

        self.__mutate_genome_structure(map(lambda individual: individual.genome, chosen_species_individuals))
        for chosen_individual in chosen_species_individuals:
            chosen_individual.species_id = self.__species_counter

        print(
            f"Created species {self.__species[self.__species_counter].id} with {self.__species[self.__species_counter].population_size} individuals\n\tparent species id: {chosen_species.id}")
        self.__species_counter += 1

    def __estimate_species_fitness(self, species_id: int):
        species_individuals = filter(lambda individual_: individual_.species_id == species_id, self.__individuals)

        overall_fitness_values: list[float] = list(
            map(lambda individual_: individual_.overall_fitness, species_individuals))
        overall_fitness_values.sort()

        return linearly_weighted_average(overall_fitness_values)

    def __extinct_least_fitted_species(self):
        if len(self.__species) < 2:
            return

        mature_species = list(
            filter(lambda s: s.generation >= self.__config.species_maturation_generations, self.__species.values()))

        # Do not remove species if there are no enough mature species to compare. This is to prevent the best species extinction.
        if len(mature_species) < 2:
            return

        least_fitted_mature_species = min(mature_species, key=lambda s: self.__estimate_species_fitness(s.id))

        self.__species.pop(least_fitted_mature_species.id)

        extinct_species_individuals_indexes = list(filter(
            lambda i_i: self.__individuals[i_i].species_id == least_fitted_mature_species.id,
            range(len(self.__individuals))
        ))

        # Extend remaining species populations to fill loss after extincted species
        species_groups = self.get_population_grouped_by_species(only_existing_species=True)
        species_group_indexes = list(species_groups.keys())
        species_group_i = 0
        while len(extinct_species_individuals_indexes) > 0:
            species_individuals = species_groups[species_group_indexes[species_group_i]]

            species_individuals.sort(key=lambda individual_: individual_.overall_fitness, reverse=True)
            species_normalized_fitness_array = normalize_array(
                list(map(lambda individual: individual.overall_fitness, species_individuals))
            )

            def get_parent_index():
                distribution_value = 1.0 - self.__distribution(1)

                j = 0
                for fitness in species_normalized_fitness_array[1:]:
                    if fitness < distribution_value:
                        break
                    j += 1
                return j

            parent_a_index = get_parent_index()

            parent_b_index = get_parent_index()
            while parent_b_index >= len(species_individuals) or parent_b_index == parent_a_index:
                parent_b_index = get_parent_index()

            new_individual = self.__crossover(species_individuals[parent_a_index], species_individuals[parent_b_index])

            individual_id = extinct_species_individuals_indexes.pop()
            self.__individuals[individual_id] = new_individual
            self.__species[new_individual.species_id].population_size += 1

            species_group_i = (species_group_i + 1) % len(species_group_indexes)

        print(
            f"Extincted least fitted species with id {least_fitted_mature_species.id} and population size {least_fitted_mature_species.population_size}")

    @property
    def individuals(self):
        return self.__individuals

    @property
    def population_size(self):
        return len(self.__individuals)

    @property
    def generation(self):
        return self.__generation

    @property
    def __minimum_species_population(self):
        return max(2, self.population_size // self.__config.maximum_species)

    def get_population_grouped_by_species(self, only_existing_species=False):
        # Keys are species id; values are list of _Individual and its original index pairs
        groups: dict[int, list[Evolution._Individual[GenomeType]]] = {}
        for individual in self.individuals:
            species_id = individual.species_id
            if only_existing_species and species_id not in self.__species:
                continue
            if species_id not in groups:
                groups[species_id] = []
            groups[species_id].append(individual)
        return groups

    def print_stats(self):
        species_groups = self.get_population_grouped_by_species()

        newline = '\n'
        tab = '\t'
        print(f'''--- EVOLUTION STATISTICS ---
Generation: {self.__generation}
Best score: {self.__best_generation_score}
Average score: {self.__average_generation_score}
Species ({len(self.__species)}):
{f'{newline}'.join(list(map(lambda species_id: f'{tab}id: {species_id}; generation: {self.__species[species_id].generation}; population: {self.__species[species_id].population_size}', sorted(species_groups.keys()))))}
        ''')

    def save_to_file(self, file_path: str):
        data = {
            'genomes_type': self.__genomes_type.__name__,
            'config': self.__config.to_dict(),
            'generation': self.__generation,
            'best_generation_score': self.__best_generation_score,
            'average_generation_score': self.__average_generation_score,
            'species_counter': self.__species_counter,
            'species': [species.to_dict() for species in self.__species.values()],
            'individuals': [individual.to_dict() for individual in self.__individuals],
        }

        f = open(file_path, "w")
        f.write(json.dumps(data, indent=2))
        f.close()

    def save_genome_to_file(self, file_path: str, individual_id: int):
        f = open(file_path, "w")
        f.write(json.dumps(self.__individuals[individual_id].to_dict()['genome'], indent=2))
        f.close()

    def load_from_file(self, file_path: str):
        print(f"Loading evolution state from {file_path}")
        f = open(file_path, "r")
        data = json.load(f)
        f.close()

        self.__config = EvolutionConfig(
            elitism=data['config']['elitism'],
            crossover_segmentation=data['config']['crossover_segmentation'],
            crossover_chance=data['config']['crossover_chance'],
            mutation_chance=data['config']['mutation_chance'],
            mutation_scale=data['config']['mutation_scale'],
            species_maturation_generations=data['config']['species_maturation_generations'],
            maximum_species=data['config']['maximum_species'],
            species_creation_chance=data['config']['species_creation_chance'],
            species_extinction_chance=data['config']['species_extinction_chance']
        )
        self.__generation = data['generation']
        self.__best_generation_score = data['best_generation_score']
        self.__average_generation_score = data['average_generation_score']
        self.__species_counter = data['species_counter']
        self.__species = {}
        for species_data in data['species']:
            species = Evolution._Species(
                species_id=species_data['id'],
                population_size=species_data['population_size']
            )
            species.generation = species_data['generation']
            self.__species[species.id] = species

        self.__individuals = []
        if data['genomes_type'] == 'NeuralNetwork':
            self.__genomes_type = NeuralNetwork
            for individual_data in data['individuals']:
                genome = NeuralNetwork.from_dict(individual_data['genome'])

                individual = Evolution._Individual(
                    species_id=individual_data['species_id'],
                    genome=genome,
                )
                # Fitness must be set after ancestors_fitness to trigger overall_fitness update
                individual.ancestors_fitness = individual_data['ancestors_fitness']
                individual.fitness = individual_data['fitness']

                self.__individuals.append(individual)

    @staticmethod
    def __distribution(max_value: float):
        value = abs(random.gauss(0, 0.4))
        while value > max_value:
            value = abs(random.gauss(0, 0.4))
        return value

    def __mutate_genome_structure(self, genomes__: Iterable[GenomeType]):
        if self.__genomes_type == NeuralNetwork:
            networks: list[NeuralNetwork] = list(genomes__)
            blueprint = networks[0]

            minimum_hidden_layers = 1
            maximum_hidden_layers = 8
            structure_mutation_add_layer_chance = 0.1
            structure_mutation_remove_layer_chance = 0.05
            structure_mutation_add_neuron_chance = 0.2
            structure_mutation_remove_neuron_chance = 0.2
            structure_mutation_add_connection_chance = 0.3
            structure_mutation_remove_connection_chance = 0.3

            changes = 0

            def get_random_connection():
                to_layer_index = random.choice(range(1, len(blueprint.layers)))
                to_neuron_index = random.choice(range(len(blueprint.layers[to_layer_index])))
                from_layer_index = random.choice(range(0, to_layer_index))
                from_neuron_index = random.choice(range(len(blueprint.layers[from_layer_index])))

                return (from_layer_index, from_neuron_index), (to_layer_index, to_neuron_index)

            def add_neuron(layer_index: int):
                new_neuron_index = len(blueprint.layers[layer_index])

                for network_ in networks:
                    network_.add_neuron(layer_index)

                # Make neuron connected to random neuron in one of the previous layers and to random neuron in one of the next layers
                previous_layer_index = random.choice(range(0, layer_index))
                previous_neuron_index = random.choice(range(len(blueprint.layers[previous_layer_index])))
                next_layer_index = random.choice(range(layer_index + 1, len(blueprint.layers)))
                next_neuron_index = random.choice(range(len(blueprint.layers[next_layer_index])))

                for network_ in networks:
                    network_.add_connection((previous_layer_index, previous_neuron_index),
                                            (layer_index, new_neuron_index))
                    network_.add_connection((layer_index, new_neuron_index), (next_layer_index, next_neuron_index))

            def remove_random_neuron(layer_index: int):
                neuron_index = random.choice(range(len(blueprint.layers[layer_index])))

                for network_ in networks:
                    network_.remove_neuron(layer_index, neuron_index)

            if random.random() < structure_mutation_add_layer_chance and \
                    len(blueprint.layers) - 2 < maximum_hidden_layers:
                layer_to_add_index = random.choice(range(1, len(blueprint.layers)))
                for network__ in networks:
                    network__.add_layer_at(layer_to_add_index)
                add_neuron(layer_to_add_index)
                changes += 1

            if random.random() < structure_mutation_remove_layer_chance and \
                    len(blueprint.layers) - 2 > minimum_hidden_layers:
                layer_to_remove_index = random.choice(range(1, len(blueprint.layers) - 1))
                for network__ in networks:
                    network__.remove_layer(layer_to_remove_index)
                changes += 1

            if random.random() < structure_mutation_add_neuron_chance:
                # Add neuron in random layer except input and output layers
                add_neuron(random.choice(range(1, len(blueprint.layers) - 1)))
                changes += 1

            if random.random() < structure_mutation_remove_neuron_chance:
                remove_random_neuron(random.choice(range(1, len(blueprint.layers) - 1)))
                changes += 1

            if random.random() < structure_mutation_add_connection_chance:
                remaining_attempts = 8
                random_connection = get_random_connection()
                while blueprint.has_connection(random_connection[0], random_connection[1]) and remaining_attempts > 0:
                    remaining_attempts -= 1
                    random_connection = get_random_connection()
                if remaining_attempts > 0:
                    for network in networks:
                        network.add_connection(random_connection[0], random_connection[1])
                    changes += 1

            if random.random() < structure_mutation_remove_connection_chance:
                connection_index = random.choice(range(len(blueprint.connections)))
                for network in networks:
                    network.remove_connection(connection_index)
                changes += 1

            # Make sure something mutated. There is no point making new species if neural network structure doesn't change.
            if changes == 0:
                self.__mutate_genome_structure(networks)
                return

            # Fix network structure
            for network in networks:
                network.cleanup_structure()

    def __crossover(self, parent_a: _Individual[GenomeType], parent_b: _Individual[GenomeType]):
        if parent_a.species_id != parent_b.species_id:
            raise ValueError("Cannot crossover individuals from different species")

        if self.__genomes_type == NeuralNetwork:
            network_a: NeuralNetwork = parent_a.genome
            network_b: NeuralNetwork = parent_b.genome

            if not NeuralNetwork.compare_structure(network_a, network_b):
                raise ValueError("Cannot crossover networks with different structure")

            layers_structure = list(map(lambda layer: len(layer), network_a.layers))
            evolved_genome = NeuralNetwork(layers_structure, randomize_weights=False)
            evolved_genome.set_connections(network_a.connections, randomize_weights=False)

            weights_a = network_a.get_weights()
            weights_b = network_b.get_weights()

            evolved_weights: list[float] = []

            # Randomly split weights array into n segments where n is self.__config.crossover_segmentation
            weights_count = len(weights_a)
            segment_sizes = list(map(lambda _: int(random.random() * weights_count),
                                     range(self.__config.crossover_segmentation - 1)
                                     ))
            segment_sizes.extend((0, weights_count))
            segment_sizes = list(set(segment_sizes))
            segment_sizes.sort()

            for i in range(len(segment_sizes) - 1):
                index_start: int = segment_sizes[i]
                index_end: int = segment_sizes[i + 1]

                parent_weights = weights_a if random.random() < self.__config.crossover_chance else weights_b
                segment = parent_weights[index_start:index_end]

                # Mutation
                for j in range(len(segment)):
                    if random.random() < self.__config.mutation_chance:
                        # segment[j] += random.uniform(-self.__config.mutation_scale, self.__config.mutation_scale)
                        segment[j] += random.gauss(0, 0.4) * self.__config.mutation_scale
                evolved_weights.extend(segment)

            evolved_genome.set_weights(evolved_weights)

        else:
            raise ValueError("Unsupported genome type. Cannot crossover.")

        child = Evolution._Individual[GenomeType](species_id=parent_a.species_id, genome=evolved_genome)
        child.crossover_fitness(parent_a, parent_b, self.__config.crossover_chance)
        return child

    def __crossover_species(self, species_individuals: list[_Individual[GenomeType]]):
        """
        Crossover individuals in a species

        Args:
            species_individuals: sorted by fitness list of _Individual objects of same species

        Returns:
            List of evolved individuals within given species into new generation
        """
        species_size = len(species_individuals)
        elite_count = math.ceil(species_size * self.__config.elitism)

        new_species_generation = species_individuals[:elite_count]

        species_individuals.sort(key=lambda individual_: individual_.overall_fitness, reverse=True)
        species_normalized_fitness_array = normalize_array(
            list(map(lambda individual: individual.overall_fitness, species_individuals))
        )

        def get_parent_index():
            distribution_value = 1.0 - self.__distribution(1)

            j = 0
            for fitness in species_normalized_fitness_array[1:]:
                if fitness < distribution_value:
                    break
                j += 1
            return j

        for i in range(elite_count, species_size):
            parent_a = species_individuals[i]

            other_parent_index = get_parent_index()
            while other_parent_index >= len(species_individuals) or other_parent_index == i:
                other_parent_index = get_parent_index()

            parent_b = species_individuals[other_parent_index]
            child = self.__crossover(parent_a, parent_b)
            new_species_generation.append(child)

        return new_species_generation

    def evolve(self, scores: list[float]):
        if len(scores) != self.population_size:
            raise ValueError("Scores size does not match population size")

        self.__best_generation_score = max(scores)
        self.__average_generation_score = sum(scores) / len(scores)
        scores = normalize_array(scores)

        # Assign scores to individuals
        for i, individual in enumerate(self.individuals):
            individual.fitness = scores[i]

        # Sort individuals by fitness (sorting occurs also in __crossover_species)
        self.individuals.sort(key=lambda individual_: individual_.fitness, reverse=True)

        evolved_individuals: list[Evolution._Individual[GenomeType]] = []

        # Evolve each species separately
        species_groups = self.get_population_grouped_by_species()
        for species_group in species_groups.values():
            new_generation = self.__crossover_species(species_group)
            evolved_individuals.extend(new_generation)

        # Update generation with newly evolved individuals
        if len(evolved_individuals) != self.population_size:
            raise ValueError(
                "Evolved individuals size does not match population size. There must have been a problem with crossover")
        # for evolved, index in evolved_individuals:
        #     self.__individuals[index] = evolved
        self.__individuals = evolved_individuals

        for species_id in self.__species.keys():
            self.__species[species_id].generation += 1
        self.__generation += 1

        if random.random() < self.__config.species_extinction_chance:
            self.__extinct_least_fitted_species()
        if random.random() < self.__config.species_creation_chance:
            self.__create_species()
