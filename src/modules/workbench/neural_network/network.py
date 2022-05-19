import random
import numpy as np

from typing import Callable, Union


def _linear(value: float):
    return value


def _sigmoid(value: float):
    return 1.0 / (1.0 + np.exp(-value))


def _hyperbolic_tangent(value: float):
    return np.tanh(value)


class NeuralNetwork:
    class _Neuron:
        def __init__(self, activation_function: Union[_linear, _sigmoid, _hyperbolic_tangent]):
            # TODO: activation function type as part of network structure
            self.__activation_function = activation_function
            self.__value = 0.0
            self.__accumulator = 0.0

        @property
        def value(self):
            return self.__value

        @property
        def activation_function(self):
            return self.__activation_function

        @activation_function.setter
        def activation_function(self, activation_function: Union[_linear, _sigmoid, _hyperbolic_tangent]):
            self.__activation_function = activation_function

        def to_dict(self):
            return {
                'activation_function': str(self.__activation_function.__name__),
                # 'value': self.__value,
                # 'accumulator': self.__accumulator
            }

        def set_value(self, value: float):
            self.__value = value

        def accumulate(self, value: float):
            self.__accumulator += value

        def activate(self):
            self.__value = self.__activation_function(self.__accumulator)
            self.__accumulator = 0.0
            return self.__value

    @staticmethod
    def compare_structure(network1: 'NeuralNetwork', network2: 'NeuralNetwork'):
        """
        Args:
            network1: First network to compare
            network2: Second network to compare

        Returns:
            False if the networks have different structure, True otherwise
        """

        # Compare number of layers
        if len(network1.__layers) != len(network2.__layers):
            return False

        # Compare number of neurons in each layer
        for layer_index in range(len(network1.__layers)):
            if len(network1.__layers[layer_index]) != len(network2.__layers[layer_index]):
                return False

        # Compare number of connections
        if len(network1.__connections) != len(network2.__connections):
            return False

        # Compare connections (ignore weights)
        for connection_index in range(len(network1.__connections)):
            from1 = network1.__connections[connection_index][0]
            to1 = network1.__connections[connection_index][1]
            from2 = network2.__connections[connection_index][0]
            to2 = network2.__connections[connection_index][1]
            if from1 != from2 or to1 != to2:
                return False

        return True

    def __init__(self, layers: list[int], randomize_weights=False):
        if len(layers) < 2:
            raise ValueError("The network must have at least 2 layers (input and output layers).")

        self.__layers: list[list[NeuralNetwork._Neuron]] = []

        # List of pairs of neurons coordinates and connection weight
        self.__connections: list[tuple[tuple[int, int], tuple[int, int], float]] = []

        for i, layer_size in enumerate(layers):
            self.__layers.append(
                list(map(lambda _: NeuralNetwork._Neuron(_hyperbolic_tangent if i > 0 else _linear),
                         range(layer_size)))
            )

        # Generate default connections
        for layer_index in range(len(self.__layers) - 1):
            for neuron_index in range(len(self.__layers[layer_index])):
                for next_neuron_index in range(len(self.__layers[layer_index + 1])):
                    self.__connections.append((
                        (layer_index, neuron_index),
                        (layer_index + 1, next_neuron_index),
                        random.uniform(-1.0, 1.0) if randomize_weights else 0.0  # initial weights
                    ))

    @property
    def layers(self):
        return self.__layers

    @property
    def input_layer(self):
        return self.__layers[0]

    @property
    def output_layer(self):
        return self.__layers[-1]

    @property
    def connections(self):
        return self.__connections

    def copy(self):
        layers_structure = [len(layer) for layer in self.__layers]
        net = NeuralNetwork(layers_structure, randomize_weights=False)

        for l_i in range(len(self.__layers)):
            for n_i in range(len(self.__layers[l_i])):
                net.__layers[l_i][n_i].activation_function = self.__layers[l_i][n_i].activation_function

        net.set_connections(self.__connections, randomize_weights=False)

        return net

    def to_dict(self):
        return {
            'layers': [[neuron.to_dict() for neuron in layer] for layer in self.__layers],
            'connections': self.__connections
        }

    @staticmethod
    def from_dict(network_data: dict):
        layers_structure = [len(layer) for layer in network_data['layers']]

        network = NeuralNetwork(layers=layers_structure)
        for l_i in range(len(network.__layers)):
            for n_i in range(len(network.__layers[l_i])):
                activation_function_name = network_data['layers'][l_i][n_i]['activation_function']
                if activation_function_name == _linear.__name__:
                    network.__layers[l_i][n_i].activation_function = _linear
                elif activation_function_name == _sigmoid.__name__:
                    network.__layers[l_i][n_i].activation_function = _sigmoid
                elif activation_function_name == _hyperbolic_tangent.__name__:
                    network.__layers[l_i][n_i].activation_function = _hyperbolic_tangent
                else:
                    raise ValueError("Unknown activation function name: " + activation_function_name)

        parsed_connections = [(
            (int(conn[0][0]), int(conn[0][1])),
            (int(conn[1][0]), int(conn[1][1])),
            float(conn[2])
        ) for conn in network_data['connections']]
        network.set_connections(parsed_connections, randomize_weights=False)
        return network

    def get_weights(self) -> list[float]:
        return list(map(lambda conn: conn[2], self.__connections))

    def calculate(self, inputs: list[float]):
        if len(inputs) != len(self.__layers[0]):
            raise ValueError("The number of inputs must be equal to the number of neurons in the input layer.")

        # Feed input layer
        for neuron_index, neuron in enumerate(self.input_layer):
            neuron.set_value(inputs[neuron_index])

        # Accumulate neuron values from its connections layer by layer and activate all neurons in layer
        for l_i in range(1, len(self.__layers)):
            accumulated_neurons = set[NeuralNetwork._Neuron]()

            for connection in self.__connections:
                if connection[1][0] != l_i:
                    continue

                weight = connection[2]
                from_neuron = self.__layers[connection[0][0]][connection[0][1]]
                to_neuron = self.__layers[connection[1][0]][connection[1][1]]

                to_neuron.accumulate(from_neuron.value * weight)
                accumulated_neurons.add(to_neuron)

            for neuron in accumulated_neurons:
                neuron.activate()

        result: list[float] = list(map(lambda neuron_: neuron_.value, self.output_layer))
        return result

    def cleanup_structure(self):
        self.__remove_loose_neurons()
        self.__remove_empty_layers()

    def __remove_loose_neurons(self):
        # Skip input and output layers
        for l_i in range(len(self.__layers) - 2, 0, -1):
            for n_i in range(len(self.__layers[l_i]) - 1, -1, -1):
                is_loose_from = True
                is_loose_to = True

                for connection in self.__connections:
                    if connection[0] == (l_i, n_i):
                        is_loose_from = False
                    if connection[1] == (l_i, n_i):
                        is_loose_to = False

                if is_loose_from or is_loose_to:
                    self.remove_neuron(l_i, n_i)

    def __remove_empty_layers(self):
        # Skip input and output layers
        for l_i in range(len(self.__layers) - 2, 0, -1):
            if len(self.__layers[l_i]) == 0:
                self.remove_layer(l_i)

    def add_neuron(self, layer_index: int,
                   activation_function: Union[_linear, _sigmoid, _hyperbolic_tangent] = _hyperbolic_tangent):
        if layer_index < 1 or layer_index >= len(self.__layers):
            raise ValueError("The layer index must not be input layer or output layer")

        neuron = NeuralNetwork._Neuron(activation_function)
        self.__layers[layer_index].append(neuron)

    def remove_neuron(self, layer_index: int, neuron_index: int):
        if layer_index < 1 or layer_index >= len(self.__layers):
            raise ValueError("The layer index must not be input layer or output layer")

        # First remove connections associated with the neuron
        for c_i in range(len(self.__connections) - 1, -1, -1):
            connection = self.__connections[c_i]
            if (connection[0][0] == layer_index and connection[0][1] == neuron_index) or \
                    (connection[1][0] == layer_index and connection[1][1] == neuron_index):
                self.__connections.pop(c_i)

        # Shift neurons indexes for connections with higher neuron index at the same layer
        for c_i, connection in enumerate(self.__connections):
            if connection[0][0] == layer_index and connection[0][1] > neuron_index:
                self.__connections[c_i] = (
                    (layer_index, self.__connections[c_i][0][1] - 1),
                    self.__connections[c_i][1],
                    self.__connections[c_i][2]
                )
            if connection[1][0] == layer_index and connection[1][1] > neuron_index:
                self.__connections[c_i] = (
                    self.__connections[c_i][0],
                    (layer_index, self.__connections[c_i][1][1] - 1),
                    self.__connections[c_i][2]
                )

        # Now neuron can be safely removed
        self.__layers[layer_index].pop(neuron_index)

    def add_layer_at(self, layer_index: int, neurons: list[_Neuron] = None):
        if layer_index < 0 or layer_index >= len(self.__layers):
            raise ValueError("The layer index must be in range of the number of layers except last layer.")

        # Shift connections with layers above inserted index
        for c_i, connection in enumerate(self.__connections):
            # Note that both conditions can be true at the same time and connection must be updated in both places
            if connection[0][0] >= layer_index:
                self.__connections[c_i] = (
                    (self.__connections[c_i][0][0] + 1, self.__connections[c_i][0][1]),
                    self.__connections[c_i][1],
                    self.__connections[c_i][2]
                )
            if connection[1][0] >= layer_index:
                self.__connections[c_i] = (
                    self.__connections[c_i][0],
                    (self.__connections[c_i][1][0] + 1, self.__connections[c_i][1][1]),
                    self.__connections[c_i][2]
                )

        self.__layers.insert(layer_index, [] if neurons is None else neurons)

    def remove_layer(self, layer_index: int):
        if layer_index < 1 or layer_index >= len(self.__layers):
            raise ValueError("The layer index must not be input layer or output layer")

        # First remove connections associated with the layer
        for c_i in range(len(self.__connections) - 1, -1, -1):
            if self.__connections[c_i][0][0] == layer_index or self.__connections[c_i][1][0] == layer_index:
                self.__connections.pop(c_i)

        # Shift layers indexes for connections associated with higher layer index
        for c_i, connection in enumerate(self.__connections):
            if connection[0][0] > layer_index:
                self.__connections[c_i] = (
                    (self.__connections[c_i][0][0] - 1, self.__connections[c_i][0][1]),
                    self.__connections[c_i][1],
                    self.__connections[c_i][2]
                )
            if connection[1][0] > layer_index:
                self.__connections[c_i] = (
                    self.__connections[c_i][0],
                    (self.__connections[c_i][1][0] - 1, self.__connections[c_i][1][1]),
                    self.__connections[c_i][2]
                )

        # Now layer can be safely removed
        self.__layers.pop(layer_index)

    def has_connection(self, from_neuron: tuple[int, int], to_neuron: tuple[int, int]):
        for connection in self.__connections:
            if connection[0] == from_neuron and connection[1] == to_neuron:
                return True
        return False

    def add_connection(self, from_: tuple[int, int], to_: tuple[int, int], weight: float = None):
        """
        Register a new connection between two given neurons

        Args:
            from_: coordinates of first neuron
            to_: coordinates of second neuron
            weight: connection weight; if None, random value will be generated

        Returns: True if connection was added, False otherwise
        """

        if weight is None:
            weight = random.uniform(-1.0, 1.0)
        self.__connections.append((from_, to_, weight))

    def remove_connection(self, connection_index: int):
        if 0 <= connection_index < len(self.__connections):
            self.__connections.pop(connection_index)

    def set_connections(
            self, connections: list[Union[
                tuple[tuple[int, int], tuple[int, int]],
                tuple[tuple[int, int], tuple[int, int], float]
            ]], randomize_weights: bool = False
    ):
        self.__connections.clear()
        for conn in connections:
            self.__connections.append((
                conn[0],
                conn[1],
                random.uniform(-1.0, 1.0) if randomize_weights else (conn[2] if len(conn) > 2 else 0.0)
            ))

    def set_weights(self, weights: list[float]):
        if len(weights) != len(self.__connections):
            raise ValueError("The number of weights must be equal to the number of connections.")

        for connection_index in range(len(self.__connections)):
            from_, to_, _ = self.__connections[connection_index]
            self.__connections[connection_index] = (from_, to_, weights[connection_index])
