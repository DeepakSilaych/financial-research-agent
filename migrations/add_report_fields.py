import sqlite3
import os

def migrate():
    """
    Add workspace_id and visualizations columns to the reports table
    """
    # Get the path to the database file
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.db")
    
    print(f"Database path: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Error: Database file {db_path} does not exist.")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the columns already exist
        cursor.execute("PRAGMA table_info(reports)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add workspace_id column if it doesn't exist
        if "workspace_id" not in columns:
            print("Adding workspace_id column to reports table...")
            cursor.execute("ALTER TABLE reports ADD COLUMN workspace_id INTEGER REFERENCES workspaces(id)")
        else:
            print("workspace_id column already exists.")
        
        # Add visualizations column if it doesn't exist
        if "visualizations" not in columns:
            print("Adding visualizations column to reports table...")
            cursor.execute("ALTER TABLE reports ADD COLUMN visualizations TEXT")
        else:
            print("visualizations column already exists.")
        
        # Commit the changes
        conn.commit()
        print("Migration completed successfully.")
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate() 