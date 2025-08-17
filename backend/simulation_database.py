from urllib.parse import quote_plus

from config import (
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
    start_timestamp = Column(Float)
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

    def update_simulation_run_timestamp(
        self,
        simulation_run_id: int,
        start_timestamp: float = None,
        end_timestamp: float = None,
    ) -> bool:
        """
        Update the start or end timestamp for a simulation run.

        Parameters
        ----------
        simulation_run_id : int
            The ID of the simulation run.
        start_timestamp : float, optional
            The start timestamp of the simulation run, by default None.
        end_timestamp : float, optional
            The end timestamp of the simulation run, by default None.

        Returns
        -------
        bool
            True if the timestamp is updated successfully, False otherwise.
        """
        try:
            sim_run = (
                self.session.query(SimulationRun)
                .filter_by(id=simulation_run_id)
                .first()
            )
            if sim_run:
                if start_timestamp is not None:
                    sim_run.start_timestamp = start_timestamp
                elif end_timestamp is not None:
                    sim_run.end_timestamp = end_timestamp
                else:
                    raise ValueError("No timestamp provided")
                self.session.commit()
                return True
            print(f"No simulation run found with ID {simulation_run_id}")
            return False
        except SQLAlchemyError as e:
            print(f"Error updating simulation time: {e}")
            self.session.rollback()
            return False

    def log_action(
        self,
        timestamp: float,
        simulation_run_id: int,
        action: str,
        station_code: int | None = None,
        bin_code: int | None = None,
    ) -> bool:
        """
        Log an action to the simulation logs table.

        Parameters
        ----------
        timestamp : float
            The timestamp of the action.
        simulation_run_id : int
            The ID of the simulation run.
        action : str
            The action that was performed.
        station_code : int, optional
            The code of the station that the action belongs to, by default None.
        bin_code : int, optional
            The code of the bin that the action belongs to, by default None.

        Returns
        -------
        bool
            True if the action is logged successfully, False otherwise.
        """
        try:
            log = Log(
                timestamp=timestamp,
                simulation_run_id=simulation_run_id,
                action=action,
                station_code=station_code,
                bin_code=bin_code,
            )
            self.session.add(log)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            print(f"Error logging action: {e}")
            self.session.rollback()
            return False

    def close_connection(self):
        """
        Close the database connection.
        """
        self.session.close()
        self.engine.dispose()
