#!/usr/bin/env python3
"""
Test User Creation Script for Skill Swap Platform

This script creates N test users with realistic data for testing the platform.
Usage: python create_test_users.py [number_of_users]
"""

import os
import sys
import random
from faker import Faker
from app.simple_app import create_app, db, User

# Initialize Faker for generating realistic test data
fake = Faker()

# Sample skills data organized by categories
SKILLS_DATA = {
    'Programming': [
        'Python', 'JavaScript', 'Java', 'C++', 'React', 'Node.js', 'Angular', 
        'Vue.js', 'Django', 'Flask', 'Spring Boot', 'HTML/CSS', 'TypeScript',
        'PHP', 'Ruby', 'Go', 'Rust', 'Swift', 'Kotlin', 'C#'
    ],
    'Design': [
        'UI/UX Design', 'Graphic Design', 'Adobe Photoshop', 'Adobe Illustrator',
        'Figma', 'Sketch', 'InDesign', 'After Effects', 'Blender', 'AutoCAD',
        'Web Design', 'Logo Design', 'Branding', 'Typography'
    ],
    'Business': [
        'Project Management', 'Digital Marketing', 'SEO', 'Content Writing',
        'Social Media Marketing', 'Email Marketing', 'Business Analysis',
        'Financial Analysis', 'Sales', 'Customer Service', 'Leadership',
        'Public Speaking', 'Negotiation', 'Strategic Planning'
    ],
    'Languages': [
        'Spanish', 'French', 'German', 'Italian', 'Portuguese', 'Chinese',
        'Japanese', 'Korean', 'Arabic', 'Russian', 'Hindi', 'Dutch',
        'Swedish', 'Norwegian', 'Finnish'
    ],
    'Creative': [
        'Photography', 'Video Editing', 'Music Production', 'Writing',
        'Creative Writing', 'Copywriting', 'Blogging', 'Podcasting',
        'Voice Acting', 'Animation', 'Drawing', 'Painting', 'Crafting'
    ],
    'Technical': [
        'Data Analysis', 'Machine Learning', 'Artificial Intelligence',
        'Cybersecurity', 'Cloud Computing', 'DevOps', 'Database Design',
        'System Administration', 'Network Administration', 'IT Support',
        'Quality Assurance', 'Testing', 'API Development'
    ],
    'Personal': [
        'Cooking', 'Fitness Training', 'Yoga', 'Meditation', 'Life Coaching',
        'Career Coaching', 'Time Management', 'Organization', 'Mentoring',
        'Tutoring', 'Teaching', 'Public Relations'
    ],
    'Trade Skills': [
        'Carpentry', 'Plumbing', 'Electrical Work', 'Gardening', 'Auto Repair',
        'Home Renovation', 'Painting (House)', 'Landscaping', 'HVAC',
        'Welding', 'Masonry', 'Roofing'
    ]
}

# Sample locations
LOCATIONS = [
    'New York, NY', 'Los Angeles, CA', 'Chicago, IL', 'Houston, TX',
    'Phoenix, AZ', 'Philadelphia, PA', 'San Antonio, TX', 'San Diego, CA',
    'Dallas, TX', 'San Jose, CA', 'Austin, TX', 'Jacksonville, FL',
    'Fort Worth, TX', 'Columbus, OH', 'Charlotte, NC', 'San Francisco, CA',
    'Indianapolis, IN', 'Seattle, WA', 'Denver, CO', 'Washington, DC',
    'Boston, MA', 'El Paso, TX', 'Nashville, TN', 'Detroit, MI',
    'Oklahoma City, OK', 'Portland, OR', 'Las Vegas, NV', 'Memphis, TN',
    'Louisville, KY', 'Baltimore, MD', 'Milwaukee, WI', 'Albuquerque, NM',
    'Tucson, AZ', 'Fresno, CA', 'Sacramento, CA', 'Kansas City, MO',
    'Mesa, AZ', 'Atlanta, GA', 'Omaha, NE', 'Colorado Springs, CO',
    'Raleigh, NC', 'Miami, FL', 'Virginia Beach, VA', 'Oakland, CA',
    'Minneapolis, MN', 'Tulsa, OK', 'Arlington, TX', 'Tampa, FL'
]

# Availability options
AVAILABILITY_OPTIONS = [
    'Weekdays', 'Weekends', 'Evenings', 'Flexible', 'Mornings',
    'Afternoons', 'Monday-Friday', 'Weekends Only'
]

def get_all_skills():
    """Get a flat list of all available skills"""
    all_skills = []
    for category, skills in SKILLS_DATA.items():
        all_skills.extend(skills)
    return all_skills

def generate_realistic_skills(all_skills, min_offered=1, max_offered=5, min_wanted=1, max_wanted=4):
    """Generate realistic skill combinations for a user"""
    # Number of skills offered and wanted
    num_offered = random.randint(min_offered, max_offered)
    num_wanted = random.randint(min_wanted, max_wanted)
    
    # Select random skills
    skills_offered = random.sample(all_skills, min(num_offered, len(all_skills)))
    
    # For skills wanted, prefer skills different from offered (simulate learning new things)
    remaining_skills = [skill for skill in all_skills if skill not in skills_offered]
    if len(remaining_skills) >= num_wanted:
        skills_wanted = random.sample(remaining_skills, num_wanted)
    else:
        # If not enough different skills, allow some overlap
        skills_wanted = random.sample(all_skills, min(num_wanted, len(all_skills)))
    
    return skills_offered, skills_wanted

