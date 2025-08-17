import json

from core.parameters import Parameters


class InputBuffer:
    """
    Class to create the buffer from the grid designer UI buffer ratio, then to send to SM.

    Parameters
    ----------
    buffer_ratio : float
        The buffer ratio after taking into account the grid and also the number of bins
        expected.
    """

    def __init__(self, buffer_ratio: float):
        # This percentage is the percentage of the grid that is expected to be filled.
        self.percentage = round(max(0.0, min(1 - buffer_ratio, 1.0)), 2)
        self.zoneGroup = Parameters.ZONE_NAME

    def to_json(
        self, save: bool = False, filename: str = "reset-4.json", type: str = "str"
    ) -> str:
        """
        Convert the buffer to a JSON string.

        Parameters
        ----------
        save : bool, optional
            Whether to save the JSON string to a file, by default False
        filename : str, optional
            The name of the file to save the JSON string to, by default "reset-4.json"
        type : str, optional
            The type of the input; either "str" or "dict", by default "str".

        Returns
        -------
        str
            The JSON string of the buffer.
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
