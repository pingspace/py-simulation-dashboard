import pandas
from core.config import (
    MONGO_HOST_1,
    MONGO_HOST_2,
    MONGO_NAME_1,
    MONGO_NAME_2,
    MONGO_PASSWORD,
    MONGO_USER,
)
from core.exception import SimulationFrontendException
from pymongo import MongoClient


class MongoService:
    """
    Class related to interacting with TC MongoDB database.

    Parameters
    ----------
    server_number : int
        The server number of the TC database; either 1 or 2.

    Raises
    ------
    SimulationFrontendException
        If the server number is not 1 or 2.
    """

    def __init__(self, server_number: int):
        if server_number not in [1, 2]:
            raise SimulationFrontendException("Server number must be 1 or 2")

        self.host = MONGO_HOST_1 if server_number == 1 else MONGO_HOST_2
        self.username = MONGO_USER
        self.password = MONGO_PASSWORD
        self.name = MONGO_NAME_1 if server_number == 1 else MONGO_NAME_2
        self.replica_set = None

        self.client = self._get_client()

    def _get_client(self) -> MongoClient:
        """
        Get the MongoDB client.

        Returns
        -------
        MongoClient
            The MongoDB client.
        """
        client = MongoClient(
            host=self.host,
            username=self.username,
            password=self.password,
            replicaset=self.replica_set,
            serverSelectionTimeoutMS=1500,
        )
        return client

    def get_skycar_messages(
        self, start_timestamp: float, end_timestamp: float
    ) -> pandas.DataFrame:
        """
        Get raw skycar messages from the TC database.

        Parameters
        ----------
        start_timestamp : float
            The start timestamp of the time range to get the skycar messages from.
        end_timestamp : float
            The end timestamp of the time range to get the skycar messages from.

        Returns
        -------
        pandas.DataFrame
            A pandas DataFrame containing the skycar messages.

        Raises
        ------
        SimulationFrontendException
            If there is an error connecting to the MongoDB database.
        """
        try:
            self.client.server_info()

            collection = self.client[self.name]["skycar_message"]
            result = collection.aggregate(
                [
                    {
                        "$match": {
                            "created_at": {
                                "$gte": start_timestamp,
                                "$lte": end_timestamp,
                            },
                            "message_id": {"$regex": "-"},
                        },
                    },
                    {"$unwind": "$child_messages"},
                    {
                        "$replaceRoot": {
                            "newRoot": {"$mergeObjects": ["$$ROOT", "$child_messages"]}
                        }
                    },
                    {
                        "$match": {
                            "sent_by_tc": False,
                            "message": {"$not": {"$regex": "^ACK,"}, "$regex": ",I,"},
                        }
                    },
                    {"$sort": {"skycar_id": 1, "created_at": 1}},
                    {
                        "$project": {
                            "skycar_id": 1,
                            "message": 1,
                            "_id": 0,
                            "completed_at": "$created_at",
                        }
                    },
                ]
            )

            df = pandas.DataFrame(result)

            return df

        except Exception as e:
            raise SimulationFrontendException(f"Error connecting to MongoDB: {e}")

    def get_movement_data(
        self,
        start_timestamp: float,
        end_timestamp: float,
        save_filename: str = None,
    ) -> pandas.DataFrame:
        """
        Get the skycar movement data and preprocess it.

        Parameters
        ----------
        start_timestamp : float
            The start timestamp of the time range to get the skycar movement data from.
        end_timestamp : float
            The end timestamp of the time range to get the skycar movement data from.
        save_filename : str, optional
            The filename to save the preprocessed data to, by default None, i.e. not
            saved.

        Returns
        -------
        pandas.DataFrame
            A processedpandas DataFrame containing the skycar movement data.
        """
        df = self.get_skycar_messages(
            start_timestamp=start_timestamp, end_timestamp=end_timestamp
        )

        # Convert skycar_id from stringto integer
        df["skycar_id"] = df["skycar_id"].astype(int)

        # Split the message into a list of strings
        split = df["message"].str.split(",")

        # There are two kinds of entries: main (prefixed with 'LOG') and child (prefixed
        # with 'SC'). Main entries contain the information of the whole linear leg of
        # the skycar. Child entries break down the main entries into smaller individual
        # coordinates. Here, we identify the main entries.
        main_mask = split.str[0] == "LOG"

        # An example main entry is "LOG,SC,1,I,S1-19623ee623e0000,3,B,x,18,19,0,,CB,".
        # Here, from the 6th element (index 5):
        # - index 5: number of child entries (or steps).
        # - index 6: action (B = backward, F = forward, O* = bin picking, C* = bin
        # dropping, DBF = buffer, i.e. at station, the duration between start of the
        # winch to when the bin is ready to be picked).
        # - index 7: axis (x, y).
        # - index 8: x coordinate to go.
        # - index 9: y coordinate to go.
        # if is_for_movement_visualisation:
        #     df = df.loc[~main_mask, :]
        # else:
        df.loc[main_mask, "x"] = split.loc[main_mask].str[8].astype(int)
        df.loc[main_mask, "y"] = split.loc[main_mask].str[9].astype(int)
        df.loc[main_mask, "action"] = "LOG" + split.loc[main_mask].str[6]

        # For child entries, we extract the action and the coordinates to go.
        # An example child entry is "SC,1,I,S1-19623ee8d780000-1,B,y,18,13,0,,100"
        df.loc[~main_mask, "action"] = split.loc[~main_mask].str[4]
        df.loc[~main_mask, "x"] = split.loc[~main_mask].str[6].astype(int)
        df.loc[~main_mask, "y"] = split.loc[~main_mask].str[7].astype(int)

        df = df.sort_values(by=["skycar_id", "completed_at"])
        simulation_start_timestamp = df["completed_at"].min()

        # For the time of beginning of an entry, we just take the shift of the whole
        # dataset of a given skycar_id because LOG entries are the time when the
        # instruction is received.
        # For the very first entry of a given skycar_id, we assume that the message was
        # received at the start of the simulation, minus 1 second as buffer.
        df["begin_at"] = df.groupby("skycar_id")["completed_at"].shift(1)
        df.loc[df["begin_at"].isna(), "begin_at"] = simulation_start_timestamp - 1

        # To get the previous coordinates, we need to separate the main entries and the
        # child entries, then shift the coordinates of the previous entry.
        df.loc[~main_mask, "prev_x"] = (
            df.loc[~main_mask].groupby("skycar_id")["x"].shift(1)
        )
        df.loc[~main_mask, "prev_y"] = (
            df.loc[~main_mask].groupby("skycar_id")["y"].shift(1)
        )

        df.loc[main_mask, "prev_x"] = (
            df.loc[main_mask].groupby("skycar_id")["x"].shift(1)
        )
        df.loc[main_mask, "prev_y"] = (
            df.loc[main_mask].groupby("skycar_id")["y"].shift(1)
        )

        # Also for previous coordinates, we assume first entry is the same as the current
        # coordinates.
        df.loc[(~main_mask) & df["prev_x"].isna(), "prev_x"] = df.loc[
            (~main_mask) & df["prev_x"].isna(), "x"
        ]
        df.loc[(~main_mask) & df["prev_y"].isna(), "prev_y"] = df.loc[
            (~main_mask) & df["prev_y"].isna(), "y"
        ]

        df.loc[main_mask & df["prev_x"].isna(), "prev_x"] = df.loc[
            main_mask & df["prev_x"].isna(), "x"
        ]
        df.loc[main_mask & df["prev_y"].isna(), "prev_y"] = df.loc[
            (main_mask) & df["prev_y"].isna(), "y"
        ]

        # Drop the message column
        df = df.drop(columns=["message"])

        if save_filename is not None and isinstance(save_filename, str):
            df.to_csv(save_filename, index=False)

        return df

    def close_connection(self):
        """
        Close the MongoDB connection.
        """
        try:
            if hasattr(self, "client") and self.client:
                self.client.close()

        except Exception as e:
            print(f"Error closing MongoDB connection: {e}")
