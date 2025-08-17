import json

from core.parameters import Parameters


class InputSkyCarSetup:
    """
    Class to create the skycar setup, then to send to TC.

    Parameters
    ----------
    number_of_skycars : int
        The number of skycars to be used in the simulation.
    """

    def __init__(self, number_of_skycars: int):
        self.num_skycars = number_of_skycars
        self.model = Parameters.ZONE_NAME

    def to_json(
        self, save: bool = False, filename: str = "reset-5.json", type: str = "str"
    ) -> str:
        """
        Convert the skycar setup to a JSON string.

        Parameters
        ----------
        save : bool, optional
            Whether to save the JSON string to a file, by default False
        filename : str, optional
            The name of the file to save the JSON string to, by default "reset-5.json"
        type : str, optional
            The type of the input; either "str" or "dict", by default "str".

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
