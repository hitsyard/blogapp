from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId  # Import ObjectId here
import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

app = Flask(__name__)

# Use environment variables for sensitive configuration
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')  # Provide a default only for local testing

# MongoDB Configuration using environment variables
uri = os.getenv('MONGO_URI')  # MongoDB connection string from environment variable
client = MongoClient(uri)
db = client.blog_app  # Your database name is 'blog_app'

def generate_slug(title):
    """Generate a URL-friendly slug from the post title."""
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title)
    slug = slug.strip().lower()
    slug = re.sub(r'[\s]+', '-', slug)  # Replace spaces with hyphens
    return slug

def fetch_categories():
    """Fetch all categories and their post count from MongoDB."""
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    categories_list = list(db.blog_posts.aggregate(pipeline))
    return {item['_id']: item['count'] for item in categories_list}

def fetch_blog_posts(category=None):
    """Fetch blog posts filtered by category if provided."""
    if category:
        blog_posts = db.blog_posts.find({"category": category})
    else:
        blog_posts = db.blog_posts.find()
    return list(blog_posts)

@app.route('/visualX7865')
def admin_posts():
    """Admin dashboard to manage posts."""
    if not session.get('logged_in'):
        flash('You need to log in to access the admin panel.', 'warning')
        return redirect(url_for('login'))

    posts = fetch_blog_posts()
    return render_template('admin_posts.html', posts=posts)

@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    """Edit a blog post."""
    if not session.get('logged_in'):
        flash('You need to log in to edit posts.', 'warning')
        return redirect(url_for('login'))

    post = db.blog_posts.find_one({"_id": post_id})

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        image = request.form.get('image', '').strip()
        category = request.form.get('category', '').strip()
        full_content = request.form.get('full_content', '').strip()

        if not title or not description or not category:
            flash('Title, description, and category are required.', 'danger')
            return redirect(url_for('edit_post', post_id=post_id))

        # Update the post
        slug = generate_slug(title)
        db.blog_posts.update_one(
            {"_id": post_id},
            {"$set": {
                "title": title,
                "description": description,
                "image": image,
                "category": category,
                "slug": slug,
                "full_content": full_content
            }}
        )
        flash('Post updated successfully!', 'success')
        return redirect(url_for('admin_posts'))

    return render_template('edit_post.html', post=post)

@app.route('/delete_post/<post_id>', methods=['POST'])
def delete_post(post_id):
    """Delete a blog post."""
    if not session.get('logged_in'):
        flash('You need to log in to delete posts.', 'warning')
        return redirect(url_for('login'))

    db.blog_posts.delete_one({"_id": ObjectId(post_id)})

    flash('Post deleted successfully!', 'success')
    return redirect(url_for('admin_posts'))  # Redirect to admin dashboard


@app.route('/')
@app.route('/blog')
def blog():
    category = request.args.get('category')
    
    # Fetch blog posts, filtered by category if provided
    blog_posts = fetch_blog_posts(category)
    
    # Fetch categories for the sidebar or menu
    categories = fetch_categories()
    
    total_posts_count = len(blog_posts)
    
    return render_template('blog.html', 
                           posts=blog_posts, 
                           categories=categories,  # Pass categories to the template
                           total_posts_count=total_posts_count)

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    """Create a new blog post."""
    if not session.get('logged_in'):
        flash('You need to log in to create posts.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        image = request.form.get('image', '').strip()
        category = request.form.get('category', '').strip()
        full_content = request.form.get('full_content', '').strip()

        if not title or not description or not category:
            flash('Title, description, and category are required.', 'danger')
            return redirect(url_for('create_post'))

        slug = generate_slug(title)
        created_at = datetime.utcnow()  # Add current timestamp

        db.blog_posts.insert_one({
            "title": title,
            "description": description,
            "image": image,
            "category": category,
            "slug": slug,
            "full_content": full_content,
            "created_at": created_at  # Add created_at field
        })

        flash('Blog post created successfully!', 'success')
        return redirect(url_for('admin_posts'))

    return render_template('create_post.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Log in as admin."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Fetch the user from the MongoDB users collection
        user = db.users.find_one({"username": username, "password": password})

        if user:
            session['logged_in'] = True
            flash('You have successfully logged in!', 'success')
            return redirect(url_for('admin_posts'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Log out the admin."""
    session.pop('logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('blog'))

@app.route('/post/<slug>')
def post_detail(slug):
    """View a specific blog post by its slug."""
    post = db.blog_posts.find_one({"slug": slug})

    if post is None:
        flash('Post not found!', 'danger')
        return redirect(url_for('blog'))

    return render_template('post_detail.html', post=post)

if __name__ == '__main__':
    app.run(debug=True)
