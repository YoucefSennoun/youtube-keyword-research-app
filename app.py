from flask import Flask, request, jsonify, render_template
import pandas as pd
import youtube_keyword_research_tool
import logging
import traceback
import os # Import os to access environment variables
from googleapiclient.errors import HttpError 

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

app = Flask(__name__)

# Initialize the tool
tool = None
try:
    # Get API_KEY from environment variable, fall back to None if not set
    # The youtube_keyword_research_tool will then use its own default or rely on scraping.
    api_key_from_env = os.environ.get('API_KEY')
    if api_key_from_env:
        logging.info("Using YouTube API key from environment variable.")
    else:
        logging.warning("YouTube API key not found in environment variables. Tool will use default or rely on scraping.")

    tool = youtube_keyword_research_tool.YouTubeKeywordResearchTool(api_key=api_key_from_env)
except Exception as e:
    logging.error(f"Error initializing YouTubeKeywordResearchTool: {e}")
    logging.error(traceback.format_exc())

@app.route('/')
def index():
    """Renders the main HTML page for the YouTube keyword research tool."""
    return render_template('youtube-keyword-research-frontend.html')

@app.route('/analyze', methods=['POST'])
def analyze_keywords():
    """
    Handles the POST request from the frontend to analyze keywords.
    It takes a seed keyword, depth, and max results, then uses the
    YouTubeKeywordResearchTool to find and return keyword opportunities.
    """
    if tool is None:
        logging.error("Keyword analysis tool not initialized. Cannot process request.")
        return jsonify({'error': 'Keyword analysis tool is not available. Please check server logs.'}), 503 # Service Unavailable

    try:
        data = request.get_json()
        if not data:
            logging.warning("No JSON data received in POST request.")
            return jsonify({'error': 'Invalid request: No JSON data provided.'}), 400
        
        logging.debug(f"Received data from frontend: {data}")
        seed_keyword = data.get('keyword')
        
        if not seed_keyword or not isinstance(seed_keyword, str) or not seed_keyword.strip():
            logging.warning("Keyword is required but not provided or invalid.")
            return jsonify({'error': 'Keyword is required and must be a non-empty string.'}), 400

        try:
            depth = int(data.get('depth', 2))
            max_results = int(data.get('maxResults', 20))
            if not (0 < depth <= 5 and 0 < max_results <= 100): # Add reasonable limits
                logging.warning(f"Invalid depth or maxResults: depth={depth}, max_results={max_results}")
                return jsonify({'error': 'Depth (1-5) or Max Results (1-100) out of range.'}), 400
        except ValueError:
            logging.warning("Invalid depth or maxResults value (not an integer).")
            return jsonify({'error': 'Depth and Max Results must be integers.'}), 400

        results_df = tool.find_opportunities(seed_keyword.strip(), depth, max_results)
        
        if results_df is None or results_df.empty:
            logging.info(f"No opportunities found or error during analysis for keyword: {seed_keyword}")
            results_list = [] 
        else:
            logging.debug(f"Results DataFrame for '{seed_keyword}': \n{results_df}")
            results_list = results_df.to_dict(orient='records')
            logging.debug(f"Results List for '{seed_keyword}': \n{results_list}")

        return jsonify(results_list)

    except HttpError as he_custom: 
        logging.error(f"A specific HttpError occurred during analysis: {he_custom}")
        logging.error(traceback.format_exc())
        return jsonify({'error': f'A service error occurred: {he_custom}'}), 500
    except Exception as e:
        logging.error(f"Unexpected error during analysis: {e}")
        logging.error(traceback.format_exc())
        return jsonify({'error': f'An unexpected error occurred on the server.'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
