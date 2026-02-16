import sqlite3
import random
import os

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        print(e)
    return conn

def create_employee_db():
    print("Creating sample.db (Employees)...")
    if os.path.exists("sample.db"):
        os.remove("sample.db")
    
    conn = create_connection("sample.db")
    if conn is None:
        return

    cursor = conn.cursor()

    # Create Departments
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        location TEXT
    )
    ''')

    # Create Employees with expanded columns
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        salary REAL,
        department_id INTEGER,
        hire_date TEXT,
        position TEXT,
        email TEXT,
        FOREIGN KEY (department_id) REFERENCES departments (id)
    )
    ''')

    # Create Projects
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        budget REAL,
        start_date TEXT,
        end_date TEXT
    )
    ''')

    # Create Employee_Projects (Many-to-Many)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employee_projects (
        employee_id INTEGER,
        project_id INTEGER,
        hours_worked INTEGER,
        PRIMARY KEY (employee_id, project_id),
        FOREIGN KEY (employee_id) REFERENCES employees (id),
        FOREIGN KEY (project_id) REFERENCES projects (id)
    )
    ''')

    # Insert Departments
    departments = [
        ('IT', 'New York'), ('HR', 'London'), ('Sales', 'Tokyo'), 
        ('Marketing', 'San Francisco'), ('Finance', 'Chicago'), 
        ('R&D', 'Berlin'), ('Support', 'Mumbai'), ('Legal', 'Paris')
    ]
    cursor.executemany('INSERT INTO departments (name, location) VALUES (?, ?)', departments)

    # Insert specific employees (retaining original logic but expanding)
    employees = [
        ('Alice', 70000, 1, '2020-01-15', 'Software Engineer', 'alice@company.com'),
        ('Bob', 60000, 1, '2019-05-20', 'Junior Developer', 'bob@company.com'),
        ('Charlie', 55000, 2, '2021-03-10', 'HR Specialist', 'charlie@company.com'),
        ('David', 80000, 3, '2018-11-05', 'Sales Manager', 'david@company.com'),
        ('Eve', 72000, 1, '2020-08-22', 'Data Scientist', 'eve@company.com')
    ]
    # Add 45 more dummy employees
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    positions = ["Analyst", "Manager", "Coordinator", "Specialist", "Director", "Clerk"]
    
    for _ in range(45):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        name = f"{fname} {lname}"
        dept_id = random.randint(1, 8)
        salary = random.randint(40000, 120000)
        year = random.randint(2015, 2023)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        hire_date = f"{year}-{month:02d}-{day:02d}"
        pos = random.choice(positions)
        email = f"{fname.lower()}.{lname.lower()}@company.com"
        employees.append((name, salary, dept_id, hire_date, pos, email))

    cursor.executemany('INSERT INTO employees (name, salary, department_id, hire_date, position, email) VALUES (?, ?, ?, ?, ?, ?)', employees)

    # Insert Projects
    projects = [
        ('Website Redesign', 50000, '2023-01-01', '2023-06-30'),
        ('App Migration', 120000, '2023-02-15', '2023-12-31'),
        ('Marketing Campaign', 30000, '2023-03-01', '2023-05-31'),
        ('New Product Launch', 200000, '2023-04-01', '2024-04-01'),
        ('Internal Audit', 10000, '2023-05-15', '2023-06-15')
    ]
    cursor.executemany('INSERT INTO projects (name, budget, start_date, end_date) VALUES (?, ?, ?, ?)', projects)

    # Assign employees to projects
    assignments = []
    for emp_id in range(1, 51):
        if random.random() > 0.3: # 70% chance to be on a project
            proj_id = random.randint(1, 5)
            hours = random.randint(5, 40)
            assignments.append((emp_id, proj_id, hours))
    
    cursor.executemany('INSERT OR IGNORE INTO employee_projects (employee_id, project_id, hours_worked) VALUES (?, ?, ?)', assignments)

    conn.commit()
    conn.close()
    print("sample.db created successfully.")


