WarehouseOps Simulation Project

Overview

WarehouseOps is a simulation project designed to manage and optimize warehouse operations. It simulates various processes such as truck arrivals, pallet movements, and daily sales to help understand and improve warehouse efficiency.

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
