import os
import requests
from dotenv import load_dotenv
import json
import markdown
import re

# Third-party library imports - these will need to be installed
# For Medium: import medium
# For Mastodon: from mastodon import Mastodon
# For Substack: Using requests as there's no official Python library

load_dotenv()

def publish_to_medium(blog_content, title, image_url=None):
    """
    Instead of direct API publishing to Medium which is no longer supported,
    this function prepares and returns a Medium-formatted version of the content.
    
    Args:
        blog_content: The content of the blog post
        title: The title of the blog post
        image_url: URL of the cover image (optional)
        
    Returns:
        A dictionary with information for manual Medium publishing
    """
    # First, convert Markdown to HTML using the markdown library
    html_content = markdown.markdown(
        blog_content,
        extensions=[
            'markdown.extensions.fenced_code',
            'markdown.extensions.tables',
            'markdown.extensions.nl2br',
            'markdown.extensions.sane_lists'
        ]
    )
    
    # Remove any meta description or linking opportunities sections
    html_content = re.sub(r'<h2>Suggested Meta Description:.*?</h2>.*?<h2>', '<h2>', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<h2>Internal Linking Opportunities:.*?</h2>.*?<h2>', '<h2>', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<h2>External Authority Sources:.*?</h2>.*?<h2>', '<h2>', html_content, flags=re.DOTALL)
    
    # Create a Medium-friendly HTML version
    medium_formatted_content = f"<h1>{title}</h1>\n\n"
    
    # Add cover image if provided
    if image_url:
        medium_formatted_content += f'<figure><img src="{image_url}" alt="Cover image for {title}" /><figcaption>Cover image for {title}</figcaption></figure>\n\n'
    
    # Add the main content
    medium_formatted_content += html_content
    
    # Return instructions and formatted content for manual publishing
    return {
        "url": "https://medium.com/new-story",
        "note": "Copy this content and paste it directly into Medium's editor. The formatting should be preserved.",
        "formatted_content": medium_formatted_content
    }

def publish_to_substack(blog_content, title, image_url=None):
    """
    Publish a blog post to Substack.
    
    Args:
        blog_content: The content of the blog post
        title: The title of the blog post
        image_url: URL of the cover image (optional)
        
    Returns:
        URL of the published post
    """
    # This is a placeholder implementation as Substack doesn't have an official API
    # In a real implementation, you might need to use a third-party service or Substack's API if one becomes available
    
    api_key = os.environ.get("SUBSTACK_API_KEY")
    
    # Placeholder API endpoint - this is not a real Substack API endpoint
    api_url = "https://substack.com/api/v1/posts"
    
    # Prepare the request payload
    payload = {
        "title": title,
        "body": blog_content,
        "status": "draft"  # Can be "published" or "draft"
    }
    
    if image_url:
        payload["cover_image_url"] = image_url
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # In a real implementation, this would be an actual API call if an API exists
        # response = requests.post(api_url, json=payload, headers=headers)
        # response.raise_for_status()
        # return response.json()['url']
        
        # For now, we'll return a placeholder URL
        return "https://yoursubstack.substack.com/p/your-post-url"
    
    except Exception as e:
        print(f"Error publishing to Substack: {str(e)}")
        raise Exception(f"Failed to publish to Substack: {str(e)}")

def publish_to_mastodon(blog_content, title, image_url=None):
    """
    Publish a blog post to Mastodon.
    
    Args:
        blog_content: The content of the blog post
        title: The title of the blog post
        image_url: URL of the cover image (optional)
        
    Returns:
        URL of the published post
    """
    # This is a placeholder implementation using the Mastodon API
    # In a real implementation, you would use the Mastodon.py client
    
    api_key = os.environ.get("MASTODON_API_KEY")
    
    # Mastodon instance URL - replace with your Mastodon instance
    instance_url = "https://mastodon.social"
    
    # Prepare the content
    # Mastodon has character limits, so you'd need to create a summary with a link
    status_content = f"{title}\n\n{blog_content[:300]}...\n\nRead more: [Link would go here]"
    
    try:
        # In a real implementation, this would be an actual API call
        # mastodon = Mastodon(
        #     access_token=api_key,
        #     api_base_url=instance_url
        # )
        # 
        # media_id = None
        # if image_url:
        #     media = mastodon.media_post(image_url)
        #     media_id = media['id']
        # 
        # status = mastodon.status_post(
        #     status_content,
        #     media_ids=[media_id] if media_id else None
        # )
        # return f"{instance_url}/@username/{status['id']}"
        
        # For now, we'll return a placeholder URL
        return "https://mastodon.social/@yourusername/123456789"
    
    except Exception as e:
        print(f"Error publishing to Mastodon: {str(e)}")
        raise Exception(f"Failed to publish to Mastodon: {str(e)}") 