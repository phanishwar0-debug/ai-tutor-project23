from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, send_from_directory
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from bson import ObjectId
import os
import json
from werkzeug.utils import secure_filename
import random
from collections import defaultdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import threading
import base64
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/ai_tutor_db'
app.config['UPLOAD_FOLDER'] = 'static/uploads/videos'
app.config['STUDY_MATERIAL_FOLDER'] = 'static/uploads/study_materials'
app.config['CONTACT_ATTACHMENTS_FOLDER'] = 'static/uploads/contact_attachments'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
app.config['ALLOWED_VIDEO_EXTENSIONS'] = {'.mp4', '.webm', '.ogg', '.mov', '.avi'}
app.config['ALLOWED_STUDY_EXTENSIONS'] = {
    '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp',
    '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
    '.mp3', '.wav', '.ogg'
}
app.config['ALLOWED_ATTACHMENT_EXTENSIONS'] = {'.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx', '.txt'}

# Email Configuration (Update with your SMTP settings)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'fanishwarthannrru@gmail.com'
app.config['MAIL_PASSWORD'] = 'fjbc yffp eusw jchf'
app.config['MAIL_DEFAULT_SENDER'] = 'noreply@aitutor.com'

# Create upload directories with absolute paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
os.makedirs(os.path.join(BASE_DIR, 'static', 'uploads', 'videos'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'static', 'uploads', 'study_materials'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'static', 'uploads', 'contact_attachments'), exist_ok=True)

# Update config with absolute paths
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads', 'videos')
app.config['STUDY_MATERIAL_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads', 'study_materials')
app.config['CONTACT_ATTACHMENTS_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads', 'contact_attachments')

mongo = PyMongo(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'student_login'

# ============================================
# ACHIEVEMENTS SYSTEM - COMPLETE
# ============================================

# Medal definitions with full details
MEDALS = {
    'material_learner': {
        'id': 'material_learner',
        'name': 'Dedicated Learner',
        'description': 'Study 30 materials',
        'icon': '📚',
        'color': '#48bb78',
        'category': 'learning',
        'xp_bonus': 100,
        'requirement': 30,
        'requirement_type': 'material_count'
    },
    'video_learner': {
        'id': 'video_learner',
        'name': 'Video Learner',
        'description': 'Watch 20 videos',
        'icon': '🎬',
        'color': '#f56565',
        'category': 'learning',
        'xp_bonus': 100,
        'requirement': 20,
        'requirement_type': 'video_count'
    },
    'polyglot': {
        'id': 'polyglot',
        'name': 'Polyglot',
        'description': 'Learn in 3+ languages',
        'icon': '🌍',
        'color': '#9f7aea',
        'category': 'language',
        'xp_bonus': 150,
        'requirement': 3,
        'requirement_type': 'language_count'
    },
    'streak_7': {
        'id': 'streak_7',
        'name': '7 Day Streak',
        'description': 'Study 7 days in a row',
        'icon': '🔥',
        'color': '#ed8936',
        'category': 'streak',
        'xp_bonus': 50,
        'requirement': 7,
        'requirement_type': 'streak'
    },
    'streak_30': {
        'id': 'streak_30',
        'name': '30 Day Streak',
        'description': 'Study 30 days in a row',
        'icon': '🏆',
        'color': '#ecc94b',
        'category': 'streak',
        'xp_bonus': 200,
        'requirement': 30,
        'requirement_type': 'streak'
    },
    'hindi_learner': {
        'id': 'hindi_learner',
        'name': 'हिंदी Learner',
        'description': 'Complete 10 activities in Hindi',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'hindi_activities'
    },
    'telugu_learner': {
        'id': 'telugu_learner',
        'name': 'తెలుగు Learner',
        'description': 'Complete 10 activities in Telugu',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'telugu_activities'
    },
    'tamil_learner': {
        'id': 'tamil_learner',
        'name': 'தமிழ் Learner',
        'description': 'Complete 10 activities in Tamil',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'tamil_activities'
    },
    'bengali_learner': {
        'id': 'bengali_learner',
        'name': 'বাংলা Learner',
        'description': 'Complete 10 activities in Bengali',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'bengali_activities'
    },
    'marathi_learner': {
        'id': 'marathi_learner',
        'name': 'मराठी Learner',
        'description': 'Complete 10 activities in Marathi',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'marathi_activities'
    },
    'gujarati_learner': {
        'id': 'gujarati_learner',
        'name': 'ગુજરાતી Learner',
        'description': 'Complete 10 activities in Gujarati',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'gujarati_activities'
    },
    'kannada_learner': {
        'id': 'kannada_learner',
        'name': 'ಕನ್ನಡ Learner',
        'description': 'Complete 10 activities in Kannada',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'kannada_activities'
    },
    'malayalam_learner': {
        'id': 'malayalam_learner',
        'name': 'മലയാളം Learner',
        'description': 'Complete 10 activities in Malayalam',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'malayalam_activities'
    },
    'punjabi_learner': {
        'id': 'punjabi_learner',
        'name': 'ਪੰਜਾਬੀ Learner',
        'description': 'Complete 10 activities in Punjabi',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'punjabi_activities'
    },
    'assamese_learner': {
        'id': 'assamese_learner',
        'name': 'অসমীয়া Learner',
        'description': 'Complete 10 activities in Assamese',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'assamese_activities'
    },
    'oriya_learner': {
        'id': 'oriya_learner',
        'name': 'ଓଡ଼ିଆ Learner',
        'description': 'Complete 10 activities in Odia',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'oriya_activities'
    },
    'maithili_learner': {
        'id': 'maithili_learner',
        'name': 'मैथिली Learner',
        'description': 'Complete 10 activities in Maithili',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'maithili_activities'
    },
    'santali_learner': {
        'id': 'santali_learner',
        'name': 'ᱥᱟᱱᱛᱟᱲᱤ Learner',
        'description': 'Complete 10 activities in Santali',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'santali_activities'
    },
    'kashmiri_learner': {
        'id': 'kashmiri_learner',
        'name': 'कॉशुर Learner',
        'description': 'Complete 10 activities in Kashmiri',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'kashmiri_activities'
    },
    'nepali_learner': {
        'id': 'nepali_learner',
        'name': 'नेपाली Learner',
        'description': 'Complete 10 activities in Nepali',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'nepali_activities'
    },
    'sindhi_learner': {
        'id': 'sindhi_learner',
        'name': 'سنڌي Learner',
        'description': 'Complete 10 activities in Sindhi',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'sindhi_activities'
    },
    'dogri_learner': {
        'id': 'dogri_learner',
        'name': 'डोगरी Learner',
        'description': 'Complete 10 activities in Dogri',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'dogri_activities'
    },
    'konkani_learner': {
        'id': 'konkani_learner',
        'name': 'कोंकणी Learner',
        'description': 'Complete 10 activities in Konkani',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'konkani_activities'
    },
    'manipuri_learner': {
        'id': 'manipuri_learner',
        'name': 'মৈতৈলোন্ Learner',
        'description': 'Complete 10 activities in Manipuri',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'manipuri_activities'
    },
    'bodo_learner': {
        'id': 'bodo_learner',
        'name': 'बर Learner',
        'description': 'Complete 10 activities in Bodo',
        'icon': '🇮🇳',
        'color': '#38b2ac',
        'category': 'language_specific',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'bodo_activities'
    },
    'first_activity': {
        'id': 'first_activity',
        'name': 'First Steps',
        'description': 'Complete your first learning activity',
        'icon': '🌟',
        'color': '#fbbf24',
        'category': 'milestone',
        'xp_bonus': 10,
        'requirement': 1,
        'requirement_type': 'total_activities'
    },
    'ten_activities': {
        'id': 'ten_activities',
        'name': 'Active Learner',
        'description': 'Complete 10 learning activities',
        'icon': '⭐',
        'color': '#f59e0b',
        'category': 'milestone',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'total_activities'
    },
    'fifty_activities': {
        'id': 'fifty_activities',
        'name': 'Learning Master',
        'description': 'Complete 50 learning activities',
        'icon': '🏅',
        'color': '#10b981',
        'category': 'milestone',
        'xp_bonus': 200,
        'requirement': 50,
        'requirement_type': 'total_activities'
    },
    'hundred_activities': {
        'id': 'hundred_activities',
        'name': 'Learning Legend',
        'description': 'Complete 100 learning activities',
        'icon': '🏆',
        'color': '#f59e0b',
        'category': 'milestone',
        'xp_bonus': 500,
        'requirement': 100,
        'requirement_type': 'total_activities'
    },
    'perfect_score': {
        'id': 'perfect_score',
        'name': 'Perfect Score',
        'description': 'Get 100% on any quiz or assessment',
        'icon': '💯',
        'color': '#fbbf24',
        'category': 'achievement',
        'xp_bonus': 100,
        'requirement': 1,
        'requirement_type': 'perfect_scores'
    },
    'early_bird': {
        'id': 'early_bird',
        'name': 'Early Bird',
        'description': 'Complete 5 activities before 9 AM',
        'icon': '🌅',
        'color': '#f97316',
        'category': 'special',
        'xp_bonus': 25,
        'requirement': 5,
        'requirement_type': 'early_activities'
    },
    'night_owl': {
        'id': 'night_owl',
        'name': 'Night Owl',
        'description': 'Complete 5 activities after 10 PM',
        'icon': '🦉',
        'color': '#6b7280',
        'category': 'special',
        'xp_bonus': 25,
        'requirement': 5,
        'requirement_type': 'night_activities'
    },
    'weekend_warrior': {
        'id': 'weekend_warrior',
        'name': 'Weekend Warrior',
        'description': 'Complete 10 activities on weekends',
        'icon': '🎯',
        'color': '#8b5cf6',
        'category': 'special',
        'xp_bonus': 50,
        'requirement': 10,
        'requirement_type': 'weekend_activities'
    }
}

def get_medal_details(medal_id):
    """Get details for a specific medal"""
    return MEDALS.get(medal_id, {
        'id': medal_id,
        'name': medal_id.replace('_', ' ').title(),
        'description': 'Achievement unlocked!',
        'icon': '🏅',
        'color': '#48bb78',
        'category': 'other'
    })

def check_and_award_medals(user_id):
    """Check all medal conditions and award any new medals"""
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return {'awarded': []}
    
    current_medals = set(user.get('medals', []))
    newly_awarded = []
    
    # Get user stats
    total_materials = user.get('total_materials', 0)
    total_videos = user.get('total_videos', 0)
    streak = user.get('streak', 0)
    
    # Count activities by language
    language_activities = defaultdict(int)
    if 'material_views' in mongo.db.list_collection_names():
        activities = mongo.db.material_views.find({'user_id': str(user_id)})
        for act in activities:
            lang = act.get('material_language', 'english')
            language_activities[lang] += 1
    
    if 'video_watch_time' in mongo.db.list_collection_names():
        activities = mongo.db.video_watch_time.find({'user_id': str(user_id)})
        for act in activities:
            # Videos might not have language field, but we can add it later
            pass
    
    # Count distinct languages used
    distinct_languages = set(language_activities.keys())
    distinct_languages.add(user.get('language', 'english'))
    language_count = len(distinct_languages)
    
    # Total activities
    total_activities = total_materials + total_videos
    
    # Check each medal
    for medal_id, medal in MEDALS.items():
        if medal_id in current_medals:
            continue
            
        should_award = False
        req_type = medal['requirement_type']
        requirement = medal['requirement']
        
        if req_type == 'material_count':
            should_award = total_materials >= requirement
        elif req_type == 'video_count':
            should_award = total_videos >= requirement
        elif req_type == 'language_count':
            should_award = language_count >= requirement
        elif req_type == 'streak':
            should_award = streak >= requirement
        elif req_type == 'total_activities':
            should_award = total_activities >= requirement
        elif req_type.endswith('_activities'):
            lang = req_type.replace('_activities', '')
            should_award = language_activities.get(lang, 0) >= requirement
        elif req_type == 'perfect_scores':
            perfect_scores = user.get('perfect_scores', 0)
            should_award = perfect_scores >= requirement
        elif req_type == 'early_activities':
            early_count = user.get('early_activities', 0)
            should_award = early_count >= requirement
        elif req_type == 'night_activities':
            night_count = user.get('night_activities', 0)
            should_award = night_count >= requirement
        elif req_type == 'weekend_activities':
            weekend_count = user.get('weekend_activities', 0)
            should_award = weekend_count >= requirement
        
        if should_award:
            # Award the medal
            mongo.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$addToSet': {'medals': medal_id}}
            )
            
            # Award XP bonus
            xp_bonus = medal.get('xp_bonus', 0)
            if xp_bonus > 0:
                mongo.db.users.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$inc': {'xp': xp_bonus}}
                )
                
                # Update level if needed
                user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
                new_level = calculate_level(user['xp'])
                if new_level > user.get('level', 1):
                    mongo.db.users.update_one(
                        {'_id': ObjectId(user_id)},
                        {'$set': {'level': new_level}}
                    )
            
            newly_awarded.append({
                'medal_id': medal_id,
                'name': medal['name'],
                'description': medal['description'],
                'icon': medal['icon'],
                'xp_bonus': xp_bonus
            })
            
            # Track medal award activity
            track_activity(
                user_id=user_id,
                user_name=user.get('name', 'Student'),
                user_email=user.get('email', ''),
                activity_type='medal_award',
                item_id=medal_id,
                item_title=medal['name'],
                item_type='medal',
                details=f'Awarded medal: {medal["name"]}',
                xp_earned=xp_bonus
            )
    
    return {'awarded': newly_awarded}

def award_medal(user_id, medal_type):
    """Award a medal to a user (legacy function)"""
    if medal_type in MEDALS:
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$addToSet': {'medals': medal_type}}
        )
        medal = MEDALS[medal_type]
        return {'awarded': True, 'medal_name': medal['name']}
    return {'awarded': False}

# ============================================
# Helper Function: Get Time Ago
# ============================================
def get_time_ago(dt):
    """Convert datetime to human readable time ago"""
    if not dt:
        return 'Unknown'
    diff = datetime.now() - dt
    if diff.days > 365:
        return f'{diff.days // 365} year{"s" if diff.days // 365 > 1 else ""} ago'
    elif diff.days > 30:
        return f'{diff.days // 30} month{"s" if diff.days // 30 > 1 else ""} ago'
    elif diff.days > 0:
        return f'{diff.days} day{"s" if diff.days > 1 else ""} ago'
    elif diff.seconds > 3600:
        return f'{diff.seconds // 3600} hour{"s" if diff.seconds // 3600 > 1 else ""} ago'
    elif diff.seconds > 60:
        return f'{diff.seconds // 60} minute{"s" if diff.seconds // 60 > 1 else ""} ago'
    else:
        return 'just now'

# Make helper functions available to templates
app.jinja_env.globals.update(get_time_ago=get_time_ago)
app.jinja_env.globals.update(get_medal_details=get_medal_details)
app.jinja_env.globals.update(MEDALS=MEDALS)

def calculate_level(xp):
    return (xp // 1000) + 1

def award_xp(user_id, xp_amount):
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$inc': {'xp': xp_amount}}
    )
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    new_level = calculate_level(user['xp'])
    if new_level > user.get('level', 1):
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'level': new_level}}
        )
        return {'leveled_up': True, 'new_level': new_level}
    return {'leveled_up': False}

def get_language_name(lang_code):
    names = {
        'english': 'English',
        'hindi': 'हिंदी',
        'bengali': 'বাংলা',
        'telugu': 'తెలుగు',
        'marathi': 'मराठी',
        'tamil': 'தமிழ்',
        'urdu': 'اردو',
        'gujarati': 'ગુજરાતી',
        'kannada': 'ಕನ್ನಡ',
        'malayalam': 'മലയാളം',
        'oriya': 'ଓଡ଼ିଆ',
        'punjabi': 'ਪੰਜਾਬੀ',
        'assamese': 'অসমীয়া',
        'maithili': 'मैथिली',
        'santali': 'ᱥᱟᱱᱛᱟᱲᱤ',
        'kashmiri': 'कॉशुर',
        'nepali': 'नेपाली',
        'sindhi': 'سنڌي',
        'dogri': 'डोगरी',
        'konkani': 'कोंकणी',
        'manipuri': 'মৈতৈলোন্',
        'bodo': 'बर'
    }
    return names.get(lang_code, lang_code.title())

app.jinja_env.globals.update(get_language_name=get_language_name)

# ============================================
# Activity Tracking Function
# ============================================

