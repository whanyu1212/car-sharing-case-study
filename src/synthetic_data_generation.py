import random
from datetime import datetime, timedelta
from typing import List, Tuple

import numpy as np
import polars as pl


class DataSynthesizer:
    def __init__(self, seed=42):
        self.seed = seed
        np.random.seed(seed)
        self.trip_hist_data = self.generate_trip_hist_data()
        self.charge_status_data = self.generate_charge_status_data(self.trip_hist_data)
        self.car_q_pop_data = self.generate_car_q_pop_data(self.trip_hist_data)
        self.park_q_pop_data = self.generate_park_q_pop_data(self.trip_hist_data)

    def generate_random_datetimes(self, n: int) -> Tuple[list, list]:
        """
        Generate random datetimes for start and end of trips.

        Args:
            n (int): number of entries to generate

        Returns:
            Tuple[list, list]: list of start and end datetimes
        """
        start_datetimes = [
            datetime.now() - timedelta(days=random.randint(0, 365)) for _ in range(n)
        ]
        end_datetimes = [
            start + timedelta(hours=random.uniform(0, 3)) for start in start_datetimes
        ]
        return start_datetimes, end_datetimes

    def generate_random_ids(
        self, prefix: str, id_range: Tuple[int, int], n: int
    ) -> List[str]:
        """
        Generate synthetic car and customer ids.

        Args:
            prefix (str): prefix for the id
            id_range (Tuple[int, int]): lower and upper bounds for the id
            n (int): number of entries to generate

        Returns:
            List[str]: list of ids
        """
        return [prefix + str(id) for id in np.random.randint(*id_range, n)]

    def generate_random_distances(self, n: int) -> List[float]:
        """
        Generate random distances travelled.

        Args:
            n (int): number of entries to generate

        Returns:
            List[float]: list of distances
        """
        return np.random.uniform(1.0, 50.0, n)

    def generate_trip_hist_data(self, n=10000) -> pl.DataFrame:
        """
        Generate synthetic trip history data by calling the other helper
        functions.

        Args:
            n (int, optional): number of entries to generate.
            Defaults to 10000.

        Returns:
            pl.DataFrame: trip history data in a polars DataFrame
        """
        start_datetimes, end_datetimes = self.generate_random_datetimes(n)
        start_station_ids = np.random.randint(1, 380, n)
        end_station_ids = np.random.randint(1, 380, n)
        distances_travelled = self.generate_random_distances(n)
        car_ids = self.generate_random_ids("CAR", (1000, 9999), n)
        customer_ids = self.generate_random_ids("CUS", (1000, 9999), n)

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

    def generate_charge_levels(self, n: int) -> Tuple[pl.Series, pl.Series]:
        start_charge_level = np.random.randint(0, 100, n)
        end_charge_level = start_charge_level - np.random.randint(0, 100, n)
        end_charge_level[end_charge_level < 0] = np.random.randint(
            0, 10, size=(end_charge_level < 0).sum()
        )
        return pl.Series(start_charge_level), pl.Series(end_charge_level)

    def generate_charge_status_data(
        self, trip_data: pl.DataFrame, n: int = 10000
    ) -> pl.DataFrame:
        """
        Using the trip history data to generate charge status data.

        Args:
            trip_data (pl.DataFrame): trip history data
            n (int, optional): number of entries. Defaults to 10000.

        Returns:
            pl.DataFrame: charge status data in a polars DataFrame
        """
        start_charge_level, end_charge_level = self.generate_charge_levels(n)

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
        trip_data,
        creation_delta_min: int = 30,
        expiry_delta_min: int = 30,
        add_time: bool = False,
    ) -> pl.DataFrame:
        if add_time:
            event_creation_datetime = pl.col("trip_start_datetime") + timedelta(
                minutes=random.randint(0, creation_delta_min)
            )
        else:
            event_creation_datetime = pl.col("trip_start_datetime") - timedelta(
                minutes=random.randint(0, creation_delta_min)
            )

        return (
            trip_data.with_columns(pl.lit("successful").alias("event_status"))
            .with_columns(event_creation_datetime=event_creation_datetime)
            .with_columns(
                event_expiry_datetime=pl.col("event_creation_datetime")
                + timedelta(minutes=expiry_delta_min)
            )
        )

    def generate_unsuccessful_data(self, col: str, m: int = 1000) -> pl.DataFrame:
        df = pl.DataFrame(
            {
                "trip_start_datetime": [None] * m,
                "trip_end_datetime": [None] * m,
                "start_station_id": [None] * m,
                "end_station_id": [None] * m,
                "distance_travelled": [None] * m,
                "car_id": [None] * m,
                "customer_id": self.generate_random_ids("CUS", (1000, 9999), m),
                "event_status": ["unsuccessful"] * m,
                "event_creation_datetime": [
                    datetime.now() - timedelta(days=random.randint(0, 365))
                    for _ in range(m)
                ],
                "event_expiry_datetime": [
                    datetime.now() + timedelta(minutes=30) for _ in range(m)
                ],
            }
        )
        df.with_columns(col=np.random.randint(1, 380, m))
        return df

    def generate_car_q_pop_data(self, trip_data, m: int = 1000) -> pl.DataFrame:
        successful_data = self.generate_successful_data(trip_data)
        unsuccessful_data = self.generate_unsuccessful_data("start_station_id", m)
        return successful_data.vstack(unsuccessful_data)

    def generate_park_q_pop_data(self, trip_data, m: int = 1000) -> pl.DataFrame:
        successful_data = self.generate_successful_data(trip_data, 30, 10, True)
        unsuccessful_data = self.generate_unsuccessful_data(m)
        return successful_data.vstack(unsuccessful_data)


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
    # df.write_csv("trip_hist_data.csv")
