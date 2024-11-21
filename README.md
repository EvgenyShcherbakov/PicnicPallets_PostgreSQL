WarehouseOps Simulation Project

Overview

WarehouseOps is a simulation project designed to manage and optimize warehouse operations. It simulates various processes such as truck arrivals, pallet movements, and daily sales to help understand and improve warehouse efficiency.

Workflow

The basic model workflow represents a simplified reality of warehouse operations:

•	Loading and Selling: Units are loaded onto pallets and sold from designated Floor locations for each product. Empty pallets are stored in the Storage location.

•	Replenishment: Trucks arrive to replenish stock. Pallets are taken from storage, filled with products, and left at the Loading dock location.

•	Database Query: The algorithm queries the database to check if the product's specific location can accept another pallet (each location can hold up to 2 pallets). If there is no space on the Floor, the pallet is sent to the Buffer location. The Loading dock must be cleared if possible.

•	Sales Simulation: During the day, sales are simulated by reducing the quantities on pallets at the Floor location with random variations. When a pallet becomes empty, it is sent to Storage, making space available on the Floor.

•	End of Day Checks: At the end of the day, the algorithm checks if fully loaded pallets in the Buffer can be moved to empty spots on the Floor. If any pallets were left in the Loading dock because they couldn't be moved in the morning, they are moved now.

•	Daily Cycle: The day ends, and the next day starts with the arrival of a truck with new products.

Simulation Parameters

The simulation parameters, found in the warehouse_settings dictionary, allow for different scenarios under various constraints, including:

•	Daily product delivery amounts (matching, higher than, or lower than the sale speed).

Investigation Goal

The goal is to determine under which parameters a bottleneck appears in the warehouse operations.

Features

•	Database Integration: Connects to a PostgreSQL database to manage warehouse data.

•	Simulation of Daily Operations: Simulates daily activities including truck arrivals, pallet movements, and sales.

•	Logging and Visualization: Logs important events and creates visualizations to analyze operations over time.

•	Configurable Settings: Allows customization of warehouse settings such as capacity and sale quantities.

Installation

Prerequisites

•	Python 3.x

•	PostgreSQL

Steps

1.	Clone the repository:

git clone https://github.com/EvgenyShcherbakov/PicnicPallets_PostgreSQL.git

cd PicnicPallets_PostgreSQL

2.	Install the required Python packages:
pip install -r requirements.txt

Usage
1.	Initialize the WarehouseOps instance:

from warehouse_ops import WarehouseOps

ops = WarehouseOps(dbname='your_db_name', user='your_username', password='your_password', host='your_host', drop_db_flag=True)

2.	Connect to the Database:

ops.connect_db()

3.	Create Tables:

ops.create_tables()

4.	Run the Simulation:

ops.simulate(days=10)

5.	Generate Visualization:

ops.make_figure()

Methods
__init__(self, dbname: str, user: str, password: str, host: str, drop_db_flag: bool)
Initializes the WarehouseOps instance.

drop_db(self)
Drops the existing database.

log(self, message: str)
Writes a log message to the log file.

connect_db(self)
Connects to the PostgreSQL database.

warehouse_settings(self)
Retrieves the warehouse settings.

create_tables(self)
Creates the necessary tables in the database.

truck_arrives(self)
Handles the arrival of a truck with new pallets.

move_pallets_from_loading_dock(self)
Moves pallets from the loading dock to the floor or buffer areas.

simulate_daily_sales(self)
Simulates daily sales of products on the floor area.

move_from_buffer(self)
Moves pallets from the buffer area to the floor area.

simulate(self, days=10)
Runs the warehouse operations simulation for a given number of days.

log_movement(self, event: str)
Logs the movement of pallets in the warehouse.

make_figure(self)
Creates a bar chart showing pallet movements over time.

__del__(self)
Destructor method to close the log file.

Contributing
Contributions are welcome! Please open an issue or submit a pull request.

Contact
If you have any questions or feedback, feel free to contact Evgeny Shcherbakov.