def track_activity(user_id, user_name, user_email=None, activity_type='view',
                   item_id=None, item_title=None, item_type='material',
                   details=None, xp_earned=0):
    """Track student activity in real-time with enhanced data"""
    try:
        # Get user email if not provided
        if not user_email and user_id:
            user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            if user:
                user_email = user.get('email', '')
       
        activity_data = {
            '_id': str(uuid.uuid4()),
            'user_id': user_id,
            'user_name': user_name,
            'user_email': user_email or '',
            'activity_type': activity_type,
            'item_id': item_id,
            'item_title': item_title,
            'item_type': item_type,
            'details': details,
            'xp_earned': xp_earned,
            'activity_at': datetime.now(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'hour': datetime.now().hour,
            'ip_address': request.remote_addr if request else None
        }
       
        mongo.db.student_activities.insert_one(activity_data)
        mongo.db.activities.insert_one(activity_data)
        
        # Update user's recent activity list
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$push': {
                'recent_activities': {
                    '$each': [{
                        'type': activity_type,
                        'title': item_title,
                        'timestamp': datetime.now(),
                        'xp': xp_earned
                    }],
                    '$slice': -20
                }
            }}
        )
        
        # Check for special time-based achievements
        hour = datetime.now().hour
        is_weekend = datetime.now().weekday() >= 5  # 5=Saturday, 6=Sunday
        
        if hour < 9:
            mongo.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$inc': {'early_activities': 1}}
            )
        if hour >= 22:
            mongo.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$inc': {'night_activities': 1}}
            )
        if is_weekend:
            mongo.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$inc': {'weekend_activities': 1}}
            )
        
        # Check for new medals after activity
        check_and_award_medals(user_id)
        
        return str(activity_data['_id'])
    except Exception as e:
        print(f"Error tracking activity: {e}")
        return None

def get_recent_activities(limit=50, user_id=None):
    """Get recent activities from student_activities collection"""
    query = {}
    if user_id:
        query['user_id'] = user_id
   
    activities = list(mongo.db.student_activities.find(query).sort('activity_at', -1).limit(limit))
   
    for activity in activities:
        activity['_id'] = str(activity['_id'])
        activity['time_ago'] = get_time_ago(activity.get('activity_at'))
   
    return activities

def get_activity_stats(days=7):
    """Get activity statistics for dashboard"""
    start_date = datetime.now() - timedelta(days=days)
   
    total_activities = mongo.db.student_activities.count_documents({
        'activity_at': {'$gte': start_date}
    })
   
    activities_by_type = {}
    for activity_type in ['view', 'download', 'watch', 'favorite', 'contact', 'ai_chat', 'login', 'register', 'upload', 'reply', 'email_campaign', 'medal_award']:
        count = mongo.db.student_activities.count_documents({
            'activity_type': activity_type,
            'activity_at': {'$gte': start_date}
        })
        activities_by_type[activity_type] = count
   
    daily_counts = []
    for i in range(days):
        day = datetime.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
       
        count = mongo.db.student_activities.count_documents({
            'activity_at': {'$gte': day_start, '$lte': day_end}
        })
       
        daily_counts.append({
            'date': day.strftime('%Y-%m-%d'),
            'count': count
        })
   
    return {
        'total_activities': total_activities,
        'by_type': activities_by_type,
        'daily_counts': daily_counts
    }

def get_recent_activities_feed(limit=15):
    """Get recent activities for the real-time feed"""
    activities = list(mongo.db.student_activities.find().sort('activity_at', -1).limit(limit))
   
    for activity in activities:
        activity['_id'] = str(activity['_id'])
        activity['time_ago'] = get_time_ago(activity.get('activity_at'))
       
        if activity.get('activity_type') == 'view':
            activity['display_text'] = f'viewed "{activity.get("item_title", "content")}"'
        elif activity.get('activity_type') == 'download':
            activity['display_text'] = f'downloaded "{activity.get("item_title", "content")}"'
        elif activity.get('activity_type') == 'watch':
            activity['display_text'] = f'watched "{activity.get("item_title", "video")}"'
        elif activity.get('activity_type') == 'favorite':
            activity['display_text'] = f'favorited "{activity.get("item_title", "content")}"'
        elif activity.get('activity_type') == 'medal_award':
            activity['display_text'] = f'earned medal: {activity.get("item_title", "")}'
        elif activity.get('activity_type') == 'contact':
            activity['display_text'] = f'sent a support message'
        elif activity.get('activity_type') == 'ai_chat':
            activity['display_text'] = f'asked AI Tutor a question'
        elif activity.get('activity_type') == 'login':
            activity['display_text'] = 'logged in'
        elif activity.get('activity_type') == 'register':
            activity['display_text'] = 'registered as a new student'
        else:
            activity['display_text'] = 'performed an action'
   
    return activities

# ============================================
# Email Helper Functions
# ============================================

def send_email_async(recipient, subject, body, html_body=None, attachments=None):
    """Send email asynchronously with optional attachments"""
    def send():
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = app.config['MAIL_USERNAME']
            msg['To'] = recipient

            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)

            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)

            if attachments:
                for filepath, filename in attachments:
                    try:
                        if filepath and os.path.exists(filepath):
                            with open(filepath, 'rb') as attachment:
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(attachment.read())
                                encoders.encode_base64(part)
                                part.add_header(
                                    'Content-Disposition',
                                    f'attachment; filename={filename}'
                                )
                                msg.attach(part)
                    except Exception as e:
                        print(f"Error attaching file {filename}: {e}")

            server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
            server.starttls()
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
            server.quit()

            mongo.db.email_logs.insert_one({
                'recipient': recipient,
                'subject': subject,
                'status': 'delivered',
                'sent_at': datetime.now(),
                'body_preview': body[:100]
            })

        except Exception as e:
            print(f"Error sending email to {recipient}: {e}")
            mongo.db.email_logs.insert_one({
                'recipient': recipient,
                'subject': subject,
                'status': 'failed',
                'error': str(e),
                'sent_at': datetime.now()
            })

    thread = threading.Thread(target=send)
    thread.daemon = True
    thread.start()

def send_bulk_emails(recipients, subject, body, html_body=None):
    """Send bulk emails to multiple recipients"""
    for recipient in recipients:
        send_email_async(recipient, subject, body, html_body)

def allowed_attachment_file(filename):
    return '.' in filename and os.path.splitext(filename)[1].lower() in app.config['ALLOWED_ATTACHMENT_EXTENSIONS']

# ============================================
# User Class
# ============================================
class User(UserMixin):
    def __init__(self, user_data):
        self.user_data = user_data
        self.id = str(user_data['_id'])
        self.name = user_data.get('name', '')
        self.email = user_data.get('email', '')
        self.role = user_data.get('role', 'student')
        self.xp = user_data.get('xp', 0)
        self.level = user_data.get('level', 1)
        self.medals = user_data.get('medals', [])
        self.grade = user_data.get('grade', 5)
        self.language = user_data.get('language', 'english')
        self.total_materials = user_data.get('total_materials', 0)
        self.total_videos = user_data.get('total_videos', 0)
        self.average_score = user_data.get('average_score', 0)
        self.streak = user_data.get('streak', 0)
        self.joined_date = user_data.get('joined_date')
        self.last_login = user_data.get('last_login')

    def get_id(self):
        return self.id

@login_manager.user_loader
def load_user(user_id):
    try:
        user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if user_data:
            return User(user_data)
    except:
        pass
    return None

# ============================================
# Helper Functions for Files
# ============================================
def allowed_video_file(filename):
    return '.' in filename and os.path.splitext(filename)[1].lower() in app.config['ALLOWED_VIDEO_EXTENSIONS']

def allowed_study_file(filename):
    return '.' in filename and os.path.splitext(filename)[1].lower() in app.config['ALLOWED_STUDY_EXTENSIONS']

