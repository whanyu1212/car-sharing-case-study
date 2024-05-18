## Summary
This repository is dedicated to solving a complex optimization problem that arises in the context of car-sharing services. We want to determine which stations should be prioritized if the business is looking to increase the number of charging points per station from 4 to 6 to accommodate growing demand

### Data
Due to confidentiality restrictions, the actual dataset cannot be shared or viewed. Therefore, this project utilizes a synthetic dataset specifically designed to replicate the characteristics and behavior of the original data as closely as possible

### Data Schema and Entity Relationship
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

### Sample raw data (synthetic)

<img src="./img/trip.jpg" alt="trip" width="600" height="200"> <img src="./img/charge_level.jpg" alt="charge_level" width="600" height="200">
<img src="./img/car_qpop.jpg" alt="trip" width="500" height="200"> <img src="./img/park_qpop.jpg" alt="trip" width="500" height="200">

### Objective Function

Failed reservations for vehicles and parking spots **directly correlate with user dissatisfaction**, as each failed event can lead to frustration and potentially unsubscribing from the service. Measuring dissatisfaction through the number of failed car and parking reservation events provides a quantifiable metric to minimize. By increasing the number of charging points to fulfill unmet demands, we effectively reduce the likelihood of negative user experience. This approach not only enhances user experience and service reliability which aligns with the business objective of customer retention. 

<u>The objective can be formulated as:</u>
<br>
<img src="./img/equation.png" alt="eqn" width="400" height="100">

- **S**: Set of all charging stations.
- **T**: Set of all time periods.
- **f<sub>c</sub>(s, t)**: Number of failed car reservations at station *s* at time *t* due to lack of charging ports.
- **f<sub>p</sub>(s, t)**: Number of failed parking reservations at station *s* at time *t* due to lack of charging ports.
- **D<sub>c</sub>**: Dissatisfaction cost per failed car reservation.
- **D<sub>p</sub>**: Dissatisfaction cost per failed parking reservation.
- **x<sub>s</sub>**: Number of additional charging ports to install at station *s*.
- **c(s, t)**: Current capacity (number of charging ports) at station *s* at time *t*.

**Remark:** Assume the `dissatisfaction cost` for both car reservation and parking reservation to be the same, i.e., `1 unit each`

### Sample processed data (synthetic):
Ideally, we aim to have our daily aggregated or forecasted demand, along with the unmet demand, distributed evenly across various times of the day and different stations as follows:

<img src="./img/sample_processed_data.jpg" alt="trip" width="600" height="200">

### Additional considerations:
To prevent encountering an infeasible problem where the optimizer, in this case, a minimizer, can only deliver partial solutions. I have chosen not to set any upper limits on the number of additional charging ports required at each station or on the total budget. This strategy ensures that we can always generate a solvable solution to address all unmet demands comprehensively. From there, we will rank the stations by their demand in descending order. This ranking will then guide us in prioritizing which stations to upgrade first, ensuring an efficient allocation of resources based on actual demand levels.


### Sample final output

<img src="./img/sample_solution_output.jpg" alt="trip" width="600" height="400">

<br>

After evaluating the demand and sorting the stations in descending order, we can strategically prioritize the installation of additional charging ports. Based on available budget and cost considerations, we will focus on adding two more charging ports to the stations with the highest demand first.