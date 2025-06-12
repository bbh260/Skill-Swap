import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.simple_app import create_app
    
    print("=== STARTING DATA DELETION ===")
    
    app = create_app()
    
    with app.app_context():
        # Import models inside app context
        from app.simple_app import User, SwapRequest, db
        
        print("Connected to database successfully")
        
        # Check existing data
        users = User.query.all()
        swap_requests = SwapRequest.query.all()
        
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"  - {user.email} (ID: {user.id})")
        
        print(f"Found {len(swap_requests)} swap requests")
        
        if len(users) == 0:
            print("No data to delete!")
        else:
            # Delete swap requests first
            deleted_requests = SwapRequest.query.delete()
            print(f"Deleted {deleted_requests} swap requests")
            
            # Delete users
            deleted_users = User.query.delete()
            print(f"Deleted {deleted_users} users")
            
            # Commit changes
            db.session.commit()
            print("✅ ALL DATA DELETED SUCCESSFULLY!")
            print("Your email, password, name, skills, and all other personal data have been removed.")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
