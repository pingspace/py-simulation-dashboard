from typing import List

from pydantic import BaseModel


class Configuration(BaseModel):
    """
    Class to represent the configuration of the simulation from input JSON

    Attributes
    ----------
    id : int
        The ID of the simulation.
    name : str
        The name of the simulation.
    server_number : int
        The server number used to run the simulation.
    duration_string : str
        The duration of the simulation to indicate the normal and advance order
        operation ranges. An example is "N800;AO1000;N500".
    """

    id: int
    name: str
    server_number: int
    duration_string: str


class Station(BaseModel):
    """
    Class to represent a station from input JSON.

    Attributes
    ----------
    code : int
        The code of the station.
    type : str
        The type of the station. Usually "I" for inbound and "O" for outbound.
    """

    code: int
    type: str


class Parameters(BaseModel):
    """
    Class to represent the parameters of the simulation from input JSON.

    Attributes
    ----------
    inbound_time : int
        The inbound handling time in seconds.
    outbound_time : int
        The outbound handling time in seconds.
    inbound_bins_per_order : int
        The number of inbound bins per order.
    outbound_bins_per_order : int
        The number of outbound bins per order.
    inbound_orders_per_hour : int
        The number of inbound orders per hour.
    outbound_orders_per_hour : int
        The number of outbound orders per hour.
    pareto_probabilities : List[float]
        The Pareto probabilities of the simulation. The length of the list is the
        z-height of the grid.
    """

    inbound_time: int
    outbound_time: int
    inbound_bins_per_order: int
    outbound_bins_per_order: int
    inbound_orders_per_hour: int
    outbound_orders_per_hour: int
    pareto_probabilities: List[float]


class StationGroup(BaseModel):
    """
    Class to represent a station group from input JSON. A group of two stations will
    share the same order.

    Attributes
    ----------
    group : int
        The group index of the station group.
    station_codes : List[int]
        The codes of the stations in the group.
    """

    group: int
    station_codes: List[int]


class JobsCreationRequest(BaseModel):
    """
    Class to represent the jobs creation request from input JSON.

    Attributes
    ----------
    parameters : Parameters
        The parameters of the simulation.
    configuration : Configuration
        The configuration of the simulation.
    stations : List[Station]
        The stations of the simulation.
    station_groups : List[StationGroup]
        The station groups of the simulation.
    """

    parameters: Parameters
    configuration: Configuration
    stations: List[Station]
    station_groups: List[StationGroup]
