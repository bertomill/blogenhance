from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and profile information."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Free tier tracking
    free_posts_remaining = db.Column(db.Integer, default=3)
    
    # Profile information stored as JSON
    personality = db.Column(db.Text, nullable=True)
    writing_style = db.Column(db.Text, nullable=True)
    expertise = db.Column(db.Text, nullable=True)
    background = db.Column(db.Text, nullable=True)
    
    # Social media links
    twitter = db.Column(db.String(255), nullable=True)
    linkedin = db.Column(db.String(255), nullable=True)
    instagram = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    
    # Relationships
    blog_posts = db.relationship('BlogPost', backref='author', lazy=True)
    subscription = db.relationship('Subscription', backref='user', lazy=True, uselist=False)
    
    def __init__(self, username=None, email=None, password=None):
        self.username = username
        self.email = email
        if password:
            self.set_password(password)
        self.free_posts_remaining = 3  # Set default free posts
    
    def set_password(self, password):
        """Set a hashed password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the user's password hash."""
        return check_password_hash(self.password_hash, password)
    
    def update_profile(self, profile_data):
        """Update the user's profile with new data."""
        if 'personality' in profile_data:
            self.personality = profile_data['personality']
        if 'writing_style' in profile_data:
            self.writing_style = profile_data['writing_style']
        if 'expertise' in profile_data:
            self.expertise = profile_data['expertise']
        if 'background' in profile_data:
            self.background = profile_data['background']
        
        # Update social media links
        if 'twitter' in profile_data:
            self.twitter = profile_data['twitter']
        if 'linkedin' in profile_data:
            self.linkedin = profile_data['linkedin']
        if 'instagram' in profile_data:
            self.instagram = profile_data['instagram']
        if 'website' in profile_data:
            self.website = profile_data['website']
            
        db.session.commit()
    
    @property
    def profile(self):
        """Return profile information as a dictionary."""
        return {
            'personality': self.personality,
            'writing_style': self.writing_style,
            'expertise': self.expertise,
            'background': self.background,
            'social_media': {
                'twitter': self.twitter,
                'linkedin': self.linkedin,
                'instagram': self.instagram,
                'website': self.website
            }
        }
    
    def get_tone_instructions(self):
        """Generate tone instructions based on user profile."""
        instructions = []
        
        if self.personality:
            instructions.append(f"Write with a {self.personality} personality.")
            
        if self.writing_style:
            instructions.append(f"Use a {self.writing_style} writing style.")
            
        if self.expertise:
            instructions.append(f"Incorporate knowledge in {self.expertise} where relevant.")
            
        if self.background:
            instructions.append(f"Draw on this background: {self.background}.")
        
        # Include social media links instruction if any social media is provided
        has_social = any([self.twitter, self.linkedin, self.instagram, self.website])
        if has_social:
            instructions.append("Include a 'Connect with me' section at the end with my social media links.")
            
        return " ".join(instructions)
    
    def has_active_subscription(self):
        """Check if the user has an active subscription."""
        return (
            self.subscription is not None and
            self.subscription.status in ['active', 'trialing'] and
            self.subscription.current_period_end > datetime.utcnow()
        )
    
    def can_generate_post(self):
        """Check if the user can generate a new blog post."""
        # User has free posts remaining
        if self.free_posts_remaining > 0:
            return True
        
        # User has an active subscription
        if self.has_active_subscription():
            # Get the subscription plan details
            from app.payment import PLANS
            plan = PLANS.get(self.subscription.plan_id)
            
            if plan:
                # If unlimited posts or not reached limit yet
                if plan['blog_limit'] is None:
                    return True
                
                # Count blog posts created this month
                month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                posts_this_month = BlogPost.query.filter(
                    BlogPost.user_id == self.id,
                    BlogPost.created_at >= month_start
                ).count()
                
                return posts_this_month < plan['blog_limit']
        
        return False
    
    def decrement_free_posts(self):
        """Decrement the number of free posts if available."""
        if self.free_posts_remaining > 0:
            self.free_posts_remaining -= 1
            db.session.commit()
            return True
        return False
    
    def get_subscription_plan(self):
        """Get the user's current subscription plan."""
        if not self.has_active_subscription():
            return None
        return self.subscription.plan_id
    
    def __repr__(self):
        return f'<User {self.username}>'

# Helper functions to make transition from old code easier
def save_user(user):
    """Save user to database."""
    db.session.add(user)
    db.session.commit()
    return user

def get_user(user_id):
    """Get a user by ID."""
    return User.query.get(user_id)

def get_user_by_email(email):
    """Get a user by email."""
    return User.query.filter_by(email=email).first()

def get_user_by_username(username):
    """Get a user by username."""
    return User.query.filter_by(username=username).first()

# Add a BlogPost model to store the generated blog posts
class BlogPost(db.Model):
    """Model for storing generated blog posts."""
    __tablename__ = 'blog_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    formatted_content = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(255), nullable=False)
    audience = db.Column(db.String(255), nullable=True)
    user_thoughts = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Cover and meme image prompts if generated
    cover_image_prompt = db.Column(db.Text, nullable=True)
    meme_image_prompt = db.Column(db.Text, nullable=True)
    
    # Foreign key to user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __init__(self, title, content, formatted_content, topic, audience, user_id, 
                cover_image_prompt=None, meme_image_prompt=None, user_thoughts=None):
        self.title = title
        self.content = content
        self.formatted_content = formatted_content
        self.topic = topic
        self.audience = audience
        self.user_id = user_id
        self.cover_image_prompt = cover_image_prompt
        self.meme_image_prompt = meme_image_prompt
        self.user_thoughts = user_thoughts

# Subscription model to track user subscriptions
class Subscription(db.Model):
    """Model for storing user subscription information."""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Stripe information
    stripe_customer_id = db.Column(db.String(255), nullable=False)
    stripe_subscription_id = db.Column(db.String(255), nullable=False)
    
    # Subscription details
    plan_id = db.Column(db.String(50), nullable=False)  # 'basic', 'pro', 'enterprise'
    status = db.Column(db.String(50), nullable=False)  # 'active', 'canceled', 'past_due', etc.
    current_period_end = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id, stripe_customer_id, stripe_subscription_id, plan_id, status, current_period_end):
        self.user_id = user_id
        self.stripe_customer_id = stripe_customer_id
        self.stripe_subscription_id = stripe_subscription_id
        self.plan_id = plan_id
        self.status = status
        self.current_period_end = current_period_end
    
    def is_active(self):
        """Check if subscription is active."""
        return (
            self.status in ['active', 'trialing'] and
            self.current_period_end > datetime.utcnow()
        )
    
    def __repr__(self):
        return f'<Subscription {self.id} - User {self.user_id} - Plan {self.plan_id}>' 