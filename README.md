![image](https://github.com/user-attachments/assets/40cb2c82-0fab-4f21-a452-ed7b304c8a4e)

![image](https://github.com/user-attachments/assets/696ebf36-03e1-407c-90eb-251011ffb334)


online : visit this link to use it online \[https://youtube-keyword-research-app.onrender.com\](https://youtube-keyword-research-app.onrender.com)

locally :

How to Run YouTube Keyword Research App Locally This guide will help you set up and run the YouTube Keyword Research application on your local PC.

1\. Prepare Your Files Ensure all the necessary application files are in the same directory (folder) on your computer. You should have these files:

app.py youtube\\keyword\\research\\tool.py youtube-keyword-research-frontend.html requirements.txt Procfile

2\. Install Python If you don't already have it, download and install Python. Version 3.7 or newer is recommended.

Download from: \[https://www.python.org/downloads/\](https://www.python.org/downloads/)

3\. Set Up a Virtual Environment (Recommended) Using a virtual environment keeps your project dependencies separate from other Python projects.

Open your Terminal or Command Prompt: On Windows: Search for "Command Prompt" or "PowerShell". On macOS/Linux: Open "Terminal". Navigate to your project directory: Use the cd command (e.g., cd C:\\\\Users\\\\YourUser\\\\Documents\\\\YouTubeApp or cd /Documents/YouTubeApp). Create the virtual environment: python -m venv venv Activate the virtual environment: On Windows: .\\\\venv\\\\Scripts\\\\activate On macOS/Linux: source venv/bin/activate

if you face security problem scroll down in this page to read the solution

4\. Install Dependencies While your virtual environment is active, install all the required Python libraries listed in requirements.txt.

pip install -r requirements.txt

5\. Set Your YouTube API Key (Optional but Recommended) For the best performance and to utilize the YouTube Data API instead of web scraping, set your API key as an environment variable. If you don't set it, the tool will fall back to less reliable scraping methods.

Replace YOUR\\YOUTUBE\\API\\KEY with your actual YouTube Data API v3 key.

On Windows (Command Prompt): set API\\KEY=YOUR\\YOUTUBE\\API\\KEY On Windows (PowerShell): $env:API\\KEY="YOUR\\YOUTUBE\\API\\KEY" On macOS/Linux: export API\\KEY=YOUR\\YOUTUBE\\API\\KEY Note: This setting is usually temporary for the current terminal session. For a more permanent solution, you might add it to your system's environment variables or your shell's configuration file (e.g., .bashrc or .zshrc).

6\. Run the Application In the same terminal where your virtual environment is active and you've set the API key (if applicable), run the main application file:

python app.py

7\. Access the App in Your Browser Once app.py starts, you will see a message in the terminal indicating where the app is running (e.g., Running on \[http://127.0.0.1:5000/\](http://127.0.0.1:5000/)).

Open that address in your web browser, and you should see the frontend of the YouTube Keyword Research Tool.

if you're encountering a common security feature in Windows PowerShell called "Execution Policy." By default, PowerShell often prevents running local scripts (like the activate.ps1 script for your virtual environment) to protect your system from malicious scripts.

To fix this, you need to change your PowerShell's execution policy. Here's how you can do it:

Open PowerShell as Administrator:

Search for "PowerShell" in the Windows Start Menu. Right-click on "Windows PowerShell" (or "PowerShell") and select "Run as administrator." Confirm the User Account Control (UAC) prompt if it appears. Change the Execution Policy:

In the Administrator PowerShell window, type the following command and press Enter:

Set-ExecutionPolicy RemoteSigned

You will be asked to confirm the change. Type Y and press Enter. Close the Administrator PowerShell window.

Open a NEW, REGULAR PowerShell window (or Command Prompt) and try again:

Go back to your project directory in a regular (non-admin) PowerShell window or Command Prompt. Now, try activating your virtual environment again: PowerShell

.\\\\venv\\\\Scripts\\\\activate This should now activate your virtual environment successfully. The RemoteSigned policy is generally a good balance for development, as it allows your local scripts to run while still requiring scripts downloaded from the internet to be digitally signed.

If you ever want to revert the policy later, you can set it back to Restricted (the default for some systems) or Default by running Set-ExecutionPolicy Restricted or Set-ExecutionPolicy Default in an administrator PowerShell window.
