import tweepy
import os
import time
import random
from datetime import datetime
import logging
import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
import tweepy.client

# Load environment variables from .env file
load_dotenv()

# Set up logging
log_file_path = "/tmp/twitter_agent.log"  # Change log file path to /tmp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),  # Update the log file path
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TwitterAgent")

class TwitterAgent:
    def __init__(self, api_key, api_secret, access_token, access_token_secret,bearer_token):
        """Initialize the Twitter agent with API credentials."""
        self.api_key = api_key
        self.client = None
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.bearer_token = bearer_token  # Add Bearer Token
        self.api = self._authenticate()
        logger.info("Twitter Agent initialized")
        
    def _authenticate(self):
        """Authenticate with Twitter API."""
        try:
            auth = tweepy.OAuth1UserHandler(
                self.api_key, self.api_secret,
                self.access_token, self.access_token_secret
            )
            client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret
            )
            self.client = client
            api = tweepy.API(auth)
            api.verify_credentials()
            logger.info("Authentication successful")
            return api
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise
    
    def get_trending_ai_topics(self):
        """
        Fetch trending AI topics from various sources.
        Returns a list of trending AI topics.
        """
        trending_topics = []
        
        try:
            # Method 1: Scrape from ArXiv's AI section for recent papers
            arxiv_url = "https://arxiv.org/list/cs.AI/recent"
            response = requests.get(arxiv_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                titles = soup.select('div.list-title')
                for title in titles[:5]:  # Get top 5 recent papers
                    clean_title = title.text.replace('Title:', '').strip()
                    trending_topics.append(clean_title)
            
            # Method 2: Check AI news from TechCrunch
            techcrunch_url = "https://techcrunch.com/category/artificial-intelligence/"
            response = requests.get(techcrunch_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                headlines = soup.select('h2.post-block__title a')
                for headline in headlines[:5]:  # Get top 5 headlines
                    trending_topics.append(headline.text.strip())
            
            # If we couldn't get any trending topics, use fallback topics
            if not trending_topics:
                trending_topics = [
                    "Large Language Models and their applications",
                    "AI in healthcare advancements",
                    "Ethical considerations in AI development",
                    "Computer vision breakthroughs",
                    "AI for climate change solutions",
                    "Multimodal AI systems",
                    "Reinforcement learning from human feedback",
                    "AI alignment research progress"
                ]
            
            logger.info(f"Found {len(trending_topics)} trending AI topics")
            return trending_topics
            
        except Exception as e:
            logger.error(f"Error fetching trending AI topics: {str(e)}")
            # Return fallback topics if there's an error
            return [
                "Large Language Models and their applications",
                "AI in healthcare advancements",
                "Ethical considerations in AI development",
                "Computer vision breakthroughs",
                "AI for climate change solutions"
            ]
    
    def generate_tweet_with_link_and_comments(self, topic=None):
        """
        Generate a tweet about AI trends with a relevant link and multiple follow-up comments using OpenAI.
        Returns a tuple containing the tweet and a list of follow-up comments.
        """
        if not topic:
            trending_topics = self.get_trending_ai_topics()
            topic = random.choice(trending_topics)
        
        # Determine randomly how many comments to generate (1-3)
        num_comments = random.randint(1, 3)
        
        prompt = f"""Create a tweet about this AI topic: "{topic}".
        
        Your response should include {num_comments + 2} parts, clearly separated:
        
        1. TWEET: A concise, engaging tweet (under 240 characters) that:
           - Is professional yet conversational
           - Includes relevant hashtags like #AI #MachineLearning
           - Focus only on the tweet text, no additional commentary
           - Has a call-to-action
           - Act as if you're speaking to a close friend about {topic}.
                Keep the tone friendly, light, and engaging. Use casual phrases like [good,bad,interesting,exciting,etc] 
                (‘Here's what I think...’) or [conversational phrase] (‘You won't believe this, but...’).
                Make sure the sentences are short and flow naturally, with relaxed connectors like [connector] 
                (‘So,’ 'Well,'). Add a few casual questions like [question] (‘What do you think?’ or 'Can you imagine that?’) 
                to keep the conversation interactive. Don't be afraid to use informal words to make the reader feel comfortable.
            - use appropriate images for the tweet and hyperlinks
            - must be like a human written tweet  
            - Be under 280 characters
    
              
        2. LINK: A specific, relevant URL to an article, research paper, or resource about this topic.
           The link should be a real, working URL (e.g., https://example.com/article).
        
        3. COMMENT1: A brief follow-up comment (under 200 characters) that could be posted as a reply to the tweet.
           This should add additional insight or ask an engaging question related to the topic.
        """
        
        # Add additional comment prompts based on the random number
        if num_comments >= 2:
            prompt += """
        4. COMMENT2: A second follow-up comment (under 200 characters) that adds more information or perspective.
           This should be different from the first comment but still related to the topic.
        """
        
        if num_comments >= 3:
            prompt += """
        5. COMMENT3: A third follow-up comment (under 200 characters) that concludes the thread with a call-to-action.
           This could ask for opinions, encourage sharing, or invite further discussion.
        """
        
        prompt += """
        Format your response exactly like this:
        TWEET: [your tweet text here]
        LINK: [your relevant URL here]
        COMMENT1: [your first follow-up comment here]
        """
        
        if num_comments >= 2:
            prompt += "COMMENT2: [your second follow-up comment here]\n"
        
        if num_comments >= 3:
            prompt += "COMMENT3: [your third follow-up comment here]\n"

        try:
            
            openai_key =  os.getenv("OPENAI_API_KEY")
            
            if not openai_key:
                logger.warning("OpenAI API key not found, using template-based generation")
                raise KeyError("OpenAI API key not found")
            
            import openai
            openai.api_key = openai_key

            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional AI social media manager with expertise in finding relevant resources."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,  # Increased for multiple comments
                temperature=0.7
            )
            
            # Extract the full response
            full_response = response.choices[0].message.content.strip()
            
            # Parse the response to extract tweet, link, and comments
            tweet_part = ""
            link_part = ""
            comments = []
            
            # Extract each part using simple string parsing
            lines = full_response.split('\n')
            for line in lines:
                if line.startswith("TWEET:"):
                    tweet_part = line.replace("TWEET:", "").strip()
                elif line.startswith("LINK:"):
                    link_part = line.replace("LINK:", "").strip()
                elif line.startswith("COMMENT1:"):
                    comments.append(line.replace("COMMENT1:", "").strip())
                elif line.startswith("COMMENT2:"):
                    comments.append(line.replace("COMMENT2:", "").strip())
                elif line.startswith("COMMENT3:"):
                    comments.append(line.replace("COMMENT3:", "").strip())
            
            # Validate the link (basic check)
            if not link_part.startswith("http"):
                link_part = "https://arxiv.org/abs/2303.08774"  # Fallback link
                logger.warning(f"Invalid link format: {link_part}. Using fallback link.")
            
            # Format the tweet with a natural call-to-action before the link
            if "check this" not in tweet_part.lower() and "check it out" not in tweet_part.lower() and "learn more" not in tweet_part.lower():
                # If the tweet doesn't already have a call-to-action, add one
                call_to_action_phrases = [
                    "Check this out: ",
                    "Learn more here: ",
                    "Read the full article: ",
                    "Dive deeper: ",
                    "More details here: ",
                    "Fascinating read: ",
                    "👉 ",
                    "Explore this: "
                ]
                call_to_action = random.choice(call_to_action_phrases)
                
                # Combine tweet and link, ensuring we're under the character limit
                max_tweet_length = 280 - len(call_to_action) - len(link_part) - 1  # -1 for space
                if len(tweet_part) > max_tweet_length:
                    tweet_part = tweet_part[:max_tweet_length-3] + "..."
                
                final_tweet = f"{tweet_part} {call_to_action}{link_part}"
            else:
                # If the tweet already has a call-to-action, just append the link
                max_tweet_length = 280 - len(link_part) - 1  # -1 for space
                if len(tweet_part) > max_tweet_length:
                    tweet_part = tweet_part[:max_tweet_length-3] + "..."
                
                final_tweet = f"{tweet_part} {link_part}"
            
            # Remove any quotes
            final_tweet = final_tweet.replace('"', '')
            
            # Ensure we have at least one comment
            if not comments:
                comments.append("What do you think about this? Let me know in the replies! 💬")
            
            return final_tweet, comments
            
        except Exception as e:
            logger.error(f"Error generating tweet with OpenAI: {str(e)}")
            # Fallback
            fallback_tweet = self._generate_template_tweet(topic)
            fallback_comments = ["What do you think about this? Let me know in the replies! 💬"]
            return fallback_tweet, fallback_comments

    def post_tweet_with_comments(self, content=None):
        """Post a tweet to Twitter and then post multiple follow-up comments."""
        if not content:
            tweet_content, comments = self.generate_tweet_with_link_and_comments()
        else:
            tweet_content = content
            comments = ["What are your thoughts on this? Let's discuss! 💬"]
        
        try:
            # Post the initial tweet using the v2 API
            tweet_response = self.client.create_tweet(text=tweet_content)
            tweet_id = tweet_response.data['id']
            logger.info(f"Tweet posted successfully: {tweet_content}")
            
            # Post each follow-up comment as a reply to the initial tweet
            comment_responses = []
            parent_id = tweet_id  # Start with the original tweet as parent
            
            for comment in comments:
                # Add a small delay between comments to make it look more natural
                time.sleep(random.uniform(5, 15))  # Random delay between 5-15 seconds
                
                comment_response = self.client.create_tweet(
                    text=comment,
                    in_reply_to_tweet_id=parent_id
                )
                comment_id = comment_response.data['id']
                logger.info(f"Follow-up comment posted successfully: {comment}")
                comment_responses.append(comment_response)
                
                # For a thread-like structure, make each comment a reply to the previous one
                # Uncomment the next line if you want comments to form a thread
                # parent_id = comment_id
            
            return tweet_response, comment_responses
        except Exception as e:
            logger.error(f"Failed to post tweet or comments: {str(e)}")
            return None, None
    
    def post_tweet(self, content=None):
        """Post a tweet to Twitter."""
        if not content:
            content = self.generate_tweet_with_link_and_comments()
        # print(content)
        # return
        try:
            # Corrected the call to post_tweet_v2
            tweet = self.post_tweet_v3(content)  # Removed 'self' from the call
            logger.info(f"Tweet posted successfully: {content}")
            return tweet
        except Exception as e:
            logger.error(f"Failed to post tweet: {str(e)}")
            return None
    
    def post_tweet_v3(self, content=None):
        """Post a tweet to Twitter."""
        if not content:
            content = self.generate_tweet_with_link_and_comments()
        
        try:
            # Corrected the call to post_tweet_v2
            response = self.client.create_tweet( text=content )
            logger.info(f"Tweet posted successfully: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to post tweet: {str(e)}")
            return None

    def schedule_tweets(self, frequency_hours=24):
        """
        Schedule tweets to be posted at regular intervals.
        
        Args:
            frequency_hours: Hours between tweets
        """
        logger.info(f"Starting scheduled tweets every {frequency_hours} hours")
        
        try:
            while True:
                # Get trending topics and generate tweet
                trending_topics = self.get_trending_ai_topics()
                topic = random.choice(trending_topics)
                tweet_content = self.generate_tweet_with_link_and_comments(topic)
                self.post_tweet(tweet_content)
                
                # Sleep for the specified number of hours
                time.sleep(frequency_hours * 3600)
        except KeyboardInterrupt:
            logger.info("Tweet scheduling stopped by user")
        except Exception as e:
            logger.error(f"Error in tweet scheduling: {str(e)}")

    def post_tweet_v2(self, content):
        """Post a tweet to Twitter using API v2."""
        url = "https://api.twitter.com/2/tweets"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "text": content
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 201:
            logger.info(f"Tweet posted successfully: {content}")
            return response.json()
        else:
            logger.error(f"Failed to post tweet: {response.status_code} - {response.text}")
            return None

    def generate_and_post_custom_tweet(self, custom_topic):
        """
        Generate and post a tweet about a custom topic provided by the user.
        
        Args:
            custom_topic (str): The topic to generate a tweet about
            
        Returns:
            tuple: The tweet response and comment responses
        """
        if not custom_topic or custom_topic.strip() == "":
            logger.warning("No custom topic provided. Using trending topics instead.")
            return self.post_tweet_with_comments()
        
        logger.info(f"Generating tweet about custom topic: {custom_topic}")
        
        # Determine randomly how many comments to generate (1-3)
        num_comments = random.randint(1, 3)
        
        prompt = f"""Create a tweet about this topic: "{custom_topic}".
        
        Your response should include {num_comments + 2} parts, clearly separated:
        
        1. TWEET: A concise, engaging tweet (under 240 characters) that:
           - Is professional yet conversational
           - Includes relevant hashtags
           - Has a call-to-action
           - Uses emojis appropriately
           - Sounds like you're speaking to a close friend (use phrases like "You won't believe this" or "Check this out")
           - Focuses specifically on the topic: "{custom_topic}"
        
        2. LINK: A specific, relevant URL to an article, research paper, or resource about this topic.
           The link should be a real, working URL (e.g., https://example.com/article).
        
        3. COMMENT1: A brief follow-up comment (under 200 characters) that could be posted as a reply to the tweet.
           This should add additional insight or ask an engaging question related to the topic.
        """
        
        # Add additional comment prompts based on the random number
        if num_comments >= 2:
            prompt += """
        4. COMMENT2: A second follow-up comment (under 200 characters) that adds more information or perspective.
           This should be different from the first comment but still related to the topic.
        """
        
        if num_comments >= 3:
            prompt += """
        5. COMMENT3: A third follow-up comment (under 200 characters) that concludes the thread with a call-to-action.
           This could ask for opinions, encourage sharing, or invite further discussion.
        """
        
        prompt += """
        Format your response exactly like this:
        TWEET: [your tweet text here]
        LINK: [your relevant URL here]
        COMMENT1: [your first follow-up comment here]
        """
        
        if num_comments >= 2:
            prompt += "COMMENT2: [your second follow-up comment here]\n"
        
        if num_comments >= 3:
            prompt += "COMMENT3: [your third follow-up comment here]\n"

        try:
            
            openai_key =  os.getenv("OPENAI_API_KEY")
            
            if not openai_key:
                logger.warning("OpenAI API key not found, using template-based generation")
                return self._generate_template_tweet(custom_topic)
            
            import openai
            openai.api_key = openai_key

            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional AI social media manager with expertise in finding relevant resources."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,  # Increased for multiple comments
                temperature=0.7
            )
            
            # Extract the full response
            full_response = response.choices[0].message.content.strip()
            
            # Parse the response to extract tweet, link, and comments
            tweet_part = ""
            link_part = ""
            comments = []
            
            # Extract each part using simple string parsing
            lines = full_response.split('\n')
            for line in lines:
                if line.startswith("TWEET:"):
                    tweet_part = line.replace("TWEET:", "").strip()
                elif line.startswith("LINK:"):
                    link_part = line.replace("LINK:", "").strip()
                elif line.startswith("COMMENT1:"):
                    comments.append(line.replace("COMMENT1:", "").strip())
                elif line.startswith("COMMENT2:"):
                    comments.append(line.replace("COMMENT2:", "").strip())
                elif line.startswith("COMMENT3:"):
                    comments.append(line.replace("COMMENT3:", "").strip())
            
            # Validate the link (basic check)
            if not link_part.startswith("http"):
                link_part = "https://arxiv.org/abs/2303.08774"  # Fallback link
                logger.warning(f"Invalid link format: {link_part}. Using fallback link.")
            
            # Format the tweet with a natural call-to-action before the link
            if "check this" not in tweet_part.lower() and "check it out" not in tweet_part.lower() and "learn more" not in tweet_part.lower():
                # If the tweet doesn't already have a call-to-action, add one
                call_to_action_phrases = [
                    "Check this out: ",
                    "Learn more here: ",
                    "Read the full article: ",
                    "Dive deeper: ",
                    "More details here: ",
                    "Fascinating read: ",
                    "👉 ",
                    "Explore this: "
                ]
                call_to_action = random.choice(call_to_action_phrases)
                
                # Combine tweet and link, ensuring we're under the character limit
                max_tweet_length = 280 - len(call_to_action) - len(link_part) - 1  # -1 for space
                if len(tweet_part) > max_tweet_length:
                    tweet_part = tweet_part[:max_tweet_length-3] + "..."
                
                final_tweet = f"{tweet_part} {call_to_action}{link_part}"
            else:
                # If the tweet already has a call-to-action, just append the link
                max_tweet_length = 280 - len(link_part) - 1  # -1 for space
                if len(tweet_part) > max_tweet_length:
                    tweet_part = tweet_part[:max_tweet_length-3] + "..."
                
                final_tweet = f"{tweet_part} {link_part}"
            
            # Remove any quotes
            final_tweet = final_tweet.replace('"', '')
            
            # Ensure we have at least one comment
            if not comments:
                comments.append("What do you think about this? Let me know in the replies! 💬")
            
            # Post the tweet and comments
            return self.post_tweet_with_comments_content(final_tweet, comments)
            
        except Exception as e:
            logger.error(f"Error generating custom tweet with OpenAI: {str(e)}")
            # Fallback
            fallback_tweet = f"Interesting thoughts on {custom_topic}. What's your take on this topic? #Discussion"
            fallback_comments = ["I'd love to hear your perspectives on this! Share your thoughts below. 💬"]
            return self.post_tweet_with_comments_content(fallback_tweet, fallback_comments)

    def post_tweet_with_comments_content(self, tweet_content, comments):
        """Post a specific tweet content to Twitter and then post the provided follow-up comments."""
        try:
            # Post the initial tweet using the v2 API
            tweet_response = self.client.create_tweet(text=tweet_content)
            tweet_id = tweet_response.data['id']
            logger.info(f"Tweet posted successfully: {tweet_content}")
            
            # Post each follow-up comment as a reply to the initial tweet
            comment_responses = []
            parent_id = tweet_id  # Start with the original tweet as parent
            
            for comment in comments:
                # Add a small delay between comments to make it look more natural
                time.sleep(random.uniform(5, 15))  # Random delay between 5-15 seconds
                
                comment_response = self.client.create_tweet(
                    text=comment,
                    in_reply_to_tweet_id=parent_id
                )
                comment_id = comment_response.data['id']
                logger.info(f"Follow-up comment posted successfully: {comment}")
                comment_responses.append(comment_response)
                
                # For a thread-like structure, make each comment a reply to the previous one
                # Uncomment the next line if you want comments to form a thread
                # parent_id = comment_id
            
            return tweet_response, comment_responses
        except Exception as e:
            logger.error(f"Failed to post tweet or comments: {str(e)}")
            return None, None


if __name__ == "__main__":
    # Load credentials from environment variables for security
    api_key =  os.getenv("TWITTER_API_KEY")
    api_secret =  os.getenv("TWITTER_API_SECRET")
    access_token =  os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret =  os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    bearer_token =  os.getenv("TWITTER_BEARER_TOKEN")
    
    
    # Check if credentials are available
    if not all([api_key, api_secret, access_token, access_token_secret]):
        logger.error("Twitter API credentials not found in environment variables")
        print("Please set the following environment variables:")
        print("TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET")
        exit(1)
    
    # Create and run the agent
    agent = TwitterAgent(api_key, api_secret, access_token, access_token_secret,bearer_token)
    
    # Example usage:
    # Post a single tweet about a trending AI topic
    
    # agent.post_tweet_with_comments()
    
    custom_topic = "MCP is an open protocol that standardizes how applications provide context to LLMs. Think of MCP like a USB-C port for AI applications."
    agent.generate_and_post_custom_tweet(custom_topic)
    
    # Or schedule regular tweets about trending AI topics
    # agent.schedule_tweets(frequency_hours=12)
