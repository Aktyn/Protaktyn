from src.modules.workbench.neural_network.network import NeuralNetwork
from src.common.math_utils import clamp_f, mix
from src.gui.core.circle import Circle
from src.gui.core.line import Line
from src.gui.core.widget import Widget
from src.modules.workbench.view import WorkbenchView


def visualize_network(network: NeuralNetwork, view_x: float, view_y: float, view_width: float, view_height: float):
    layers = network.layers
    connections = network.connections

    widgets: list[Widget] = []

    positions: list[list[tuple[int, int]]] = []
    padding = 0.05

    def transpose_pos(pos: tuple[int, int]):
        return (int(pos[0] * view_width + view_x * WorkbenchView.VIEW_SIZE),
                int(WorkbenchView.VIEW_SIZE + (pos[1] - WorkbenchView.VIEW_SIZE) * view_height +
                    view_y * WorkbenchView.VISUALISATION_SIZE))

    def add_node_circle(layer_index: int, neuron_index: int):
        pos = positions[layer_index][neuron_index]
        neuron_ = layers[layer_index][neuron_index]

        value = clamp_f(neuron_.value, -1, 1)
        neuron_color = (
            mix(241, 80, value),
            mix(239, 83, value),
            mix(236, 239, value),
        ) if value > 0 else (
            mix(241, 101, -value),
            mix(239, 204, -value),
            mix(236, 156, -value),
        )

        widgets.append(
            Circle(transpose_pos(pos), radius=int(WorkbenchView.VISUALISATION_SIZE * 0.025 * view_height),
                   background_color=neuron_color),
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
            mix(241, 101, -weight),
            mix(239, 204, -weight),
            mix(236, 156, -weight),
        )
        widgets.append(
            Line(pos_start=transpose_pos(from_pos), pos_end=transpose_pos(to_pos), color=connection_color)
        )

    for i, layer in enumerate(layers):
        for j in range(len(layer)):
            add_node_circle(i, j)

    return widgets
