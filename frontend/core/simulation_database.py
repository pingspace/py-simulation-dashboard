import time
from typing import Dict
from urllib.parse import quote_plus

import pandas
from core.config import (
    SIMULATION_DATABASE_HOST,
    SIMULATION_DATABASE_PASSWORD,
    SIMULATION_DATABASE_PORT,
    SIMULATION_DATABASE_USER,
)
from sqlalchemy import Column, Float, Integer, String, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class SimulationRun(Base):
    """
    Table to store simulation run information.

    Attributes
    ----------
    id : int
        The ID of the simulation run. It is incremented automatically.
    name : str
        The name of the simulation run.
    server_number : int
        The server number of the simulation run; either 1 or 2.
    start_timestamp : float
        The UNIX timestamp of the start of the simulation.
    end_timestamp : float
        The UNIX timestamp of the end of the simulation.
    """

    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    server_number = Column(Integer)
    start_timestamp = Column(Float, nullable=True)
    end_timestamp = Column(Float, nullable=True)


class Log(Base):
    """
    Table to store the simulation logs

    Attributes
    ----------
    id : int
        The ID of the log entry. It is incremented automatically.
    timestamp : float
        The UNIX timestamp of the log entry.
    simulation_run_id : int
        The ID of the simulation run that the log belongs to.
    action : str
        The action that was performed.
    station_code : int
        The code of the station that the log belongs to. If null, the log is not
        associated with a station.
    bin_code : int
        The code of the bin that the log belongs to. If null, the log is not
        associated with a bin.
    """

    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(Float)
    simulation_run_id = Column(Integer)
    action = Column(String)
    station_code = Column(Integer, nullable=True)
    bin_code = Column(Integer, nullable=True)


class Parameter(Base):
    """
    Table to store the simulation parameters.

    Attributes
    ----------
    id : int
        The ID of the parameter entry. It is incremented automatically.
    simulation_run_id : int
        The ID of the simulation run that the parameter belongs to.
    simulation_name : str
        The name of the simulation.
    simulation_duration : int
        The duration of the simulation in seconds.
    inbound_bins_per_order : int
        The number of inbound bins per order.
    outbound_bins_per_order : int
        The number of outbound bins per order.
    inbound_orders_per_hour : int
        The number of inbound orders per hour.
    outbound_orders_per_hour : int
        The number of outbound orders per hour.
    number_of_skycars : int
        The number of skycars in the simulation.
    inbound_handling_time : int
        The handling time for inbound orders in seconds.
    outbound_handling_time : int
        The handling time for outbound orders in seconds.
    pareto_p : float
        The Pareto p parameter.
    pareto_q : float
        The Pareto q parameter.
    number_of_bins : int
        The number of bins in the simulation.
    stations_string : str
        The string representation of the stations in the simulation.
    timestamp : float
        The UNIX timestamp of the parameter entry.
    duration_string : str
        The string representation of the duration of the simulation.
    station_groups_string : str
        The string representation of the station groups in the simulation.
    desired_skycar_directions_string : str
        The string representation of the desired skycar directions in the simulation, as
        given like the input.
    """

    __tablename__ = "parameters"

    id = Column(Integer, primary_key=True)
    simulation_run_id = Column(Integer)
    simulation_name = Column(String, nullable=True)
    simulation_duration = Column(Integer, nullable=True)
    inbound_bins_per_order = Column(Integer, nullable=True)
    outbound_bins_per_order = Column(Integer, nullable=True)
    inbound_orders_per_hour = Column(Integer, nullable=True)
    outbound_orders_per_hour = Column(Integer, nullable=True)
    number_of_skycars = Column(Integer, nullable=True)
    inbound_handling_time = Column(Integer, nullable=True)
    outbound_handling_time = Column(Integer, nullable=True)
    pareto_p = Column(Float, nullable=True)
    pareto_q = Column(Float, nullable=True)
    number_of_bins = Column(Integer, nullable=True)
    stations_string = Column(String, nullable=True)
    timestamp = Column(Float, nullable=True)
    duration_string = Column(String, nullable=True)
    station_groups_string = Column(String, nullable=True)
    desired_skycar_directions_string = Column(String, nullable=True)


