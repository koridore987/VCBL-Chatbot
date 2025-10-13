#!/bin/bash

# Create super admin account
# Usage: ./create-admin.sh <student_id> <name> <password>

if [ $# -ne 3 ]; then
    echo "Usage: $0 <student_id> <name> <password>"
    exit 1
fi

STUDENT_ID=$1
NAME=$2
PASSWORD=$3

# Use Flask shell to create admin
cd backend

python << END
from app import create_app, db, bcrypt
from app.models.user import User

app = create_app()

with app.app_context():
    # Check if user exists
    existing_user = User.query.filter_by(student_id='$STUDENT_ID').first()
    
    if existing_user:
        print(f"User {STUDENT_ID} already exists")
        exit(1)
    
    # Create super admin
    password_hash = bcrypt.generate_password_hash('$PASSWORD').decode('utf-8')
    
    admin = User(
        student_id='$STUDENT_ID',
        password_hash=password_hash,
        name='$NAME',
        role='super',
        is_active=True
    )
    
    db.session.add(admin)
    db.session.commit()
    
    print(f"Super admin created: {admin.student_id}")
END

