YouTube Keyword Research App
This guide provides comprehensive instructions on how to access and run the YouTube Keyword Research App, both as an online service and locally on your personal computer.

Online Version
You can access and use the YouTube Keyword Research App directly through your web browser by visiting the following link:

https://youtube-keyword-research-app.onrender.com

Running the Application Locally
This section details the steps required to set up and run the YouTube Keyword Research application on your local machine.

1. Prepare Your Files
Before you begin, ensure that all the necessary application files are located together in a single directory (folder) on your computer. The required files are:

app.py

youtube_keyword_research_tool.py

youtube-keyword-research-frontend.html

requirements.txt

Procfile

2. Install Python
If you do not already have Python installed on your system, please download and install it. Python version 3.7 or newer is highly recommended for compatibility and performance.

You can download Python from its official website:
https://www.python.org/downloads/

3. Set Up a Virtual Environment (Recommended)
Utilizing a virtual environment is a best practice for Python projects. It helps to isolate your project's dependencies, preventing conflicts with other Python projects or system-wide installations.

Open your Terminal or Command Prompt:

On Windows: Search for "Command Prompt" or "PowerShell" in the Start Menu.

On macOS/Linux: Open the "Terminal" application.

Navigate to your project directory:
Use the cd command to change your current directory to where you have placed the application files.

Example for Windows: cd C:\Users\YourUser\Documents\YouTubeApp

Example for macOS/Linux: cd ~/Documents/YouTubeApp

Create the virtual environment:
Execute the following command to create a new virtual environment named venv within your project directory:

python -m venv venv

Activate the virtual environment:

On Windows:

.\venv\Scripts\activate

On macOS/Linux:

source venv/bin/activate

If you encounter a security-related issue when activating the virtual environment on Windows PowerShell, please refer to the "Troubleshooting Windows PowerShell Execution Policy" section located at the end of this guide for a solution.

4. Install Dependencies
With your virtual environment successfully activated, proceed to install all the required Python libraries. These libraries are listed in the requirements.txt file.

pip install -r requirements.txt

5. Set Your YouTube API Key (Optional but Recommended)
To ensure the best performance and to leverage the official YouTube Data API (instead of relying on less reliable web scraping methods), it is highly recommended to set your YouTube Data API v3 key as an environment variable.

Replace YOUR_YOUTUBE_API_KEY with your actual API key.

On Windows (Command Prompt):

set API_KEY=YOUR_YOUTUBE_API_KEY

On Windows (PowerShell):

$env:API_KEY="YOUR_YOUTUBE_API_KEY"

On macOS/Linux:

export API_KEY=YOUR_YOUTUBE_API_KEY

Note: Environment variables set this way are typically temporary and only persist for the current terminal session. For a more permanent solution, you might consider adding the API key to your system's environment variables or to your shell's configuration file (e.g., .bashrc or .zshrc).

6. Run the Application
In the same terminal window where your virtual environment is active and you have set the API key (if applicable), execute the main application file:

python app.py

7. Access the App in Your Browser
Once app.py starts, your terminal will display a message indicating the address where the application is running (e.g., Running on http://127.0.0.1:5000/).

Open this address in your preferred web browser. You should then see the frontend interface of the YouTube Keyword Research Tool.

Troubleshooting Windows PowerShell Execution Policy
If you are using Windows PowerShell and encounter a security error when trying to activate your virtual environment (e.g., .\venv\Scripts\activate), it is likely due to PowerShell's "Execution Policy." By default, PowerShell often restricts the execution of local scripts to enhance system security.

To resolve this, you need to temporarily modify your PowerShell's execution policy. Follow these steps:

Open PowerShell as Administrator:

Search for "PowerShell" in the Windows Start Menu.

Right-click on "Windows PowerShell" (or "PowerShell") from the search results.

Select "Run as administrator." If a User Account Control (UAC) prompt appears, confirm it.

Change the Execution Policy:
In the Administrator PowerShell window, type the following command and press Enter:

Set-ExecutionPolicy RemoteSigned

You will be prompted to confirm this change. Type Y and press Enter.

Close the Administrator PowerShell window.

Open a NEW, REGULAR PowerShell window (or Command Prompt) and try again:

Return to your project directory in a standard (non-admin) PowerShell window or Command Prompt.

Attempt to activate your virtual environment once more:

.\venv\Scripts\activate

This time, your virtual environment should activate successfully. The RemoteSigned policy is generally a good balance for development, allowing your locally created scripts to run while still requiring scripts downloaded from the internet to be digitally signed.

Should you wish to revert the execution policy later, you can set it back to Restricted (the default for some systems) or Default by running Set-ExecutionPolicy Restricted or Set-ExecutionPolicy Default in an administrator PowerShell window.
