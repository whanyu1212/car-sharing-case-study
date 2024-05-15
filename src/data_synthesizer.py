import random
from datetime import datetime, timedelta
from typing import List, Tuple

import numpy as np
import polars as pl


class DataSynthesizer:
    def __init__(self, seed: int = 42, n: int = 10000, m: int = 1000):
        self.seed = seed
        np.random.seed(seed)
        self.n = n
        self.m = m
        self.trip_hist_data = self.generate_trip_hist_data()
        self.charge_status_data = self.generate_charge_status_data(self.trip_hist_data)
        self.car_q_pop_data = self.generate_car_q_pop_data(self.trip_hist_data)
        self.park_q_pop_data = self.generate_park_q_pop_data(self.trip_hist_data)

    def generate_random_datetimes(self) -> Tuple[list, list]:
        """
        Generate random datetimes for start and end of trips.

        Returns:
            Tuple[list, list]: list of start and end datetimes
        """
        start_datetimes = [
            datetime.now()
            - timedelta(
                days=random.randint(0, 365),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59),
            )
            for _ in range(self.n)
        ]
        end_datetimes = [
            start
            + timedelta(
                hours=random.randint(0, 2),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59),
            )
            for start in start_datetimes
        ]
        return start_datetimes, end_datetimes

    def generate_random_ids(self, prefix: str, id_range: Tuple[int, int]) -> List[str]:
        """
        Generate synthetic car and customer ids.

        Args:
            prefix (str): prefix for the id
            id_range (Tuple[int, int]): lower and upper bounds for the id

        Returns:
            List[str]: list of ids
        """
        return [prefix + str(id) for id in np.random.randint(*id_range, self.n)]

    def generate_random_distances(self) -> List[float]:
        """
        Generate random distances travelled.

        Args:
            n (int): number of entries to generate

        Returns:
            List[float]: list of distances
        """
        return np.random.uniform(1.0, 50.0, self.n)

    def generate_trip_hist_data(self) -> pl.DataFrame:
        """
        Generate synthetic trip history data by calling the other helper
        functions.

        Returns:
            pl.DataFrame: trip history data in a polars DataFrame
        """
        start_datetimes, end_datetimes = self.generate_random_datetimes()
        start_station_ids = np.random.randint(1, 380, self.n)
        end_station_ids = np.random.randint(1, 380, self.n)
        distances_travelled = self.generate_random_distances()
        car_ids = self.generate_random_ids("CAR", (1000, 9999))
        customer_ids = self.generate_random_ids("CUS", (1000, 9999))

        data = {
            "trip_start_datetime": start_datetimes,
            "trip_end_datetime": end_datetimes,
            "start_station_id": start_station_ids,
            "end_station_id": end_station_ids,
            "distance_travelled": distances_travelled,
            "car_id": car_ids,
            "customer_id": customer_ids,
        }

        df = pl.DataFrame(data)

        return df

    def generate_charge_levels(self) -> Tuple[pl.Series, pl.Series]:
        """Generate random charge levels for the start and end of trips.

        Returns:
            Tuple[pl.Series, pl.Series]: tuple of start and end charge levels
        """
        start_charge_level = np.random.randint(0, 100, self.n)
        end_charge_level = start_charge_level - np.random.randint(0, 100, self.n)
        end_charge_level[end_charge_level < 0] = np.random.randint(
            0, 10, size=(end_charge_level < 0).sum()
        )
        return pl.Series(start_charge_level), pl.Series(end_charge_level)

    def generate_charge_status_data(self, trip_data: pl.DataFrame) -> pl.DataFrame:
        """
        Using the trip history data to generate charge status data.

        Args:
            trip_data (pl.DataFrame): trip history data

        Returns:
            pl.DataFrame: charge status data in a polars DataFrame
        """
        start_charge_level, end_charge_level = self.generate_charge_levels()

        df = (
            trip_data.select(
                [
                    pl.col("trip_start_datetime"),
                    pl.col("trip_end_datetime"),
                    pl.col("start_station_id"),
                    pl.col("end_station_id"),
                    pl.col("car_id"),
                ]
            )
            .with_columns(start_charge_level.alias("start_charge_level"))
            .with_columns(end_charge_level.alias("end_charge_level"))
        )

        return df

    def generate_successful_data(
        self,
        trip_data: pl.DataFrame,
        creation_delta_max: int = 30,
        expiry_delta_max: int = 30,
        add_time: bool = False,
    ) -> pl.DataFrame:
        """Generate event data where the event
        status is successful. We will use the trip
        history data as basis and assume that the event creation
        is somewhere near the trip start time. negative timedelta for
        reserving a car and positive timedelta for reserving a parking
        spot.

        Args:
            trip_data (pl.DataFrame): trip history data
            creation_delta_max (int, optional): Upper bound of creation delta. Defaults to 30.
            expiry_delta_max (int, optional): . Defaults to 30.
            add_time (bool, optional): Boolean to decide whether the event is initialized
            before or after starting the trip. This will help us determine whether it
            is a car reservation event or parking spot reservation event. Defaults to False.

        Returns:
            pl.DataFrame: data with event status as successful
        """
        if add_time:
            event_creation_datetime = pl.col("trip_start_datetime") + timedelta(
                minutes=random.randint(0, creation_delta_max)
            )
        else:
            event_creation_datetime = pl.col("trip_start_datetime") - timedelta(
                minutes=random.randint(0, creation_delta_max)
            )

        return (
            trip_data.with_columns(pl.lit("successful").alias("event_status"))
            .with_columns(event_creation_datetime=event_creation_datetime)
            .with_columns(
                event_expiry_datetime=pl.col("event_creation_datetime")
                + timedelta(minutes=expiry_delta_max)
            )
        )

    def generate_unsuccessful_data(self, col: str) -> pl.DataFrame:
        """Generate event data where the event status is unsuccessful.
        The column name is passed as an argument to determine the type of event.

        Args:
            col (str): Either start_station_id or end_station_id

        Returns:
            pl.DataFrame: data with event status as unsuccessful
        """
        creation_datetimes = [
            datetime.now()
            - timedelta(
                days=random.randint(0, 365),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59),
            )
            for _ in range(self.m)
        ]

        expiry_datetimes = [
            creation + timedelta(minutes=30) for creation in creation_datetimes
        ]
        df = pl.DataFrame(
            {
                "trip_start_datetime": [None] * self.m,
                "trip_end_datetime": [None] * self.m,
                "start_station_id": [None] * self.m,
                "end_station_id": [None] * self.m,
                "distance_travelled": [None] * self.m,
                "car_id": [None] * self.m,
                "customer_id": [
                    "CUS" + str(id) for id in np.random.randint(1000, 9999, self.m)
                ],
                "event_status": ["unsuccessful"] * self.m,
                "event_creation_datetime": creation_datetimes,
                "event_expiry_datetime": expiry_datetimes,
            }
        )
        df = df.with_columns(
            pl.col(col).apply(
                lambda _: np.random.randint(1, 380), return_dtype=pl.Int64
            )
        )
        return df

    def generate_car_q_pop_data(self, trip_data: pl.DataFrame) -> pl.DataFrame:
        """Generate car queue population data by concatenating successful and unsuccessful
        event data.

        Args:
            trip_data (pl.DataFrame): trip history data, basis for generating event data

        Returns:
            pl.DataFrame: car queue population data
        """
        successful_data = self.generate_successful_data(trip_data)
        unsuccessful_data = self.generate_unsuccessful_data("start_station_id")
        return successful_data.vstack(unsuccessful_data)

    def generate_park_q_pop_data(self, trip_data: pl.DataFrame) -> pl.DataFrame:
        """Generate parking queue population data by concatenating successful and unsuccessful
        event data.

        Args:
            trip_data (pl.DataFrame): trip history data, basis for generating event data

        Returns:
            pl.DataFrame: parking queue population data
        """
        successful_data = self.generate_successful_data(trip_data, 30, 10, True)
        unsuccessful_data = self.generate_unsuccessful_data("end_station_id")
        return successful_data.vstack(unsuccessful_data)


# sample usage
if __name__ == "__main__":
    ds = DataSynthesizer()
    trip_df = ds.trip_hist_data
    charge_df = ds.charge_status_data
    car_q_pop_df = ds.car_q_pop_data
    park_q_pop_df = ds.park_q_pop_data
    print(trip_df)
    print(charge_df)
    print(car_q_pop_df)
    print(park_q_pop_df)
