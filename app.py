from flask import Flask, request, jsonify, render_template
import pandas as pd
import youtube_keyword_research_tool
import logging
import traceback
# import ssl  # Removed the import for ssl as the bypass is removed
from googleapiclient.errors import HttpError # Import HttpError explicitly

# Removed the SSL bypass code block as it's often the cause of such issues
# if hasattr(ssl, '_create_unverified_context'):
#     try:
#         ssl._create_default_https_context = ssl._create_unverified_context
#         logging.warning("SSL certificate verification bypassed. This is insecure and not for production.")
#     except Exception as e:
#         logging.error(f"Could not bypass SSL verification: {e}")

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

app = Flask(__name__)

# Initialize the tool. Consider loading API_KEY from environment variable or config file.
API_KEY = "AIzaSyCvHOl7FIlDBp3wWnm_AccbrqD4JRSdKv4"  # Replace with your API key or manage securely
tool = None
try:
    tool = youtube_keyword_research_tool.YouTubeKeywordResearchTool(api_key=API_KEY)
except Exception as e:
    logging.error(f"Error initializing YouTubeKeywordResearchTool: {e}")
    logging.error(traceback.format_exc())
    # The application can still run, but /analyze will fail until tool is fixed.

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
            # Check if specific error columns exist from tool, otherwise send empty list
            # For now, sending empty list if no results which frontend handles.
            results_list = [] 
        else:
            logging.debug(f"Results DataFrame for '{seed_keyword}': \n{results_df}")
            results_list = results_df.to_dict(orient='records')
            logging.debug(f"Results List for '{seed_keyword}': \n{results_list}")

        return jsonify(results_list)

    except HttpError as he_custom: # Assuming HttpError is a custom or specific error tool might raise
        logging.error(f"A specific HttpError occurred during analysis: {he_custom}")
        logging.error(traceback.format_exc())
        return jsonify({'error': f'A service error occurred: {he_custom}'}), 500 # Or a more specific code
    except Exception as e:
        logging.error(f"Unexpected error during analysis: {e}")
        logging.error(traceback.format_exc())
        return jsonify({'error': f'An unexpected error occurred on the server.'}), 500

if __name__ == "__main__":
    # For development, debug=True is fine. For production, use a proper WSGI server like Gunicorn.
    # Host '0.0.0.0' makes it accessible on your network, ensure firewall allows if needed.
    app.run(host='0.0.0.0', port=5000, debug=True)
