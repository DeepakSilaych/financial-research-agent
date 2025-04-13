import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from migrations.add_report_fields import migrate as add_report_fields

def run_migrations():
    """Run all database migrations"""
    print("Running database migrations...")
    
    # Add report fields migration
    add_report_fields()
    
    print("Database migrations completed")
    
if __name__ == "__main__":
    run_migrations() 