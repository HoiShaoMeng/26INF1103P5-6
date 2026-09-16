#P5-Group 6 Project Initial Details

## 1. Problem Statement and Target Users:

###Project title: Phishing / Suspicious email triage assistant

Small IT teams without a dedicated SOC (Security Operations Center) face a major bottleneck. General staff constantly report suspicious emails, but with limited manpower, often just a handful of staff supporting an entire organization, there’s no quick way to determine if each report is genuine phishing or just spam. Every reported email must be read and judged one at time by a small IT team. 

> **Real-World Context:**
We experienced this firsthand during an internship. Our IT team was small with just 4 of us, and we managed up to 80 staff. We used KnowBe4, which had a phishing report button that let staff flag suspicious emails easily. But once a report came in, someone still had to read through it to figure out the legitimacy. With limited manpower and so many reports coming in, the screening process could not keep up.

This delay leaves staff vulnerable, a real phishing attempt can be sitting in the queue behind spam emails for a while before anyone catches it, giving attackers more time to succeed.

### Project Objective
This application aims to reduce the manual effort required for screening emails by automatically analyzing reported emails, identifying red flags, and prioritizing reports based on their severity.

### Target users: Small IT teams without a dedicated SOC (e.g. a team of 3-5 IT staff supporting 80-100+ employees) that need help prioritizing which reports to act first.

## 2. User Inputs:
All relevant information about the reported email will be input:
-	Reporter’s name, date/time the email was reported
-	Suspected sender’s email address and display name
-	Email subject line
-	Email body text
-	Attachment filenames and file extensions [AJ1.1][TF1.2][TW1.3][HM1.4][HM1.5] 

## 3. Use of AI:
Each reported email subject body, and sender details are sent to an AI model which performs the core judgement a human analyst would have to make manually. The AI will return a structured (JSON) response[AX2.1][TW2.2][HM2.3][AX2.4] containing:
-	A classification: phishing / spear-phishing / spam / benign[TW3.1][HM3.2]
-	A threat level score (0-100, with higher scores indicating higher severity)
-	Any suspicious cues identified in the body
-	Whether the sender’s claimed identity matches their domain
-	A short rationale explaining the assessment 

## 4. Business Rules:
Once AI gives back its analysis, we will run it through a set of fixed rules to decide how serious each report is. 
If the AI is at least 80% threat level and[AX4.1][HM4.2][AX4.3][HM4.4] picked up impersonation tactics and the sender domain does not match who they are claiming to be, we mark it CRITICAL. We also mark something critical straight away if it detects credential harvesting tactics together with suspicious links or attachments even if the threat level score is not that high.
If threat level is somewhere between 50-79, it goes into NEEDS REVIEW. This means email is not clearly dangerous but one we cannot just ignore either and will need further action from the IT team.
Anything below 50 threat level gets logged, most likely being a false alarm, we can just keep a record.
In addition, we can check for patterns across reports. If we find 3 or more coming from the same sender or domain within a defined time window, such as 24 hours.[AJ5.1][TW5.2][HM5.3][HM5.4][TW5.5] We will instantly treat all their emails as CRITICAL regardless of threat level because this usually means it's a coordinated attack, not a false report.

### Severity Action Matrix
Each severity level also comes with an action attached:
Severity | Threat Level | Recommended Action
CRITICAL | ≥ 80	| We block the sender’s domain and alert everyone right away
NEEDS REVIEW |	50 - 79 |	IT team must manually check it within 24 hours
LOG ONLY |	< 50 |	LOG ONLY just gets archived, no action needed.



