from src.modules.workbench.neural_network.network import NeuralNetwork
from src.common.math import clamp_f, mix
from src.gui.core.circle import Circle
from src.gui.core.line import Line
from src.gui.core.widget import Widget
from src.modules.workbench.view import WorkbenchView


def visualize_network(network: NeuralNetwork):
    layers = network.get_layers()
    connections = network.get_connections()

    widgets: list[Widget] = []

    positions: list[list[tuple[int, int]]] = []
    padding = 0.05

    def add_node_circle(layer_index: int, neuron_index: int):
        pos = positions[layer_index][neuron_index]
        neuron_ = layers[layer_index][neuron_index]

        value = clamp_f(neuron_.get_value(), 0, 1)
        neuron_color = (
            mix(203, 132, value),
            mix(134, 199, value),
            mix(121, 129, value),
        )

        widgets.append(
            Circle(pos, radius=int(WorkbenchView.VISUALISATION_SIZE * 0.025), background_color=neuron_color),
        )

    largest_layer_size = max(map(len, layers))

    for i, layer in enumerate(layers):
        y = 1 - (padding + (i / max(1, (len(layers) - 1))) * (1. - 2. * padding))
        positions.append([])

        for j, neuron in enumerate(layer):
            x = padding + (0.5 + ((j + 0.5) - len(layer) / 2.0) / max(1, (largest_layer_size - 1))) * \
                (1. - 2. * padding)
            positions[i].append((
                int(x * WorkbenchView.VIEW_SIZE),
                WorkbenchView.VIEW_SIZE + int(y * WorkbenchView.VISUALISATION_SIZE)
            ))

    for connection in connections:
        from_pos = positions[connection[0][0]][connection[0][1]]
        to_pos = positions[connection[1][0]][connection[1][1]]

        weight = clamp_f(connection[2], -1, 1)
        connection_color = (
            mix(241, 80, weight),
            mix(239, 83, weight),
            mix(236, 239, weight),
        ) if weight >= 0 else (
            mix(241, 218, weight),
            mix(239, 198, weight),
            mix(236, 38, weight),
        )
        widgets.append(
            Line(pos_start=from_pos, pos_end=to_pos, color=connection_color)
        )

    for connection in connections:
        add_node_circle(connection[0][0], connection[0][1])

        if connection[1][0] == len(layers) - 1:
            add_node_circle(connection[1][0], connection[1][1])

    return widgets
