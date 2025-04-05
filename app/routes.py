from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, Markup
import os
import anthropic
from flask_login import current_user, login_required
from app.blog_generator import generate_blog_post
from app.image_generator import generate_cover_image, generate_meme_image
import markdown
import bleach
from bleach.sanitizer import ALLOWED_TAGS, ALLOWED_ATTRIBUTES
from app.models import db, BlogPost
import re
import json

main_bp = Blueprint('main', __name__)

# Add additional allowed HTML tags for richer formatting
ALLOWED_TAGS.extend(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'span', 'img', 'hr', 'br'])
# Add additional allowed attributes
ALLOWED_ATTRIBUTES.update({
    'img': ['src', 'alt', 'title', 'width', 'height', 'class'],
    'a': ['href', 'title', 'target', 'rel', 'class'],
    'div': ['class', 'id'],
    'span': ['class', 'id'],
    'h1': ['id', 'class'],
    'h2': ['id', 'class'],
    'h3': ['id', 'class'],
    'h4': ['id', 'class'],
    'h5': ['id', 'class'],
    'h6': ['id', 'class'],
    'p': ['class']
})

@main_bp.route('/', methods=['GET'])
def index():
    # If user is not logged in, show landing page
    if not current_user.is_authenticated:
        return render_template('landing.html')
    # Otherwise show the normal index page for logged in users
    return render_template('index.html')

@main_bp.route('/check_progress', methods=['GET'])
def check_progress():
    """
    Route to check the progress of a blog post generation.
    This is a placeholder for future implementation that will return the actual progress.
    
    In a real implementation, this would:
    1. Check the status of the generation job
    2. Return the current progress percentage
    3. Return the current status message
    
    Returns:
        JSON with progress information
    """
    # In a production app, we would track each user's generation job
    # using a task queue like Celery and return real progress
    
    # For now, we return a simple mock response
    import random
    
    # Mock progress values
    progress_values = [10, 25, 40, 60, 75, 90, 100]
    status_messages = [
        "Analyzing topic...",
        "Researching key points...",
        "Creating outline...",
        "Drafting content...",
        "Adding details and examples...",
        "Optimizing for readability...",
        "Finalizing blog post..."
    ]
    
    # For demo purposes, choose random progress
    progress_index = random.randint(0, len(progress_values) - 1)
    
    return jsonify({
        'progress': progress_values[progress_index],
        'status': status_messages[progress_index],
        'completed': progress_values[progress_index] == 100
    })

@main_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    try:
        # Check if user can generate a post
        if not current_user.can_generate_post():
            flash('You have reached your blog generation limit. Please upgrade your subscription to continue.', 'warning')
            return redirect(url_for('payment.plans'))
        
        # Get form inputs
        topic = request.form.get('topic', '')
        audience = request.form.get('audience', '')
        user_thoughts = request.form.get('user_thoughts', '')
        custom_prompt = request.form.get('custom_prompt', '')  # Get custom prompt if provided
        
        # Process structured reference materials
        reference_titles = request.form.getlist('reference_title[]')
        reference_links = request.form.getlist('reference_link[]')
        reference_contents = request.form.getlist('reference_content[]')
        
        # Combine into a list of dictionaries
        reference_materials = []
        for i in range(len(reference_titles)):
            if reference_titles[i].strip() or reference_contents[i].strip():
                reference_materials.append({
                    'title': reference_titles[i].strip(),
                    'link': reference_links[i].strip() if i < len(reference_links) else '',
                    'content': reference_contents[i].strip()
                })
        
        # Get user profile information for tone
        tone_instructions = ""
        if current_user.is_authenticated:
            if current_user.personality:
                tone_instructions += f"Personality: {current_user.personality}\n"
            if current_user.writing_style:
                tone_instructions += f"Writing Style: {current_user.writing_style}\n"
            if current_user.expertise:
                tone_instructions += f"Expertise: {current_user.expertise}\n"
            if current_user.background:
                tone_instructions += f"Background: {current_user.background}\n"
        
        # Generate blog post
        blog_post = generate_blog_post(
            topic=topic,
            audience=audience,
            reference_materials=reference_materials,
            tone_instructions=tone_instructions,
            user_thoughts=user_thoughts,
            custom_prompt=custom_prompt,  # Pass custom prompt to generator
            user=current_user  # Pass current user to include their social media info
        )
        
        # Format the blog post
        formatted_blog_post = format_blog_post(blog_post)
        
        # Process cover image if requested
        cover_image_data = None
        if request.form.get('generate_cover') == 'on':
            cover_image_data = generate_cover_image(topic, audience)
        
        # Save the blog post to database
        title = extract_title(blog_post)
        new_blog = BlogPost(
            title=title,
            content=blog_post,
            formatted_content=formatted_blog_post,
            topic=topic,
            audience=audience,
            user_id=current_user.id,
            cover_image_prompt=cover_image_data.get('sora_prompt') if cover_image_data else None,
            user_thoughts=user_thoughts
        )
        db.session.add(new_blog)
        
        # Decrement free posts if user doesn't have an active subscription
        if not current_user.has_active_subscription():
            current_user.decrement_free_posts()
        
        db.session.commit()
        
        # Pass data to the template
        return render_template(
            'result.html',
            blog_post=blog_post,
            formatted_blog_post=formatted_blog_post,
            form_data=request.form,
            cover_image_data=cover_image_data
        )
    
    except Exception as e:
        flash(f'Error generating blog post: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/my-blogs')
@login_required
def my_blogs():
    # Get all blogs for the current user
    blogs = BlogPost.query.filter_by(user_id=current_user.id).order_by(BlogPost.created_at.desc()).all()
    return render_template('my_blogs.html', blogs=blogs)

@main_bp.route('/view-blog/<int:blog_id>')
@login_required
def view_blog(blog_id):
    # Get the specific blog post
    blog = BlogPost.query.get_or_404(blog_id)
    
    # Make sure the user owns this blog post
    if blog.user_id != current_user.id:
        flash('You do not have permission to view this blog post.', 'danger')
        return redirect(url_for('main.my_blogs'))
    
    return render_template(
        'result.html',
        blog_post=blog.content,
        formatted_blog_post=blog.formatted_content,
        form_data={'generate_cover': 'on'} if blog.cover_image_prompt else {},
        cover_image_data={'sora_prompt': blog.cover_image_prompt} if blog.cover_image_prompt else None
    )

def format_blog_post(blog_post):
    """Convert markdown to HTML and clean up the content."""
    from markdown import markdown
    import bleach
    
    # Convert markdown to HTML
    html = markdown(blog_post)
    
    # Remove unwanted sections using regex
    html = re.sub(r'<h2>Suggested Meta Description.*?</p>', '', html, flags=re.DOTALL)
    html = re.sub(r'<h2>Internal Linking Opportunities.*?</ul>', '', html, flags=re.DOTALL)
    html = re.sub(r'<h2>External Authority Sources.*?</ul>', '', html, flags=re.DOTALL)
    
    # Clean up the HTML
    allowed_tags = [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'ul', 'ol', 'li', 'blockquote',
        'code', 'pre', 'strong', 'em', 'strike', 'hr', 'br', 'div', 'table', 'thead', 
        'tbody', 'tr', 'th', 'td'
    ]
    allowed_attrs = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title']
    }
    
    return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)

def extract_title(blog_post):
    """Extract the title from the blog post content."""
    lines = blog_post.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()
    return "Untitled Blog Post" 