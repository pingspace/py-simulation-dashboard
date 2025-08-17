import json
from typing import List

from ui_components.simulation_input import SimulationInputUI
from ui_components.grid_designer import GridDesignerUI
from core.exception import SimulationFrontendException


class InputSimulation:
    """
    Create the simulation input.

    Parameters
    ----------
    simulation_input_ui : SimulationInputUI
        The simulation input UI.
    grid_designer_ui : GridDesignerUI
        The grid designer UI.
    server_number : int
        The server number.
    """

    def __init__(
        self,
        simulation_input_ui: SimulationInputUI,
        grid_designer_ui: GridDesignerUI,
        server_number: int,
    ):
        self._create_parameters(simulation_input_ui=simulation_input_ui)
        self._create_configuration(
            simulation_input_ui=simulation_input_ui,
            server_number=server_number,
        )
        self._create_stations(grid_designer_ui=grid_designer_ui)
        self._create_station_groups(grid_designer_ui=grid_designer_ui)

    def _create_parameters(self, simulation_input_ui: SimulationInputUI):
        """
        Create simulation parameters

        Parameters
        ----------
        simulation_input_ui : SimulationInputUI
            The simulation input UI.
        """
        self.parameters = InputParameters(
            inbound_time=simulation_input_ui.inbound_time,
            outbound_time=simulation_input_ui.outbound_time,
            inbound_bins_per_order=simulation_input_ui.inbound_bins_per_order,
            outbound_bins_per_order=simulation_input_ui.outbound_bins_per_order,
            inbound_orders_per_hour=simulation_input_ui.inbound_orders_per_hour,
            outbound_orders_per_hour=simulation_input_ui.outbound_orders_per_hour,
            pareto_probabilities=simulation_input_ui.pareto_probabilities,
        )

    def _create_configuration(
        self,
        simulation_input_ui: SimulationInputUI,
        server_number: int,
    ):
        """
        Create simulation configuration

        Parameters
        ----------
        simulation_input_ui : SimulationInputUI
            The simulation input UI.
        server_number : int
            The server number.
        """
        self.configuration = InputConfiguration(
            name=simulation_input_ui.simulation_name,
            server_number=server_number,
            duration_string=simulation_input_ui.duration_string,
        )

    def _create_stations(self, grid_designer_ui: GridDesignerUI):
        """
        Create station information

        Parameters
        ----------
        grid_designer_ui : GridDesignerUI
            The grid designer UI.
        """
        stations: List[InputStation] = []
        for grid_station in grid_designer_ui.station_cells:
            code = int("".join(filter(str.isdigit, grid_station)))
            last_character = grid_station[-1]
            if last_character not in ["I", "O"]:
                raise SimulationFrontendException(
                    f"Invalid station type: {grid_station}"
                )

            # Check if the station code is already in the list to avoid duplicates
            if any(
                station.code == code and station.type == last_character
                for station in stations
            ):
                continue

            stations.append(InputStation(code=code, type_=last_character))

        self.stations = stations

    def _create_station_groups(self, grid_designer_ui: GridDesignerUI):
        """
        Create station groups.

        Parameters
        ----------
        grid_designer_ui : GridDesignerUI
            The grid designer UI.
        """
        self.station_groups = [
            InputStationGroup(group=index, station_codes=sorted(group))
            for index, group in enumerate(grid_designer_ui.station_code_groups)
        ]

    def update_simulation_run_id(self, simulation_run_id: int):
        """
        Update the simulation run ID

        Parameters
        ----------
        simulation_run_id : int
            The simulation run ID.
        """
        self.configuration.id = simulation_run_id

    def to_json(
        self,
        save: bool = False,
        filename: str = "reset-simulation.json",
        type: str = "str",
    ) -> str:
        """
        Convert the simulation input to a JSON string.

        Parameters
        ----------
        save : bool, optional
            Whether to save the JSON string to a file, by default False
        filename : str, optional
            The name of the file to save the JSON string to, by default "reset-simulation.json"
        type : str, optional
            The type of the input; either "str" or "dict", by default "str"

        Returns
        -------
        str
            The JSON string of the input.
        """
        json_str = json.dumps(
            self, default=lambda o: o.__dict__, sort_keys=True, indent=4
        )

        if save:
            with open(filename, "w") as file:
                file.write(json_str)

        if type == "str":
            return json_str
        elif type == "dict":
            return json.loads(json_str)




class InputParameters:
    """
    Class to store the simulation parameters.

    Parameters
    ----------
    inbound_time : int
        The inbound time in seconds.
    outbound_time : int
        The outbound time in seconds.
    inbound_bins_per_order : int
        The inbound bins per order.
    outbound_bins_per_order : int
        The outbound bins per order.
    inbound_orders_per_hour : int
        The inbound orders per hour.
    outbound_orders_per_hour : int
        The outbound orders per hour.
    pareto_probabilities : List[float]
        The Pareto probabilities from grid designer UI.
    """
    def __init__(
        self,
        inbound_time: int,
        outbound_time: int,
        inbound_bins_per_order: int,
        outbound_bins_per_order: int,
        inbound_orders_per_hour: int,
        outbound_orders_per_hour: int,
        pareto_probabilities: List[float],
    ):
        self.inbound_time = inbound_time
        self.outbound_time = outbound_time
        self.inbound_bins_per_order = inbound_bins_per_order
        self.outbound_bins_per_order = outbound_bins_per_order
        self.inbound_orders_per_hour = inbound_orders_per_hour
        self.outbound_orders_per_hour = outbound_orders_per_hour
        self.pareto_probabilities = pareto_probabilities


class InputConfiguration:
    """
    Class to store the simulation configuration.

    Parameters
    ----------
    name : str
        The name of the simulation.
    server_number : int
        The server number.
    duration_string : str
        The string that stores the operation durations. Example is N1800;AO700.
    """
    def __init__(
        self,
        name: str,
        server_number: int,
        duration_string: str,
    ):
        self.name = name
        self.server_number = server_number
        self.duration_string = duration_string

        # To be updated by the database
        self.id = None


class InputStation:
    """
    Class to store the station information.

    Parameters
    ----------
    code : int
        The station code.
    type_ : str
        The station type. Can be "I" for inbound or "O" for outbound.
    """
    def __init__(self, code: int, type_: str):
        self.code = code
        self.type = type_


class InputStationGroup:
    """
    Class to store the station group information.

    Parameters
    ----------
    group : int
        The group index.
    station_codes : List[int]
        The station codes in the group.
    """
    def __init__(self, group: int, station_codes: List[int]):
        self.group = group
        self.station_codes = station_codes
