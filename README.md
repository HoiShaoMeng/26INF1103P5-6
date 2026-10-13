# 26INF1103P5-6
Group 6's project repository for module INF1103

## Problem Statement and Target Users: 

### Project title: Phishing / Suspicious email triage assistant 
 

Small IT teams without a dedicated SOC (Security Operations Center) face a major bottleneck. General staff constantly report suspicious emails, but with limited manpower, often just a handful of staff supporting an entire organization, there’s no quick way to determine if each report is genuine phishing or just spam. Every reported email must be read and judged one at a time by a small IT team.  


We experienced this firsthand during an internship. Our IT team was small with just 4 of us, and we managed up to 80 staff. We used KnowBe4, which had a phishing report button that let staff flag suspicious emails easily. But once a report came in, someone still had to read through it to figure out the legitimacy. With limited manpower and so many reports coming in, the screening process could not keep up. 


This delay leaves staff vulnerable, a real phishing attempt can be sitting in the queue behind spam emails for a while before anyone catches it, giving attackers more time to succeed. 


### Target users: Small IT teams without a dedicated SOC (e.g. a team of 3-5 IT staff supporting 80-100+ employees) that need help prioritizing which reports to act first. 

## Features
- Email report collection and validation
  - Prompts the user to enter key email details such as sender, subject, body text, URLs, and attachments
  - Validates the input to reduce errors before analysis
  - Supports multi-line email bodies and optional attachment or URL collection

- AI-powered phishing classification
  - Sends the reported email to an external AI model through OpenRouter
  - Builds a structured prompt using YAML configuration file
  - Validates the AI response by checking if it matches the expected schema
  - Returns safe fallback result if the AI cannot assess the email

- Threat assessment and prioritisation
  - Evaluates the AI's classification, threat level, suspicious URLs, suspicious attachments, and sender-domain mismatch
  - Determines whether the report is low risk, needs review, or is critical

- Campaign detection
  - Identifies whether multiple suspicious reports are connected by sender or domain within 24-hour window
  - Treats repeated reports from the same sender or domain as a possible coordinated attack

- Severity-based triage
  - Classifies each report as:
    - LOG_ONLY
    - NEEDS_REVIEW
    - CRITICAL
  - Escalates severity when multiple suspicious indicators are present

- Recommended response actions
  - Produces action guidance for each severity level, such as blocking a domain, escalating for manual review, or archiving the report
  - Helps IT staff quickly decide the next step and what to prioritize

- Persistent reporting history
  - Saves all processed reports to a local JSON history file
  - Allows previously submitted emails to be reviewed later
  - Supports filtering by severity and sorting by threat level

- Report review menu
  - Lets users:
    - Screen a new suspicious email,
    - View saved reports grouped by severity
    - Review the most urgent cases first

## Setup

### Prerequisites
- Git 
- Docker Desktop or Docker Engine
- A personal OpenRouter API key (Create one at https://openrouter.ai/keys)

### 1. Clone and configure
```bash
git clone https://github.com/HoiShaoMeng/26INF1103P5-6.git
cd 26INF1103P5-6
cp .env.example .env
```
Open `.env` and add your key, with no spaces around `=` and no quotes:
```
OPENROUTER_API_KEY=sk-or-v1-yourkeyhere
```
On Windows, save `.env` as UTF-8 (not "with BOM") with LF line endings, or Docker
won't read the key.

### 2. Build
```bash
docker build -t phishing-triage .
```

### 3. Run
```bash
docker run -it --rm --env-file .env -v ./data:/app/data phishing-triage
```
- `-it` lets you type into the program
- `-v ./data:/app/data` saves reports to `data/` on your machine, so history is kept
  between runs

On Windows PowerShell, use `-v ${PWD}/data:/app/data` if `./data` gives an error.