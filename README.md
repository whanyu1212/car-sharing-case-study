# Car sharing Case Study
This repository is dedicated to solving a complex optimization problem that arises in the context of car-sharing services. The problem involves determining the optimal number of charging ports to install at various stations to minimize dissatisfaction due to failed car and parking reservations.

## Data

The data used in this project is synthetically generated. This means that it's not based on real-world observations but is instead created artificially, often using random processes that mimic the real-world scenarios we're interested in. Synthetic data is a powerful tool for testing and development because it allows us to create a wide variety of scenarios that might not be readily available in collected datasets.

### Raw data
```mermaid
erDiagram
    TRIP-HISTORY ||--|| CHARGET-STATUS : has 
    TRIP-HISTORY {
        datetime trip_start_datetime
        datetime trip_end_datetime
        string start_station_id
        string end_station_id
        float64 distance_travelled
        string car_id
        string customer_id
    }

    CHARGET-STATUS {
        float64 charge_level_in
        float64 charget_level_out
        datetime datetime_in
        datetime datetime_out
        string station_id
        string car_id
    }

    CAR-Q-POP ||--o{ TRIP-HISTORY : contains
    CAR-Q-POP {
        string customer_id
        datetime event_creation_datetime
        datetime event_expiry_datetime
        string station_id
        string event_status
    }
    PARK-Q-POP ||--o{ TRIP-HISTORY : contains
    PARK-Q-POP {
        string customer_id
        datetime event_creation_datetime
        datetime event_expiry_datetime
        string station_id
        string event_status
    }
```
### Processed data that is ready for optimization


## Optimization Problem

The optimization problem we're solving is a form of resource allocation problem. We have a limited budget to install additional charging ports at various stations. The goal is to decide how many additional ports to install at each station in order to minimize the total dissatisfaction. Dissatisfaction is quantified based on the number of failed car and parking reservations, which occur when the demand exceeds the available resources.

The problem is solved using linear programming, a powerful mathematical technique for optimizing a linear objective function subject to linear equality and inequality constraints. The Python library `PuLP` is used to define and solve the problem.