def get_file_type(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.pdf']:
        return 'pdf'
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
        return 'image'
    elif ext in ['.mp3', '.wav', '.ogg']:
        return 'audio'
    elif ext in ['.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx']:
        return 'document'
    else:
        return 'other'

# ============================================
# Public Routes
# ============================================
@app.route('/')
def index():
    total_students = mongo.db.users.count_documents({'role': 'student'})
    total_materials = mongo.db.study_materials.count_documents({})
    total_videos = mongo.db.videos.count_documents({})
    
    return render_template('index.html', 
                          total_students=total_students,
                          total_materials=total_materials,
                          total_videos=total_videos)

# ============================================
# Student Authentication
# ============================================
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
       
        user_data = mongo.db.users.find_one({'email': email, 'role': 'student'})
       
        if user_data and bcrypt.check_password_hash(user_data['password'], password):
            user = User(user_data)
            login_user(user)
           
            now = datetime.now()
            last_login = user_data.get('last_login')
            streak = user_data.get('streak', 0)
           
            if last_login:
                if (now.date() - last_login.date()).days == 1:
                    streak += 1
                elif (now.date() - last_login.date()).days > 1:
                    streak = 1
            else:
                streak = 1
           
            mongo.db.users.update_one(
                {'_id': user_data['_id']},
                {'$set': {'last_login': now, 'streak': streak}}
            )
           
            track_activity(
                user_id=str(user_data['_id']),
                user_name=user_data.get('name', 'Student'),
                user_email=email,
                activity_type='login',
                item_id=str(user_data['_id']),
                item_title='User Login',
                item_type='user',
                details='Student logged in',
                xp_earned=0
            )
           
            # Check for streak medals
            if streak >= 7:
                award_medal(str(user_data['_id']), 'streak_7')
            if streak >= 30:
                award_medal(str(user_data['_id']), 'streak_30')
           
            flash('Login successful!', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid email or password', 'error')
   
    return render_template('student_login.html')

@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        grade = request.form.get('grade')
        school = request.form.get('school', '')
        language = request.form.get('language', 'english')
       
        if mongo.db.users.find_one({'email': email}):
            flash('Email already registered', 'error')
            return redirect(url_for('student_register'))
       
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
       
        user_data = {
            'name': name,
            'email': email,
            'password': hashed_password,
            'role': 'student',
            'grade': int(grade),
            'school': school,
            'xp': 0,
            'level': 1,
            'medals': [],
            'language': language,
            'joined_date': datetime.now(),
            'last_login': datetime.now(),
            'streak': 1,
            'total_materials': 0,
            'total_videos': 0,
            'average_score': 0,
            'perfect_scores': 0,
            'early_activities': 0,
            'night_activities': 0,
            'weekend_activities': 0,
            'recent_activities': []
        }
       
        result = mongo.db.users.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        user = User(user_data)
        login_user(user)
       
        track_activity(
            user_id=str(result.inserted_id),
            user_name=name,
            user_email=email,
            activity_type='register',
            item_id=str(result.inserted_id),
            item_title='User Registration',
            item_type='user',
            details=f'New student registered: {name}',
            xp_earned=10
        )
       
        # Send welcome email
        welcome_subject = "Welcome to AI Tutor!"
        welcome_body = f"""Dear {name},

Welcome to AI Tutor! We're excited to have you on board.

Your account has been successfully created with the following details:
- Email: {email}
- Grade: {grade}
- Preferred Language: {get_language_name(language)}

Start your learning journey today by exploring our vast collection of study materials and videos.

Best regards,
AI Tutor Team
"""
        welcome_html = f"""
        <html>
        <body>
            <h2>Welcome to AI Tutor! 🎓</h2>
            <p>Dear {name},</p>
            <p>Welcome to AI Tutor! We're excited to have you on board.</p>
            <p>Your account has been successfully created with the following details:</p>
            <ul>
                <li><strong>Email:</strong> {email}</li>
                <li><strong>Grade:</strong> {grade}</li>
                <li><strong>Preferred Language:</strong> {get_language_name(language)}</li>
            </ul>
            <p>Start your learning journey today by exploring our vast collection of study materials and videos.</p>
            <br>
            <p>Best regards,<br>AI Tutor Team</p>
        </body>
        </html>
        """
        send_email_async(email, welcome_subject, welcome_body, welcome_html)
       
        flash('Registration successful! Welcome to AI Tutor!', 'success')
        return redirect(url_for('student_dashboard'))
   
    return render_template('student_register.html')

# ============================================
# Admin Authentication
# ============================================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
       
        user_data = mongo.db.users.find_one({'email': email, 'role': 'admin'})
       
        if user_data and bcrypt.check_password_hash(user_data['password'], password):
            user = User(user_data)
            login_user(user)
            mongo.db.users.update_one(
                {'_id': user_data['_id']},
                {'$set': {'last_login': datetime.now()}}
            )
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'error')
   
    return render_template('admin_login.html')

# ============================================
# STUDENT ACHIEVEMENTS PAGE
# ============================================

@app.route('/student/achievements')
@login_required
def student_achievements():
    """Student achievements page showing all medals and progress"""
    if current_user.role != 'student':
        return redirect(url_for('admin_dashboard'))
    
    student = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    if not student:
        flash('Student not found', 'error')
        return redirect(url_for('logout'))
    
    # Get earned medals
    earned_medal_ids = set(student.get('medals', []))
    earned_medals = []
    
    for medal_id in earned_medal_ids:
        medal = get_medal_details(medal_id)
        earned_medals.append({
            'id': medal_id,
            'name': medal['name'],
            'description': medal['description'],
            'icon': medal['icon'],
            'color': medal['color'],
            'category': medal['category'],
            'earned_at': None
        })
    
    # Get all available medals
    all_medals = []
    for medal_id, medal in MEDALS.items():
        is_earned = medal_id in earned_medal_ids
        all_medals.append({
            'id': medal_id,
            'name': medal['name'],
            'description': medal['description'],
            'icon': medal['icon'],
            'color': medal['color'],
            'category': medal['category'],
            'earned': is_earned,
            'requirement': medal['requirement'],
            'requirement_type': medal['requirement_type']
        })
    
    # Calculate progress for each medal type
    total_materials = student.get('total_materials', 0)
    total_videos = student.get('total_videos', 0)
    streak = student.get('streak', 0)
    
    language_activities = defaultdict(int)
    if 'material_views' in mongo.db.list_collection_names():
        activities = mongo.db.material_views.find({'user_id': current_user.id})
        for act in activities:
            lang = act.get('material_language', 'english')
            language_activities[lang] += 1
    
    distinct_languages = set(language_activities.keys())
    distinct_languages.add(student.get('language', 'english'))
    language_count = len(distinct_languages)
    
    total_activities = total_materials + total_videos
    
    perfect_scores = student.get('perfect_scores', 0)
    early_count = student.get('early_activities', 0)
    night_count = student.get('night_activities', 0)
    weekend_count = student.get('weekend_activities', 0)
    
    medal_progress = {}
    for medal_id, medal in MEDALS.items():
        req_type = medal['requirement_type']
        requirement = medal['requirement']
        current = 0
        
        if req_type == 'material_count':
            current = total_materials
        elif req_type == 'video_count':
            current = total_videos
        elif req_type == 'language_count':
            current = language_count
        elif req_type == 'streak':
            current = streak
        elif req_type == 'total_activities':
            current = total_activities
        elif req_type.endswith('_activities'):
            lang = req_type.replace('_activities', '')
            current = language_activities.get(lang, 0)
        elif req_type == 'perfect_scores':
            current = perfect_scores
        elif req_type == 'early_activities':
            current = early_count
        elif req_type == 'night_activities':
            current = night_count
        elif req_type == 'weekend_activities':
            current = weekend_count
        
        medal_progress[medal_id] = {
            'current': current,
            'required': requirement,
            'percentage': min(100, int((current / requirement) * 100)) if requirement > 0 else 0
        }
    
    # Group medals by category
    medals_by_category = {
        'learning': [],
        'streak': [],
        'milestone': [],
        'language': [],
        'language_specific': [],
        'special': [],
        'achievement': []
    }
    
    for medal in all_medals:
        category = medal['category']
        if category not in medals_by_category:
            medals_by_category[category] = []
        
        medal['progress'] = medal_progress.get(medal['id'], {'current': 0, 'required': 0, 'percentage': 0})
        medals_by_category[category].append(medal)
    
    total_medals = len(earned_medals)
    total_possible = len(MEDALS)
    completion_percentage = int((total_medals / total_possible) * 100) if total_possible > 0 else 0
    
    recent_medal_awards = []
    if 'student_activities' in mongo.db.list_collection_names():
        medal_activities = list(mongo.db.student_activities.find({
            'user_id': current_user.id,
            'activity_type': 'medal_award'
        }).sort('activity_at', -1).limit(10))
        
        for act in medal_activities:
            recent_medal_awards.append({
                'medal_name': act.get('item_title', 'Medal'),
                'icon': act.get('icon', '🏅'),
                'awarded_at': act.get('activity_at'),
                'time_ago': get_time_ago(act.get('activity_at'))
            })
    
    next_medals = []
    for medal_id, medal in MEDALS.items():
        if medal_id not in earned_medal_ids:
            progress = medal_progress.get(medal_id, {})
            if progress.get('percentage', 0) > 0:
                next_medals.append({
                    'id': medal_id,
                    'name': medal['name'],
                    'icon': medal['icon'],
                    'color': medal['color'],
                    'progress': progress.get('percentage', 0),
                    'current': progress.get('current', 0),
                    'required': progress.get('required', 0),
                    'description': medal['description']
                })
    
    next_medals.sort(key=lambda x: x['progress'], reverse=True)
    next_medals = next_medals[:5]
    
    return render_template(
        'student_achievements.html',
        student=student,
        earned_medals=earned_medals,
        all_medals=all_medals,
        medals_by_category=medals_by_category,
        total_medals=total_medals,
        total_possible=total_possible,
        completion_percentage=completion_percentage,
        recent_medal_awards=recent_medal_awards,
        next_medals=next_medals,
        medal_progress=medal_progress,
        now=datetime.now()
    )

# ============================================
# API Endpoints for Achievements
# ============================================

@app.route('/api/student/medals')
@login_required
def api_student_medals():
    """API endpoint to get student medals"""
    if current_user.role != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    student = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    if not student:
        return jsonify({'success': False, 'error': 'Student not found'}), 404
    
    earned_medals = []
    for medal_id in student.get('medals', []):
        medal = get_medal_details(medal_id)
        earned_medals.append({
            'id': medal_id,
            'name': medal['name'],
            'description': medal['description'],
            'icon': medal['icon'],
            'color': medal['color']
        })
    
    return jsonify({
        'success': True,
        'medals': earned_medals,
        'count': len(earned_medals)
    })

@app.route('/api/student/medal-progress')
@login_required
def api_medal_progress():
    """API endpoint to get progress towards all medals"""
    if current_user.role != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    student = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    if not student:
        return jsonify({'success': False, 'error': 'Student not found'}), 404
    
    earned_medals = set(student.get('medals', []))
    
    total_materials = student.get('total_materials', 0)
    total_videos = student.get('total_videos', 0)
    streak = student.get('streak', 0)
    
    language_activities = defaultdict(int)
    if 'material_views' in mongo.db.list_collection_names():
        activities = mongo.db.material_views.find({'user_id': current_user.id})
        for act in activities:
            lang = act.get('material_language', 'english')
            language_activities[lang] += 1
    
    distinct_languages = set(language_activities.keys())
    distinct_languages.add(student.get('language', 'english'))
    language_count = len(distinct_languages)
    total_activities = total_materials + total_videos
    perfect_scores = student.get('perfect_scores', 0)
    early_count = student.get('early_activities', 0)
    night_count = student.get('night_activities', 0)
    weekend_count = student.get('weekend_activities', 0)
    
    progress = {}
    for medal_id, medal in MEDALS.items():
        req_type = medal['requirement_type']
        requirement = medal['requirement']
        current = 0
        
        if req_type == 'material_count':
            current = total_materials
        elif req_type == 'video_count':
            current = total_videos
        elif req_type == 'language_count':
            current = language_count
        elif req_type == 'streak':
            current = streak
        elif req_type == 'total_activities':
            current = total_activities
        elif req_type.endswith('_activities'):
            lang = req_type.replace('_activities', '')
            current = language_activities.get(lang, 0)
        elif req_type == 'perfect_scores':
            current = perfect_scores
        elif req_type == 'early_activities':
            current = early_count
        elif req_type == 'night_activities':
            current = night_count
        elif req_type == 'weekend_activities':
            current = weekend_count
        
        progress[medal_id] = {
            'name': medal['name'],
            'icon': medal['icon'],
            'current': current,
            'required': requirement,
            'percentage': min(100, int((current / requirement) * 100)) if requirement > 0 else 0,
            'earned': medal_id in earned_medals
        }
    
    return jsonify({'success': True, 'progress': progress})

# ============================================
# Contact Admin Routes
# ============================================
@app.route('/contact-admin', methods=['GET', 'POST'])
@login_required
def contact_admin():
    """Student contact form to send messages to admin"""
    if current_user.role != 'student':
        return redirect(url_for('admin_dashboard'))
   
    success = request.args.get('success', False)
   
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        category = request.form.get('category')
        priority = request.form.get('priority', 'medium')
        subject = request.form.get('subject')
        message = request.form.get('message')
       
        attachment_file = request.files.get('attachment')
        attachment_path = None
        attachment_filename = None
       
        if attachment_file and attachment_file.filename:
            if allowed_attachment_file(attachment_file.filename):
                filename = secure_filename(attachment_file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                attachment_filename = f"{timestamp}_{filename}"
                attachment_path = os.path.join(app.config['CONTACT_ATTACHMENTS_FOLDER'], attachment_filename)
                attachment_file.save(attachment_path)
       
        contact_data = {
            'student_id': current_user.id,
            'student_name': name,
            'student_email': email,
            'category': category,
            'priority': priority,
            'subject': subject,
            'message': message,
            'attachment_path': attachment_path,
            'attachment_filename': attachment_filename,
            'status': 'pending',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'admin_notes': '',
            'resolved_at': None,
            'resolved_by': None
        }
       
        result = mongo.db.contact_messages.insert_one(contact_data)
        message_id = str(result.inserted_id)
       
        track_activity(
            user_id=current_user.id,
            user_name=current_user.name,
            user_email=email,
            activity_type='contact',
            item_id=message_id,
            item_title=subject,
            item_type='contact',
            details=f'Category: {category}, Priority: {priority}',
            xp_earned=5
        )
       
        admin = mongo.db.users.find_one({'role': 'admin'})
        if admin:
            admin_email = admin.get('email', 'admin@aitutor.com')
           
            email_subject = f"[AI Tutor Support] {category.upper()} - {subject}"
           
            priority_emoji = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🟠',
                'urgent': '🔴'
            }.get(priority, '🟡')
           
            email_body = f"""
New support request received from {name} ({email})

Priority: {priority_emoji} {priority.upper()}
Category: {category}
Subject: {subject}
Message: {message}

Student ID: {current_user.id}
Message ID: {message_id}
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please log in to the admin dashboard to respond to this message.
            """
           
            email_html = f"""
            <html>
            <body>
                <h2>New Support Request</h2>
                <p><strong>From:</strong> {name} ({email})</p>
                <p><strong>Priority:</strong> {priority_emoji} {priority.upper()}</p>
                <p><strong>Category:</strong> {category}</p>
                <p><strong>Subject:</strong> {subject}</p>
                <p><strong>Message:</strong></p>
                <p>{message}</p>
                <hr>
                <p><small>Student ID: {current_user.id}<br>
                Message ID: {message_id}<br>
                Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
                <p>Please log in to the admin dashboard to respond to this message.</p>
            </body>
            </html>
            """
           
            attachments = [(attachment_path, attachment_filename)] if attachment_path and attachment_filename else None
            send_email_async(admin_email, email_subject, email_body, email_html, attachments)
       
        flash('Your message has been sent successfully! Our team will get back to you within 24-48 hours.', 'success')
        return redirect(url_for('contact_admin', success=True))
   
    student = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    return render_template('contact_admin.html', student=student, success=success)

@app.route('/api/contact', methods=['POST'])
@login_required
def api_contact():
    """API endpoint for contact form submission"""
    if current_user.role != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    name = request.form.get('name')
    email = request.form.get('email')
    category = request.form.get('category')
    priority = request.form.get('priority', 'medium')
    subject = request.form.get('subject')
    message = request.form.get('message')
   
    attachment_file = request.files.get('attachment')
    attachment_path = None
    attachment_filename = None
   
    if attachment_file and attachment_file.filename:
        if allowed_attachment_file(attachment_file.filename):
            filename = secure_filename(attachment_file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            attachment_filename = f"{timestamp}_{filename}"
            attachment_path = os.path.join(app.config['CONTACT_ATTACHMENTS_FOLDER'], attachment_filename)
            attachment_file.save(attachment_path)
   
    contact_data = {
        'student_id': current_user.id,
        'student_name': name,
        'student_email': email,
        'category': category,
        'priority': priority,
        'subject': subject,
        'message': message,
        'attachment_path': attachment_path,
        'attachment_filename': attachment_filename,
        'status': 'pending',
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'admin_notes': '',
        'resolved_at': None,
        'resolved_by': None
    }
   
    result = mongo.db.contact_messages.insert_one(contact_data)
   
    track_activity(
        user_id=current_user.id,
        user_name=current_user.name,
        user_email=email,
        activity_type='contact',
        item_id=str(result.inserted_id),
        item_title=subject,
        item_type='contact',
        details=f'Category: {category}, Priority: {priority}',
        xp_earned=5
    )
   
    admin = mongo.db.users.find_one({'role': 'admin'})
    if admin:
        admin_email = admin.get('email', 'admin@aitutor.com')
       
        email_subject = f"[AI Tutor Support] {category.upper()} - {subject}"
       
        priority_emoji = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'urgent': '🔴'
        }.get(priority, '🟡')
       
        email_body = f"""
New support request received from {name} ({email})

Priority: {priority_emoji} {priority.upper()}
Category: {category}
Subject: {subject}
Message: {message}

Student ID: {current_user.id}
Message ID: {str(result.inserted_id)}
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please log in to the admin dashboard to respond to this message.
        """
       
        attachments = [(attachment_path, attachment_filename)] if attachment_path and attachment_filename else None
        send_email_async(admin_email, email_subject, email_body, None, attachments)
   
    return jsonify({'success': True, 'message_id': str(result.inserted_id)})

# ============================================
# Admin Contact Management Routes
# ============================================
@app.route('/admin/contact-messages')
@login_required
def admin_contact_messages():
    """Admin view to manage contact messages from students"""
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
   
    status_filter = request.args.get('status', 'all')
    category_filter = request.args.get('category', 'all')
    priority_filter = request.args.get('priority', 'all')
   
    query = {}
    if status_filter != 'all':
        query['status'] = status_filter
    if category_filter != 'all':
        query['category'] = category_filter
    if priority_filter != 'all':
        query['priority'] = priority_filter
   
    messages = list(mongo.db.contact_messages.find(query).sort('created_at', -1))
   
    for message in messages:
        message['_id'] = str(message['_id'])
        message['student_id'] = str(message['student_id'])
   
    total_messages = mongo.db.contact_messages.count_documents({})
    pending_messages = mongo.db.contact_messages.count_documents({'status': 'pending'})
    in_progress_messages = mongo.db.contact_messages.count_documents({'status': 'in_progress'})
    resolved_messages = mongo.db.contact_messages.count_documents({'status': 'resolved'})
   
    categories = ['technical', 'academic', 'account', 'feedback', 'other']
    category_counts = {}
    for cat in categories:
        category_counts[cat] = mongo.db.contact_messages.count_documents({'category': cat})
   
    priorities = ['low', 'medium', 'high', 'urgent']
    priority_counts = {}
    for pri in priorities:
        priority_counts[pri] = mongo.db.contact_messages.count_documents({'priority': pri})
   
    return render_template(
        'admin_contact_messages.html',
        messages=messages,
        total_messages=total_messages,
        pending_messages=pending_messages,
        in_progress_messages=in_progress_messages,
        resolved_messages=resolved_messages,
        category_counts=category_counts,
        priority_counts=priority_counts,
        status_filter=status_filter,
        category_filter=category_filter,
        priority_filter=priority_filter,
        now=datetime.now()
    )

@app.route('/api/admin/contact-message/<message_id>', methods=['GET', 'POST'])
@login_required
def admin_contact_message_detail(message_id):
    """Get or update a specific contact message"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    if request.method == 'GET':
        message = mongo.db.contact_messages.find_one({'_id': ObjectId(message_id)})
        if not message:
            return jsonify({'success': False, 'error': 'Message not found'}), 404
       
        message['_id'] = str(message['_id'])
        message['student_id'] = str(message['student_id'])
        return jsonify(message)
   
    elif request.method == 'POST':
        data = request.json
        update_data = {
            'status': data.get('status'),
            'admin_notes': data.get('admin_notes', ''),
            'updated_at': datetime.now()
        }
       
        if data.get('status') == 'resolved':
            update_data['resolved_at'] = datetime.now()
            update_data['resolved_by'] = current_user.id
       
        mongo.db.contact_messages.update_one(
            {'_id': ObjectId(message_id)},
            {'$set': update_data}
        )
       
        if data.get('send_response') and data.get('response_message'):
            message = mongo.db.contact_messages.find_one({'_id': ObjectId(message_id)})
            if message:
                student = mongo.db.users.find_one({'_id': ObjectId(message['student_id'])})
                if student:
                    response_subject = f"Re: {message['subject']}"
                    response_body = f"""
Dear {message['student_name']},

Thank you for contacting AI Tutor Support. Here's the response to your query:

{data['response_message']}

Your message details:
- Category: {message['category']}
- Subject: {message['subject']}
- Status: {update_data['status']}

If you have any further questions, please don't hesitate to reach out again.

Best regards,
AI Tutor Support Team
                    """
                    send_email_async(student['email'], response_subject, response_body)
       
        return jsonify({'success': True})

@app.route('/api/admin/contact-message/<message_id>/reply', methods=['POST'])
@login_required
def admin_reply_contact_message(message_id):
    """Send a reply to a contact message"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    data = request.json
    reply_message = data.get('reply_message')
   
    if not reply_message:
        return jsonify({'success': False, 'error': 'Reply message is required'}), 400
   
    message = mongo.db.contact_messages.find_one({'_id': ObjectId(message_id)})
    if not message:
        return jsonify({'success': False, 'error': 'Message not found'}), 404
   
    student = mongo.db.users.find_one({'_id': ObjectId(message['student_id'])})
   
    subject = f"Re: {message['subject']}"
    body = f"""
Dear {message['student_name']},

Thank you for contacting AI Tutor Support. Here's the response to your query:

{reply_message}

Your message details:
- Category: {message['category']}
- Subject: {message['subject']}
- Priority: {message['priority'].upper()}

If you have any further questions, please don't hesitate to reach out again.

Best regards,
AI Tutor Support Team
"""
   
    send_email_async(message['student_email'], subject, body)
   
    mongo.db.contact_messages.update_one(
        {'_id': ObjectId(message_id)},
        {'$set': {
            'admin_reply': reply_message,
            'admin_reply_at': datetime.now(),
            'admin_reply_by': current_user.id,
            'status': 'resolved',
            'resolved_at': datetime.now(),
            'resolved_by': current_user.id,
            'updated_at': datetime.now()
        }}
    )
   
    track_activity(
        user_id=current_user.id,
        user_name=current_user.name,
        user_email=current_user.email,
        activity_type='reply',
        item_id=message_id,
        item_title=message['subject'],
        item_type='contact',
        details='Admin replied to support message',
        xp_earned=0
    )
   
    return jsonify({'success': True, 'message': 'Reply sent successfully'})

@app.route('/api/admin/contact-stats')
@login_required
def admin_contact_stats():
    """Get contact message statistics for admin dashboard"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = datetime.now() - timedelta(days=7)
   
    stats = {
        'total': mongo.db.contact_messages.count_documents({}),
        'pending': mongo.db.contact_messages.count_documents({'status': 'pending'}),
        'in_progress': mongo.db.contact_messages.count_documents({'status': 'in_progress'}),
        'resolved': mongo.db.contact_messages.count_documents({'status': 'resolved'}),
        'today': mongo.db.contact_messages.count_documents({'created_at': {'$gte': today_start}}),
        'this_week': mongo.db.contact_messages.count_documents({'created_at': {'$gte': week_ago}}),
        'by_priority': {
            'low': mongo.db.contact_messages.count_documents({'priority': 'low'}),
            'medium': mongo.db.contact_messages.count_documents({'priority': 'medium'}),
            'high': mongo.db.contact_messages.count_documents({'priority': 'high'}),
            'urgent': mongo.db.contact_messages.count_documents({'priority': 'urgent'})
        },
        'by_category': {
            'technical': mongo.db.contact_messages.count_documents({'category': 'technical'}),
            'academic': mongo.db.contact_messages.count_documents({'category': 'academic'}),
            'account': mongo.db.contact_messages.count_documents({'category': 'account'}),
            'feedback': mongo.db.contact_messages.count_documents({'category': 'feedback'}),
            'other': mongo.db.contact_messages.count_documents({'category': 'other'})
        }
    }
   
    return jsonify(stats)

@app.route('/api/admin/contact-messages/export', methods=['GET'])
@login_required
def export_contact_messages():
    """Export contact messages to CSV"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    status_filter = request.args.get('status', 'all')
    category_filter = request.args.get('category', 'all')
    priority_filter = request.args.get('priority', 'all')
   
    query = {}
    if status_filter != 'all':
        query['status'] = status_filter
    if category_filter != 'all':
        query['category'] = category_filter
    if priority_filter != 'all':
        query['priority'] = priority_filter
   
    messages = list(mongo.db.contact_messages.find(query).sort('created_at', -1))
   
    import csv
    import io
   
    output = io.StringIO()
    writer = csv.writer(output)
   
    writer.writerow(['ID', 'Student Name', 'Student Email', 'Category', 'Priority', 'Subject', 'Message', 'Status', 'Created At', 'Resolved At', 'Admin Notes'])
   
    for msg in messages:
        writer.writerow([
            str(msg['_id']),
            msg.get('student_name', ''),
            msg.get('student_email', ''),
            msg.get('category', ''),
            msg.get('priority', ''),
            msg.get('subject', ''),
            msg.get('message', '').replace('\n', ' '),
            msg.get('status', ''),
            msg.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if msg.get('created_at') else '',
            msg.get('resolved_at', '').strftime('%Y-%m-%d %H:%M:%S') if msg.get('resolved_at') else '',
            msg.get('admin_notes', '').replace('\n', ' ')
        ])
   
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'contact_messages_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/api/admin/contact-messages/mark-all-read', methods=['POST'])
@login_required
def mark_all_messages_read():
    """Mark all pending messages as read (in_progress)"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    result = mongo.db.contact_messages.update_many(
        {'status': 'pending'},
        {'$set': {
            'status': 'in_progress',
            'updated_at': datetime.now(),
            'admin_notes': 'Marked as read by admin'
        }}
    )
   
    return jsonify({'success': True, 'updated_count': result.modified_count})

# ============================================
# Admin Activity Dashboard
# ============================================

@app.route('/admin/activity-dashboard')
@login_required
def admin_activity_dashboard():
    """Admin dashboard for viewing student activities"""
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
   
    recent_activities = get_recent_activities(limit=100)
    activity_stats = get_activity_stats(days=7)
   
    students_activity = list(mongo.db.student_activities.aggregate([
        {'$match': {'activity_at': {'$gte': datetime.now() - timedelta(days=7)}}},
        {'$group': {
            '_id': '$user_id',
            'user_name': {'$first': '$user_name'},
            'user_email': {'$first': '$user_email'},
            'activity_count': {'$sum': 1},
            'xp_earned': {'$sum': '$xp_earned'},
            'last_activity': {'$max': '$activity_at'}
        }},
        {'$sort': {'activity_count': -1}},
        {'$limit': 20}
    ]))
   
    return render_template(
        'admin_activity_dashboard.html',
        recent_activities=recent_activities,
        activity_stats=activity_stats,
        students_activity=students_activity,
        now=datetime.now()
    )

@app.route('/api/admin/activity-stats')
@login_required
def api_activity_stats():
    """API endpoint for activity statistics"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    days = request.args.get('days', 7, type=int)
    stats = get_activity_stats(days)
    return jsonify(stats)

