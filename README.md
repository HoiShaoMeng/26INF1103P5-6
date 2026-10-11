# 26INF1103P5-6
Group 6's project repository for module INF1103

## Problem Statement and Target Users: 

### Project title: Phishing / Suspicious email triage assistant 
 

Small IT teams without a dedicated SOC (Security Operations Center) face a major bottleneck. General staff constantly report suspicious emails, but with limited manpower, often just a handful of staff supporting an entire organization, there’s no quick way to determine if each report is genuine phishing or just spam. Every reported email must be read and judged one at time by a small IT team.  


We experienced this firsthand during an internship. Our IT team was small with just 4 of us, and we managed up to 80 staff. We used KnowBe4, which had a phishing report button that let staff flag suspicious emails easily. But once a report came in, someone still had to read through it to figure out the legitimacy. With limited manpower and so many reports coming in, the screening process could not keep up. 


This delay leaves staff vulnerable, a real phishing attempt can be sitting in the queue behind spam emails for a while before anyone catches it, giving attackers more time to succeed. 


### Target users: Small IT teams without a dedicated SOC (e.g. a team of 3-5 IT staff supporting 80-100+ employees) that need help prioritizing which reports to act first. 

## Features


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