class SimulationDatabase:
    """
    Class related to interacting with the simulation database.
    """

    def __init__(self):
        database_url = (
            f"postgresql://{quote_plus(SIMULATION_DATABASE_USER)}:{quote_plus(SIMULATION_DATABASE_PASSWORD)}"
            f"@{SIMULATION_DATABASE_HOST}:{SIMULATION_DATABASE_PORT}/matrix_simulation"
        )
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        Base.metadata.create_all(self.engine)

    def add_simulation_run(self, name: str, server_number: int) -> int | None:
        """
        Adds a new simulation run to the simulation_runs table.

        Parameters
        ----------
        name : str
            The name of the simulation run.
        server_number : int
            The server number of the simulation run; either 1 or 2.

        Returns
        -------
        int | None
            The ID of the simulation run if successful, None if unsuccessful.
        """
        try:
            sim_run = SimulationRun(name=name, server_number=server_number)
            self.session.add(sim_run)
            self.session.commit()
            return sim_run.id
        except SQLAlchemyError as e:
            print(f"Error adding simulation run: {e}")
            self.session.rollback()
            return None

    def add_simulation_parameters(
        self, simulation_run_id: int, parameters: Dict
    ) -> int | None:
        """
        Adds new simulation parameters to the parameters table.

        Parameters
        ----------
        simulation_run_id : int
            The ID of the simulation run that the parameters belong to.
        parameters : dict
            A dictionary of parameters to add to the parameters table. This dictionary 
            assumes that the keys are the same as the attributes of the Parameter class.

        Returns
        -------
        int | None
            The ID of the parameter entry if successful, None if unsuccessful.
        """
        try:
            param = Parameter(
                **parameters, simulation_run_id=simulation_run_id, timestamp=time.time()
            )
            self.session.add(param)
            self.session.commit()
            return param.id
        except SQLAlchemyError as e:
            print(f"Error adding simulation parameters: {e}")
            self.session.rollback()
            return None

    def get_simulation_runs_by_timestamp_range(
        self, timestamp1: float, timestamp2: float
    ) -> pandas.DataFrame:
        """
        Retrieves simulation runs within a specified timestamp range.

        Parameters
        ----------
        timestamp1 : float
            The start timestamp of the range
        timestamp2 : float
            The end timestamp of the range

        Returns
        -------
        pandas.DataFrame
            A DataFrame of simulation runs within the specified timestamp range
        """
        try:
            query = text(
                f"""
                SELECT * FROM 
                get_simulation_runs_by_timestamp_range({timestamp1}, {timestamp2})
                """
            )
            result = self.session.execute(query)
            df = pandas.DataFrame(result.fetchall())
            if not df.empty:
                df.columns = result.keys()
            return df
    
        except SQLAlchemyError as e:
            print(f"Error retrieving simulation runs: {e}")
            return pandas.DataFrame()

    def get_logs_by_simulation_run(self, simulation_run_id: int) -> pandas.DataFrame:
        """
        Retrieves logs for a specific simulation run.

        Parameters
        ----------
        simulation_run_id : int
            The ID of the simulation run

        Returns
        -------
        pandas.DataFrame
            A DataFrame of logs for the specified simulation run
        """
        try:
            query = text(
                f"""
                SELECT * FROM get_logs_by_simulation_run({simulation_run_id})
                """
            )

            result = self.session.execute(query)
            df = pandas.DataFrame(result.fetchall())
            if not df.empty:
                df.columns = result.keys()
            return df
        except SQLAlchemyError as e:
            print(f"Error retrieving logs: {e}")
            return pandas.DataFrame()

    def get_parameters_by_simulation_run(
        self, simulation_run_id: int
    ) -> pandas.DataFrame:
        """
        Retrieves parameters for a specific simulation run.

        Parameters
        ----------
        simulation_run_id : int
            The ID of the simulation run

        Returns
        -------
        pandas.DataFrame
            A DataFrame of parameters for the specified simulation run
        """
        try:
            query = text(
                f"""
                SELECT * FROM public.parameters
                WHERE simulation_run_id = {simulation_run_id}
                """
            )
            result = self.session.execute(query)
            df = pandas.DataFrame(result.fetchall())
            if not df.empty:
                df.columns = result.keys()
            return df
        except SQLAlchemyError as e:
            print(f"Error retrieving parameters: {e}")
            return pandas.DataFrame()

    def close_connection(self):
        """
        Closes the database connection properly.
        """
        self.session.close()
        self.engine.dispose()
