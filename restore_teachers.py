"""
Run this script ONCE on your local machine or Render shell to restore teachers.
Command: python restore_teachers.py
"""

import sys
import os

# Add your app directory to path
sys.path.insert(0, '.')

from app import app, db, User, TeacherProfile
from werkzeug.security import generate_password_hash

teachers_data = [
    {
        "first_name": "Rajesh", "last_name": "Kumar",
        "email": "rajesh@vaanyan.com", "phone": "+91 98765 43210",
        "qualification": "Masters", "experience": "5-10",
        "city": "Dehradun", "subjects": "mathematics,physics",
        "hourly_rate": 500, "teaching_mode": "Home Tuition",
        "bio": "", "address": "Dehradun"
    },
    {
        "first_name": "Nitin", "last_name": "Rawat",
        "email": "nitin.rawat2@gmail.com", "phone": "9012977681",
        "qualification": "phd", "experience": "10+",
        "city": "Dehradun", "subjects": "mathematics,computer",
        "hourly_rate": 600, "teaching_mode": "Home Tuition",
        "bio": "", "address": "Dehradun"
    },
    {
        "first_name": "Pankaj", "last_name": "Kumar",
        "email": "pankaj.kumar@gmail.com", "phone": "9897602932",
        "qualification": "phd", "experience": "5-10",
        "city": "Dehradun", "subjects": "mathematics,physics,chemistry",
        "hourly_rate": 300, "teaching_mode": "Home Tuition",
        "bio": "", "address": "Dehradun"
    },
    {
        "first_name": "Siddhant", "last_name": "Jajedi",
        "email": "siddhantjajedi98765@gmail.com", "phone": "9870924762",
        "qualification": "masters", "experience": "5-10",
        "city": "Balasaur kotdwara", "subjects": "chemistry",
        "hourly_rate": 400, "teaching_mode": "Home Tuition",
        "bio": "", "address": "Balasaur kotdwara"
    },
    {
        "first_name": "Mohammad", "last_name": "Shadan",
        "email": "Mohdshadan.info@gmail.com", "phone": "+918953103250",
        "qualification": "masters", "experience": "3-5",
        "city": "Shahjahanpur", "subjects": "general",
        "hourly_rate": 500, "teaching_mode": "Home Tuition",
        "bio": "", "address": "Shahjahanpur"
    },
    {
        "first_name": "Shubham", "last_name": "Sundriyal",
        "email": "shubhamsun1999@gmail.com", "phone": "9639046070",
        "qualification": "masters", "experience": "5-10",
        "city": "Kotdwar", "subjects": "chemistry",
        "hourly_rate": 1000, "teaching_mode": "Home Tuition",
        "bio": "", "address": "Kotdwar"
    },
    {
        "first_name": "Deepa", "last_name": "Rani",
        "email": "dhanipal19011015@gmail.com", "phone": "9695421300",
        "qualification": "b.ed", "experience": "10+",
        "city": "Sitapur", "subjects": "mathematics",
        "hourly_rate": 500, "teaching_mode": "Home Tuition",
        "bio": "", "address": "Sitapur"
    },
    {
        "first_name": "Rakesh", "last_name": "Yadav",
        "email": "rokyarjun4949@gmail.com", "phone": "7976619053",
        "qualification": "masters", "experience": "5-10",
        "city": "Dehradun", "subjects": "biology,hindi",
        "hourly_rate": 600, "teaching_mode": "Home Tuition",
        "bio": "", "address": "Dehradun"
    },
    {
        "first_name": "Sparsh", "last_name": "Rawat",
        "email": "rawatsparsh079@gmail.com", "phone": "6395190541",
        "qualification": "bachelors", "experience": "10+",
        "city": "Kotdwar", "subjects": "mathematics",
        "hourly_rate": 500, "teaching_mode": "Home Tuition",
        "bio": "", "address": "Kotdwar"
    },
    {
        "first_name": "Gangotri", "last_name": "Bhaisora",
        "email": "jigangotri91@gmail.com", "phone": "9761319402",
        "qualification": "diploma", "experience": "5-10",
        "city": "Dehradun", "subjects": "hindi",
        "hourly_rate": 500, "teaching_mode": "Home Tuition",
        "bio": "", "address": "Dehradun"
    },
]

DEFAULT_PASSWORD = "Vaanyan@123"

with app.app_context():
    restored = 0
    for t in teachers_data:
        existing = User.query.filter_by(email=t['email']).first()
        if existing:
            if existing.teacher_profile:
                db.session.delete(existing.teacher_profile)
            db.session.delete(existing)
            db.session.commit()
            print(f"DELETED old: {t['email']}")

        user = User(
            role='teacher',
            first_name=t['first_name'],
            last_name=t['last_name'],
            email=t['email'],
            phone=t['phone']
        )
        user.password_hash = generate_password_hash(DEFAULT_PASSWORD)
        db.session.add(user)
        db.session.flush()

        profile = TeacherProfile(
            user_id=user.id,
            qualification=t['qualification'],
            experience=t['experience'],
            subjects=t['subjects'],
            teaching_mode=t['teaching_mode'],
            hourly_rate=t['hourly_rate'],
            bio=t['bio'],
            city=t['city'],
            address=t['address']
        )
        db.session.add(profile)
        db.session.commit()
        print(f"✅ RESTORED: {t['first_name']} {t['last_name']} ({t['email']})")
        restored += 1

    print(f"\n🎉 Done! Restored: {restored}")
    print(f"Default password: {DEFAULT_PASSWORD}")