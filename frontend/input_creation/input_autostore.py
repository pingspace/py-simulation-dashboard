import json
from typing import List

from frontend.input_creation.input_zones_stations import InputZonesAndStations


class InputAutostore:
    """
    Create the autostore input, then to send to SM. The station codes are reused from
    the input zones and stations.

    Parameters
    ----------
    input_zones_and_stations : InputZonesAndStations
        The input zones and stations.
    """

    def __init__(
        self,
        input_zones_and_stations: InputZonesAndStations,
    ):
        self.action = "DISABLE"
        self.stations = self._get_list_of_stations(
            input_zones_and_stations=input_zones_and_stations
        )

    def _get_list_of_stations(
        self, input_zones_and_stations: InputZonesAndStations
    ) -> List[int]:
        """
        Get the list of station codes.

        Parameters
        ----------
        input_zones_and_stations : InputZonesAndStations
            The input zones and stations.

        Returns
        -------
        List[int]
            The list of station codes.
        """
        return [station.code for station in input_zones_and_stations.stations]

    def to_json(
        self,
        save: bool = False,
        filename: str = "reset-autostore.json",
        type: str = "str",
    ) -> str:
        """
        Convert the autostore input to a JSON string.

        Parameters
        ----------
        save : bool, optional
            Whether to save the JSON string to a file, by default False
        filename : str, optional
            The name of the file to save the JSON string to, by default "reset-autostore.json"
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