def create_student_db():
    print("Creating student.db...")
    if os.path.exists("student.db"):
        os.remove("student.db")
        
    conn = create_connection("student.db")
    if conn is None:
        return

    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT,
        last_name TEXT,
        email TEXT UNIQUE,
        enrollment_year INTEGER,
        major TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_name TEXT,
        credits INTEGER,
        department TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS enrollments (
        enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        grade TEXT,
        semester TEXT,
        FOREIGN KEY (student_id) REFERENCES students (student_id),
        FOREIGN KEY (course_id) REFERENCES courses (course_id)
    )
    ''')

    # Dummy Data
    majors = ["Computer Science", "Mathematics", "Physics", "History", "Literature", "Biology"]
    students = []
    for i in range(1, 101):
        fname = f"Student{i}"
        lname = f"Lastname{i}"
        email = f"student{i}@university.edu"
        year = random.randint(2019, 2023)
        major = random.choice(majors)
        students.append((fname, lname, email, year, major))
    
    cursor.executemany('INSERT INTO students (first_name, last_name, email, enrollment_year, major) VALUES (?, ?, ?, ?, ?)', students)

    courses = [
        ('Intro to CS', 4, 'Computer Science'),
        ('Calculus I', 4, 'Mathematics'),
        ('Physics I', 4, 'Physics'),
        ('World History', 3, 'History'),
        ('English Lit', 3, 'Literature'),
        ('Data Structures', 4, 'Computer Science'),
        ('Algorithms', 4, 'Computer Science'),
        ('Linear Algebra', 3, 'Mathematics')
    ]
    cursor.executemany('INSERT INTO courses (course_name, credits, department) VALUES (?, ?, ?)', courses)

    enrollments = []
    grades = ['A', 'B', 'C', 'D', 'F']
    semesters = ['Fall 2023', 'Spring 2023', 'Fall 2022']
    
    for s_id in range(1, 101):
        # Enroll in 3-5 courses
        num_courses = random.randint(3, 5)
        chosen_courses = random.sample(range(1, 9), num_courses)
        for c_id in chosen_courses:
            g = random.choice(grades)
            sem = random.choice(semesters)
            enrollments.append((s_id, c_id, g, sem))
            
    cursor.executemany('INSERT INTO enrollments (student_id, course_id, grade, semester) VALUES (?, ?, ?, ?)', enrollments)

    conn.commit()
    conn.close()
    print("student.db created successfully.")


def create_ecommerce_db():
    print("Creating ecommerce.db...")
    if os.path.exists("ecommerce.db"):
        os.remove("ecommerce.db")

    conn = create_connection("ecommerce.db")
    if conn is None:
        return

    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        join_date TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        price REAL,
        stock_quantity INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        order_date TEXT,
        total_amount REAL,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        price_at_purchase REAL,
        FOREIGN KEY (order_id) REFERENCES orders (order_id),
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    )
    ''')

    # Dummy Data
    users = []
    for i in range(1, 51):
        users.append((f"user{i}", f"user{i}@shop.com", "2023-01-01"))
    cursor.executemany('INSERT INTO users (username, email, join_date) VALUES (?, ?, ?)', users)

    products = [
        ('Laptop', 'Electronics', 1200.00, 50),
        ('Smartphone', 'Electronics', 800.00, 100),
        ('Headphones', 'Electronics', 150.00, 200),
        ('T-Shirt', 'Clothing', 25.00, 500),
        ('Jeans', 'Clothing', 50.00, 300),
        ('Sneakers', 'Footwear', 80.00, 150),
        ('Coffee Maker', 'Home', 40.00, 80),
        ('Blender', 'Home', 35.00, 60),
        ('Book', 'Books', 15.00, 1000),
        ('Desk Chair', 'Furniture', 120.00, 40)
    ]
    cursor.executemany('INSERT INTO products (name, category, price, stock_quantity) VALUES (?, ?, ?, ?)', products)

    orders = []
    order_items = []
    
    for o_id in range(1, 101):
        u_id = random.randint(1, 50)
        o_date = f"2023-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        
        # Create items for this order
        num_items = random.randint(1, 5)
        current_total = 0
        
        for _ in range(num_items):
            p_idx = random.randint(0, 9)
            p = products[p_idx]
            p_id = p_idx + 1 # 1-based ID
            qty = random.randint(1, 3)
            price = p[2]
            current_total += price * qty
            order_items.append((o_id, p_id, qty, price))
            
        orders.append((u_id, o_date, current_total))

    cursor.executemany('INSERT INTO orders (user_id, order_date, total_amount) VALUES (?, ?, ?)', orders)
    
    cursor.executemany('INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase) VALUES (?, ?, ?, ?)', order_items)

    conn.commit()
    conn.close()
    print("ecommerce.db created successfully.")

if __name__ == "__main__":
    create_employee_db()
    create_student_db()
    create_ecommerce_db()
