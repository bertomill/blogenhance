import os
import requests
import json
import base64
import time
import random
from dotenv import load_dotenv

load_dotenv()

def generate_cover_image(topic, audience=None):
    """
    Generates a cover image for a blog post using Stable Diffusion models.
    
    Args:
        topic: The topic of the blog post
        audience: Optional target audience to refine the image generation
        
    Returns:
        Dictionary with image_url and sora_prompt (kept for compatibility)
    """
    # Create detailed prompts for image generation
    prompts = [
        f"A professional, cinematic cover image for a blog post about {topic}. High-quality, photorealistic style with stunning lighting and composition. The image should convey the essence of {topic} in a visually appealing way that would attract readers. NO TEXT OR WORDS in the image.",
        
        f"An artistic, visually striking cover image for an article about {topic}. The scene should have depth, perfect lighting, and professional composition. Include subtle elements that represent {topic} without any text or typography. NO TEXT allowed in the image.",
        
        f"A beautiful, professional cover image representing {topic}. Cinematic quality with perfect lighting, detailed textures, and a composition that draws the viewer in. The image should be suitable for a premium blog or publication. Do not include any words, labels, or text in the image."
    ]
    
    # If audience is provided, refine the prompt
    if audience:
        prompts = [
            f"A professional, cinematic cover image for a blog post about {topic}, targeted at {audience}. High-quality, photorealistic style with stunning lighting and composition. IMPORTANT: No text, no words, no typography anywhere in the image.",
            
            f"An artistic, visually striking cover image for an article about {topic} for {audience}. The scene should have depth, perfect lighting, and professional composition. Absolutely no text or writing should appear anywhere in the image.",
            
            f"A beautiful, professional cover image representing {topic} for an audience of {audience}. Cinematic quality with perfect lighting, detailed textures, and a composition that draws the viewer in. The image must not contain any text, titles, captions, or labels."
        ]
    
    # Select a random prompt
    selected_prompt = random.choice(prompts)
    
    # Get Hugging Face API key from environment variables
    api_key = os.environ.get("HUGGINGFACE_API_KEY")
    
    if not api_key:
        print("Warning: HUGGINGFACE_API_KEY not found in environment variables")
        # Return a placeholder image and the prompt
        placeholder_url = f"https://placehold.co/1024x576/EEE/31343C?text=Cover+Image+for+{topic.replace(' ', '+')}"
        return {
            "image_url": placeholder_url,
            "sora_prompt": selected_prompt
        }
    
    # Define the models to try in order of preference
    models = [
        "stabilityai/stable-diffusion-xl-base-1.0",
        "runwayml/stable-diffusion-v1-5",
        "CompVis/stable-diffusion-v1-4"
    ]
    
    # Try each model in sequence until one succeeds
    for model_id in models:
        success, image_url = try_generate_with_model(
            model_id=model_id,
            prompt=selected_prompt,
            api_key=api_key,
            topic=topic,
            timeout=30,  # Increased timeout for better image quality
            is_cover=True
        )
        
        if success:
            return {
                "image_url": image_url,
                "sora_prompt": selected_prompt  # Keep this for compatibility
            }
    
    # If all models fail, return a placeholder image
    print("All image generation models failed, using placeholder")
    placeholder_url = f"https://placehold.co/1024x576/EEE/31343C?text=Cover+Image+for+{topic.replace(' ', '+')}"
    
    return {
        "image_url": placeholder_url,
        "sora_prompt": selected_prompt
    }

def generate_meme_image(topic):
    """
    Instead of generating a meme image, returns a detailed prompt for Sora and meme text.
    
    Args:
        topic: The topic to generate a meme about
        
    Returns:
        Dictionary with prompt, caption and a placeholder image URL
    """
    # Generate a meme-oriented prompt for Sora
    meme_templates = [
        f"A humorous, internet-style meme about {topic}. The image should be funny and relatable with space at the top and bottom for text captions. The image itself must not contain any text, words, or writing - we will add captions later.",
        
        f"A satirical meme image related to {topic} in the style of popular internet memes. The scene should be clear, well-lit, and designed to be humorous with a setup for a joke. NO TEXT should be included in the generated image.",
        
        f"A comical scene related to {topic} that would work well as a meme. High quality image with good lighting and funny scenario that viewers would instantly recognize as a meme format. The image should be completely free of any text or typography."
    ]
    
    # Top and bottom captions for the meme
    top_captions = [
        f"When someone asks me about {topic}",
        f"That moment when you discover {topic}",
        f"Nobody: Me explaining {topic}:",
        f"{topic} experts be like",
        f"My brain at 3AM thinking about {topic}"
    ]
    
    bottom_captions = [
        "...and that's why it changed my life",
        "I'm something of an expert myself",
        "Trust me, I read an article once",
        "This is fine. Everything is fine.",
        "*confused screaming*"
    ]
    
    # Select random elements
    sora_prompt = random.choice(meme_templates)
    top_text = random.choice(top_captions)
    bottom_text = random.choice(bottom_captions)
    
    # Return placeholder and the prompt
    placeholder_url = f"https://placehold.co/800x600/EEE/31343C?text=Meme+About+{topic.replace(' ', '+')}"
    
    return {
        "image_url": placeholder_url,
        "sora_prompt": sora_prompt,
        "meme_top_text": top_text,
        "meme_bottom_text": bottom_text
    }

def try_generate_with_model(model_id, prompt, api_key, topic, timeout=25, is_cover=True):
    """
    Try to generate an image with a specific model
    
    Args:
        model_id: The Hugging Face model ID
        prompt: The prompt for image generation
        api_key: The Hugging Face API key
        topic: The topic (used for filename)
        timeout: Timeout in seconds
        is_cover: Whether this is a cover image or not
    
    Returns:
        (success, image_path) tuple
    """
    try:
        # API URL for the model
        api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        
        # Set up headers with API key
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Create payload with optimized parameters
        payload = {
            "inputs": prompt,
            "parameters": {
                "num_inference_steps": 25,  # Reduced for faster generation
                "guidance_scale": 7.5,
                "width": 1024 if is_cover else 800,
                "height": 576 if is_cover else 600,
                "negative_prompt": "text, words, letters, signature, watermark, label, title, caption, typography, writing, font, alphabet, characters"
            }
        }
        
        # Make the API request with timeout
        image_type = "cover" if is_cover else "meme"
        print(f"Generating {image_type} image with {model_id} for topic: {topic}")
        response = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Save the image to a file with a timestamped name
            timestamp = int(time.time())
            safe_topic = ''.join(c if c.isalnum() or c == '_' else '_' for c in topic)
            filename = f"app/static/images/{timestamp}_{safe_topic}.png"
            
            # Ensure the directory exists
            os.makedirs("app/static/images", exist_ok=True)
            
            # Save the image
            with open(filename, "wb") as f:
                f.write(response.content)
            
            # Return success and the URL path for the image
            # Use a URL path that Flask can serve (relative to the static folder)
            url_path = f"/static/images/{timestamp}_{safe_topic}.png"
            print(f"Successfully generated image, saved to {filename}")
            print(f"URL path: {url_path}")
            return True, url_path
        else:
            print(f"Error from Hugging Face API: {response.status_code}")
            print(response.text[:500])  # Print only part of the error to avoid huge logs
            return False, None
    
    except requests.exceptions.Timeout:
        print(f"Request to {model_id} timed out after {timeout} seconds")
        return False, None
    except Exception as e:
        print(f"Error with {model_id}: {str(e)}")
        return False, None 