def create_test_user(all_skills):
    """Create a single test user with realistic data"""
    # Generate basic info
    first_name = fake.first_name()
    last_name = fake.last_name()
    name = f"{first_name} {last_name}"
    
    # Generate email based on name
    email_prefix = f"{first_name.lower()}.{last_name.lower()}"
    email_domain = random.choice(['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'example.com'])
    email = f"{email_prefix}@{email_domain}"
    
    # Handle potential duplicate emails by adding numbers
    counter = 1
    original_email = email
    while User.query.filter_by(email=email).first():
        email = f"{original_email.split('@')[0]}{counter}@{email_domain}"
        counter += 1
    
    # Generate skills
    skills_offered, skills_wanted = generate_realistic_skills(all_skills)
    
    # Create user
    user = User(
        name=name,
        email=email,
        location=random.choice(LOCATIONS),
        availability=random.choice(AVAILABILITY_OPTIONS),
        is_public=random.choice([True, True, True, False]),  # 75% chance of being public
        is_banned=False
    )
    
    # Set password
    user.set_password('password123')  # Simple password for testing
    
    # Set skills
    user.skills_offered = skills_offered
    user.skills_wanted = skills_wanted
    
    return user

def create_test_users(num_users=10):
    """Create N test users and add them to the database"""
    
    print(f"Creating {num_users} test users...")
    print("-" * 50)
    
    # Get all available skills
    all_skills = get_all_skills()
    
    # Create users
    users_created = []
    errors = []
    
    for i in range(num_users):
        try:
            user = create_test_user(all_skills)
            db.session.add(user)
            
            # Try to commit each user individually to handle potential conflicts
            try:
                db.session.commit()
                users_created.append(user)
                print(f"✓ Created user {i+1}/{num_users}: {user.name} ({user.email})")
                print(f"  - Location: {user.location}")
                print(f"  - Skills offered: {', '.join(user.skills_offered[:3])}{'...' if len(user.skills_offered) > 3 else ''}")
                print(f"  - Skills wanted: {', '.join(user.skills_wanted[:3])}{'...' if len(user.skills_wanted) > 3 else ''}")
                print()
                
            except Exception as e:
                db.session.rollback()
                error_msg = f"Failed to create user {i+1}: {str(e)}"
                errors.append(error_msg)
                print(f"✗ {error_msg}")
                
        except Exception as e:
            error_msg = f"Error generating user {i+1}: {str(e)}"
            errors.append(error_msg)
            print(f"✗ {error_msg}")
    
    # Summary
    print("-" * 50)
    print(f"Summary:")
    print(f"✓ Successfully created: {len(users_created)} users")
    
    if errors:
        print(f"✗ Errors encountered: {len(errors)}")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors")
    
    return users_created, errors

def show_database_stats():
    """Show current database statistics"""
    total_users = User.query.count()
    public_users = User.query.filter_by(is_public=True).count()
    banned_users = User.query.filter_by(is_banned=True).count()
    
    print("\nDatabase Statistics:")
    print(f"Total users: {total_users}")
    print(f"Public users: {public_users}")
    print(f"Banned users: {banned_users}")
    print(f"Private users: {total_users - public_users}")
    
    # Show skill distribution
    all_skills = get_all_skills()
    skill_counts = {}
    
    for user in User.query.all():
        for skill in user.skills_offered:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
    
    if skill_counts:
        print(f"\nMost popular skills offered:")
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
        for skill, count in sorted_skills[:10]:
            print(f"  - {skill}: {count} users")

def main():
    """Main function to handle command line arguments and run the script"""
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        try:
            num_users = int(sys.argv[1])
            if num_users <= 0:
                print("Error: Number of users must be positive")
                sys.exit(1)
        except ValueError:
            print("Error: Please provide a valid number")
            print("Usage: python create_test_users.py [number_of_users]")
            sys.exit(1)
    else:
        num_users = 10  # Default value
    
    print("=" * 60)
    print("SKILL SWAP PLATFORM - TEST USER CREATION SCRIPT")
    print("=" * 60)
    
    # Check if faker is installed
    try:
        import faker
    except ImportError:
        print("Error: 'faker' package is required for generating realistic test data.")
        print("Please install it using: pip install faker")
        sys.exit(1)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        print(f"Connected to database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"Requested number of users: {num_users}")
        
        # Show current stats
        show_database_stats()
        print()
        
        # Ask for confirmation if creating many users
        if num_users > 50:
            response = input(f"You're about to create {num_users} users. Continue? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("Operation cancelled.")
                sys.exit(0)
        
        # Create the users
        users_created, errors = create_test_users(num_users)
        
        # Show updated stats
        show_database_stats()
        
        if users_created:
            print(f"\n✓ Script completed successfully!")
            print(f"✓ {len(users_created)} test users have been created.")
            print(f"  Default password for all test users: 'password123'")
        else:
            print(f"\n✗ No users were created. Check the errors above.")

if __name__ == "__main__":
    main()