@app.route('/api/admin/activity-feed')
@login_required
def api_activity_feed():
    """API endpoint for real-time activity feed"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    limit = request.args.get('limit', 15, type=int)
    activities = get_recent_activities_feed(limit=limit)
    return jsonify({'activities': activities})

@app.route('/api/admin/activities')
@login_required
def api_activities():
    """API endpoint for filtered activities with pagination"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    activity_type = request.args.get('type')
    date_range = request.args.get('date')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
   
    query = {}
    if activity_type:
        query['activity_type'] = activity_type
    if search:
        query['$or'] = [
            {'user_name': {'$regex': search, '$options': 'i'}},
            {'user_email': {'$regex': search, '$options': 'i'}},
            {'item_title': {'$regex': search, '$options': 'i'}}
        ]
   
    if date_range:
        now = datetime.now()
        if date_range == 'today':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            query['activity_at'] = {'$gte': start}
        elif date_range == 'week':
            start = now - timedelta(days=7)
            query['activity_at'] = {'$gte': start}
        elif date_range == 'month':
            start = now - timedelta(days=30)
            query['activity_at'] = {'$gte': start}
   
    total = mongo.db.student_activities.count_documents(query)
    total_pages = (total + limit - 1) // limit
    skip = (page - 1) * limit
   
    activities = list(mongo.db.student_activities.find(query)
                      .sort('activity_at', -1)
                      .skip(skip)
                      .limit(limit))
   
    for activity in activities:
        activity['_id'] = str(activity['_id'])
        activity['time_ago'] = get_time_ago(activity.get('activity_at'))
   
    stats = get_activity_stats(days=7)
   
    return jsonify({
        'activities': activities,
        'page': page,
        'total_pages': total_pages,
        'total': total,
        'stats': stats
    })

# ============================================
# Student Activity Feed
# ============================================

@app.route('/student/activity')
@login_required
def student_activity():
    """Student's personal activity feed"""
    if current_user.role != 'student':
        return redirect(url_for('admin_dashboard'))
   
    activities = get_recent_activities(limit=100, user_id=current_user.id)
   
    total_activities = mongo.db.student_activities.count_documents({'user_id': current_user.id})
   
    total_xp_pipeline = mongo.db.student_activities.aggregate([
        {'$match': {'user_id': current_user.id}},
        {'$group': {'_id': None, 'total': {'$sum': '$xp_earned'}}}
    ])
    total_xp = list(total_xp_pipeline)
    total_xp = total_xp[0]['total'] if total_xp else 0
   
    activity_by_type = {}
    for act_type in ['view', 'download', 'watch', 'favorite', 'contact', 'ai_chat', 'medal_award']:
        count = mongo.db.student_activities.count_documents({
            'user_id': current_user.id,
            'activity_type': act_type
        })
        activity_by_type[act_type] = count
   
    return render_template(
        'student_activity.html',
        activities=activities,
        total_activities=total_activities,
        total_xp=total_xp,
        activity_by_type=activity_by_type,
        now=datetime.now()
    )

# ============================================
# Admin Email Management
# ============================================
@app.route('/admin/emails')
@login_required
def admin_emails():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))

    students = list(mongo.db.users.find({'role': 'student'}).sort('name', 1))
    email_logs = list(mongo.db.email_logs.find().sort('sent_at', -1).limit(50))

    for log in email_logs:
        log['sent_date'] = log.get('sent_at', None)
        log['recipient_email'] = log.get('recipient', 'N/A')
        log['subject'] = log.get('subject', 'No Subject')
        log['status'] = log.get('status', 'unknown')

    campaigns = []
    top_emails = []

    return render_template(
        'admin_emails.html',
        students=students,
        email_logs=email_logs,
        campaigns=campaigns,
        templates=[],
        top_emails=top_emails,
        total_emails_sent=len(email_logs),
        emails_sent_today=0,
        open_rate=0,
        total_opened=0,
        click_rate=0,
        chart_labels=[],
        chart_data=[],
        now=datetime.now()
    )

@app.route('/api/admin/send-email', methods=['POST'])
@login_required
def send_email_api():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    data = request.json
    email_type = data.get('type')
    subject = data.get('subject')
    message = data.get('message')
    use_template = data.get('use_template', False)
    template_id = data.get('template_id')
   
    if not subject or not message:
        return jsonify({'success': False, 'error': 'Subject and message are required'}), 400
   
    recipients = []
   
    if email_type == 'individual':
        student_id = data.get('student_id')
        student = mongo.db.users.find_one({'_id': ObjectId(student_id), 'role': 'student'})
        if student:
            recipients.append(student['email'])
   
    elif email_type == 'bulk':
        student_ids = data.get('student_ids', [])
        for sid in student_ids:
            student = mongo.db.users.find_one({'_id': ObjectId(sid), 'role': 'student'})
            if student:
                recipients.append(student['email'])
   
    elif email_type == 'grade':
        grade = data.get('grade')
        students = mongo.db.users.find({'role': 'student', 'grade': int(grade)})
        for student in students:
            recipients.append(student['email'])
   
    elif email_type == 'language':
        language = data.get('language')
        students = mongo.db.users.find({'role': 'student', 'language': language})
        for student in students:
            recipients.append(student['email'])
   
    elif email_type == 'all':
        students = mongo.db.users.find({'role': 'student'})
        for student in students:
            recipients.append(student['email'])
   
    if not recipients:
        return jsonify({'success': False, 'error': 'No recipients found'}), 400
   
    html_body = None
    if use_template and template_id:
        template = mongo.db.email_templates.find_one({'_id': ObjectId(template_id)})
        if template:
            html_body = template['html_content'].replace('{{message}}', message)
   
    send_bulk_emails(recipients, subject, message, html_body)
   
    campaign_id = mongo.db.email_campaigns.insert_one({
        'type': email_type,
        'subject': subject,
        'message': message,
        'recipient_count': len(recipients),
        'sent_by': current_user.id,
        'sent_by_name': current_user.name,
        'sent_at': datetime.now(),
        'use_template': use_template,
        'template_id': template_id if use_template else None
    }).inserted_id
   
    track_activity(
        user_id=current_user.id,
        user_name=current_user.name,
        user_email=current_user.email,
        activity_type='email_campaign',
        item_id=str(campaign_id),
        item_title=subject,
        item_type='email',
        details=f'Email sent to {len(recipients)} recipients',
        xp_earned=0
    )
   
    return jsonify({
        'success': True,
        'message': f'Email sent to {len(recipients)} recipient(s)',
        'recipient_count': len(recipients)
    })

@app.route('/api/admin/email-templates', methods=['GET', 'POST'])
@login_required
def manage_email_templates():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    if request.method == 'POST':
        data = request.json
        template_data = {
            'name': data.get('name'),
            'subject': data.get('subject'),
            'html_content': data.get('html_content'),
            'created_at': datetime.now(),
            'created_by': current_user.id
        }
        result = mongo.db.email_templates.insert_one(template_data)
        return jsonify({'success': True, 'template_id': str(result.inserted_id)})
   
    else:
        templates = list(mongo.db.email_templates.find().sort('created_at', -1))
        for t in templates:
            t['_id'] = str(t['_id'])
        return jsonify({'templates': templates})

