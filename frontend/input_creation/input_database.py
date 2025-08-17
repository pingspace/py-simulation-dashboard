import json

from input_creation.input_simulation import InputSimulation
from ui_components.grid_designer import GridDesignerUI
from ui_components.simulation_input import SimulationInputUI

from core.exception import SimulationFrontendException
from input_creation.input_zones_stations import InputZonesAndStations


class InputDatabase:
    """
    Class to save the information to store in simulation database.

    Parameters
    ----------
    simulation_input_ui : SimulationInputUI
        The simulation input UI.
    grid_designer_ui : GridDesignerUI
        The grid designer UI.
    input_zones_and_stations : InputZonesAndStations
        The input zones and stations class.
    input_simulation : InputSimulation
        The input simulation class.
    """

    def __init__(
        self,
        simulation_input_ui: SimulationInputUI,
        grid_designer_ui: GridDesignerUI,
        input_zones_and_stations: InputZonesAndStations,
        input_simulation: InputSimulation,
    ):

        self.simulation_name = simulation_input_ui.simulation_name
        self.inbound_bins_per_order = simulation_input_ui.inbound_bins_per_order
        self.outbound_bins_per_order = simulation_input_ui.outbound_bins_per_order
        self.inbound_orders_per_hour = simulation_input_ui.inbound_orders_per_hour
        self.outbound_orders_per_hour = simulation_input_ui.outbound_orders_per_hour
        self.number_of_skycars = simulation_input_ui.number_of_skycars
        self.inbound_handling_time = simulation_input_ui.inbound_time
        self.outbound_handling_time = simulation_input_ui.outbound_time
        self.pareto_p = simulation_input_ui.pareto_p
        self.pareto_q = simulation_input_ui.pareto_q
        self.number_of_bins = grid_designer_ui.number_of_bins
        self.stations_string = self._encode_stations(
            input_zones_and_stations=input_zones_and_stations,
            input_simulation=input_simulation,
        )
        self.duration_string = simulation_input_ui.duration_string
        self.station_groups_string = self._encode_station_groups(
            input_simulation=input_simulation
        )
        self.desired_skycar_directions_string = self._encode_desired_skycar_directions(
            grid_designer_ui=grid_designer_ui
        )

    def _encode_desired_skycar_directions(
        self, grid_designer_ui: GridDesignerUI
    ) -> str:
        """
        Encode the desired skycar directions to store in simulation database.

        Parameters
        ----------
        grid_designer_ui : GridDesignerUI
            The grid designer UI.

        Returns
        -------
        str
            The encoded desired skycar directions. Arrow segments are separated by
            semicolons. Each segment is of the format "arrow_index:X,Y".
        """
        return_str = ""
        for _, row in grid_designer_ui.desired_skycar_directions.iterrows():
            return_str += f"{row['arrow_index']}:{row['X']},{row['Y']};"
        return return_str[:-1]

    def _encode_station_groups(self, input_simulation: InputSimulation) -> str:
        """
        Encode the station groups to store in simulation database.

        Parameters
        ----------
        input_simulation : InputSimulation
            The input simulation class.

        Returns
        -------
        str
            The encoded station groups. Each group is of the format
            "group_index:{code1},{code2},...". Groups are separated by semicolons.
        """
        return_str = ""
        for group in input_simulation.station_groups:
            return_str += (
                f"{group.group}:"
                + ",".join(str(code) for code in group.station_codes)
                + ";"
            )
        return return_str[:-1]

    def _encode_stations(
        self,
        input_zones_and_stations: InputZonesAndStations,
        input_simulation: InputSimulation,
    ) -> str:
        """
        Encode the stations to store in simulation database.

        Parameters
        ----------
        input_zones_and_stations : InputZonesAndStations
            The input zones and stations class.
        input_simulation : InputSimulation
            The input simulation class.

        Returns
        -------
        str
            The encoded stations. Each station is of the format
            "{code}{type}:D(x{drop_x}y{drop_y})P(x{pick_x}y{pick_y})".
            Stations are separated by semicolons.

        Raises
        ------
        ValueError
            _description_
        """
        # Get stations from both inputs
        stations_from_input_zones_and_stations = input_zones_and_stations.stations
        stations_from_input_simulation = input_simulation.stations

        # Build station strings
        station_segments = []
        for station_item in stations_from_input_zones_and_stations:
            code = station_item.code
            station_type = next(
                (x.type for x in stations_from_input_simulation if x.code == code),
                None,
            )

            if station_type is None:
                raise SimulationFrontendException(
                    f"Station type not found for code: {code}"
                )

            # Get coordinates
            drop_coords = (
                station_item.drop[0].coordinate.x,
                station_item.drop[0].coordinate.y,
            )
            pick_coords = (
                station_item.pick[0].coordinate.x,
                station_item.pick[0].coordinate.y,
            )

            # Format the station string
            station_str = (
                f"{code}{station_type}:"
                f"D(x{drop_coords[0]}y{drop_coords[1]})"
                f"P(x{pick_coords[0]}y{pick_coords[1]})"
            )
            station_segments.append(station_str)

        # Join all station segments with semicolons
        return ";".join(station_segments)

    def to_json(
        self,
        save: bool = False,
        filename: str = "reset-database.json",
        type: str = "str",
    ) -> str:
        """
        Convert the input database to a JSON string.

        Parameters
        ----------
        save : bool, optional
            Whether to save the JSON string to a file, by default False
        filename : str, optional
            The name of the file to save the JSON string to, by default "reset-database.json"
        type : str, optional
            The type of the input; either "str" or "dict", by default "str"

        Returns
        -------
        str
            The JSON string of the input database.
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
