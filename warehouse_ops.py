import psycopg2
from psycopg2 import sql
import random
import matplotlib.pyplot as plt


class WarehouseOps:
    def __init__(self, dbname: str, user: str, password: str, host: str,
                 drop_db_flag: bool):
        """
        Initialize the WarehouseOps instance.

        Parameters:
        dbname (str): Name of the database.
        user (str): Username for the database.
        password (str): Password for the database user.
        host (str): Database host address.
        drop_db_flag (bool): Flag indicating whether to drop the existing database.

        Returns:
        None
        """

        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.conn = None
        self.cur = None
        self.settings = self.warehouse_settings()

        # Open log file in write mode to clear existing content
        self.log_file = open("log.txt", "w")

        self.log("Starting database operations")
        if drop_db_flag:
            self.drop_db()
        self.connect_db()
        if drop_db_flag:
            self.create_tables()

    def log(self, message):
        """
        Write a log message to the log file.

        Parameters:
        message (str): The message to be logged.

        Returns:
        None
        """
        self.log_file.write(f"{message}\n")

    def drop_db(self):
        """
        Drop the existing database.

        This method deletes the current database if the drop_db_flag is set to True during initialization.

        Returns:
        None
        """
        try:
            conn = psycopg2.connect(dbname="postgres", user=self.user, password=self.password, host=self.host)
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute(sql.SQL("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = %s
                AND pid <> pg_backend_pid()
            """), [self.dbname])
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(self.dbname)))
            self.log(f"Database {self.dbname} dropped if it existed")
            cur.close()
            conn.close()
        except Exception as e:
            self.log(f"Error dropping database: {e}")

    def connect_db(self):
        """
        Connect to the PostgreSQL database.

        This method establishes a connection to the specified PostgreSQL database using the credentials and host provided during initialization.

        Returns:
        None
        """
        try:
            conn = psycopg2.connect(dbname="postgres", user=self.user, password=self.password, host=self.host)
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{self.dbname}'")
            exists = cur.fetchone()
            if not exists:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.dbname)))
                self.log(f"Database {self.dbname} created")
            cur.close()
            conn.close()
            self.conn = psycopg2.connect(dbname=self.dbname, user=self.user, password=self.password, host=self.host)
            self.cur = self.conn.cursor()
            self.log(f"Connected to database {self.dbname}")
        except Exception as e:
            self.log(f"Error connecting to database: {e}")

    def warehouse_settings(self):
        """
        Retrieve the warehouse settings.

        This method fetches and returns the configuration settings for the warehouse,
        which include parameters such as minimum sale quantity, maximum capacity, and other operational limits.

        Returns:
        dict: A dictionary containing warehouse configuration settings.
        """
        settings = {
            "product_name": ["Coca-Cola 1.5L", "Sprite 1.5L", "Fanta 1.5L",
                             "Spa 1.5L", "Lipton Tea 1L", "Heinz Ketchup 750ml",
                             "Calve Mayonnaise 250ml", "Italian Pasta 500g",
                             "Penne Pasta 350g", "Witte Rijst 1kg", "Bruine Rijst 600g",
                             "Salted Nuts 200g", "Bloemenhoning 300g", "Hero Jam 600g",
                             "Robijn Wasmiddel 1L", "Ariel 4in1 30pods", "Parodontax Tandpasta 75ml",
                             "Colgate 80ml", "Oral-B 80ml", "Listerine 500ml"],
            "n_units_per_pallet": [350, 350, 350, 350, 400, 500, 500, 200, 250,
                                   600, 550, 800, 400, 550, 350, 500, 800, 800,
                                   800, 450],
            "floor_locations": [f"AM-D-0{i}-01-1" for i in range(21, 61, 2)],
            "n_pallets_floor": 2,
            "loading_dock_label": "L-PALLET",
            "n_pallets_loading_dock": 30,
            "buffer_locations": [f"AM-PALLET-{20+i}-01" for i in range(30)],
            "n_pallets_buffer": 1,
            "storage_label": "STORAGE",
            "n_pallets_storage": 100,
            "new_pallets": 0.7,  # expected n = 20 * 0.7
            "variation": 0.2,    #
            "min_sale": 0        # 0-nothing sells, 1-all sells,
        }
        return settings

    def create_tables(self):
        """
        Create the necessary tables in the database.

        This method creates the required tables for the warehouse operations,
        such as tables for pallets, products, and locations.

        Returns:
        None
        """
        try:
            # Create Products table
            self.cur.execute("""
                CREATE TABLE Products (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    units_per_pallet INTEGER NOT NULL
                )
            """)
            self.log("Products table created")

            # Create Locations table
            self.cur.execute("""
                CREATE TABLE Locations (
                    id SERIAL PRIMARY KEY,
                    label VARCHAR(255) NOT NULL,
                    area VARCHAR(255) NOT NULL CHECK (area IN ('Floor', 'LoadingDock', 'Buffer', 'Storage')),
                    product_id INTEGER REFERENCES Products(id),
                    max_pallets INTEGER NOT NULL,
                    CHECK ((area = 'Floor' AND product_id IS NOT NULL) OR (area IN ('LoadingDock', 'Buffer', 'Storage') AND product_id IS NULL))
                )
            """)
            self.log("Locations table created")

            # Create Pallets table
            self.cur.execute("""
                CREATE TABLE Pallets (
                    id SERIAL PRIMARY KEY,
                    product_id INTEGER REFERENCES Products(id),
                    location_id INTEGER REFERENCES Locations(id),
                    quantity INTEGER NOT NULL
                )
            """)
            self.log("Pallets table created")

            # Create Movements table based on new design
            self.cur.execute("""
                CREATE TABLE Movements (
                    id SERIAL PRIMARY KEY,
                    event VARCHAR(50) NOT NULL,
                    storage INTEGER NOT NULL,
                    loadingdock INTEGER NOT NULL,
                    floor INTEGER NOT NULL,
                    buffer INTEGER NOT NULL
                )
            """)
            self.log("Movements table created")

            # Insert records into Products table and use the returned id to insert into Locations table
            settings = self.settings
            products = settings["product_name"]
            units_per_pallet = settings["n_units_per_pallet"]
            floor_locations = settings["floor_locations"]
            n_pallets_floor = settings["n_pallets_floor"]

            for name, units, loc in zip(products, units_per_pallet,
                                        floor_locations):
                self.cur.execute("""
                    INSERT INTO Products (name, units_per_pallet)
                    VALUES (%s, %s)
                    RETURNING id
                """, (name, units))
                product_id = self.cur.fetchone()[0]
                self.log(
                    f"Inserted product {name} with {units} units per pallet, id: {product_id}")

                self.cur.execute("""
                    INSERT INTO Locations (label, area, product_id, max_pallets)
                    VALUES (%s, 'Floor', %s, %s)
                """, (loc, product_id, n_pallets_floor))
                self.log(f"Inserted location {loc} for product id {product_id}")

            # Insert LoadingDock location
            loc = settings["loading_dock_label"]
            product_id = None  # Use None instead of NULL
            n_pallets_loading_dock = settings["n_pallets_loading_dock"]
            self.cur.execute("""
                INSERT INTO Locations (label, area, product_id, max_pallets)
                VALUES (%s, 'LoadingDock', %s, %s)
            """, (loc, product_id, n_pallets_loading_dock))
            self.log(f"Inserted location {loc} for area LoadingDock")

            # Insert Storage locations
            storage_label = settings["storage_label"]
            n_pallets_storage = settings["n_pallets_storage"]
            self.cur.execute("""
                INSERT INTO Locations (label, area, product_id, max_pallets)
                VALUES (%s, 'Storage', %s, %s)
            """, (storage_label, None, n_pallets_storage))
            self.log(f"Inserted location {storage_label} for area Storage")

            # Insert Buffer locations
            buffer_locations = settings["buffer_locations"]
            n_pallets_buffer = settings["n_pallets_buffer"]
            for buffer_loc in buffer_locations:
                self.cur.execute("""
                    INSERT INTO Locations (label, area, product_id, max_pallets)
                    VALUES (%s, 'Buffer', %s, %s)
                """, (buffer_loc, None, n_pallets_buffer))
                self.log(f"Inserted location {buffer_loc} for area Buffer")

            # Place all 100 pallets into Storage
            self.cur.execute("""
                SELECT id FROM Locations WHERE area = 'Storage'
            """)
            storage_location_id = self.cur.fetchone()[0]

            for _ in range(settings["n_pallets_storage"]):
                self.cur.execute("""
                    INSERT INTO Pallets (product_id, location_id, quantity)
                    VALUES (%s, %s, %s)
                """, (None, storage_location_id, 0))
                self.log(
                    f"Inserted a pallet into Storage with product_id=NULL and quantity=0")

            self.conn.commit()
            self.log("All products, locations, and pallets inserted")
        except Exception as e:
            self.log(f"Error creating tables: {e}")

    def truck_arrives(self):
        """
        Handle the arrival of a truck with new pallets.

        This method simulates the arrival of a truck delivering new pallets of products
        to the loading dock. The number and type of pallets are determined based on the
        warehouse settings and current inventory levels.

        Returns:
        None
        """
        settings = self.settings
        products = settings["product_name"]
        units_per_pallet = settings["n_units_per_pallet"]
        new_pallets = int(settings["new_pallets"] * len(products))
        variation = int(new_pallets * settings["variation"])

        n_new_pallets = new_pallets + random.randint(-variation, variation)

        # Select random new pallets
        new_product_indices = random.sample(range(len(products)), n_new_pallets)
        for idx in new_product_indices:
            product_name = products[idx]
            units = units_per_pallet[idx]

            # Move a pallet from Storage to LoadingDock
            self.cur.execute("""
                SELECT id FROM Pallets WHERE location_id = (
                    SELECT id FROM Locations WHERE area = 'Storage'
                ) LIMIT 1
            """)
            pallet_id = self.cur.fetchone()

            if pallet_id:
                pallet_id = pallet_id[0]
                self.cur.execute("""
                    UPDATE Pallets
                    SET product_id = %s, location_id = (
                        SELECT id FROM Locations WHERE area = 'LoadingDock'
                    ), quantity = %s
                    WHERE id = %s
                """, (idx + 1, units, pallet_id))
                self.log(
                    f"Moved pallet {pallet_id} with {product_name} to LoadingDock")
            else:
                self.log(
                    "No more pallets available in storage to move to LoadingDock")
                break  # Exit the loop if no pallets are available

        # Log the movement after all pallets have been moved
        self.log_movement('TruckArrives')

        self.conn.commit()

    def move_pallets_from_loading_dock(self):
        """
        Move pallets from the loading dock to the floor or buffer areas.

        This method checks the available space on the floor and buffer areas and moves
        pallets from the loading dock to these areas accordingly. It ensures that the
        loading dock is cleared as efficiently as possible based on space constraints.

        Returns:
        None
        """
        # Query for pallets in LoadingDock
        self.cur.execute("""
            SELECT id, product_id FROM Pallets 
            WHERE location_id = (SELECT id FROM Locations WHERE area = 'LoadingDock')
        """)
        pallets = self.cur.fetchall()

        for pallet_id, product_id in pallets:
            # Check if there's space in the Floor area for this product
            self.cur.execute("""
                SELECT id FROM Locations 
                WHERE area = 'Floor' AND product_id = %s 
                AND (SELECT COUNT(*) FROM Pallets WHERE location_id = Locations.id) < 2
            """, (product_id,))
            floor_location = self.cur.fetchone()

            if floor_location:
                # Move pallet to the available floor location
                self.cur.execute("""
                    UPDATE Pallets
                    SET location_id = %s
                    WHERE id = %s
                """, (floor_location[0], pallet_id))
                self.log(
                    f"Moved pallet {pallet_id} with product_id {product_id} to Floor location {floor_location[0]}")
            else:
                # Move pallet to an empty Buffer location
                self.cur.execute("""
                    SELECT id FROM Locations 
                    WHERE area = 'Buffer' 
                    AND (SELECT COUNT(*) FROM Pallets WHERE location_id = Locations.id) = 0
                    LIMIT 1
                """)
                buffer_location = self.cur.fetchone()
                if buffer_location:
                    self.cur.execute("""
                        UPDATE Pallets
                        SET location_id = %s
                        WHERE id = %s
                    """, (buffer_location[0], pallet_id))
                    self.log(
                        f"Moved pallet {pallet_id} with product_id {product_id} to Buffer location {buffer_location[0]}")
                else:
                    self.log(
                        f"No available space for pallet {pallet_id} with product_id {product_id}")

        # Log the movement after all pallets have been moved
        self.log_movement('LoadingDock')

        self.conn.commit()

    def simulate_daily_sales(self):
        """
        Simulate daily sales of products on the floor area.

        This method simulates the sale of products from pallets located on the floor.
        It reduces the quantity of each product based on a random sale quantity and
        updates the inventory accordingly. If a pallet is emptied, it is moved to
        storage.

        Returns:
        None
        """
        settings = self.settings
        min_sale = settings["min_sale"]

        # Query for pallets in the Floor area
        self.cur.execute("""
            SELECT p.id, p.product_id, p.quantity, pr.units_per_pallet 
            FROM Pallets p
            JOIN Products pr ON p.product_id = pr.id
            WHERE p.location_id IN (
                SELECT id FROM Locations WHERE area = 'Floor'
            )
        """)
        pallets = self.cur.fetchall()

        for pallet_id, product_id, quantity, units_per_pallet in pallets:
            # Decrease quantity by a whole number based on units_per_pallet
            sale_quantity = int(random.uniform(min_sale, 1) * units_per_pallet)
            new_quantity = quantity - sale_quantity

            if new_quantity > 0:
                # Update the pallet with the new quantity
                self.cur.execute("""
                    UPDATE Pallets
                    SET quantity = %s
                    WHERE id = %s
                """, (new_quantity, pallet_id))
                self.log(
                    f"Sold {sale_quantity} units from pallet {pallet_id}, new quantity is {new_quantity}")
            else:
                # Move the empty pallet to Storage
                self.cur.execute("""
                    UPDATE Pallets
                    SET product_id = NULL, location_id = (
                        SELECT id FROM Locations WHERE area = 'Storage'
                    ), quantity = 0
                    WHERE id = %s
                """, (pallet_id,))
                self.log(f"Pallet {pallet_id} is empty and moved to Storage")

        # Log the movement
        self.log_movement('Sales')

        self.conn.commit()

    def move_from_buffer(self):
        """
        Move pallets from the buffer area to the floor area.

        This method transfers pallets from the buffer area to the floor area, ensuring
        that products are available for sale. It checks for available space on the
        floor and moves pallets accordingly to maintain optimal inventory levels.

        Returns:
        None
        """
        # Query for available spots in the Floor area
        self.cur.execute("""
            SELECT id, product_id FROM Locations 
            WHERE area = 'Floor' AND (
                SELECT COUNT(*) FROM Pallets WHERE location_id = Locations.id
            ) < Locations.max_pallets
        """)
        floor_locations = self.cur.fetchall()

        for floor_location_id, product_id in floor_locations:
            # Find a pallet with the required product_id in the Buffer area
            self.cur.execute("""
                SELECT id FROM Pallets 
                WHERE product_id = %s AND location_id IN (
                    SELECT id FROM Locations WHERE area = 'Buffer'
                )
                LIMIT 1
            """, (product_id,))
            buffer_pallet = self.cur.fetchone()

            if buffer_pallet:
                # Move the pallet from Buffer to Floor
                self.cur.execute("""
                    UPDATE Pallets
                    SET location_id = %s
                    WHERE id = %s
                """, (floor_location_id, buffer_pallet[0]))
                self.log(
                    f"Moved pallet {buffer_pallet[0]} with product_id {product_id} from Buffer to Floor location {floor_location_id}")

        # Log the movement
        self.log_movement('BufferMoves')

        self.conn.commit()

    def simulate(self, days=10):
        """
        Run the warehouse operations simulation for a given number of days.

        This method simulates the daily operations of the warehouse over a specified number of days.
        Each day, the following events are executed in sequence:
        1. Truck arrives with new pallets.
        2. Pallets are moved from the loading dock to floor or buffer areas.
        3. Daily sales are simulated, reducing inventory on the floor.
        4. Pallets are moved from the buffer to the floor if needed.
        5. Pallets are moved from the loading dock again to clear any remaining pallets.

        Parameters:
        days (int): The number of days to run the simulation (default is 10).

        Returns:
        None
        """
        for day in range(days):
            self.log(f"Day {day + 1} simulation starts")

            # Event 1: Truck Arrives
            self.truck_arrives()

            # Event 2: Move Pallets from Loading Dock
            self.move_pallets_from_loading_dock()

            # Event 3: Simulate Daily Sales
            self.simulate_daily_sales()

            # Event 4: Move from Buffer
            self.move_from_buffer()

            # Event 5: Move Pallets from Loading Dock again
            self.move_pallets_from_loading_dock()

            self.log(f"Day {day + 1} simulation ends")

    def log_movement(self, event):
        """
        Log the movement of pallets in the warehouse.

        This method records the movement event in the database by inserting a new record
        into the Movements table. The record includes the event description and the current
        count of pallets in the storage, loading dock, floor, and buffer areas.

        Parameters:
        event (str): A description of the movement event.

        Returns:
        None
        """
        self.cur.execute("""
            INSERT INTO Movements (event, storage, loadingdock, floor, buffer)
            VALUES (
                %s,
                (SELECT COUNT(*) FROM Pallets WHERE location_id IN (
                    SELECT id FROM Locations WHERE area = 'Storage'
                )),
                (SELECT COUNT(*) FROM Pallets WHERE location_id IN (
                    SELECT id FROM Locations WHERE area = 'LoadingDock'
                )),
                (SELECT COUNT(*) FROM Pallets WHERE location_id IN (
                    SELECT id FROM Locations WHERE area = 'Floor'
                )),
                (SELECT COUNT(*) FROM Pallets WHERE location_id IN (
                    SELECT id FROM Locations WHERE area = 'Buffer'
                ))
            )
        """, (event,))
        self.log(f"Logged movement: {event}")
        self.conn.commit()

    def make_figure(self):
        """
        Create a bar chart showing pallet movements over time.

        This method retrieves data from the Movements table, converts it into lists,
        and generates a stacked bar chart using Matplotlib. The chart displays the
        number of pallets in storage, loading dock, floor, and buffer areas over time.

        Returns:
        None
        """
        self.cur.execute("""
            SELECT storage, loadingdock, floor, buffer FROM Movements
        """)
        data = self.cur.fetchall()

        # Convert data to lists
        storage = [row[0] for row in data]
        loadingdock = [row[1] for row in data]
        floor = [row[2] for row in data]
        buffer = [row[3] for row in data]

        # Create figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))

        # Create a bar chart with stacked bars
        bar_width = 0.35
        ind = range(len(storage))

        ax.bar(ind, storage, bar_width, label='Storage', color='b')
        ax.bar(ind, loadingdock, bar_width, bottom=storage, label='LoadingDock',
               color='g')
        ax.bar(ind, floor, bar_width,
               bottom=[i + j for i, j in zip(storage, loadingdock)],
               label='Floor', color='r')
        ax.bar(ind, buffer, bar_width, bottom=[i + j + k for i, j, k in
                                               zip(storage, loadingdock,
                                                   floor)], label='Buffer',
               color='y')

        # Add labels
        ax.set_xlabel('Time')
        ax.set_ylabel('Number of Pallets')
        ax.set_title('Pallet Movements Over Time')

        # Place the legend outside the figure
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        plt.tight_layout()
        plt.show()

    def __del__(self):
        """
        Destructor method to close the log file.

        This method is called when the WarehouseOps instance is about to be destroyed.
        It logs a message indicating that the log file is being closed and then closes
        the log file to ensure all log entries are properly saved.

        Returns:
        None
        """
        self.log("Closing log file")
        self.log_file.close()


# Example usage
db_pwd = input("db password=")
var = input("DROP existing db (y/n)?=")
drop_flag = True if var in ("y", "Y") else False

ops = WarehouseOps(dbname="FC3", user="postgres", password=db_pwd,
                   host="localhost", drop_db_flag=drop_flag)

days = int(input("How many days to simulate? "))
ops.simulate(days=days)
ops.make_figure()