@app.route('/api/admin/email-templates/<template_id>', methods=['DELETE'])
@login_required
def delete_email_template(template_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    mongo.db.email_templates.delete_one({'_id': ObjectId(template_id)})
    return jsonify({'success': True})

@app.route('/api/admin/email-stats')
@login_required
def email_stats():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    total_sent = mongo.db.email_logs.count_documents({'status': 'delivered'})
    total_failed = mongo.db.email_logs.count_documents({'status': 'failed'})
   
    seven_days_ago = datetime.now() - timedelta(days=7)
    daily_stats = []
    for i in range(7):
        day = datetime.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
       
        count = mongo.db.email_logs.count_documents({
            'sent_at': {'$gte': day_start, '$lte': day_end},
            'status': 'delivered'
        })
        daily_stats.append({
            'date': day.strftime('%Y-%m-%d'),
            'count': count
        })
   
    campaigns = list(mongo.db.email_campaigns.find().sort('sent_at', -1).limit(10))
    for c in campaigns:
        c['_id'] = str(c['_id'])
        c['sent_at'] = c['sent_at'].strftime('%Y-%m-%d %H:%M')
   
    return jsonify({
        'total_sent': total_sent,
        'total_failed': total_failed,
        'success_rate': (total_sent / (total_sent + total_failed) * 100) if (total_sent + total_failed) > 0 else 0,
        'daily_stats': daily_stats,
        'campaigns': campaigns
    })

# ============================================
# Admin Dashboard
# ============================================
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
   
    students_with_medals = list(mongo.db.users.find(
        {'role': 'student'}
    ).sort('xp', -1))
    
    total_medals_awarded = 0
    for student in students_with_medals:
        total_medals_awarded += len(student.get('medals', []))
    
    medal_distribution = {}
    for medal_id in MEDALS:
        medal_distribution[medal_id] = mongo.db.users.count_documents({
            'role': 'student',
            'medals': medal_id
        })
    
    top_medal_earners = []
    for student in students_with_medals[:10]:
        medal_count = len(student.get('medals', []))
        if medal_count > 0:
            top_medal_earners.append({
                'name': student.get('name', 'Unknown'),
                'medal_count': medal_count,
                'xp': student.get('xp', 0)
            })
    top_medal_earners.sort(key=lambda x: x['medal_count'], reverse=True)
    
    total_students = mongo.db.users.count_documents({'role': 'student'})
    total_materials = mongo.db.study_materials.count_documents({})
    total_videos = mongo.db.videos.count_documents({})
   
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = datetime.now() - timedelta(days=7)
   
    new_students_today = mongo.db.users.count_documents({
        'role': 'student',
        'joined_date': {'$gte': today_start}
    })
   
    new_students_week = mongo.db.users.count_documents({
        'role': 'student',
        'joined_date': {'$gte': week_ago}
    })
   
    active_today = mongo.db.users.count_documents({
        'role': 'student',
        'last_login': {'$gte': today_start}
    })
   
    pdf_count = mongo.db.study_materials.count_documents({'type': 'pdf'})
    image_count = mongo.db.study_materials.count_documents({'type': 'image'})
    audio_count = mongo.db.study_materials.count_documents({'type': 'audio'})
    document_count = mongo.db.study_materials.count_documents({'type': 'document'})
   
    pipeline = [{
        '$group': {
            '_id': None,
            'total_views': {'$sum': '$views'},
            'total_downloads': {'$sum': '$downloads'},
            'total_favorites': {'$sum': '$favorites'}
        }
    }]
    result = list(mongo.db.study_materials.aggregate(pipeline))
   
    total_material_views = result[0]['total_views'] if result else 0
    total_material_downloads = result[0]['total_downloads'] if result else 0
    total_material_favorites = result[0]['total_favorites'] if result else 0
   
    new_materials_today = mongo.db.study_materials.count_documents({
        'uploaded_at': {'$gte': today_start}
    })
   
    downloads_today = 0
    material_views_today = 0
   
    if 'material_views' in mongo.db.list_collection_names():
        material_views_today = mongo.db.material_views.count_documents({
            'viewed_at': {'$gte': today_start}
        })
   
    if 'material_downloads' in mongo.db.list_collection_names():
        downloads_today = mongo.db.material_downloads.count_documents({
            'downloaded_at': {'$gte': today_start}
        })
   
    video_pipeline = [{
        '$group': {
            '_id': None,
            'total_views': {'$sum': '$views'},
            'total_downloads': {'$sum': '$downloads'}
        }
    }]
    video_result = list(mongo.db.videos.aggregate(video_pipeline))
   
    total_video_views = video_result[0]['total_views'] if video_result else 0
    total_video_downloads = video_result[0]['total_downloads'] if video_result else 0
   
    total_watch_hours = 0
    if 'video_watch_time' in mongo.db.list_collection_names():
        watch_pipeline = [{
            '$group': {
                '_id': None,
                'total_seconds': {'$sum': '$duration'}
            }
        }]
        watch_result = list(mongo.db.video_watch_time.aggregate(watch_pipeline))
        total_watch_hours = watch_result[0]['total_seconds'] // 3600 if watch_result else 0
   
    contact_pending = mongo.db.contact_messages.count_documents({'status': 'pending'})
    contact_in_progress = mongo.db.contact_messages.count_documents({'status': 'in_progress'})
    contact_resolved = mongo.db.contact_messages.count_documents({'status': 'resolved'})
   
    recent_contact_messages = list(mongo.db.contact_messages.find().sort('created_at', -1).limit(5))
    for msg in recent_contact_messages:
        msg['_id'] = str(msg['_id'])
   
    activity_stats = get_activity_stats(days=7)
    recent_activities_feed = get_recent_activities_feed(limit=15)
   
    total_emails_sent = mongo.db.email_logs.count_documents({'status': 'delivered'})
    emails_sent_today = mongo.db.email_logs.count_documents({
        'sent_at': {'$gte': today_start},
        'status': 'delivered'
    })
   
    all_languages = [
        'english', 'hindi', 'bengali', 'telugu', 'marathi', 'tamil', 'urdu',
        'gujarati', 'kannada', 'malayalam', 'oriya', 'punjabi', 'assamese',
        'maithili', 'santali', 'kashmiri', 'nepali', 'sindhi', 'dogri',
        'konkani', 'manipuri', 'bodo'
    ]
   
    language_names = {
        'english': 'English', 'hindi': 'हिंदी', 'bengali': 'বাংলা', 'telugu': 'తెలుగు',
        'marathi': 'मराठी', 'tamil': 'தமிழ்', 'urdu': 'اردو', 'gujarati': 'ગુજરાતી',
        'kannada': 'ಕನ್ನಡ', 'malayalam': 'മലയാളം', 'oriya': 'ଓଡ଼ିଆ', 'punjabi': 'ਪੰਜਾਬੀ',
        'assamese': 'অসমীয়া', 'maithili': 'मैथिली', 'santali': 'ᱥᱟᱱᱛᱟᱲᱤ',
        'kashmiri': 'कॉशुर', 'nepali': 'नेपाली', 'sindhi': 'سنڌي', 'dogri': 'डोगरी',
        'konkani': 'कोंकणी', 'manipuri': 'মৈতৈলোন্', 'bodo': 'बर'
    }
   
    all_languages_stats = []
    material_languages = []
    video_languages = []
    top_languages = []
   
    for lang in all_languages:
        materials_count = mongo.db.study_materials.count_documents({'language': lang})
        videos_count = mongo.db.videos.count_documents({'language': lang})
       
        material_views = 0
        material_views_pipeline = [
            {'$match': {'language': lang}},
            {'$group': {'_id': None, 'total': {'$sum': '$views'}}}
        ]
        views_result = list(mongo.db.study_materials.aggregate(material_views_pipeline))
        material_views = views_result[0]['total'] if views_result else 0
       
        total_count = materials_count + videos_count
       
        if total_count > 0:
            top_languages.append({
                'name': language_names.get(lang, lang.title()),
                'code': lang,
                'count': total_count,
                'percentage': min(100, total_count * 2)
            })
       
        all_languages_stats.append({
            'name': language_names.get(lang, lang.title()),
            'code': lang,
            'materials': materials_count,
            'videos': videos_count,
            'views': material_views,
            'total': total_count
        })
       
        if materials_count > 0:
            material_languages.append({
                'name': language_names.get(lang, lang.title()),
                'code': lang,
                'count': materials_count
            })
       
        if videos_count > 0:
            video_languages.append({
                'name': language_names.get(lang, lang.title()),
                'code': lang,
                'count': videos_count
            })
   
    top_languages.sort(key=lambda x: x['count'], reverse=True)
    material_languages.sort(key=lambda x: x['count'], reverse=True)
    video_languages.sort(key=lambda x: x['count'], reverse=True)
   
    grade_distribution = []
    for grade in range(5, 13):
        materials_count = mongo.db.study_materials.count_documents({'grade': grade})
        videos_count = mongo.db.videos.count_documents({'grade': grade})
        total_count = materials_count + videos_count
        if total_count > 0:
            grade_distribution.append({
                'grade': grade,
                'count': total_count,
                'percentage': min(100, total_count * 5)
            })
   
    subjects = ['mathematics', 'science', 'english', 'hindi', 'social', 'general']
    material_by_subject = []
   
    for subject in subjects:
        subject_views = 0
        views_pipeline = [
            {'$match': {'subject': subject}},
            {'$group': {'_id': None, 'total': {'$sum': '$views'}}}
        ]
        views_result = list(mongo.db.study_materials.aggregate(views_pipeline))
        subject_views = views_result[0]['total'] if views_result else 0
       
        if subject_views > 0:
            material_by_subject.append({
                '_id': subject,
                'views': subject_views,
                'count': mongo.db.study_materials.count_documents({'subject': subject})
            })
   
    material_by_subject.sort(key=lambda x: x['views'], reverse=True)
   
    top_materials = list(mongo.db.study_materials.find().sort('views', -1).limit(5))
    for m in top_materials:
        m['_id'] = str(m['_id'])
   
    recent_students = list(mongo.db.users.find(
        {'role': 'student'}
    ).sort('joined_date', -1).limit(10))
   
    for student in recent_students:
        student['_id'] = str(student['_id'])
   
    recent_materials = list(mongo.db.study_materials.find().sort('uploaded_at', -1).limit(5))
    for m in recent_materials:
        m['_id'] = str(m['_id'])
   
    recent_videos = list(mongo.db.videos.find().sort('uploaded_at', -1).limit(5))
    for v in recent_videos:
        v['_id'] = str(v['_id'])
   
    recent_activities = []
   
    for m in recent_materials:
        recent_activities.append({
            'icon': 'upload',
            'text': f'Uploaded study material: {m["title"]}',
            'timestamp': m['uploaded_at'],
            'time': get_time_ago(m['uploaded_at']),
            'user': current_user.name,
            'type': 'material'
        })
   
    for v in recent_videos:
        recent_activities.append({
            'icon': 'video',
            'text': f'Uploaded video: {v["title"]}',
            'timestamp': v['uploaded_at'],
            'time': get_time_ago(v['uploaded_at']),
            'user': current_user.name,
            'type': 'video'
        })
   
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:10]
   
    daily_views = []
    if 'material_views' in mongo.db.list_collection_names():
        for i in range(7):
            day = datetime.now() - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
           
            count = mongo.db.material_views.count_documents({
                'viewed_at': {'$gte': day_start, '$lte': day_end}
            })
            daily_views.append({
                'date': day.strftime('%Y-%m-%d'),
                'count': count
            })
        daily_views.reverse()
   
    return render_template(
        'admin_dashboard.html',
        now=datetime.now(),
        total_students=total_students,
        new_students_today=new_students_today,
        new_students_week=new_students_week,
        active_today=active_today,
        total_materials=total_materials,
        pdf_count=pdf_count,
        image_count=image_count,
        audio_count=audio_count,
        document_count=document_count,
        total_material_views=total_material_views,
        total_material_downloads=total_material_downloads,
        total_material_favorites=total_material_favorites,
        new_materials_today=new_materials_today,
        downloads_today=downloads_today,
        material_views_today=material_views_today,
        total_videos=total_videos,
        total_video_views=total_video_views,
        total_video_downloads=total_video_downloads,
        total_watch_hours=total_watch_hours,
        contact_pending=contact_pending,
        contact_in_progress=contact_in_progress,
        contact_resolved=contact_resolved,
        recent_contact_messages=recent_contact_messages,
        activity_stats=activity_stats,
        recent_activities_feed=recent_activities_feed,
        total_emails_sent=total_emails_sent,
        emails_sent_today=emails_sent_today,
        all_languages_stats=all_languages_stats,
        material_languages=material_languages,
        video_languages=video_languages,
        top_languages=top_languages,
        grade_distribution=grade_distribution,
        material_by_subject=material_by_subject,
        top_materials=top_materials,
        recent_students=recent_students,
        recent_materials=recent_materials,
        recent_videos=recent_videos,
        recent_activities=recent_activities,
        daily_views=daily_views,
        total_medals_awarded=total_medals_awarded,
        medal_distribution=medal_distribution,
        top_medal_earners=top_medal_earners
    )

# ============================================
# Admin Activity Page
# ============================================
@app.route('/admin/activity')
@login_required
def admin_activity():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
   
    activities = []
   
    materials = mongo.db.study_materials.find().sort('uploaded_at', -1).limit(20)
    for m in materials:
        activities.append({
            'icon': 'upload',
            'text': f'Uploaded study material: {m["title"]}',
            'timestamp': m['uploaded_at'],
            'time': get_time_ago(m['uploaded_at']),
            'user': 'Admin',
            'type': 'material'
        })
   
    videos = mongo.db.videos.find().sort('uploaded_at', -1).limit(20)
    for v in videos:
        activities.append({
            'icon': 'video',
            'text': f'Uploaded video: {v["title"]}',
            'timestamp': v['uploaded_at'],
            'time': get_time_ago(v['uploaded_at']),
            'user': 'Admin',
            'type': 'video'
        })
   
    if 'material_views' in mongo.db.list_collection_names():
        recent_views = mongo.db.material_views.find().sort('viewed_at', -1).limit(20)
        for v in recent_views:
            activities.append({
                'icon': 'eye',
                'text': f'{v["user_name"]} viewed {v["material_title"]}',
                'timestamp': v['viewed_at'],
                'time': get_time_ago(v['viewed_at']),
                'user': v['user_name'],
                'type': 'view'
            })
   
    if 'material_downloads' in mongo.db.list_collection_names():
        recent_downloads = mongo.db.material_downloads.find().sort('downloaded_at', -1).limit(20)
        for d in recent_downloads:
            activities.append({
                'icon': 'download',
                'text': f'{d["user_name"]} downloaded {d["material_title"]}',
                'timestamp': d['downloaded_at'],
                'time': get_time_ago(d['downloaded_at']),
                'user': d['user_name'],
                'type': 'download'
            })
   
    if 'video_watch_time' in mongo.db.list_collection_names():
        recent_watches = mongo.db.video_watch_time.find().sort('watched_at', -1).limit(20)
        for w in recent_watches:
            activities.append({
                'icon': 'video',
                'text': f'{w["user_name"]} watched {w["video_title"]}',
                'timestamp': w['watched_at'],
                'time': get_time_ago(w['watched_at']),
                'user': w['user_name'],
                'type': 'view'
            })
   
    if 'email_logs' in mongo.db.list_collection_names():
        recent_emails = mongo.db.email_logs.find().sort('sent_at', -1).limit(20)
        for e in recent_emails:
            activities.append({
                'icon': 'mail',
                'text': f'Email sent to: {e["recipient"]} - {e["subject"]}',
                'timestamp': e['sent_at'],
                'time': get_time_ago(e['sent_at']),
                'user': 'System',
                'type': 'email'
            })
   
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    activities = activities[:50]
   
    return render_template('admin_activity.html', activities=activities, now=datetime.now())

# ============================================
# Admin Reports Page
# ============================================
@app.route('/admin/reports')
@login_required
def admin_reports():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))

    total_students = mongo.db.users.count_documents({'role': 'student'})
    total_materials = mongo.db.study_materials.count_documents({})
    total_videos = mongo.db.videos.count_documents({})

    views_result = list(mongo.db.study_materials.aggregate([
        {'$group': {'_id': None, 'total': {'$sum': '$views'}}}
    ]))
    total_views = views_result[0]['total'] if views_result else 0

    downloads_result = list(mongo.db.study_materials.aggregate([
        {'$group': {'_id': None, 'total': {'$sum': '$downloads'}}}
    ]))
    total_downloads = downloads_result[0]['total'] if downloads_result else 0

    favorites_result = list(mongo.db.study_materials.aggregate([
        {'$group': {'_id': None, 'total': {'$sum': '$favorites'}}}
    ]))
    total_favorites = favorites_result[0]['total'] if favorites_result else 0

    pdf_count = mongo.db.study_materials.count_documents({'type': 'pdf'})
    image_count = mongo.db.study_materials.count_documents({'type': 'image'})
    audio_count = mongo.db.study_materials.count_documents({'type': 'audio'})
    document_count = mongo.db.study_materials.count_documents({'type': 'document'})

    top_materials = list(
        mongo.db.study_materials.find()
        .sort('views', -1)
        .limit(10)
    )

    video_views_result = list(mongo.db.videos.aggregate([
        {'$group': {'_id': None, 'total': {'$sum': '$views'}}}
    ]))
    total_video_views = video_views_result[0]['total'] if video_views_result else 0

    video_downloads_result = list(mongo.db.videos.aggregate([
        {'$group': {'_id': None, 'total': {'$sum': '$downloads'}}}
    ]))
    total_video_downloads = video_downloads_result[0]['total'] if video_downloads_result else 0

    top_videos = list(
        mongo.db.videos.find()
        .sort('views', -1)
        .limit(10)
    )

    top_students = list(
        mongo.db.users.find({'role': 'student'})
        .sort('xp', -1)
        .limit(10)
    )

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    active_today = mongo.db.users.count_documents({
        'role': 'student',
        'last_login': {'$gte': today_start}
    })

    avg_xp_result = list(mongo.db.users.aggregate([
        {'$match': {'role': 'student'}},
        {'$group': {'_id': None, 'avg': {'$avg': '$xp'}}}
    ]))
    avg_xp = int(avg_xp_result[0]['avg']) if avg_xp_result else 0

    medals_result = list(mongo.db.users.aggregate([
        {'$match': {'role': 'student'}},
        {'$group': {'_id': None, 'total': {'$sum': {'$size': '$medals'}}}}
    ]))
    total_medals = medals_result[0]['total'] if medals_result else 0

    streak_result = list(mongo.db.users.aggregate([
        {'$match': {'role': 'student'}},
        {'$group': {'_id': None, 'avg': {'$avg': '$streak'}}}
    ]))
    avg_streak = int(streak_result[0]['avg']) if streak_result else 0

    recent_students = list(
        mongo.db.users.find({'role': 'student'})
        .sort('last_login', -1)
        .limit(20)
    )

    total_emails_sent = mongo.db.email_logs.count_documents({'status': 'delivered'})
    emails_sent_today = mongo.db.email_logs.count_documents({
        'sent_at': {'$gte': today_start},
        'status': 'delivered'
    })

    activity_stats = get_activity_stats(days=30)

    return render_template(
        'admin_reports.html',
        total_students=total_students,
        total_materials=total_materials,
        total_videos=total_videos,
        total_views=total_views,
        top_students=top_students,
        total_downloads=total_downloads,
        total_favorites=total_favorites,
        pdf_count=pdf_count,
        image_count=image_count,
        audio_count=audio_count,
        document_count=document_count,
        top_materials=top_materials,
        total_video_views=total_video_views,
        total_video_downloads=total_video_downloads,
        top_videos=top_videos,
        active_today=active_today,
        avg_xp=avg_xp,
        total_medals=total_medals,
        avg_streak=avg_streak,
        recent_students=recent_students,
        total_emails_sent=total_emails_sent,
        emails_sent_today=emails_sent_today,
        activity_stats=activity_stats,
        now=datetime.now()
    )

@app.route('/admin/languages')
@login_required
def admin_languages():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))

    all_languages = [
        'english', 'hindi', 'bengali', 'telugu', 'marathi', 'tamil', 'urdu',
        'gujarati', 'kannada', 'malayalam', 'oriya', 'punjabi', 'assamese',
        'maithili', 'santali', 'kashmiri', 'nepali', 'sindhi', 'dogri',
        'konkani', 'manipuri', 'bodo'
    ]

    total_materials = mongo.db.study_materials.count_documents({})
    total_videos = mongo.db.videos.count_documents({})
    total_users = mongo.db.users.count_documents({})

    views_result = list(mongo.db.study_materials.aggregate([
        {'$group': {'_id': None, 'total': {'$sum': '$views'}}}
    ]))
    total_views = views_result[0]['total'] if views_result else 0

    languages = []

    for lang in all_languages:
        materials = mongo.db.study_materials.count_documents({'language': lang})
        videos = mongo.db.videos.count_documents({'language': lang})

        views_result = list(mongo.db.study_materials.aggregate([
            {'$match': {'language': lang}},
            {'$group': {'_id': None, 'total': {'$sum': '$views'}}}
        ]))
        views = views_result[0]['total'] if views_result else 0

        downloads_result = list(mongo.db.study_materials.aggregate([
            {'$match': {'language': lang}},
            {'$group': {'_id': None, 'total': {'$sum': '$downloads'}}}
        ]))
        downloads = downloads_result[0]['total'] if downloads_result else 0

        students = mongo.db.users.count_documents({
            'role': 'student',
            'language': lang
        })

        languages.append({
            'code': lang,
            'materials': materials,
            'videos': videos,
            'views': views,
            'downloads': downloads,
            'students': students,
            'total': materials + videos
        })

    return render_template(
        'admin_languages.html',
        languages=languages,
        total_materials=total_materials,
        total_videos=total_videos,
        total_users=total_users,
        total_views=total_views,
        now=datetime.now()
    )

# ============================================
# Admin Content Management
# ============================================

@app.route('/admin/manage-content')
@login_required
def admin_manage_content():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
   
    study_materials = list(mongo.db.study_materials.find().sort('uploaded_at', -1))
    for m in study_materials:
        m['_id'] = str(m['_id'])
   
    videos = list(mongo.db.videos.find().sort('uploaded_at', -1))
    for v in videos:
        v['_id'] = str(v['_id'])
   
    total_downloads = 0
    for m in study_materials:
        total_downloads += m.get('downloads', 0)
    for v in videos:
        total_downloads += v.get('downloads', 0)
   
    return render_template('admin_manage_content.html',
                         study_materials=study_materials,
                         videos=videos,
                         total_downloads=total_downloads)

