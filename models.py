from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

db = SQLAlchemy()

class AliceUser(db.Model):
    __tablename__ = 'alice_users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), unique=True, nullable=False)
    weight = db.Column(db.Float, default=75.0)
    height = db.Column(db.Integer, default=175)
    age = db.Column(db.Integer, default=25)
    gender = db.Column(db.String(20), default='не указан')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    workouts = db.relationship('Workout', backref='user', cascade="all, delete-orphan", lazy=True)

    def calculate_bmi(self):
        height_in_meters = self.height / 100
        bmi_value = self.weight / (height_in_meters * height_in_meters)
        return round(bmi_value, 2)

    def get_bmi_category(self):
        bmi = self.calculate_bmi()
        if bmi < 18.5: return "Дефицит массы"
        elif 18.5 <= bmi < 25: return "Норма"
        elif 25 <= bmi < 30: return "Избыточный вес"
        else: return "Ожирение"

    def get_fitness_level(self):
        total_dist = sum(w.distance for w in self.workouts)
        if total_dist < 10: return "Новичок"
        elif total_dist < 50: return "Атлет"
        elif total_dist < 150: return "Марафонец"
        else: return "Ультрамарафонер"

    def get_analytics(self):
        if not self.workouts:
            return None
        
        distances = [w.distance for w in self.workouts]
        total_dist = sum(distances)
        max_dist = max(distances)
        avg_dist = total_dist / len(self.workouts)
        
        total_minutes = sum(w.duration for w in self.workouts)
        avg_pace = total_minutes / total_dist if total_dist > 0 else 0
        
        return {
            'total_dist': round(total_dist, 2),
            'max_dist': round(max_dist, 2),
            'avg_dist': round(avg_dist, 2),
            'avg_pace': round(avg_pace, 2),
            'count': len(self.workouts)
        }

class Workout(db.Model):
    __tablename__ = 'workouts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('alice_users.id'), nullable=False)
    distance = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, default=30)
    calories = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
