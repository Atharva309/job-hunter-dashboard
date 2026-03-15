# Job Hunter Agent

A job search assistant for Atharva Patil that automatically scrapes career pages and uses Claude API to find matching entry-level jobs with visa sponsorship potential.

## Setup Instructions

1. **Install Dependencies:**
   Install the required Python packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API Key:**
   Export your Anthropic API key as an environment variable:
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   ```
   *(For Windows Command Prompt, use `set ANTHROPIC_API_KEY=sk-ant-...`)*

3. **Prepare the Excel Tracker:**
   Run the `job_agent.py` script once. It will create `job_tracker.xlsx`. Open it and fill in the "Company Name" and "Career Page URL" in columns A and B for the companies you want to track.
   Alternatively, create it manually with the specific columns, or run the script and let it initialize an empty file, then fill it.

4. **Add Your Portfolio:**
   Place your portfolio PDF file in this directory and name it precisely `portfolio.pdf`.

5. **Run the Agent:**
   Execute the agent script:
   ```bash
   python job_agent.py
   ```
   The agent will read the companies, scrape their career portals, read the PDF, query Claude to extract matching jobs based on Atharva's F1 student profile and tech stack, and append the results back to `job_tracker.xlsx`.

## Output Behavior
- "No matches found" will be listed if zero valid roles exist.
- Progress will be printed directly to the console.
- In case of multiple job matches for the same company, the agent will insert new rows below the original company entry to accommodate the extra matches.