@app.route('/api/admin/study-material/upload', methods=['POST'])
@login_required
def upload_study_material():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
   
    file = request.files['file']
   
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
   
    if file and allowed_study_file(file.filename):
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name}_{timestamp}{ext}"
        filepath = os.path.join(app.config['STUDY_MATERIAL_FOLDER'], filename)
        file.save(filepath)
       
        file_type = get_file_type(filename)
       
        material_data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'language': request.form.get('language'),
            'grade': int(request.form.get('grade')),
            'subject': request.form.get('subject'),
            'chapter': request.form.get('chapter', ''),
            'tags': request.form.get('tags', '').split(','),
            'type': file_type,
            'filename': filename,
            'filepath': filepath,
            'filesize': os.path.getsize(filepath),
            'views': 0,
            'downloads': 0,
            'favorites': 0,
            'uploaded_by': current_user.id,
            'uploaded_at': datetime.now(),
            'active': True,
            'is_new': True
        }
       
        result = mongo.db.study_materials.insert_one(material_data)
        material_data['_id'] = str(result.inserted_id)
       
        track_activity(
            user_id=current_user.id,
            user_name=current_user.name,
            user_email=current_user.email,
            activity_type='upload',
            item_id=str(result.inserted_id),
            item_title=material_data['title'],
            item_type='material',
            details=f'Uploaded {file_type} file: {material_data["title"]}',
            xp_earned=0
        )
       
        return jsonify({'success': True, 'material': material_data})
   
    return jsonify({'success': False, 'error': 'Invalid file type'}), 400

