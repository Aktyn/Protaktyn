import random
import numpy as np

from typing import Callable


class NeuralNetwork:
    class _ActivationFunction:
        LINEAR = lambda value: value
        SIGMOID = lambda value: 1.0 / (1.0 + np.exp(-value))
        HYPERBOLIC_TANGENT = lambda value: np.tanh(value)

    class _Neuron:
        def __init__(self, activation_function: Callable[[float], float]):
            # TODO: activation function type as part of network structure
            self.__activation_function = activation_function
            self.__value = 0.0

        def set_value(self, value: float):
            self.__value = value

        def get_value(self):
            return self.__value

        def activate(self, value):
            self.__value = self.__activation_function(value)
            return self.__value

    def __init__(self, layers: list[int]):
        if len(layers) < 2:
            raise ValueError("The network must have at least 2 layers (input and output layers).")

        self.__layers: list[list[NeuralNetwork._Neuron]] = []

        # List of pairs of neurons coordinates and connection weight
        self.__connections: list[tuple[tuple[int, int], tuple[int, int], float]] = []

        for i, layer_size in enumerate(layers):
            self.__layers.append(
                list(map(lambda _: NeuralNetwork._Neuron(
                    NeuralNetwork._ActivationFunction.HYPERBOLIC_TANGENT if i > 0 else NeuralNetwork._ActivationFunction.LINEAR
                ), range(layer_size)))
            )

        # Generate default connections
        for layer_index in range(len(self.__layers) - 1):
            for neuron_index in range(len(self.__layers[layer_index])):
                for next_neuron_index in range(len(self.__layers[layer_index + 1])):
                    self.__connections.append((
                        (layer_index, neuron_index),
                        (layer_index + 1, next_neuron_index),
                        random.uniform(-1, 1)  # initial weight (it can be randomized); TODO: parameterize randomization
                    ))

    def __input_layer(self):
        return self.__layers[0]

    def __output_layer(self):
        return self.__layers[-1]

    def calculate(self, inputs: list[float]):
        if len(inputs) != len(self.__layers[0]):
            raise ValueError("The number of inputs must be equal to the number of neurons in the input layer.")

        # Feed input layer
        for neuron_index, neuron in enumerate(self.__input_layer()):
            neuron.set_value(inputs[neuron_index])

        # Propagate each layer after the input layer
        for i in range(1, len(self.__layers)):
            # For each neuron in the current layer
            for j, neuron in enumerate(self.__layers[i]):
                # Calculate weighted sum of all the neurons (not necessarily from previous layer) connected to the current neuron
                sum_ = 0.0
                for connection in self.__connections:
                    if connection[1][0] == i - 1 and connection[1][1] == j:
                        connected_neuron = self.__layers[connection[0][0]][connection[0][1]]
                        # Add connected neuron value multiplied by connection weight to the sum
                        sum_ += connection[2] * connected_neuron.get_value()
                neuron.activate(sum_)

        result: list[float] = list(map(lambda neuron_: neuron_.get_value(), self.__output_layer()))
        return result

    def get_layers(self):
        return self.__layers

    def get_connections(self):
        return self.__connections
