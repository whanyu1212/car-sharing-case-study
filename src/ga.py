import random
import pandas as pd
import numpy as np
from typing import Tuple


class GeneticAlgo:
    def __init__(
        self,
        data,
        chromosome_length,
        population_size,
        max_ones,
        # generations,
        # crossover_rate,
        mutation_rate,
    ):
        self.data = data
        self.chromosome_length = chromosome_length
        self.population_size = population_size
        self.max_ones = max_ones
        # self.generations = generations
        # self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate

    def generate_chromosome(self) -> list:
        """Generate a valid chromosome with a
        constraint of max number of ones

        Returns:
            list: binary encoded list
        """
        chromosome = [0] * self.chromosome_length
        ones_positions = random.sample(range(self.chromosome_length), self.max_ones)
        for pos in ones_positions:
            chromosome[pos] = 1
        return chromosome

    def calculate_fitness(self, chromosome: list) -> int:
        """Calculate the fitness of a chromosome

        Args:
            chromosome (list): a list that contains 0 and 1

        Returns:
            int: _description_
        """
        total_sum = sum(
            sum(max(0, value - 2) if label == 1 else value for value in sublist)
            for label, sublist in zip(chromosome, self.data)  # creates an iterator
        )
        return -total_sum  # maximize the negative value or minimize the positive value

    def generate_valid_population(self) -> list:
        """
        Generates a valid initial population where each individual meets the budget constraint of max_ones '1's.

        Args:
        - pop_size (int): Number of individuals in the population.
        - num_stations (int): Number of stations (length of each individual).
        - max_ones (int): Maximum number of '1's allowed in each individual.

        Returns:
        - list of ndarray: The initial population, with each individual meeting the budget constraint.
        """
        population = [self.generate_chromosome() for _ in range(self.population_size)]
        return population

    def crossover(
        self, parent1: list, parent2: list, max_attempts=10
    ) -> Tuple[list, list]:
        """Creating children from parents using crossover while maintaining
        the max_ones constraint if possible.

        Args:
            parent1 (list): parent 1
            parent2 (list): parent 2
            max_attempts (int, optional): max attempt if the 1s exceeds. Defaults to 10.
            max_ones (int, optional): _description_. Defaults to 100.

        Returns:
            Tuple[list, list]: 2 children chromosomes
        """
        attempts = 0
        while attempts < max_attempts:
            point = random.randint(1, len(parent1) - 1)

            # Create children by swapping segments
            child1 = parent1[:point] + parent2[point:]
            child2 = parent2[:point] + parent1[point:]

            if child1.count(1) <= self.max_ones and child2.count(1) <= self.max_ones:
                return child1, child2
            attempts += 1

        # If unable to generate valid children after max_attempts, return the original parents
        return parent1, parent2

    def mutate(self, chromosome: list) -> list:
        """Mutate a chromosome by flipping a random '0' to '1' and a random '1' to '0'
        by chance

        Args:
            chromosome (list): individual chromosome
            mutation_rate (float, optional): threshold. Defaults to 0.01.

        Returns:
            list: mutated chromosome or the same chromosome
        """
        if random.random() < self.mutation_rate:
            # Indices where elements are 0 and 1
            zero_indices = [i for i, x in enumerate(chromosome) if x == 0]
            one_indices = [i for i, x in enumerate(chromosome) if x == 1]

            # Ensure there is at least one zero and one one to flip
            if zero_indices and one_indices:
                # Randomly choose one '0' to change to '1' and one '1' to change to '0'
                zero_to_flip = random.choice(zero_indices)
                one_to_flip = random.choice(one_indices)

                # Flip the chosen genes
                chromosome[zero_to_flip] = 1
                chromosome[one_to_flip] = 0

        return chromosome

    def evolve_population(self, population):
        """
        Evolves a population over one generation using tournament selection, crossover, and mutation.
        Also ensures the population size remains constant by adding randomly generated individuals if necessary.

        Args:
        - population (list of list of int): The current population of chromosomes.
        - lst (list of list of int): Data used for fitness calculation.
        - mutation_rate (float): The probability of each chromosome undergoing mutation.
        - tournament_size (int): The number of individuals participating in each tournament for selection.

        Returns:
        - list of list of int: The new generation of the population.
        """
        fitnesses = [self.calculate_fitness(chromosome) for chromosome in population]
        num_parents = len(population) // 2

        sorted_population = [
            x
            for _, x in sorted(
                zip(fitnesses, population), key=lambda pair: pair[0], reverse=True
            )
        ]
        # selected the fittest half to be parents and pass on to the next generation
        parents = sorted_population[:num_parents]

        # Generate new population through crossover
        children = []
        while len(children) < len(population):
            # randomly select two parents to mate?
            parent1, parent2 = random.sample(parents, 2)
            child1, child2 = self.crossover(parent1, parent2)

            if len(children) < len(population):
                children.append(child1)
            if len(children) < len(population) and len(children) < len(population):
                children.append(child2)

        # Apply mutation to the new generation
        new_population = [self.mutate(child) for child in children]

        # Supplement the population if necessary
        while len(new_population) < len(population):
            new_individual = self.generate_chromosome()
            new_population.append(new_individual)

        return new_population


if __name__ == "__main__":
    df = pd.read_csv("./data/sample_data.csv")
    lst = [
        df.loc[df["Station"] == i]["Failed Parking Reservations"].tolist()
        for i in df["Station"].unique()
    ]

    ga = GeneticAlgo(
        data=lst,
        chromosome_length=380,
        population_size=1000,
        max_ones=100,
        mutation_rate=0.01,
    )

    initial_population = ga.generate_valid_population()
    # Evolve over multiple generations
    for generation in range(100):
        population = ga.evolve_population(initial_population)
        # Optionally, print the best individual or average fitness of the population at each generation
        fitnesses = [ga.calculate_fitness(chromosome) for chromosome in population]
        best_fitness = max(fitnesses)

        print(
            f"Generation {generation + 1}: Best Fitness = {best_fitness}, the_best_individual = {population[fitnesses.index(best_fitness)]}"
        )
