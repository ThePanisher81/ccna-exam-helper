import json
import psycopg2

# Load the JSON data
with open('CCNA.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Database connection parameters
db_params = {
    'dbname': 'ccna_db',
    'user': '**********',
    'password': '***********',
    'host': 'localhost',
    'port': 5432
}

try:
    # Connect to the database
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    create_table_query = """
    CREATE TABLE IF NOT EXISTS questions (
        id SERIAL PRIMARY KEY,
        question TEXT NOT NULL,
        correct_answer TEXT NOT NULL,
        incorrect_answers TEXT[] NOT NULL
    )
    """
    cursor.execute(create_table_query)

    # Insert data into the table
    insert_query = """
    INSERT INTO questions (question, correct_answer, incorrect_answers)
    VALUES (%s, %s, %s)
    """
    for item in data:
        cursor.execute(insert_query, (item['question'], item['correct_answer'], item['incorrect_answers']))

    # Commit changes
    conn.commit()
    print("Table created and data inserted successfully!")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close the database connection
    if cursor:
        cursor.close()
    if conn:
        conn.close()
