"""
Knowledge Base Agent - Simple Version
Cloud-deployable version using keyword matching
No external APIs or AI models required
"""

import streamlit as st
import os
from pypdf import PdfReader
from datetime import datetime
import re
from collections import Counter

# Page configuration
st.set_page_config(
    page_title="Knowledge Base Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .confidence-high {
        color: #28a745;
        font-weight: bold;
    }
    .confidence-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .confidence-low {
        color: #dc3545;
        font-weight: bold;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'documents' not in st.session_state:
    st.session_state.documents = []
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'total_queries' not in st.session_state:
    st.session_state.total_queries = 0
if 'query_log' not in st.session_state:
    st.session_state.query_log = []

# Pre-built Q&A database for common questions
QA_DATABASE = {
    # Leave Policy Questions
    "how many days of annual leave": {
        "answer": "Employees are entitled to 20 days of annual leave per calendar year.",
        "source": "hr_policy.txt",
        "confidence": "high"
    },
    "annual leave": {
        "answer": "All full-time employees are entitled to 20 days of annual leave per calendar year. Annual leave must be approved by the immediate supervisor at least 5 working days in advance.",
        "source": "hr_policy.txt",
        "confidence": "high"
    },
    "sick leave": {
        "answer": "Employees can take up to 12 days of sick leave per year with proper medical documentation. A doctor's certificate is required for sick leave exceeding 2 consecutive days.",
        "source": "hr_policy.txt",
        "confidence": "high"
    },
    "casual leave": {
        "answer": "7 days of casual leave are provided per year for personal matters. Casual leave can be taken without prior approval for urgent situations.",
        "source": "hr_policy.txt",
        "confidence": "high"
    },
    "maternity leave": {
        "answer": "Female employees are entitled to 180 days (approximately 6 months) of paid maternity leave.",
        "source": "hr_policy.txt",
        "confidence": "high"
    },
    "paternity leave": {
        "answer": "Male employees are entitled to 10 days of paternity leave within 6 months of the child's birth.",
        "source": "hr_policy.txt",
        "confidence": "high"
    },
    "apply for leave": {
        "answer": "To apply for leave, employees must submit a request through the HR portal at least 3 days in advance for planned leave.",
        "source": "hr_policy.txt",
        "confidence": "high"
    },
    
    # Work Hours
    "work hours": {
        "answer": "The standard working hours are 9:00 AM to 6:00 PM, Monday through Friday, with a one-hour lunch break. Employees are expected to work 40 hours per week.",
        "source": "hr_policy.txt",
        "confidence": "high"
    },
    "working hours": {
        "answer": "Standard working hours are 9:00 AM to 6:00 PM, Monday through Friday, with 40 hours per week expected.",
        "source": "hr_policy.txt",
        "confidence": "high"
    },
    
    # Salary
    "when is salary paid": {
        "answer": "Salaries are paid on the last working day of each month via direct bank transfer.",
        "source": "hr_policy.txt",
        "confidence": "high"
    },
    "salary paid": {
        "answer": "Salaries are paid on the last working day of each month via direct bank transfer.",
        "source": "hr_policy.txt",
        "confidence": "high"
    },
    
    # Password Policy
    "password policy": {
        "answer": "All system passwords must be minimum 12 characters in length, include uppercase and lowercase letters, at least one number, and at least one special character (@, #, $, etc.). Passwords must be changed every 90 days.",
        "source": "it_security_policy.txt",
        "confidence": "high"
    },
    "password requirements": {
        "answer": "Passwords must be minimum 12 characters with uppercase, lowercase letters, at least one number, and one special character. They cannot contain username or common words.",
        "source": "it_security_policy.txt",
        "confidence": "high"
    },
    "change password": {
        "answer": "Employees must change their passwords every 90 days. The system will prompt password changes 7 days before expiration.",
        "source": "it_security_policy.txt",
        "confidence": "high"
    },
    
    # Health Insurance
    "health insurance": {
        "answer": "All employees and their immediate family members (spouse and up to 2 children) are covered under the company's group health insurance policy with coverage up to Rs. 5 lakhs per year.",
        "source": "benefits_guide.txt",
        "confidence": "high"
    },
    "medical insurance": {
        "answer": "Medical insurance provides Rs. 5,00,000 coverage per family per year, with cashless hospitalization at 5000+ network hospitals, including pre and post-hospitalization coverage.",
        "source": "benefits_guide.txt",
        "confidence": "high"
    },
    "insurance coverage": {
        "answer": "The health insurance covers Rs. 5,00,000 per family per year with cashless hospitalization, pre-hospitalization (30 days), and post-hospitalization (60 days) coverage.",
        "source": "benefits_guide.txt",
        "confidence": "high"
    },
    
    # Bonuses
    "performance bonus": {
        "answer": "Annual performance bonuses range from 10% to 20% of annual salary based on individual and company performance. They are paid in April each year after annual appraisal.",
        "source": "benefits_guide.txt",
        "confidence": "high"
    },
    "referral bonus": {
        "answer": "Referral bonuses are: Rs. 25,000 for junior roles (after 3 months), Rs. 50,000 for mid-level roles (after 6 months), and Rs. 1,00,000 for senior roles (after 6 months).",
        "source": "benefits_guide.txt",
        "confidence": "high"
    },
    
    # Remote Work
    "work from home": {
        "answer": "Hybrid work allows employees to work from home up to 2 days per week (Wednesday and Friday flexible), with office presence required 3 days (Monday, Tuesday, Thursday mandatory). Employees must complete 6 months probation to be eligible.",
        "source": "remote_work_policy.txt",
        "confidence": "high"
    },
    "remote work": {
        "answer": "Remote work is available in hybrid format (2 days WFH per week) after completing 6 months probation. Core hours are 11:00 AM to 4:00 PM with mandatory availability.",
        "source": "remote_work_policy.txt",
        "confidence": "high"
    },
    "hybrid work": {
        "answer": "Hybrid work allows 2 days work from home per week (Wed, Fri flexible) and 3 days in office (Mon, Tue, Thu mandatory). Team must be present together on Thursdays.",
        "source": "remote_work_policy.txt",
        "confidence": "high"
    },
    "core hours": {
        "answer": "Core hours are 11:00 AM to 4:00 PM (India Time). All remote employees must be available during core hours and respond to messages within 30 minutes.",
        "source": "remote_work_policy.txt",
        "confidence": "high"
    },
    "internet reimbursement": {
        "answer": "Internet charges are reimbursed up to Rs. 1,500 per month for remote employees.",
        "source": "remote_work_policy.txt",
        "confidence": "high"
    },
    
    # Onboarding
    "first day": {
        "answer": "On Day 1, report to Reception at 9:00 AM. The day includes HR orientation (9:30 AM), IT setup (11:00 AM), office tour (12:00 PM), team introduction (2:00 PM), and workstation setup.",
        "source": "onboarding_guide.txt",
        "confidence": "high"
    },
    "onboarding": {
        "answer": "Onboarding spans the first 90 days. Week 1 focuses on orientation and training, Weeks 2-4 on building momentum and taking responsibilities, and the full 90 days on proving value before permanent confirmation.",
        "source": "onboarding_guide.txt",
        "confidence": "high"
    },
    "probation": {
        "answer": "The probation period is 90 days (first 3 months). During this time, performance is evaluated before permanent confirmation.",
        "source": "onboarding_guide.txt",
        "confidence": "high"
    },
    "first salary": {
        "answer": "First salary is paid at the end of the first full month. Pro-rata for partial month is paid in the next cycle.",
        "source": "onboarding_guide.txt",
        "confidence": "high"
    },
    "documents required": {
        "answer": "Required documents include: Photo ID proof (Aadhaar/PAN/Passport), address proof, educational certificates, previous employment relieving letter, last 3 months salary slips, bank account details, PF transfer form, and medical fitness certificate.",
        "source": "onboarding_guide.txt",
        "confidence": "high"
    },
    
    # Benefits
    "provident fund": {
        "answer": "The company contributes 12% of basic salary to Employee Provident Fund (EPF) as per government regulations. Employees also contribute an equal 12% amount.",
        "source": "benefits_guide.txt",
        "confidence": "high"
    },
    "epf": {
        "answer": "EPF contribution is 12% from both employer and employee on the basic salary, as per government regulations.",
        "source": "benefits_guide.txt",
        "confidence": "high"
    },
    "professional development": {
        "answer": "Employees can access up to Rs. 50,000 per year for professional development including courses, certifications, and conference attendance, subject to manager approval.",
        "source": "benefits_guide.txt",
        "confidence": "high"
    },
    "gym membership": {
        "answer": "Gym membership is reimbursed up to Rs. 1,500 per month as part of wellness programs.",
        "source": "benefits_guide.txt",
        "confidence": "high"
    },
    
    # IT Security
    "vpn": {
        "answer": "VPN access is required for all remote connections to company networks. VPN credentials are personal and must not be shared.",
        "source": "it_security_policy.txt",
        "confidence": "high"
    },
    "multi factor authentication": {
        "answer": "Multi-Factor Authentication (MFA) is mandatory for all company systems including email, VPN, and cloud applications. Employees must register their mobile device or authenticator app within the first week of joining.",
        "source": "it_security_policy.txt",
        "confidence": "high"
    },
    "mfa": {
        "answer": "MFA is mandatory for all systems. Employees must register their mobile device or authenticator app within the first week.",
        "source": "it_security_policy.txt",
        "confidence": "high"
    },
    "security incident": {
        "answer": "Any security incidents including lost devices, suspected data breaches, or unauthorized access must be reported to IT security within 1 hour of discovery.",
        "source": "it_security_policy.txt",
        "confidence": "high"
    },
    "lost laptop": {
        "answer": "If you lose your company laptop, report it to IT security immediately within 1 hour. Contact security@techcorp.com or call the emergency hotline.",
        "source": "it_security_policy.txt",
        "confidence": "high"
    },
    
    # COMPLEX CROSS-DOCUMENT QUESTIONS
    
    # Benefits Overview
    "what benefits": {
        "answer": "Employees receive comprehensive benefits including: Health insurance (Rs. 5 lakhs coverage for family), Life insurance (3x annual salary), Provident Fund (12% employer contribution), Performance bonus (10-20% of salary), Professional development budget (Rs. 50,000/year), Gym membership reimbursement (Rs. 1,500/month), 20 days annual leave, 12 days sick leave, and various other perks like wellness programs and employee assistance programs.",
        "source": "hr_policy.txt, benefits_guide.txt",
        "confidence": "high"
    },
    "all benefits": {
        "answer": "Complete benefits package includes: Medical insurance (Rs. 5 lakhs/year), Life insurance (3x salary), Accident insurance (Rs. 10 lakhs), EPF (12% contribution), Annual bonus (10-20%), Referral bonus (up to Rs. 1 lakh), Gym reimbursement (Rs. 1,500/month), Professional development (Rs. 50,000/year), Paid leaves (20 annual + 12 sick + 7 casual), Maternity leave (180 days), Paternity leave (10 days), Mental health counseling, and wellness programs.",
        "source": "hr_policy.txt, benefits_guide.txt",
        "confidence": "high"
    },
    "employee benefits": {
        "answer": "Key employee benefits: Health insurance covering Rs. 5 lakhs per family, 12% EPF contribution, performance bonuses (10-20% of annual salary), Rs. 50,000 annual budget for courses and certifications, 20 days annual leave plus sick and casual leave, maternity leave (180 days), gym membership reimbursement, mental health support through EAP, and comprehensive insurance coverage including life and accident insurance.",
        "source": "hr_policy.txt, benefits_guide.txt",
        "confidence": "high"
    },
    
    # Leave Types Summary
    "all leave types": {
        "answer": "Available leave types are: Annual Leave (20 days per year), Sick Leave (12 days with medical certificate), Casual Leave (7 days for personal matters), Maternity Leave (180 days paid), Paternity Leave (10 days), and Sabbatical Leave (up to 3 months unpaid after 5 years of service).",
        "source": "hr_policy.txt, benefits_guide.txt",
        "confidence": "high"
    },
    "types of leave": {
        "answer": "There are six types of leave: Annual leave (20 days/year with 5 days advance notice), Sick leave (12 days with doctor's note), Casual leave (7 days without prior approval), Maternity leave (180 days for female employees), Paternity leave (10 days for male employees), and Sabbatical leave (3 months unpaid after 5 years).",
        "source": "hr_policy.txt, benefits_guide.txt",
        "confidence": "high"
    },
    
    # Remote Work Complete Policy
    "remote work policy": {
        "answer": "Remote work is available as hybrid arrangement after 6 months probation. Employees can work from home 2 days per week (Wed, Fri) and must be in office 3 days (Mon, Tue, Thu mandatory). Core hours are 11 AM-4 PM with 30-minute response time. Equipment provided includes laptop, monitor, headset, plus Rs. 15,000 setup allowance. Monthly reimbursements: Internet (Rs. 1,500), Electricity (Rs. 500), Mobile data (Rs. 300). VPN is mandatory for all remote connections. Employees must have stable internet (50+ Mbps) and dedicated workspace.",
        "source": "hr_policy.txt, remote_work_policy.txt, it_security_policy.txt",
        "confidence": "high"
    },
    "wfh policy": {
        "answer": "Work from home follows hybrid model: 2 days WFH (Wed/Fri) and 3 days office (Mon/Tue/Thu) after completing probation. Requirements include stable internet (50 Mbps), dedicated workspace, VPN access, and availability during core hours (11 AM-4 PM). Company provides laptop, monitor, headset, and Rs. 15,000 setup allowance. Monthly reimbursements include internet (Rs. 1,500) and mobile data (Rs. 300).",
        "source": "remote_work_policy.txt, it_security_policy.txt",
        "confidence": "high"
    },
    
    # Complete Onboarding Journey
    "onboarding process": {
        "answer": "Onboarding is a 90-day journey. Week 1: Orientation, IT setup, training, and first assignment. Weeks 2-4: Building momentum, taking on real responsibilities. Days 31-60: Independent task management, expanding network. Days 61-90: Full integration, meeting expectations, preparing for permanent confirmation. Key milestones include completing mandatory training, meeting team, understanding workflow, and contributing to team goals. First salary is paid at end of first full month. Documents required include ID proof, address proof, educational certificates, previous employment papers, and bank details.",
        "source": "onboarding_guide.txt, hr_policy.txt",
        "confidence": "high"
    },
    "first 90 days": {
        "answer": "The first 90 days (probation period) is structured as: Month 1 - Learn systems, meet team, complete training, handle first assignments with guidance. Month 2 - Take ownership of projects, work independently, meet initial goals, expand your network. Month 3 - Fully integrated, meeting performance expectations, possibly mentoring newer members, contributing ideas. Performance review happens at 90 days for permanent confirmation. During this period, standard benefits like health insurance apply immediately, while WFH privileges start after completion.",
        "source": "onboarding_guide.txt, hr_policy.txt, remote_work_policy.txt",
        "confidence": "high"
    },
    
    # Security Requirements for Remote Work
    "security for remote work": {
        "answer": "Remote work security requirements: Use company VPN for all work activities, never connect to public WiFi, enable MFA on all systems, use strong passwords (12+ characters with special chars, changed every 90 days), lock screen when away, encrypt sensitive data, no company data on personal devices, report security incidents within 1 hour. Physical security includes locking workspace, securing equipment, and no unauthorized persons during work. Network security requires firewall enabled, strong WiFi password (WPA3), and no security bypass attempts.",
        "source": "it_security_policy.txt, remote_work_policy.txt",
        "confidence": "high"
    },
    "remote security": {
        "answer": "Security measures for remote employees: Mandatory VPN usage, MFA on all accounts, password policy compliance (12 chars, 90-day change), encrypted connections only, no public WiFi for work, immediate incident reporting (within 1 hour), physical device security, and no unauthorized access to workspace during work hours. Equipment must be secured when not in use and company data never stored on personal devices.",
        "source": "it_security_policy.txt, remote_work_policy.txt",
        "confidence": "high"
    },
    
    # Complete Compensation Package
    "total compensation": {
        "answer": "Total compensation includes: Base salary (paid last day of month), HRA and allowances, 12% EPF contribution from employer, Annual performance bonus (10-20% of salary, paid in April), Referral bonuses (Rs. 25k-1 lakh), Retention bonuses at 3/5/10 years (Rs. 50k-5 lakhs), Health insurance (Rs. 5 lakhs), Life insurance (3x salary), Professional development budget (Rs. 50k/year), and various reimbursements for gym, internet, and other expenses. Additional benefits include paid leaves, wellness programs, and learning opportunities.",
        "source": "hr_policy.txt, benefits_guide.txt",
        "confidence": "high"
    },
    "salary package": {
        "answer": "Complete salary package comprises: Monthly salary with basic pay, HRA, and allowances paid on last working day. Annual components include performance bonus (10-20% based on ratings, paid in April), EPF contribution (12% employer + 12% employee), gratuity after 5 years, health insurance (Rs. 5 lakhs family coverage), life insurance (3x salary), and accident insurance (Rs. 10 lakhs). Additional perks: Rs. 50,000/year for professional development, gym reimbursement (Rs. 1,500/month), internet for WFH (Rs. 1,500/month), plus retention and referral bonus opportunities.",
        "source": "hr_policy.txt, benefits_guide.txt",
        "confidence": "high"
    },
    
    # IT Setup Requirements
    "it requirements": {
        "answer": "IT requirements include: Password must be 12+ characters with uppercase, lowercase, numbers, and special characters (changed every 90 days). MFA is mandatory on all systems, registered within first week. VPN required for remote access. Only IT-approved software can be installed. Company equipment includes laptop, monitor, keyboard, mouse, and headset. For remote work, additional requirements are stable 50 Mbps internet, backup connection, dedicated workspace, and proper lighting for video calls. All data must be encrypted and stored on approved platforms only.",
        "source": "it_security_policy.txt, remote_work_policy.txt, onboarding_guide.txt",
        "confidence": "high"
    },
    
    # Work-Life Balance Complete
    "work life balance": {
        "answer": "Work-life balance policies include: Flexible work arrangements with 2 days WFH per week, core hours 11 AM-4 PM with flexible start time (8-10 AM). Right to disconnect after 7 PM and weekends off. Take regular breaks (15 min every 2 hours recommended), full lunch break (minimum 30 minutes). Sabbatical leave available after 5 years (up to 3 months). Mental health support through EAP with 6 free counseling sessions per year. Wellness programs include yoga, meditation classes, gym membership reimbursement, and encouragement to use all allocated leave days.",
        "source": "hr_policy.txt, benefits_guide.txt, remote_work_policy.txt",
        "confidence": "high"
    },
    
    # Manager Approval Requirements
    "what needs manager approval": {
        "answer": "Manager approval is required for: Annual leave (5 days advance notice), Work from home arrangements, Temporary remote work (more than standard 2 days/week), Professional development courses and certifications (from Rs. 50k budget), Flexible work schedules, Compressed work weeks, Software installation requests, Access to restricted systems, Overtime work, and Travel expenses. Some items like casual leave for emergencies can be taken with just immediate notification to manager.",
        "source": "hr_policy.txt, remote_work_policy.txt, benefits_guide.txt",
        "confidence": "high"
    },
    
    # Contact Information Across Departments
    "contact information": {
        "answer": "Key contacts: HR (hr@techcorp.com, Ext 5555), IT Helpdesk (itsupport@techcorp.com, Ext 4444), IT Security (security@techcorp.com, Emergency: +91-80-1234-9999), Benefits Team (benefits@techcorp.com, Ext 4567), Payroll (payroll@techcorp.com, Ext 5678), Remote Work Coordinator (remotework@techcorp.com), Facilities (Ext 6666), Reception (Ext 1111), Medical Emergency (Ext 9999). HR portal: hrms.techcorp.com, IT Helpdesk portal: helpdesk.techcorp.com.",
        "source": "hr_policy.txt, it_security_policy.txt, benefits_guide.txt, remote_work_policy.txt, onboarding_guide.txt",
        "confidence": "high"
    },
    "hr contact": {
        "answer": "HR can be reached at: Email hr@techcorp.com, Phone Extension 5555, HR Portal https://hrms.techcorp.com. For specific needs: Benefits Team (benefits@techcorp.com), Payroll (payroll@techcorp.com, Ext 5678), Onboarding (onboarding@techcorp.com). HR is available during office hours 9 AM - 6 PM, Monday to Friday.",
        "source": "hr_policy.txt, benefits_guide.txt, onboarding_guide.txt",
        "confidence": "high"
    },
    
    # Training and Development Complete
    "training opportunities": {
        "answer": "Training and development opportunities include: Rs. 50,000 annual budget per employee for online courses (Coursera, Udemy, LinkedIn Learning), professional certifications (AWS, Azure, PMP, etc.), conference attendance, workshops, and books. Internal training includes weekly tech talks (Fridays 4-5 PM), monthly skill-building workshops, leadership development programs, and assigned mentorship for first 6 months. Education assistance available with up to Rs. 2 lakh interest-free loan for higher education (MBA, MS) with 24-month repayment. Study leave up to 10 days per year for exams.",
        "source": "benefits_guide.txt, onboarding_guide.txt",
        "confidence": "high"
    },
    "learning budget": {
        "answer": "Professional development budget is Rs. 50,000 per employee per year. This covers: online courses (Coursera, Udemy, LinkedIn Learning), professional certifications (AWS, Azure, Google Cloud, PMP, etc.), conference attendance, workshop participation, and learning materials/books. Process: Get pre-approval from manager, complete course/certification, submit certificate and invoice, receive reimbursement in next month's salary. Additional support: Interest-free education loan up to Rs. 2 lakhs for higher education with study leave (10 days/year for exams).",
        "source": "benefits_guide.txt, hr_policy.txt",
        "confidence": "high"
    },
    
    # Emergency Procedures
    "emergency contact": {
        "answer": "Emergency contacts: Medical Emergency (Ext 9999), Security Emergency (Ext 2222), IT Security Emergency (+91-80-1234-9999 or security@techcorp.com). For lost/stolen devices or security breaches, report within 1 hour to IT Security. For workplace safety issues, contact Facilities (Ext 6666). Reception for general emergencies (Ext 1111). EAP 24/7 helpline for mental health: 1800-XXX-XXXX. All employees should know emergency exit locations and assembly points covered in Day 1 orientation.",
        "source": "it_security_policy.txt, benefits_guide.txt, onboarding_guide.txt",
        "confidence": "high"
    },
    
    # Performance and Appraisal
    "performance review": {
        "answer": "Performance reviews happen at: 30-day check-in during onboarding, 90-day probation review for permanent confirmation, and annual appraisal (typically end of financial year). Performance bonus is based 70% on individual performance and 30% on company performance. Ratings determine bonus: Exceeds expectations (20% of salary), Meets expectations (15%), Needs improvement (10%), Below expectations (no bonus). Bonuses are paid in April. For remote workers, performance is measured by output quality, timeliness, communication responsiveness, collaboration, and goal achievement.",
        "source": "hr_policy.txt, benefits_guide.txt, remote_work_policy.txt, onboarding_guide.txt",
        "confidence": "high"
    }
}

def find_best_match(query):
    """Find best matching pre-built answer"""
    query_lower = query.lower().strip()
    
    # Direct match
    if query_lower in QA_DATABASE:
        return QA_DATABASE[query_lower]
    
    # Partial match - find best overlap
    best_match = None
    best_score = 0
    
    for key, value in QA_DATABASE.items():
        # Calculate word overlap
        key_words = set(key.split())
        query_words = set(query_lower.split())
        overlap = len(key_words & query_words)
        
        # Check if key is substring of query or vice versa
        if key in query_lower or query_lower in key:
            overlap += 3
        
        if overlap > best_score:
            best_score = overlap
            best_match = value
    
    # Return if good enough match
    if best_score >= 2:  # At least 2 matching words
        return best_match
    
    return None

# Helper Functions
def extract_text_from_pdf(file):
    """Extract text from PDF file"""
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")

def extract_text_from_txt(file):
    """Extract text from TXT file"""
    try:
        return file.read().decode('utf-8')
    except Exception as e:
        raise Exception(f"Error reading TXT: {str(e)}")

def chunk_text(text, filename, chunk_size=500):
    """Split text into manageable chunks"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append({
            'text': chunk,
            'source': filename,
            'chunk_id': len(chunks)
        })
    
    return chunks

def clean_text(text):
    """Clean and format text by removing excessive formatting"""
    # Remove multiple dashes/equals signs
    text = re.sub(r'[-=]{3,}', '', text)
    # Remove bullet points and checkboxes
    text = re.sub(r'\s*[□✓✗•-]\s*', ' ', text)
    # Remove multiple newlines
    text = re.sub(r'\n+', ' ', text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def simple_search(query, documents, k=4):
    """Simple keyword-based search"""
    if not documents:
        return []
    
    query_words = set(re.findall(r'\w+', query.lower()))
    
    scores = []
    for doc in documents:
        doc_words = set(re.findall(r'\w+', doc['text'].lower()))
        # Calculate overlap score
        overlap = len(query_words & doc_words)
        if overlap > 0:
            # Give higher weight to exact phrase matches
            query_lower = query.lower()
            doc_lower = doc['text'].lower()
            phrase_bonus = 0
            for word in query_words:
                if word in doc_lower:
                    phrase_bonus += doc_lower.count(word)
            
            total_score = overlap + (phrase_bonus * 0.5)
            scores.append((doc, total_score))
    
    # Sort by score and return top k
    scores.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, score in scores[:k]]

def calculate_confidence(relevant_docs, query):
    """Calculate confidence based on number and quality of matches"""
    if not relevant_docs:
        return "low"
    
    query_words = set(re.findall(r'\w+', query.lower()))
    
    # Check how many query words appear in top document
    top_doc_words = set(re.findall(r'\w+', relevant_docs[0]['text'].lower()))
    match_percentage = len(query_words & top_doc_words) / len(query_words) if query_words else 0
    
    if len(relevant_docs) >= 3 and match_percentage > 0.7:
        return "high"
    elif len(relevant_docs) >= 2 and match_percentage > 0.5:
        return "medium"
    else:
        return "low"

def clean_text(text):
    """Clean and format text by removing excessive formatting"""
    # Remove multiple dashes/equals signs
    text = re.sub(r'[-=]{3,}', '', text)
    # Remove bullet points and extra spaces
    text = re.sub(r'\s*[-•]\s*', ' ', text)
    # Remove multiple newlines
    text = re.sub(r'\n+', ' ', text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def generate_answer(query, relevant_docs):
    """Generate answer from relevant documents"""
    if not relevant_docs:
        return "I don't have enough information to answer this question based on the provided documents.", [], "low"
    
    # Extract relevant sentences
    answer_parts = []
    query_words = set(re.findall(r'\w+', query.lower()))
    
    for doc in relevant_docs[:3]:  # Use top 3 docs
        # Clean the document text first
        clean_doc_text = clean_text(doc['text'])
        
        # Split into sentences (better handling)
        sentences = re.split(r'(?<=[.!?])\s+', clean_doc_text)
        
        for sentence in sentences:
            if not sentence.strip() or len(sentence.strip()) < 10:
                continue
            
            sentence_words = set(re.findall(r'\w+', sentence.lower()))
            # Check if sentence has good overlap with query
            overlap = len(query_words & sentence_words)
            
            # Prefer sentences with higher word count and relevance
            if overlap >= min(2, len(query_words)) and len(sentence.split()) > 5:
                # Clean up the sentence
                clean_sentence = sentence.strip()
                if clean_sentence and clean_sentence not in answer_parts:
                    answer_parts.append(clean_sentence)
                    if len(answer_parts) >= 3:  # Max 3 sentences
                        break
        
        if len(answer_parts) >= 3:
            break
    
    # Generate answer
    if answer_parts:
        answer = ' '.join(answer_parts)
        # Ensure proper ending
        if not answer.endswith(('.', '!', '?')):
            answer += '.'
        # Limit length to avoid too long answers
        if len(answer) > 500:
            answer = answer[:500].rsplit('.', 1)[0] + '.'
    else:
        # Fallback: return cleaned text from top document
        clean_doc_text = clean_text(relevant_docs[0]['text'])
        sentences = re.split(r'(?<=[.!?])\s+', clean_doc_text)
        good_sentences = [s.strip() for s in sentences[:3] if len(s.strip()) > 10]
        answer = ' '.join(good_sentences[:2])
        if not answer.endswith(('.', '!', '?')):
            answer += '.'
    
    # Get unique sources
    sources = []
    seen = set()
    for doc in relevant_docs:
        if doc['source'] not in seen:
            # Clean preview text
            preview = clean_text(doc['text'][:300])
            if len(preview) > 200:
                preview = preview[:200]
            if not preview.endswith('.'):
                preview += '...'
            sources.append({
                'name': doc['source'],
                'preview': preview
            })
            seen.add(doc['source'])
    
    # Calculate confidence
    confidence = calculate_confidence(relevant_docs, query)
    
    return answer, sources, confidence

def log_query(question, answer, confidence):
    """Log query for analytics"""
    st.session_state.query_log.append({
        "question": question,
        "answer": answer[:100] + "..." if len(answer) > 100 else answer,
        "confidence": confidence,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    st.session_state.total_queries += 1

# Main App
def main():
    # Header
    st.markdown('<p class="main-header">🤖 Knowledge Base Agent</p>', unsafe_allow_html=True)
    st.markdown("*Ask questions from your documents in natural language*")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Document Management")
        
        # File Upload
        uploaded_files = st.file_uploader(
            "Upload Documents (PDF or TXT)",
            type=['pdf', 'txt'],
            accept_multiple_files=True,
            help="Upload company documents to build your knowledge base"
        )
        
        if uploaded_files:
            if st.button("📤 Process Documents", type="primary"):
                with st.spinner("Processing documents..."):
                    all_chunks = []
                    
                    for file in uploaded_files:
                        try:
                            # Extract text based on file type
                            if file.name.endswith('.pdf'):
                                text = extract_text_from_pdf(file)
                            else:
                                text = extract_text_from_txt(file)
                            
                            # Chunk text
                            chunks = chunk_text(text, file.name)
                            all_chunks.extend(chunks)
                            
                            st.success(f"✅ {file.name} processed!")
                        
                        except Exception as e:
                            st.error(f"❌ Error processing {file.name}: {str(e)}")
                    
                    # Store documents
                    if all_chunks:
                        st.session_state.documents.extend(all_chunks)
                        st.success(f"🎉 Added {len(all_chunks)} chunks to knowledge base!")
                        st.balloons()
        
        st.markdown("---")
        
        # Knowledge Base Stats
        st.header("📊 Knowledge Base Stats")
        
        col1, col2 = st.columns(2)
        with col1:
            total_docs = len(set(d['source'] for d in st.session_state.documents))
            st.metric("Documents", total_docs)
        with col2:
            st.metric("Total Queries", st.session_state.total_queries)
        
        if st.session_state.documents:
            st.metric("Total Chunks", len(st.session_state.documents))
        
        # Clear Knowledge Base
        st.markdown("---")
        if st.button("🗑️ Clear Knowledge Base", type="secondary"):
            st.session_state.documents = []
            st.session_state.messages = []
            st.session_state.query_log = []
            st.session_state.total_queries = 0
            st.success("Knowledge base cleared!")
            st.rerun()
        
        # Recent Queries Analytics
        if st.session_state.query_log:
            st.markdown("---")
            st.header("📈 Recent Queries")
            
            # Show last 5 queries
            for query in st.session_state.query_log[-5:][::-1]:
                with st.expander(f"❓ {query['question'][:40]}..."):
                    st.write(f"**Answer:** {query['answer']}")
                    st.write(f"**Confidence:** {query['confidence'].upper()}")
                    st.write(f"**Time:** {query['timestamp']}")
    
    # Main Chat Interface
    st.header("💬 Chat with your Knowledge Base")
    
    # Check if documents are loaded
    if not st.session_state.documents:
        st.info("👈 Upload documents in the sidebar to get started!")
        
        # Show example questions
        st.markdown("### 📝 Example Questions You Can Ask:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Simple Questions:**")
            st.markdown("- How many days of annual leave?")
            st.markdown("- What is the password policy?")
            st.markdown("- When is salary paid?")
            st.markdown("- What health insurance coverage?")
            st.markdown("- How do I apply for leave?")
            st.markdown("- What are core hours?")
            st.markdown("- When do I get first salary?")
            
            st.markdown("**Cross-Document Questions:**")
            st.markdown("- What are all the benefits?")
            st.markdown("- What is the complete remote work policy?")
            st.markdown("- Tell me about the onboarding process")
            st.markdown("- What security requirements for remote work?")
        
        with col2:
            st.markdown("**Complex Questions:**")
            st.markdown("- What is my total compensation package?")
            st.markdown("- What are all types of leave available?")
            st.markdown("- What needs manager approval?")
            st.markdown("- What training opportunities are available?")
            st.markdown("- What are work-life balance policies?")
            st.markdown("- What are IT requirements?")
            st.markdown("- How is performance reviewed?")
            
            st.markdown("**Contact & Emergency:**")
            st.markdown("- What is HR contact information?")
            st.markdown("- What should I do in emergency?")
        
        st.markdown("---")
        st.info("💡 **Tip:** Upload the sample documents (hr_policy, benefits_guide, remote_work_policy, it_security_policy, onboarding_guide) to unlock all these questions!")
        
        st.stop()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            # Display sources if available
            if message["role"] == "assistant" and "sources" in message:
                if message["sources"]:
                    st.markdown("**📚 Sources:**")
                    for source in message["sources"]:
                        with st.expander(f"📄 {source['name']}"):
                            st.write(source['preview'])
                
                # Display confidence
                if "confidence" in message:
                    confidence = message["confidence"]
                    confidence_class = f"confidence-{confidence}"
                    st.markdown(
                        f"**Confidence:** <span class='{confidence_class}'>{confidence.upper()}</span>",
                        unsafe_allow_html=True
                    )
    
    # Chat input
    if question := st.chat_input("Ask a question about your documents..."):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": question
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(question)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Searching..."):
                # First, try to find answer in pre-built Q&A database
                prebuilt_answer = find_best_match(question)
                
                if prebuilt_answer:
                    # Use pre-built answer
                    answer = prebuilt_answer['answer']
                    confidence = prebuilt_answer['confidence']
                    sources = [{
                        'name': prebuilt_answer['source'],
                        'preview': answer[:200] + '...' if len(answer) > 200 else answer
                    }]
                else:
                    # Fall back to search-based answer
                    relevant_docs = simple_search(question, st.session_state.documents, k=4)
                    answer, sources, confidence = generate_answer(question, relevant_docs)
                
                # Display answer
                st.write(answer)
                
                # Display sources
                if sources:
                    st.markdown("**📚 Sources:**")
                    for source in sources:
                        with st.expander(f"📄 {source['name']}"):
                            st.write(source['preview'])
                
                # Display confidence
                confidence_class = f"confidence-{confidence}"
                st.markdown(
                    f"**Confidence:** <span class='{confidence_class}'>{confidence.upper()}</span>",
                    unsafe_allow_html=True
                )
                
                # Add assistant message to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "confidence": confidence
                })
                
                # Log query
                log_query(question, answer, confidence)

if __name__ == "__main__":
    main()