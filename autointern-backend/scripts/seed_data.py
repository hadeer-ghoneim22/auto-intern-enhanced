#!/usr/bin/env python3
"""
Additional seed data script for AutoIntern.AI
Adds more comprehensive test data for development and testing.
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta
import random

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def add_more_internships():
    """Add additional internship opportunities"""
    
    additional_internships = [
        # Tech Companies
        ('Backend Engineer Intern', 'Stripe', 'San Francisco, CA', 
         'Build payment infrastructure that powers internet commerce. Work on APIs, databases, and distributed systems.',
         'https://stripe.com/jobs/123456', 'Backend development, API design, Database knowledge',
         '$8,500 - $10,500/month', '12 weeks', '2024-04-10'),
        
        ('Mobile Developer Intern', 'Spotify', 'New York, NY',
         'Develop features for the Spotify mobile app used by millions of music lovers worldwide.',
         'https://www.lifeatspotify.com/jobs/123456', 'iOS/Android development, Swift/Kotlin, Music streaming knowledge',
         '$7,500 - $9,500/month', '12 weeks', '2024-04-15'),
        
        ('Cloud Engineer Intern', 'Amazon Web Services', 'Seattle, WA',
         'Help build and scale cloud services that power businesses around the world.',
         'https://amazon.jobs/en/jobs/123456', 'Cloud computing, AWS services, Infrastructure automation',
         '$8,000 - $10,000/month', '12-16 weeks', '2024-03-28'),
        
        # Startups
        ('Full Stack Intern', 'Notion', 'San Francisco, CA',
         'Build features for the all-in-one workspace that millions of users rely on for productivity.',
         'https://www.notion.so/careers/123456', 'Full stack development, React, Node.js, Database design',
         '$7,000 - $9,000/month', '12 weeks', '2024-04-20'),
        
        ('AI Research Intern', 'Anthropic', 'San Francisco, CA',
         'Conduct research on AI safety and help build helpful, harmless, and honest AI systems.',
         'https://www.anthropic.com/careers/123456', 'Machine Learning, AI research, Python, Research publications',
         '$10,000 - $12,000/month', '12 weeks', '2024-04-08'),
        
        # Finance & Fintech
        ('Quantitative Analyst Intern', 'Two Sigma', 'New York, NY',
         'Apply mathematical and statistical methods to financial markets and trading strategies.',
         'https://careers.twosigma.com/careers/123456', 'Mathematics/Statistics, Python/R, Financial modeling',
         '$9,000 - $11,000/month', '10-12 weeks', '2024-03-22'),
        
        ('Software Engineer Intern', 'Robinhood', 'Menlo Park, CA',
         'Build financial products that democratize access to the financial markets.',
         'https://robinhood.com/careers/123456', 'Software engineering, Financial systems, Mobile development',
         '$8,000 - $10,000/month', '12 weeks', '2024-04-12'),
        
        # Gaming
        ('Game Developer Intern', 'Epic Games', 'Cary, NC',
         'Work on Fortnite, Unreal Engine, or Epic Games Store. Create experiences enjoyed by millions.',
         'https://www.epicgames.com/site/careers/123456', 'Game development, C++, Unreal Engine, 3D graphics',
         '$7,500 - $9,500/month', '12 weeks', '2024-04-18'),
        
        # Healthcare Tech
        ('Health Tech Intern', 'Teladoc Health', 'Purchase, NY',
         'Build technology that improves healthcare access and outcomes for patients worldwide.',
         'https://careers.teladochealth.com/123456', 'Healthcare technology, HIPAA compliance, Web development',
         '$6,500 - $8,500/month', '12 weeks', '2024-04-25'),
        
        # E-commerce
        ('Data Analyst Intern', 'Shopify', 'Ottawa, Canada',
         'Analyze merchant data to help improve the e-commerce platform used by millions of businesses.',
         'https://www.shopify.com/careers/123456', 'Data analysis, SQL, Business intelligence, E-commerce',
         '$6,000 - $8,000/month', '12-16 weeks', '2024-04-30'),
    ]
    
    return additional_internships

def add_sample_users():
    """Add sample users for testing"""
    
    sample_users = [
        ('john.doe@example.com', 'John Doe', 'Computer Science student at Stanford University'),
        ('jane.smith@example.com', 'Jane Smith', 'Data Science student at MIT'),
        ('alex.johnson@example.com', 'Alex Johnson', 'Software Engineering student at UC Berkeley'),
        ('sarah.wilson@example.com', 'Sarah Wilson', 'Product Management student at Harvard Business School'),
        ('mike.brown@example.com', 'Mike Brown', 'UX Design student at RISD'),
    ]
    
    return sample_users

def add_sample_applications():
    """Add sample applications for testing"""
    
    # This will be populated after users and internships are created
    statuses = ['submitted', 'under_review', 'interview_scheduled', 'accepted', 'rejected']
    
    return statuses

def main():
    """Main function to seed additional data"""
    
    print("🌱 Seeding additional data for AutoIntern.AI...")
    print("=" * 50)
    
    # Database file path
    db_path = os.path.join(project_root, 'src', 'database', 'app.db')
    
    if not os.path.exists(db_path):
        print("❌ Database not found. Please run create_db.py first.")
        sys.exit(1)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("📊 Adding additional internships...")
        
        # Add more internships
        additional_internships = add_more_internships()
        for internship in additional_internships:
            cursor.execute("""
                INSERT OR IGNORE INTO internships 
                (title, company, location, description, url, requirements, salary_range, duration, application_deadline)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, internship)
        
        print(f"✅ Added {len(additional_internships)} additional internships!")
        
        print("👥 Adding sample users...")
        
        # Add sample users
        sample_users = add_sample_users()
        for email, name, bio in sample_users:
            cursor.execute("""
                INSERT OR IGNORE INTO users (email, name, created_at)
                VALUES (?, ?, ?)
            """, (email, name, datetime.now()))
            
            # Add user profile
            user_id = cursor.lastrowid
            if user_id:
                cursor.execute("""
                    INSERT OR IGNORE INTO user_profiles 
                    (user_id, first_name, last_name, bio, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, name.split()[0], name.split()[1], bio, datetime.now()))
        
        print(f"✅ Added {len(sample_users)} sample users!")
        
        print("📝 Adding sample applications...")
        
        # Get user and internship IDs for creating applications
        cursor.execute("SELECT id FROM users LIMIT 5")
        user_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM internships LIMIT 10")
        internship_ids = [row[0] for row in cursor.fetchall()]
        
        statuses = add_sample_applications()
        applications_added = 0
        
        # Create random applications
        for user_id in user_ids:
            # Each user applies to 2-4 internships
            num_applications = random.randint(2, 4)
            selected_internships = random.sample(internship_ids, min(num_applications, len(internship_ids)))
            
            for internship_id in selected_internships:
                status = random.choice(statuses)
                applied_date = datetime.now() - timedelta(days=random.randint(1, 30))
                
                cursor.execute("""
                    INSERT OR IGNORE INTO applications 
                    (user_id, internship_id, status, applied_date, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, internship_id, status, applied_date, datetime.now()))
                
                applications_added += 1
        
        print(f"✅ Added {applications_added} sample applications!")
        
        # Commit all changes
        conn.commit()
        
        # Final statistics
        cursor.execute("SELECT COUNT(*) FROM internships")
        total_internships = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM applications")
        total_applications = cursor.fetchone()[0]
        
        print(f"\n📈 Updated Database Statistics:")
        print(f"   • Total Internships: {total_internships}")
        print(f"   • Total Users: {total_users}")
        print(f"   • Total Applications: {total_applications}")
        
        conn.close()
        
        print("\n🎉 Additional data seeding completed successfully!")
        print("Your database now has comprehensive test data for development.")
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
