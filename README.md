# BlogEnhance

BlogEnhance is an AI-powered platform that makes creating high-quality blog posts fast and effortless. Using advanced AI technology, it generates SEO-optimized content tailored to your style and audience in minutes.

## Features

- **AI-Powered Content Generation**: Create complete blog posts with a few clicks
- **Personalized Style**: Content matches your unique voice and writing preferences
- **SEO Optimization**: Built-in recommendations to help your content rank higher
- **Custom Cover Images**: Generate eye-catching cover images that match your content
- **Audience Targeting**: Content tailored to resonate with specific audiences
- **Free Tier**: 3 free blog posts for all new users
- **Subscription Plans**: Flexible pricing options for regular content creators

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLAlchemy with SQLite
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Authentication**: Flask-Login
- **Payments**: Stripe API integration

## Setup Instructions

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/bertomill/blogenhance.git
   cd blogenhance
   ```

2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy the `.env.example` file to `.env` if it exists, or create a new `.env` file
   - Add your API keys and configuration values

5. Initialize the database:
   ```
   flask db upgrade
   ```

6. Run the application:
   ```
   python run.py
   ```

7. Open your browser and navigate to:
   ```
   http://127.0.0.1:5001
   ```

## Usage

1. Create an account to get 3 free blog generations
2. Enter your blog topic and target audience
3. Add any reference materials or personal thoughts
4. Generate your AI-powered blog post in seconds
5. Review, edit, and export your content

## Deployment

For production deployment, consider using:
- Heroku
- PythonAnywhere
- AWS Elastic Beanstalk
- Google Cloud Run

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions or support, please contact [your-email@example.com] 