@app.route('/api/admin/study-material/<material_id>', methods=['GET'])
@login_required
def get_study_material(material_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    material = mongo.db.study_materials.find_one({'_id': ObjectId(material_id)})
    if material:
        material['_id'] = str(material['_id'])
        return jsonify(material)
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/admin/study-material/<material_id>/update', methods=['PUT'])
@login_required
def update_study_material(material_id):
    """Update study material content"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    material = mongo.db.study_materials.find_one({'_id': ObjectId(material_id)})
    if not material:
        return jsonify({'success': False, 'error': 'Material not found'}), 404
   
    update_data = {
        'title': request.form.get('title'),
        'description': request.form.get('description'),
        'language': request.form.get('language'),
        'grade': int(request.form.get('grade')),
        'subject': request.form.get('subject'),
        'chapter': request.form.get('chapter', ''),
        'updated_at': datetime.now()
    }
   
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename and allowed_study_file(file.filename):
            try:
                if os.path.exists(material['filepath']):
                    os.remove(material['filepath'])
            except Exception as e:
                print(f"Error deleting old file: {e}")
           
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{name}_{timestamp}{ext}"
            filepath = os.path.join(app.config['STUDY_MATERIAL_FOLDER'], filename)
            file.save(filepath)
           
            update_data['filename'] = filename
            update_data['filepath'] = filepath
            update_data['filesize'] = os.path.getsize(filepath)
            update_data['type'] = get_file_type(filename)
   
    mongo.db.study_materials.update_one(
        {'_id': ObjectId(material_id)},
        {'$set': update_data}
    )
   
    track_activity(
        user_id=current_user.id,
        user_name=current_user.name,
        user_email=current_user.email,
        activity_type='upload',
        item_id=material_id,
        item_title=update_data['title'],
        item_type='material',
        details=f'Updated material: {update_data["title"]}',
        xp_earned=0
    )
   
    return jsonify({'success': True})

@app.route('/api/admin/study-material/<material_id>', methods=['DELETE'])
@login_required
def delete_study_material(material_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    material = mongo.db.study_materials.find_one({'_id': ObjectId(material_id)})
    if material:
        try:
            if os.path.exists(material['filepath']):
                os.remove(material['filepath'])
        except Exception as e:
            print(f"Error deleting file: {e}")
       
        mongo.db.study_materials.delete_one({'_id': ObjectId(material_id)})
       
        if 'material_views' in mongo.db.list_collection_names():
            mongo.db.material_views.delete_many({'material_id': material_id})
        if 'material_downloads' in mongo.db.list_collection_names():
            mongo.db.material_downloads.delete_many({'material_id': material_id})
        if 'material_favorites' in mongo.db.list_collection_names():
            mongo.db.material_favorites.delete_many({'material_id': material_id})
   
    return jsonify({'success': True})

@app.route('/api/admin/study-material/<material_id>/download', methods=['GET'])
@login_required
def download_study_material_admin(material_id):
    """Admin download endpoint for study material"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    material = mongo.db.study_materials.find_one({'_id': ObjectId(material_id)})
    if not material:
        return jsonify({'error': 'Material not found'}), 404
   
    return send_file(
        material['filepath'],
        as_attachment=True,
        download_name=material['filename']
    )

@app.route('/api/admin/study-material/<material_id>/analytics', methods=['GET'])
@login_required
def get_study_material_analytics(material_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    material = mongo.db.study_materials.find_one({'_id': ObjectId(material_id)})
    if not material:
        return jsonify({'error': 'Material not found'}), 404
   
    views = []
    if 'material_views' in mongo.db.list_collection_names():
        view_pipeline = [
            {'$match': {'material_id': material_id}},
            {'$group': {
                '_id': {
                    'year': {'$year': '$viewed_at'},
                    'month': {'$month': '$viewed_at'},
                    'day': {'$dayOfMonth': '$viewed_at'}
                },
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id.year': 1, '_id.month': 1, '_id.day': 1}}
        ]
        views = list(mongo.db.material_views.aggregate(view_pipeline))
   
    downloads = []
    if 'material_downloads' in mongo.db.list_collection_names():
        download_pipeline = [
            {'$match': {'material_id': material_id}},
            {'$group': {
                '_id': {
                    'year': {'$year': '$downloaded_at'},
                    'month': {'$month': '$downloaded_at'},
                    'day': {'$dayOfMonth': '$downloaded_at'}
                },
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id.year': 1, '_id.month': 1, '_id.day': 1}}
        ]
        downloads = list(mongo.db.material_downloads.aggregate(download_pipeline))
   
    top_users = []
    if 'material_views' in mongo.db.list_collection_names():
        user_pipeline = [
            {'$match': {'material_id': material_id}},
            {'$group': {
                '_id': '$user_id',
                'user_name': {'$first': '$user_name'},
                'count': {'$sum': 1},
                'last_viewed': {'$max': '$viewed_at'}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        top_users = list(mongo.db.material_views.aggregate(user_pipeline))
   
    return jsonify({
        'material': {
            'title': material['title'],
            'type': material['type'],
            'views': material['views'],
            'downloads': material['downloads'],
            'favorites': material['favorites'],
            'uploaded_at': material['uploaded_at']
        },
        'views_history': views,
        'downloads_history': downloads,
        'top_users': top_users
    })

@app.route('/api/admin/videos/upload', methods=['POST'])
@login_required
def upload_video():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    if 'video' not in request.files:
        return jsonify({'success': False, 'error': 'No video file'}), 400
   
    video_file = request.files['video']
   
    if video_file.filename == '':
        return jsonify({'success': False, 'error': 'No video selected'}), 400
   
    if video_file and allowed_video_file(video_file.filename):
        filename = secure_filename(video_file.filename)
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name}_{timestamp}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        video_file.save(filepath)
       
        video_data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'language': request.form.get('language'),
            'grade': int(request.form.get('grade')),
            'subject': request.form.get('subject'),
            'chapter': request.form.get('chapter', ''),
            'duration': int(request.form.get('duration', 30)),
            'filename': filename,
            'filepath': filepath,
            'filesize': os.path.getsize(filepath),
            'views': 0,
            'downloads': 0,
            'likes': 0,
            'uploaded_by': current_user.id,
            'uploaded_at': datetime.now(),
            'active': True
        }
       
        result = mongo.db.videos.insert_one(video_data)
        video_data['_id'] = str(result.inserted_id)
       
        track_activity(
            user_id=current_user.id,
            user_name=current_user.name,
            user_email=current_user.email,
            activity_type='upload',
            item_id=str(result.inserted_id),
            item_title=video_data['title'],
            item_type='video',
            details=f'Uploaded video: {video_data["title"]}',
            xp_earned=0
        )
       
        return jsonify({'success': True, 'video': video_data})
   
    return jsonify({'success': False, 'error': 'Invalid file type'}), 400

@app.route('/api/admin/videos/<video_id>', methods=['GET'])
@login_required
def get_video(video_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    video = mongo.db.videos.find_one({'_id': ObjectId(video_id)})
    if video:
        video['_id'] = str(video['_id'])
        return jsonify(video)
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/admin/videos/<video_id>/update', methods=['PUT'])
@login_required
def update_video(video_id):
    """Update video content"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    video = mongo.db.videos.find_one({'_id': ObjectId(video_id)})
    if not video:
        return jsonify({'success': False, 'error': 'Video not found'}), 404
   
    update_data = {
        'title': request.form.get('title'),
        'description': request.form.get('description'),
        'language': request.form.get('language'),
        'grade': int(request.form.get('grade')),
        'subject': request.form.get('subject'),
        'chapter': request.form.get('chapter', ''),
        'duration': int(request.form.get('duration', 30)),
        'updated_at': datetime.now()
    }
   
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename and allowed_video_file(file.filename):
            try:
                if os.path.exists(video['filepath']):
                    os.remove(video['filepath'])
            except Exception as e:
                print(f"Error deleting old video: {e}")
           
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{name}_{timestamp}{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
           
            update_data['filename'] = filename
            update_data['filepath'] = filepath
            update_data['filesize'] = os.path.getsize(filepath)
   
    mongo.db.videos.update_one(
        {'_id': ObjectId(video_id)},
        {'$set': update_data}
    )
   
    track_activity(
        user_id=current_user.id,
        user_name=current_user.name,
        user_email=current_user.email,
        activity_type='upload',
        item_id=video_id,
        item_title=update_data['title'],
        item_type='video',
        details=f'Updated video: {update_data["title"]}',
        xp_earned=0
    )
   
    return jsonify({'success': True})

@app.route('/api/admin/videos/<video_id>', methods=['DELETE'])
@login_required
def delete_video(video_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    video = mongo.db.videos.find_one({'_id': ObjectId(video_id)})
    if video:
        try:
            if os.path.exists(video['filepath']):
                os.remove(video['filepath'])
        except Exception as e:
            print(f"Error deleting file: {e}")
       
        mongo.db.videos.delete_one({'_id': ObjectId(video_id)})
   
    return jsonify({'success': True})

@app.route('/api/admin/videos/<video_id>/download', methods=['GET'])
@login_required
def download_video_admin(video_id):
    """Admin download endpoint for video"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
   
    video = mongo.db.videos.find_one({'_id': ObjectId(video_id)})
    if not video:
        return jsonify({'error': 'Video not found'}), 404
   
    return send_file(
        video['filepath'],
        as_attachment=True,
        download_name=video['filename']
    )

# ============================================
# Admin Analytics API
# ============================================
@app.route('/api/admin/analytics/materials')
@login_required
def get_material_analytics():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
   
    period = request.args.get('period', '30days')
   
    if period == '7days':
        start_date = datetime.now() - timedelta(days=7)
    elif period == '30days':
        start_date = datetime.now() - timedelta(days=30)
    elif period == '90days':
        start_date = datetime.now() - timedelta(days=90)
    else:
        start_date = datetime.now() - timedelta(days=30)
   
    total_materials = mongo.db.study_materials.count_documents({})
    total_views = 0
    total_downloads = 0
    total_favorites = 0
   
    stats_pipeline = [{'$group': {
        '_id': None,
        'views': {'$sum': '$views'},
        'downloads': {'$sum': '$downloads'},
        'favorites': {'$sum': '$favorites'}
    }}]
    stats_result = list(mongo.db.study_materials.aggregate(stats_pipeline))
    if stats_result:
        total_views = stats_result[0]['views']
        total_downloads = stats_result[0]['downloads']
        total_favorites = stats_result[0]['favorites']
   
    daily_views = []
    if 'material_views' in mongo.db.list_collection_names():
        daily_pipeline = [
            {'$match': {'viewed_at': {'$gte': start_date}}},
            {'$group': {
                '_id': {
                    'year': {'$year': '$viewed_at'},
                    'month': {'$month': '$viewed_at'},
                    'day': {'$dayOfMonth': '$viewed_at'}
                },
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id.year': 1, '_id.month': 1, '_id.day': 1}}
        ]
        daily_views = list(mongo.db.material_views.aggregate(daily_pipeline))
   
    type_pipeline = [
        {'$group': {
            '_id': '$type',
            'views': {'$sum': '$views'},
            'downloads': {'$sum': '$downloads'},
            'count': {'$sum': 1}
        }},
        {'$sort': {'views': -1}}
    ]
    views_by_type = list(mongo.db.study_materials.aggregate(type_pipeline))
   
    language_pipeline = [
        {'$group': {
            '_id': '$language',
            'views': {'$sum': '$views'},
            'downloads': {'$sum': '$downloads'},
            'count': {'$sum': 1}
        }},
        {'$sort': {'views': -1}}
    ]
    views_by_language = list(mongo.db.study_materials.aggregate(language_pipeline))
   
    subject_pipeline = [
        {'$group': {
            '_id': '$subject',
            'views': {'$sum': '$views'},
            'downloads': {'$sum': '$downloads'},
            'count': {'$sum': 1}
        }},
        {'$sort': {'views': -1}}
    ]
    views_by_subject = list(mongo.db.study_materials.aggregate(subject_pipeline))
   
    grade_pipeline = [
        {'$group': {
            '_id': '$grade',
            'views': {'$sum': '$views'},
            'downloads': {'$sum': '$downloads'},
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': 1}}
    ]
    views_by_grade = list(mongo.db.study_materials.aggregate(grade_pipeline))
   
    top_materials = list(mongo.db.study_materials.find().sort('views', -1).limit(10))
    for m in top_materials:
        m['_id'] = str(m['_id'])
   
    return jsonify({
        'total_materials': total_materials,
        'total_views': total_views,
        'total_downloads': total_downloads,
        'total_favorites': total_favorites,
        'daily_views': daily_views,
        'views_by_type': views_by_type,
        'views_by_language': views_by_language,
        'views_by_subject': views_by_subject,
        'views_by_grade': views_by_grade,
        'top_materials': top_materials
    })

@app.route('/api/admin/analytics/top-students')
@login_required
def get_top_students_analytics():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
   
    students = list(mongo.db.users.find(
        {'role': 'student'}
    ).sort('xp', -1).limit(10))
   
    result = []
    for student in students:
        result.append({
            'name': student.get('name', 'Unknown'),
            'grade': student.get('grade', 'N/A'),
            'xp': student.get('xp', 0),
            'level': student.get('level', 1),
            'material_count': student.get('total_materials', 0),
            'video_count': student.get('total_videos', 0),
            'medal_count': len(student.get('medals', []))
        })
   
    return jsonify({'students': result})

# ============================================
# Analytics Dashboard
# ============================================
@app.route('/analytics')
@login_required
def analytics_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
   
    return render_template('analytics.html')

@app.route('/api/admin/analytics')
@login_required
def get_analytics_data():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
   
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    grade = request.args.get('grade', 'all')
    subject = request.args.get('subject', 'all')
   
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end = datetime.now()
        start = end - timedelta(days=30)
   
    match_query = {}
    if grade != 'all':
        match_query['grade'] = int(grade)
    if subject != 'all':
        match_query['subject'] = subject
   
    total_students = mongo.db.users.count_documents({'role': 'student'})
    new_students = mongo.db.users.count_documents({
        'role': 'student',
        'joined_date': {'$gte': start, '$lte': end}
    })
   
    material_pipeline = [
        {'$match': match_query},
        {'$group': {
            '_id': None,
            'total_views': {'$sum': '$views'},
            'total_downloads': {'$sum': '$downloads'},
            'count': {'$sum': 1}
        }}
    ]
    material_stats = list(mongo.db.study_materials.aggregate(material_pipeline))
    total_material_views = material_stats[0]['total_views'] if material_stats else 0
    material_downloads = material_stats[0]['total_downloads'] if material_stats else 0
   
    video_pipeline = [
        {'$match': match_query},
        {'$group': {
            '_id': None,
            'total_views': {'$sum': '$views'},
            'total_downloads': {'$sum': '$downloads'},
            'count': {'$sum': 1}
        }}
    ]
    video_stats = list(mongo.db.videos.aggregate(video_pipeline))
    total_video_views = video_stats[0]['total_views'] if video_stats else 0
   
    watch_hours = 0
    if 'video_watch_time' in mongo.db.list_collection_names():
        watch_pipeline = [
            {'$match': {'watched_at': {'$gte': start, '$lte': end}}},
            {'$group': {'_id': None, 'total': {'$sum': '$duration'}}}
        ]
        watch_result = list(mongo.db.video_watch_time.aggregate(watch_pipeline))
        watch_hours = watch_result[0]['total'] // 60 if watch_result else 0
   
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    active_today = mongo.db.users.count_documents({
        'role': 'student',
        'last_login': {'$gte': today_start}
    })
   
    daily_dates = []
    daily_material_views = []
    daily_video_views = []
   
    current = start
    while current <= end:
        day_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = current.replace(hour=23, minute=59, second=59, microsecond=999999)
       
        daily_dates.append(current.strftime('%Y-%m-%d'))
       
        if 'material_views' in mongo.db.list_collection_names():
            material_views_count = mongo.db.material_views.count_documents({
                'viewed_at': {'$gte': day_start, '$lte': day_end}
            })
        else:
            material_views_count = 0
        daily_material_views.append(material_views_count)
       
        if 'video_watch_time' in mongo.db.list_collection_names():
            video_views_count = mongo.db.video_watch_time.count_documents({
                'watched_at': {'$gte': day_start, '$lte': day_end}
            })
        else:
            video_views_count = 0
        daily_video_views.append(video_views_count)
       
        current += timedelta(days=1)
   
    content_dist = {
        'labels': [],
        'values': []
    }
    type_counts = mongo.db.study_materials.aggregate([
        {'$group': {'_id': '$type', 'count': {'$sum': 1}}}
    ])
    for t in type_counts:
        content_dist['labels'].append(t['_id'].title())
        content_dist['values'].append(t['count'])
   
    growth_dates = []
    new_users = []
    total_users = []
   
    current = start
    running_total = mongo.db.users.count_documents({
        'role': 'student',
        'joined_date': {'$lt': start}
    })
   
    while current <= end:
        day_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = current.replace(hour=23, minute=59, second=59, microsecond=999999)
       
        growth_dates.append(current.strftime('%Y-%m-%d'))
       
        new = mongo.db.users.count_documents({
            'role': 'student',
            'joined_date': {'$gte': day_start, '$lte': day_end}
        })
        new_users.append(new)
        running_total += new
        total_users.append(running_total)
       
        current += timedelta(days=1)
   
    subjects = ['mathematics', 'science', 'english', 'hindi', 'telugu', 'tamil', 'social']
    material_views_by_subject = []
    video_views_by_subject = []
   
    for subj in subjects:
        mv = mongo.db.study_materials.aggregate([
            {'$match': {'subject': subj}},
            {'$group': {'_id': None, 'total': {'$sum': '$views'}}}
        ])
        mv_result = list(mv)
        material_views_by_subject.append(mv_result[0]['total'] if mv_result else 0)
       
        vv = mongo.db.videos.aggregate([
            {'$match': {'subject': subj}},
            {'$group': {'_id': None, 'total': {'$sum': '$views'}}}
        ])
        vv_result = list(vv)
        video_views_by_subject.append(vv_result[0]['total'] if vv_result else 0)
   
    grade_labels = []
    grade_values = []
    for g in range(5, 13):
        count = mongo.db.users.count_documents({'role': 'student', 'grade': g})
        if count > 0:
            grade_labels.append(f'Grade {g}')
            grade_values.append(count)
   
    top_students_list = list(mongo.db.users.find(
        {'role': 'student'}
    ).sort('xp', -1).limit(10))
   
    top_students = []
    for s in top_students_list:
        top_students.append({
            'name': s['name'],
            'grade': s['grade'],
            'xp': s['xp'],
            'level': s['level'],
            'materialCount': s.get('total_materials', 0),
            'videoCount': s.get('total_videos', 0),
            'language': s.get('language', 'english'),
            'medalCount': len(s.get('medals', []))
        })
   
    recent_interactions = []
   
    if 'material_views' in mongo.db.list_collection_names():
        recent_views = list(mongo.db.material_views.find().sort('viewed_at', -1).limit(10))
        for v in recent_views:
            recent_interactions.append({
                'type': 'material',
                'student': v['user_name'],
                'activity': f'Viewed: {v["material_title"]}',
                'subject': v.get('material_subject', 'General'),
                'language': v.get('material_language', 'english'),
                'xp': 5,
                'time': get_time_ago(v['viewed_at']),
                'date': v['viewed_at'].strftime('%Y-%m-%d'),
                'grade': v.get('material_grade', 'N/A')
            })
   
    if 'video_watch_time' in mongo.db.list_collection_names():
        recent_watches = list(mongo.db.video_watch_time.find().sort('watched_at', -1).limit(10))
        for w in recent_watches:
            recent_interactions.append({
                'type': 'video',
                'student': w['user_name'],
                'activity': f'Watched: {w["video_title"]}',
                'subject': 'General',
                'language': 'english',
                'xp': 5,
                'time': get_time_ago(w['watched_at']),
                'date': w['watched_at'].strftime('%Y-%m-%d'),
                'grade': 'N/A'
            })
   
    recent_interactions.sort(key=lambda x: x['date'], reverse=True)
    recent_interactions = recent_interactions[:10]
   
    return jsonify({
        'kpis': {
            'totalStudents': total_students,
            'newStudents': new_students,
            'studentTrend': 12,
            'totalMaterialViews': total_material_views,
            'materialDownloads': material_downloads,
            'materialTrend': 8,
            'totalVideoViews': total_video_views,
            'watchHours': watch_hours,
            'videoTrend': 15,
            'activeToday': active_today
        },
        'dailyInteractions': {
            'dates': daily_dates[-30:],
            'materialViews': daily_material_views[-30:],
            'videoViews': daily_video_views[-30:]
        },
        'contentDistribution': content_dist,
        'userGrowth': {
            'dates': growth_dates[-30:],
            'newUsers': new_users[-30:],
            'totalUsers': total_users[-30:]
        },
        'subjectEngagement': {
            'subjects': subjects,
            'materialViews': material_views_by_subject,
            'videoViews': video_views_by_subject
        },
        'gradeDistribution': {
            'labels': grade_labels,
            'values': grade_values
        },
        'topStudents': {
            'students': top_students
        },
        'recentInteractions': recent_interactions
    })

# ============================================
# Student Dashboard
# ============================================
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('admin_dashboard'))
   
    student = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    if not student:
        flash('Student not found', 'error')
        return redirect(url_for('logout'))
   
    student_grade = student.get('grade', 5)
    student_language = student.get('language', 'english')
   
    available_materials = list(mongo.db.study_materials.find({
        'active': True
    }).sort('uploaded_at', -1))
   
    available_videos = list(mongo.db.videos.find({
        'active': True
    }).sort('uploaded_at', -1))
   
    language_counts = {}
    all_languages = ['english', 'hindi', 'bengali', 'telugu', 'marathi', 'tamil', 'urdu',
                     'gujarati', 'kannada', 'malayalam', 'oriya', 'punjabi', 'assamese',
                     'maithili', 'santali', 'kashmiri', 'nepali', 'sindhi', 'dogri',
                     'konkani', 'manipuri', 'bodo']
   
    for lang in all_languages:
        count = mongo.db.study_materials.count_documents({'language': lang}) + \
                mongo.db.videos.count_documents({'language': lang})
        language_counts[lang] = count
   
    recent_activities = []
   
    if 'material_views' in mongo.db.list_collection_names():
        material_views = list(mongo.db.material_views.find(
            {'user_id': current_user.id}
        ).sort('viewed_at', -1).limit(5))
       
        for v in material_views:
            material = mongo.db.study_materials.find_one({'_id': ObjectId(v['material_id'])})
            if material:
                recent_activities.append({
                    'type': 'material',
                    'id': v['material_id'],
                    'icon': 'book',
                    'color': '#48bb78',
                    'title': f'Viewed: {material["title"]}',
                    'date': v['viewed_at'],
                    'xp': 5
                })
   
    if 'video_watch_time' in mongo.db.list_collection_names():
        video_watches = list(mongo.db.video_watch_time.find(
            {'user_id': current_user.id}
        ).sort('watched_at', -1).limit(5))
       
        for v in video_watches:
            video = mongo.db.videos.find_one({'_id': ObjectId(v['video_id'])})
            if video:
                recent_activities.append({
                    'type': 'video',
                    'id': v['video_id'],
                    'icon': 'video',
                    'color': '#f56565',
                    'title': f'Watched: {video["title"]}',
                    'date': v['watched_at'],
                    'xp': 5
                })
   
    recent_activities.sort(key=lambda x: x['date'], reverse=True)
    recent_activities = recent_activities[:10]
   
    all_students = list(mongo.db.users.find({'role': 'student'}).sort('xp', -1))
    position = next((i+1 for i, s in enumerate(all_students) if str(s['_id']) == current_user.id), 0)
   
    streak = student.get('streak', 0)
    student_activities = get_recent_activities(limit=5, user_id=current_user.id)
    medal_count = len(student.get('medals', []))
    
    recent_medals = []
    if 'student_activities' in mongo.db.list_collection_names():
        medal_activities = list(mongo.db.student_activities.find({
            'user_id': current_user.id,
            'activity_type': 'medal_award'
        }).sort('activity_at', -1).limit(5))
        
        for act in medal_activities:
            recent_medals.append({
                'name': act.get('item_title', 'Medal'),
                'icon': act.get('icon', '🏅')
            })
    
    return render_template('student_dashboard.html',
                         student=student,
                         position=position,
                         streak=streak,
                         medal_count=medal_count,
                         recent_medals=recent_medals,
                         available_materials=available_materials,
                         materials_count=len(available_materials),
                         available_videos=available_videos,
                         videos_count=len(available_videos),
                         recent_activities=recent_activities,
                         student_activities=student_activities,
                         language_counts=language_counts,
                         suggested_topics=[
                            "Algebra Basics",
                            "Photosynthesis",
                            "English Grammar",
                            "Fractions and Decimals",
                            "Solar System"
                         ])

# ============================================
# Student Learning Routes
# ============================================
@app.route('/student/learning')
@login_required
def student_learning():
    if current_user.role != 'student':
        return redirect(url_for('admin_dashboard'))

    student = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    if not student:
        flash('Student not found', 'error')
        return redirect(url_for('logout'))

    materials = list(mongo.db.study_materials.find({
        'active': True
    }).sort('uploaded_at', -1))
    
    videos = list(mongo.db.videos.find({
        'active': True
    }).sort('uploaded_at', -1))

    language_progress = student.get('language_progress', {
        "english": 75,
        "hindi": 45,
        "telugu": 30,
        "bengali": 20,
        "tamil": 25,
        "marathi": 15,
        "gujarati": 10,
        "kannada": 12,
        "malayalam": 8,
        "punjabi": 5,
        "assamese": 3,
        "oriya": 4
    })

    language_counts = {}
    all_languages = ['english', 'hindi', 'bengali', 'telugu', 'marathi', 'tamil', 'urdu',
                     'gujarati', 'kannada', 'malayalam', 'oriya', 'punjabi', 'assamese',
                     'maithili', 'santali', 'kashmiri', 'nepali', 'sindhi', 'dogri',
                     'konkani', 'manipuri', 'bodo']
    
    for lang in all_languages:
        material_count = mongo.db.study_materials.count_documents({'language': lang, 'active': True})
        video_count = mongo.db.videos.count_documents({'language': lang, 'active': True})
        language_counts[lang] = material_count + video_count

    streak = student.get('streak', 7)

    return render_template(
        'student_learning.html',
        student=student,
        materials=materials,
        videos=videos,
        streak=streak,
        language_progress=language_progress,
        language_counts=language_counts
    )

@app.route('/student/language', methods=['POST'])
@login_required
def update_language():
    data = request.json
    mongo.db.users.update_one(
        {'_id': ObjectId(current_user.id)},
        {'$set': {'language': data['language']}}
    )
    return jsonify({'success': True})

# ============================================
# Study Material Routes
# ============================================
@app.route('/preview-study-material/<material_id>')
@login_required
def preview_study_material(material_id):
    if current_user.role != 'student':
        return redirect(url_for('admin_dashboard'))
   
    material = mongo.db.study_materials.find_one({'_id': ObjectId(material_id)})
    if not material:
        flash('Material not found', 'error')
        return redirect(url_for('student_dashboard'))
   
    mongo.db.study_materials.update_one(
        {'_id': ObjectId(material_id)},
        {'$inc': {'views': 1}}
    )
   
    xp_result = award_xp(current_user.id, 5)
   
    mongo.db.users.update_one(
        {'_id': ObjectId(current_user.id)},
        {'$inc': {'total_materials': 1}}
    )
   
    if 'material_views' not in mongo.db.list_collection_names():
        mongo.db.create_collection('material_views')
   
    mongo.db.material_views.insert_one({
        'user_id': current_user.id,
        'user_name': current_user.name,
        'material_id': material_id,
        'material_title': material['title'],
        'material_type': material['type'],
        'material_language': material['language'],
        'material_grade': material['grade'],
        'material_subject': material['subject'],
        'viewed_at': datetime.now()
    })
   
    track_activity(
        user_id=current_user.id,
        user_name=current_user.name,
        user_email=current_user.email,
        activity_type='view',
        item_id=material_id,
        item_title=material['title'],
        item_type='material',
        details=f'Viewed {material["type"]} material: {material["title"]}',
        xp_earned=5
    )
   
    student = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    material_count = student.get('total_materials', 0)
   
    if material_count >= 30:
        award_medal(current_user.id, 'material_learner')
   
    if 'material_views' in mongo.db.list_collection_names():
        viewed_languages = mongo.db.material_views.distinct('material_language', {'user_id': current_user.id})
        if len(viewed_languages) >= 3:
            award_medal(current_user.id, 'polyglot')
   
    file_path = material['filepath']
    file_ext = os.path.splitext(material['filename'])[1].lower()
   
    if file_ext in ['.pdf']:
        return send_file(file_path, mimetype='application/pdf')
    elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
        return send_file(file_path, mimetype=f'image/{file_ext[1:]}')
    elif file_ext in ['.mp3', '.wav', '.ogg']:
        return send_file(file_path, mimetype=f'audio/{file_ext[1:]}')
    else:
        return redirect(url_for('download_study_material', material_id=material_id))

@app.route('/api/study-material/<material_id>/view', methods=['POST'])
@login_required
def track_material_view(material_id):
    material = mongo.db.study_materials.find_one({'_id': ObjectId(material_id)})
    if not material:
        return jsonify({'success': False, 'error': 'Material not found'}), 404
   
    mongo.db.study_materials.update_one(
        {'_id': ObjectId(material_id)},
        {'$inc': {'views': 1}}
    )
   
    award_xp(current_user.id, 5)
   
    mongo.db.users.update_one(
        {'_id': ObjectId(current_user.id)},
        {'$inc': {'total_materials': 1}}
    )
   
    if 'material_views' not in mongo.db.list_collection_names():
        mongo.db.create_collection('material_views')
   
    mongo.db.material_views.insert_one({
        'user_id': current_user.id,
        'user_name': current_user.name,
        'material_id': material_id,
        'material_title': material['title'],
        'material_type': material['type'],
        'material_language': material['language'],
        'material_grade': material['grade'],
        'material_subject': material['subject'],
        'viewed_at': datetime.now()
    })
   
    track_activity(
        user_id=current_user.id,
        user_name=current_user.name,
        user_email=current_user.email,
        activity_type='view',
        item_id=material_id,
        item_title=material['title'],
        item_type='material',
        details=f'Viewed {material["type"]} material: {material["title"]}',
        xp_earned=5
    )
   
    student = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    material_count = student.get('total_materials', 0)
   
    if material_count >= 30:
        award_medal(current_user.id, 'material_learner')
   
    if 'material_views' in mongo.db.list_collection_names():
        viewed_languages = mongo.db.material_views.distinct('material_language', {'user_id': current_user.id})
        if len(viewed_languages) >= 3:
            award_medal(current_user.id, 'polyglot')
   
    return jsonify({'success': True})

@app.route('/download-study-material/<material_id>')
@login_required
def download_study_material(material_id):
    if current_user.role != 'student':
        return redirect(url_for('admin_dashboard'))
   
    material = mongo.db.study_materials.find_one({'_id': ObjectId(material_id)})
    if not material:
        flash('Material not found', 'error')
        return redirect(url_for('student_learning'))
   
    mongo.db.study_materials.update_one(
        {'_id': ObjectId(material_id)},
        {'$inc': {'downloads': 1}}
    )
   
    if 'material_downloads' not in mongo.db.list_collection_names():
        mongo.db.create_collection('material_downloads')
   
    mongo.db.material_downloads.insert_one({
        'user_id': current_user.id,
        'user_name': current_user.name,
        'material_id': material_id,
        'material_title': material['title'],
        'material_type': material['type'],
        'downloaded_at': datetime.now()
    })
   
    award_xp(current_user.id, 5)
   
    track_activity(
        user_id=current_user.id,
        user_name=current_user.name,
        user_email=current_user.email,
        activity_type='download',
        item_id=material_id,
        item_title=material['title'],
        item_type='material',
        details=f'Downloaded {material["type"]} material: {material["title"]}',
        xp_earned=5
    )
   
    return send_file(material['filepath'],
                    as_attachment=True,
                    download_name=material['filename'],
                    mimetype='application/octet-stream')

@app.route('/api/study-material/<material_id>/favorite', methods=['POST'])
@login_required
def favorite_study_material(material_id):
    action = request.json.get('action', 'add')
   
    if action == 'add':
        mongo.db.study_materials.update_one(
            {'_id': ObjectId(material_id)},
            {'$inc': {'favorites': 1}}
        )
        if 'material_favorites' not in mongo.db.list_collection_names():
            mongo.db.create_collection('material_favorites')
       
        mongo.db.material_favorites.insert_one({
            'user_id': current_user.id,
            'material_id': material_id,
            'favorited_at': datetime.now()
        })
       
        material = mongo.db.study_materials.find_one({'_id': ObjectId(material_id)})
        if material:
            track_activity(
                user_id=current_user.id,
                user_name=current_user.name,
                user_email=current_user.email,
                activity_type='favorite',
                item_id=material_id,
                item_title=material['title'],
                item_type='material',
                details=f'Favorited material: {material["title"]}',
                xp_earned=2
            )
    else:
        mongo.db.study_materials.update_one(
            {'_id': ObjectId(material_id)},
            {'$inc': {'favorites': -1}}
        )
   
    return jsonify({'success': True})

# ============================================
# Video Routes
# ============================================
@app.route('/download-video/<video_id>')
@login_required
def download_video(video_id):
    if current_user.role != 'student':
        return redirect(url_for('admin_dashboard'))
   
    video = mongo.db.videos.find_one({'_id': ObjectId(video_id)})
    if not video:
        flash('Video not found', 'error')
        return redirect(url_for('student_learning'))
   
    mongo.db.videos.update_one(
        {'_id': ObjectId(video_id)},
        {'$inc': {'downloads': 1}}
    )
   
    mongo.db.users.update_one(
        {'_id': ObjectId(current_user.id)},
        {'$inc': {'total_videos': 1}}
    )
   
    award_xp(current_user.id, 5)
   
    track_activity(
        user_id=current_user.id,
        user_name=current_user.name,
        user_email=current_user.email,
        activity_type='download',
        item_id=video_id,
        item_title=video['title'],
        item_type='video',
        details=f'Downloaded video: {video["title"]}',
        xp_earned=5
    )
   
    return send_file(video['filepath'],
                    as_attachment=True,
                    download_name=video['filename'],
                    mimetype='video/mp4')

@app.route('/api/videos/<video_id>/view', methods=['POST'])
@login_required
def track_video_view(video_id):
    data = request.json
    watch_duration = data.get('duration', 0)
   
    mongo.db.videos.update_one(
        {'_id': ObjectId(video_id)},
        {'$inc': {'views': 1}}
    )
   
    if 'video_watch_time' not in mongo.db.list_collection_names():
        mongo.db.create_collection('video_watch_time')
   
    video = mongo.db.videos.find_one({'_id': ObjectId(video_id)})
    mongo.db.video_watch_time.insert_one({
        'user_id': current_user.id,
        'user_name': current_user.name,
        'video_id': video_id,
        'video_title': video['title'] if video else 'Unknown',
        'duration': watch_duration,
        'watched_at': datetime.now()
    })
   
    award_xp(current_user.id, 5)
   
    mongo.db.users.update_one(
        {'_id': ObjectId(current_user.id)},
        {'$inc': {'total_videos': 1}}
    )
   
    if video:
        track_activity(
            user_id=current_user.id,
            user_name=current_user.name,
            user_email=current_user.email,
            activity_type='watch',
            item_id=video_id,
            item_title=video['title'],
            item_type='video',
            details=f'Watched video: {video["title"]} for {watch_duration} seconds',
            xp_earned=5
        )
   
    student = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    video_count = student.get('total_videos', 0)
   
    if video_count >= 20:
        award_medal(current_user.id, 'video_learner')
   
    return jsonify({'success': True})

@app.route('/watch-video/<video_id>')
@login_required
def watch_video(video_id):
    if current_user.role != 'student':
        return redirect(url_for('admin_dashboard'))
   
    video = mongo.db.videos.find_one({'_id': ObjectId(video_id)})
    if not video:
        flash('Video not found', 'error')
        return redirect(url_for('student_learning'))
   
    return send_file(video['filepath'], mimetype='video/mp4')

# ============================================
# AI Tutor
# ============================================
@app.route('/ai-tutor', methods=['GET', 'POST'])
@login_required
def ai_tutor_chat():
    if current_user.role != 'student':
        return redirect(url_for('admin_dashboard'))
   
    if request.method == 'POST':
        data = request.json
        question = data['question']
        subject = data.get('subject', 'general')
       
        responses = {
            'mathematics': f"Here's help with your math question: {question}\n\nLet me explain step by step...",
            'science': f"Great science question! {question}\n\nHere's what you need to know...",
            'english': f"Let me help you with English: {question}\n\nHere's the explanation...",
            'general': f"I'll help you with: {question}\n\nHere's what I found..."
        }
       
        response = responses.get(subject, responses['general'])
       
        award_xp(current_user.id, 10)
       
        chat_entry = {
            'user_id': current_user.id,
            'question': question,
            'response': response,
            'subject': subject,
            'timestamp': datetime.now()
        }
        mongo.db.chat_history.insert_one(chat_entry)
       
        track_activity(
            user_id=current_user.id,
            user_name=current_user.name,
            user_email=current_user.email,
            activity_type='ai_chat',
            item_id=str(chat_entry['_id']) if '_id' in chat_entry else None,
            item_title=question[:50],
            item_type='ai_interaction',
            details=f'Asked about {subject}: {question[:100]}',
            xp_earned=10
        )
       
        return jsonify({'response': response})
   
    chat_history = list(mongo.db.chat_history.find(
        {'user_id': current_user.id}
    ).sort('timestamp', -1).limit(50))
    chat_history.reverse()
   
    return render_template('ai_tutor.html', chat_history=chat_history)

# ============================================
# Leaderboard
# ============================================
@app.route('/leaderboard')
@login_required
def leaderboard():
    existing_students = list(mongo.db.users.find({
        'role': 'student',
        '$or': [
            {'last_login': {'$ne': None}},
            {'total_materials': {'$gt': 0}},
            {'total_videos': {'$gt': 0}}
        ]
    }).sort('xp', -1))
   
    top_students = existing_students[:50]
   
    position = 0
    if current_user.is_authenticated and current_user.role == 'student':
        for i, student in enumerate(existing_students, 1):
            if str(student['_id']) == current_user.id:
                position = i
                break
   
    enhanced_students = []
    for student in top_students[:20]:
        material_count = student.get('total_materials', 0)
        video_count = student.get('total_videos', 0)
        medal_count = len(student.get('medals', []))
       
        last_active = 'Never'
        if student.get('last_login'):
            days_ago = (datetime.now() - student['last_login']).days
            if days_ago == 0:
                last_active = 'Today'
            elif days_ago == 1:
                last_active = 'Yesterday'
            else:
                last_active = f"{days_ago} days ago"
       
        enhanced_students.append({
            'id': str(student['_id']),
            'name': student.get('name', 'Unknown'),
            'grade': student.get('grade', 'N/A'),
            'xp': student.get('xp', 0),
            'level': student.get('level', 1),
            'streak': student.get('streak', 0),
            'material_count': material_count,
            'video_count': video_count,
            'medal_count': medal_count,
            'last_active': last_active,
            'language': student.get('language', 'english'),
            'avatar': student.get('avatar', 'default')
        })
   
    material_masters = []
    for student in existing_students[:20]:
        if student.get('total_materials', 0) > 0:
            if 'material_views' in mongo.db.list_collection_names():
                views_pipeline = [
                    {'$match': {'user_id': str(student['_id'])}},
                    {'$group': {'_id': None, 'total': {'$sum': 1}}}
                ]
                views_result = list(mongo.db.material_views.aggregate(views_pipeline))
                total_views = views_result[0]['total'] if views_result else 0
            else:
                total_views = 0
           
            if 'material_downloads' in mongo.db.list_collection_names():
                downloads_pipeline = [
                    {'$match': {'user_id': str(student['_id'])}},
                    {'$group': {'_id': None, 'total': {'$sum': 1}}}
                ]
                downloads_result = list(mongo.db.material_downloads.aggregate(downloads_pipeline))
                total_downloads = downloads_result[0]['total'] if downloads_result else 0
            else:
                total_downloads = 0
           
            material_masters.append({
                'id': str(student['_id']),
                'name': student.get('name', 'Unknown'),
                'grade': student.get('grade', 'N/A'),
                'material_count': student.get('total_materials', 0),
                'total_views': total_views,
                'total_downloads': total_downloads,
                'language': student.get('language', 'english')
            })
    material_masters.sort(key=lambda x: x['material_count'], reverse=True)
   
    video_learners = []
    for student in existing_students[:20]:
        if student.get('total_videos', 0) > 0:
            if 'video_watch_time' in mongo.db.list_collection_names():
                watch_pipeline = [
                    {'$match': {'user_id': str(student['_id'])}},
                    {'$group': {'_id': None, 'total': {'$sum': '$duration'}}}
                ]
                watch_result = list(mongo.db.video_watch_time.aggregate(watch_pipeline))
                total_watch_time = watch_result[0]['total'] if watch_result else 0
            else:
                total_watch_time = 0
           
            completion_rate = min(100, int((total_watch_time / (student.get('total_videos', 1) * 10)) * 100))
           
            video_learners.append({
                'id': str(student['_id']),
                'name': student.get('name', 'Unknown'),
                'grade': student.get('grade', 'N/A'),
                'video_count': student.get('total_videos', 0),
                'watch_time': total_watch_time,
                'completion_rate': completion_rate,
                'language': student.get('language', 'english')
            })
    video_learners.sort(key=lambda x: x['video_count'], reverse=True)
   
    language_leaders = []
    language_groups = defaultdict(list)
    for student in existing_students:
        lang = student.get('language', 'english')
        language_groups[lang].append(student)
   
    for lang, students in language_groups.items():
        top_student = students[0] if students else None
        if top_student:
            language_leaders.append({
                'id': str(top_student['_id']),
                'name': top_student.get('name', 'Unknown'),
                'grade': top_student.get('grade', 'N/A'),
                'language': lang,
                'material_count': top_student.get('total_materials', 0),
                'video_count': top_student.get('total_videos', 0),
                'total_activities': top_student.get('total_materials', 0) +
                                  top_student.get('total_videos', 0)
            })
    language_leaders.sort(key=lambda x: x['total_activities'], reverse=True)
   
    polyglots = []
    for student in existing_students:
        if 'material_views' in mongo.db.list_collection_names():
            viewed_languages = mongo.db.material_views.distinct('material_language', {'user_id': str(student['_id'])})
            language_count = len(set([student.get('language')] + viewed_languages))
        else:
            language_count = 1
       
        if language_count >= 2:
            polyglots.append({
                'id': str(student['_id']),
                'name': student.get('name', 'Unknown'),
                'language_count': language_count,
                'primary_language': student.get('language', 'english'),
                'xp': student.get('xp', 0)
            })
    polyglots.sort(key=lambda x: x['language_count'], reverse=True)
   
    language_counts = {}
    all_languages = ['english', 'hindi', 'bengali', 'telugu', 'marathi', 'tamil', 'urdu',
                     'gujarati', 'kannada', 'malayalam', 'oriya', 'punjabi', 'assamese',
                     'maithili', 'santali', 'kashmiri', 'nepali', 'sindhi', 'dogri',
                     'konkani', 'manipuri', 'bodo']
   
    for lang in all_languages:
        count = mongo.db.users.count_documents({'role': 'student', 'language': lang})
        language_counts[lang] = count
   
    total_materials = mongo.db.study_materials.count_documents({})
   
    return render_template('leaderboard.html',
                         top_students=enhanced_students,
                         material_masters=material_masters[:10],
                         video_learners=video_learners[:10],
                         language_leaders=language_leaders[:10],
                         polyglots=polyglots[:5],
                         position=position,
                         total_active=len(existing_students),
                         total_materials=total_materials,
                         language_counts=language_counts)

# ============================================
# Static File Serving (for development)
# ============================================
@app.route('/static/uploads/study_materials/<path:filename>')
def serve_study_material(filename):
    return send_from_directory(app.config['STUDY_MATERIAL_FOLDER'], filename)

@app.route('/static/uploads/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ============================================
# Initialize Database
# ============================================
@app.route('/init-db')
def init_database():
    if not mongo.db.users.find_one({'email': 'admin@aitutor.com'}):
        admin_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        mongo.db.users.insert_one({
            'name': 'System Administrator',
            'email': 'admin@aitutor.com',
            'password': admin_password,
            'role': 'admin',
            'joined_date': datetime.now(),
            'last_login': None
        })
   
    if not mongo.db.users.find_one({'email': 'student@example.com'}):
        student_password = bcrypt.generate_password_hash('student123').decode('utf-8')
        mongo.db.users.insert_one({
            'name': 'John Student',
            'email': 'student@example.com',
            'password': student_password,
            'role': 'student',
            'grade': 5,
            'language': 'english',
            'school': 'Demo School',
            'xp': 250,
            'level': 1,
            'medals': ['first_activity', 'ten_activities'],
            'joined_date': datetime.now(),
            'last_login': datetime.now(),
            'streak': 3,
            'total_materials': 12,
            'total_videos': 8,
            'average_score': 72.5,
            'perfect_scores': 1,
            'early_activities': 2,
            'night_activities': 1,
            'weekend_activities': 3,
            'recent_activities': []
        })
   
    collections = ['study_materials', 'videos', 'material_views', 'material_downloads',
                   'material_favorites', 'video_watch_time', 'chat_history',
                   'email_logs', 'email_campaigns', 'email_templates', 'contact_messages',
                   'student_activities', 'activities']
   
    for collection in collections:
        if collection not in mongo.db.list_collection_names():
            mongo.db.create_collection(collection)
            print(f"Created collection: {collection}")
   
    if 'student_activities' in mongo.db.list_collection_names():
        mongo.db.student_activities.create_index('activity_at')
        mongo.db.student_activities.create_index('user_id')
        mongo.db.student_activities.create_index('activity_type')
   
    if mongo.db.email_templates.count_documents({}) == 0:
        sample_templates = [
            {
                'name': 'Welcome Email',
                'subject': 'Welcome to AI Tutor! 🎓',
                'html_content': """
                <html>
                <body>
                    <h2>Welcome to AI Tutor!</h2>
                    <p>Dear {{student_name}},</p>
                    <p>{{message}}</p>
                    <p>We're excited to have you on board!</p>
                    <p>Best regards,<br>AI Tutor Team</p>
                </body>
                </html>
                """,
                'created_at': datetime.now(),
                'created_by': 'admin'
            }
        ]
        mongo.db.email_templates.insert_many(sample_templates)
        print("Added sample email templates")
   
    flash('Database initialized with sample data!', 'success')
    return redirect(url_for('index'))

# ============================================
# Logout
# ============================================
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# ============================================
# Run Application
# ============================================
if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 AI TUTOR PLATFORM STARTING...")
    print("="*70)
    print("📊 Database: MongoDB (ai_tutor_db)")
    print("📁 Upload Folders:")
    print(f"   - Study Materials: {app.config['STUDY_MATERIAL_FOLDER']}")
    print(f"   - Videos: {app.config['UPLOAD_FOLDER']}")
    print(f"   - Contact Attachments: {app.config['CONTACT_ATTACHMENTS_FOLDER']}")
    print("📧 Email Configuration:")
    print(f"   - SMTP Server: {app.config['MAIL_SERVER']}")
    print(f"   - Port: {app.config['MAIL_PORT']}")
    print("🎯 URL: http://localhost:5000")
    print("👤 Admin: admin@aitutor.com / admin123")
    print("👤 Student: student@example.com / student123")
    print("🏆 Achievements System: FULLY ENABLED with 30+ medals!")
    print("="*70 + "\n")
   
    app.run(debug=True, host='0.0.0.0', port=5000)