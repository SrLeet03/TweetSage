import os
import json
from agent import TwitterAgent

def lambda_handler(event, context):
    """
    AWS Lambda handler function to run the Twitter agent.
    
    Parameters:
    - event: Contains information from the event source
    - context: Contains information about the invocation, function, and execution environment
    
    Expected event format:
    {
        "task": "post_tweet_with_comments",
        "custom_topic": "Optional custom topic for the tweet"
    }
    """
    # Load credentials from environment variables
    api_key = os.environ.get("TWITTER_API_KEY")
    api_secret = os.environ.get("TWITTER_API_SECRET")
    access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
    
    # Check if credentials are available
    if not all([api_key, api_secret, access_token, access_token_secret, bearer_token]):
        return {
            'statusCode': 500,
            'body': json.dumps('Twitter API credentials not found in environment variables')
        }
    
    # Create the Twitter agent
    agent = TwitterAgent(api_key, api_secret, access_token, access_token_secret, bearer_token)
    
    # Get the task from the event
    task = event.get('task', 'post_tweet_with_comments')
    
    # Execute the requested task
    if task == 'post_tweet_with_comments':
        custom_topic = event.get('custom_topic')
        if custom_topic:
            tweet_response, comment_responses = agent.generate_and_post_custom_tweet(custom_topic)
        else:
            tweet_response, comment_responses = agent.post_tweet_with_comments()
        
        # Return the response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Tweet and comments posted successfully',
                'tweet_id': tweet_response.data['id'] if tweet_response else None,
                'comment_ids': [resp.data['id'] for resp in comment_responses] if comment_responses else []
            })
        }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps(f'Unknown task: {task}')
        } 