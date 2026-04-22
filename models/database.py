from flask_pymongo import PyMongo
from datetime import datetime
from bson import ObjectId

class Database:
    def __init__(self, mongo):
        self.db = mongo.db
    
    def initialize_database(self):
        """Initialize database with sample data"""
        # Create indexes
        self.db.users.create_index([('email', 1)], unique=True)
        self.db.quiz_results.create_index([('user_id', 1), ('completed_at', -1)])
        self.db.questions.create_index([('subject', 1), ('difficulty', 1)])
        self.db.ai_interactions.create_index([('user_id', 1), ('timestamp', -1)])
        
        # Add sample questions if none exist
        if self.db.questions.count_documents({}) == 0:
            self.add_sample_questions()
    
    def add_sample_questions(self):
        """Add sample questions to the database"""
        sample_questions = [
            {
                'question': 'What is 15 × 4?',
                'options': ['40', '50', '60', '70'],
                'correct_answer': '60',
                'subject': 'mathematics',
                'difficulty': 'easy',
                'topic': 'multiplication'
            },
            {
                'question': 'What is the capital of France?',
                'options': ['London', 'Berlin', 'Paris', 'Madrid'],
                'correct_answer': 'Paris',
                'subject': 'social_studies',
                'difficulty': 'easy',
                'topic': 'geography'
            },
            {
                'question': 'Which planet is known as the Red Planet?',
                'options': ['Venus', 'Mars', 'Jupiter', 'Saturn'],
                'correct_answer': 'Mars',
                'subject': 'science',
                'difficulty': 'easy',
                'topic': 'astronomy'
            },
            {
                'question': 'What is the chemical symbol for water?',
                'options': ['H2O', 'CO2', 'O2', 'NaCl'],
                'correct_answer': 'H2O',
                'subject': 'science',
                'difficulty': 'easy',
                'topic': 'chemistry'
            },
            {
                'question': 'Solve: 3x + 7 = 22',
                'options': ['x = 3', 'x = 5', 'x = 6', 'x = 7'],
                'correct_answer': 'x = 5',
                'subject': 'mathematics',
                'difficulty': 'medium',
                'topic': 'algebra'
            }
        ]
        
        self.db.questions.insert_many(sample_questions)
        return len(sample_questions)