from typing import Union

from src.modules.workbench.neural_network.network import NeuralNetwork


class Evolution:
    class _Individual:
        def __init__(self, species_id: int, genome: Union[NeuralNetwork]):
            self.species_id = species_id
            self.genome = genome  # Object to crossover
            self.fitness = 0.

    class _Species:
        def __init__(self):
            self.generation = 0  # Works as species age; #TODO: utilize this

    """ 
        TODO: species creation and removal chances; 
        creating species by splitting existing species in two; 
        removing species by either merging two species (tricky) or by killing all individuals in a species
    """

    def __init__(self, genomes: Union[list[NeuralNetwork]]):
        self.__generation = 0

        self.__species_counter = 0
        self.__species: dict[int, Evolution._Species] = {}
        self.individuals: list[Evolution._Individual] = []

        # Initialize first species
        self.__add_species(genomes)

    def __add_species(self, genomes: Union[list[NeuralNetwork]]):
        self.__species[self.__species_counter] = Evolution._Species()

        species_population = list(map(lambda genome: Evolution._Individual(self.__species_counter, genome), genomes))
        self.individuals.extend(species_population)

        self.__species_counter += 1

    @property
    def population_size(self):
        return len(self.individuals)

    def print_stats(self):
        # TODO: population of each species
        print(f'''--- EVOLUTION STATISTICS ---
            Generation: {self.__generation}
            Species: {len(self.__species)}
        ''')

    # @property
    # def generation(self):
    #     return self.__generation

    def __crossover(self, individuals: list[_Individual]):
        # TODO: crossover
        pass

    def evolve(self, scores: list[float]):
        # List of individuals indexes and their fitness pairs
        sorted_fitness: list[tuple[int, float]] = sorted(
            map(lambda e: e, enumerate(scores)), key=lambda x: x[1], reverse=True)

        # TODO: species removal and separate individuals from removed species for further joining with other species

        # Keys are species id
        species_groups: dict[int, list[Evolution._Individual]] = {}
        for index, fitness in sorted_fitness:
            self.individuals[index].fitness = fitness

            species_id = self.individuals[index].species_id
            if species_id not in species_groups:
                species_groups[species_id] = []
            species_groups[species_id].append(self.individuals[index])

        # Evolve each species
        for species_group in species_groups.values():
            self.__crossover(species_group)

        # TODO: species creation

        # print("Temp", list(map(lambda i: i.fitness, crossover_groups[0])))

        for species_id in self.__species:
            self.__species[species_id].generation += 1
        self.__generation += 1
