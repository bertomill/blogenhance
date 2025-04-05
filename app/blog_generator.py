import os
import anthropic
import openai
from dotenv import load_dotenv

load_dotenv()

def get_web_search_recommendations(topic):
    """
    Use OpenAI's web search API to find relevant linking opportunities for the topic.
    
    Args:
        topic: The main topic of the blog post
    
    Returns:
        A dictionary with meta description and linking opportunities
    """
    try:
        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        search_prompt = f"""
        I'm writing a blog post about {topic} and need:
        
        1. A well-crafted meta description (150-160 characters) that includes the primary keyword
        2. 3-5 internal linking opportunities related to this topic
        3. 2-3 external authority sources (with URLs) to reference

        Please search the web for the most up-to-date and relevant information and format your response like this:
        
        Meta Description: [meta description here]
        
        Internal Linking Opportunities:
        - [topic 1]
        - [topic 2]
        - [topic 3]
        
        External Authority Sources:
        - [source name 1]: [URL 1]
        - [source name 2]: [URL 2]
        - [source name 3]: [URL 3]
        """
        
        completion = client.chat.completions.create(
            model="gpt-4o-search-preview",
            web_search_options={
                "search_context_size": "medium",
            },
            messages=[
                {"role": "user", "content": search_prompt}
            ],
        )
        
        # Parse the response to extract meta description and linking opportunities
        response_text = completion.choices[0].message.content
        
        # Initialize results with default values
        results = {
            "meta_description": "",
            "internal_links": [],
            "external_sources": []
        }
        
        # Parse the meta description
        if "Meta Description:" in response_text:
            meta_section = response_text.split("Meta Description:")[1].split("Internal Linking Opportunities:")[0].strip()
            results["meta_description"] = meta_section
        
        # Parse internal linking opportunities
        if "Internal Linking Opportunities:" in response_text:
            internal_section = response_text.split("Internal Linking Opportunities:")[1].split("External Authority Sources:")[0].strip()
            results["internal_links"] = [link.strip()[2:] for link in internal_section.split("\n") if link.strip().startswith("-")]
        
        # Parse external authority sources
        if "External Authority Sources:" in response_text:
            external_section = response_text.split("External Authority Sources:")[1].strip()
            external_links = []
            for link in external_section.split("\n"):
                if link.strip().startswith("-") and ":" in link:
                    parts = link.strip()[2:].split(":", 1)
                    if len(parts) == 2:
                        name = parts[0].strip()
                        url = parts[1].strip()
                        external_links.append({"name": name, "url": url})
            results["external_sources"] = external_links
        
        return results
    
    except Exception as e:
        print(f"Error in get_web_search_recommendations: {str(e)}")
        return {
            "meta_description": f"Learn about {topic} in this comprehensive guide that covers key concepts, best practices, and practical tips.",
            "internal_links": [
                f"{topic} strategies for beginners",
                f"Advanced {topic} techniques",
                f"{topic} case studies"
            ],
            "external_sources": [
                {"name": "Wikipedia", "url": f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"},
                {"name": "GitHub", "url": "https://github.com"}
            ]
        }

def generate_blog_post(topic, audience, reference_materials, tone_instructions=None, user_thoughts=None, custom_prompt=None, user=None):
    """
    Generate a blog post using Anthropic's Claude API.
    
    Args:
        topic: The main topic of the blog post
        audience: The target audience for the blog post
        reference_materials: List of reference materials, each with title, link, and content
        tone_instructions: Optional string containing instructions for the tone and style
        user_thoughts: Optional string containing the user's personal thoughts about the topic
        custom_prompt: Optional customized prompt template to override the default
        user: Optional user object containing profile and social media information
        
    Returns:
        A generated blog post as a string
    """
    # Get web search recommendations for linking opportunities and meta description
    web_recommendations = get_web_search_recommendations(topic)
    
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )
    
    # Format the linking opportunities as a string
    internal_links_str = "\n".join([f"- {link}" for link in web_recommendations["internal_links"]])
    external_sources_str = "\n".join([f"- {source['name']}: {source['url']}" for source in web_recommendations["external_sources"]])
    
    # Format the structured reference materials
    formatted_references = ""
    if reference_materials:
        for i, ref in enumerate(reference_materials):
            formatted_references += f"\nReference {i+1}:\n"
            formatted_references += f"Title: {ref['title']}\n"
            if ref['link']:
                formatted_references += f"Link: {ref['link']}\n"
            if ref['content']:
                # Only include the first 1000 characters of content in the prompt to avoid token limits
                content_preview = ref['content'][:1000]
                if len(ref['content']) > 1000:
                    content_preview += "... (content truncated)"
                formatted_references += f"Content: {content_preview}\n"
            formatted_references += "\n"
    else:
        formatted_references = "No reference materials provided."
    
    # Add user's personal thoughts if provided
    user_thoughts_section = ""
    if user_thoughts and user_thoughts.strip():
        user_thoughts_section = f"\nYOUR THOUGHTS (Important - incorporate these personal perspectives):\n{user_thoughts}\n"
    
    # Add social media information if available
    social_media_section = ""
    if user:
        social_links = []
        if user.twitter:
            social_links.append(f"X (Twitter): {user.twitter}")
        if user.linkedin:
            social_links.append(f"LinkedIn: {user.linkedin}")
        if user.instagram:
            social_links.append(f"Instagram: {user.instagram}")
        if user.website:
            social_links.append(f"Website: {user.website}")
        
        if social_links:
            social_media_section = "\nSOCIAL MEDIA LINKS (Include these at the end of the post):\n"
            social_media_section += "\n".join(social_links)
    
    # Determine which prompt to use
    if custom_prompt and custom_prompt.strip():
        # Use custom prompt but make sure to replace variables
        user_prompt = custom_prompt
        # Replace variables that might be in the custom prompt
        user_prompt = user_prompt.replace('${topic}', topic)
        user_prompt = user_prompt.replace('${audience}', audience)
        user_prompt = user_prompt.replace('${formattedReferences}', formatted_references)
        user_prompt = user_prompt.replace('${userThoughts}', user_thoughts or 'No personal thoughts provided.')
        user_prompt = user_prompt.replace('${toneInstructions}', tone_instructions or 'Write in a personal, conversational tone.')
        user_prompt = user_prompt.replace('${socialMediaLinks}', social_media_section)
    else:
        # Prepare the default prompt
        user_prompt = f"""
        You are a thoughtful blogger who writes engaging, personal content from a first-person perspective. Your task is to craft a blog post that feels like you're sharing your own thoughts and experiences about the topic, while drawing on the provided reference materials for insight.

        Topic: {topic}
        Target Audience: {audience}
        
        Reference Materials:
        {formatted_references}
        {user_thoughts_section}
        {social_media_section}
        
        Using these web search recommendations for research only (don't include these sections in the actual blog post):
        
        Suggested Meta Description: {web_recommendations["meta_description"]}
        
        Internal Linking Opportunities:
        {internal_links_str}
        
        External Authority Sources:
        {external_sources_str}
        
        Tone Instructions:
        {tone_instructions if tone_instructions else "Write in a personal, conversational tone."}
        
        When creating content, follow these guidelines:

        1. VOICE & TONE:
           - Write in first-person perspective (using "I", "my", "me")
           - Share personal opinions, reflections, and hypothetical experiences
           - Use a conversational, authentic tone as if you're talking to a friend
           - Express enthusiasm about the topic while maintaining credibility
           - Include relatable anecdotes or scenarios
           - Incorporate the user's thoughts and perspectives throughout

        2. STRUCTURE & FORMAT:
           - Begin with a personal hook or story related to the topic
           - Share your perspective on why this topic matters to you and the audience
           - Create 3-5 main content sections with descriptive subheadings
           - Keep paragraphs short (2-3 sentences) for better readability
           - End with a personal conclusion and reflection
           - Include a gentle call-to-action that invites readers to share their thoughts
           - End with "Thank you for listening! To learn more, please contact me" followed by all the provided social media links formatted with proper markdown links

        3. CONTENT QUALITY:
           - Draw insights from the reference materials but present them as your own discoveries
           - Share what you've "learned" in your exploration of the topic
           - Target a 7th-8th grade reading level for maximum accessibility
           - Support your opinions with relevant information from the references
           - Anticipate and address reader questions from your perspective
           - Avoid formal, academic language - keep it personal

        4. SEO OPTIMIZATION:
           - Naturally incorporate the primary keyword in the introduction, conclusion, and at least one heading
           - Use related secondary keywords and semantic variations throughout
           - Reference external sources in a natural way, as things you've discovered
           - DO NOT include separate sections for meta description or linking opportunities

        5. ENGAGEMENT ELEMENTS:
           - Include personal questions you've asked yourself about the topic
           - Suggest personal experiences readers might relate to
           - Incorporate bulleted or numbered lists when sharing "your tips" or insights
           - Use phrases like "In my experience," "I've found that," "I believe," etc.
           - Add personal takeaways or "aha moments"
           
        6. Use Markdown format for the content with # for main headings, ## for subheadings, etc.
        
        7. Make sure the blog post reads like a personal reflection or opinion piece rather than an informational article. Start with an engaging personal title and dive right into the content without including any meta description or linking sections.
        
        8. IMPORTANT: At the end of your blog post, ALWAYS add "Thank you for listening! To learn more, please contact me" followed by all the provided social media links formatted with proper markdown links.
        """
    
    # Create the message
    try:
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=20000,
            temperature=1,
            system="You are a thoughtful blogger who writes engaging, personal content from a first-person perspective. Your writing should feel authentic, opinionated, and personal while still being valuable and insightful to readers.",
            messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        
        # Extract blog content based on library version
        blog_content = ""
        
        # Handle different response formats from the Anthropic API
        if hasattr(message, 'content'):
            # Newer Anthropic API version
            content = message.content
            
            if isinstance(content, list):
                # If content is a list of message parts (e.g., text, images)
                for part in content:
                    if hasattr(part, 'text') and part.text:
                        blog_content += part.text
                    elif isinstance(part, dict) and 'text' in part:
                        blog_content += part['text']
            elif isinstance(content, str):
                # If content is directly a string
                blog_content = content
            else:
                # Fallback for other formats
                blog_content = str(content)
                
        elif hasattr(message, 'content') and isinstance(message.content, list) and len(message.content) > 0:
            # Older Anthropic API version with content as a list
            if hasattr(message.content[0], 'text'):
                blog_content = message.content[0].text
            elif isinstance(message.content[0], dict) and 'text' in message.content[0]:
                blog_content = message.content[0]['text']
            else:
                blog_content = str(message.content[0])
        else:
            # Last resort fallback
            blog_content = str(message)
            
        return blog_content
        
    except Exception as e:
        print(f"Error in generate_blog_post: {str(e)}")
        raise Exception(f"Failed to generate blog post: {str(e)}") 