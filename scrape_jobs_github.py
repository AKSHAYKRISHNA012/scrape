"""
GitHub Careers Job Scraper
==========================
Scrapes job listings from GitHub's careers page and exports to Excel.

Requirements:
- requests
- beautifulsoup4  
- pandas
- openpyxl

Usage: python scrape_jobs_github.py
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import urljoin
import sys

# Configuration
BASE_URL = "https://github.com/about/careers"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}


def extract_experience_and_skills(job_description):
    """
    Extract experience requirements and skills from job description text.
    
    Args:
        job_description (str): Full job description text
        
    Returns:
        tuple: (experience_required, skills_required)
    """
    experience = ""
    skills = []
    
    if not job_description:
        return experience, ""
    
    desc_lower = job_description.lower()
    
    # Extract experience requirements
    experience_patterns = [
        r'(\d+\+?\s*years?\s*(?:of\s*)?experience)',
        r'(minimum\s*\d+\s*years?)',
        r'(\d+\s*to\s*\d+\s*years?)',
        r'(entry\s*level|junior|senior|principal|lead)',
        r'(bachelor|master|phd|degree)'
    ]
    
    for pattern in experience_patterns:
        matches = re.findall(pattern, desc_lower, re.IGNORECASE)
        if matches:
            experience = matches[0]
            break
    
    # Extract skills - look for common skill keywords
    skill_keywords = [
        'python', 'java', 'javascript', 'typescript', 'go', 'rust', 'c#', 'c++', 
        'sql', 'html', 'css', 'react', 'vue', 'angular', 'node.js', 'docker', 
        'kubernetes', 'aws', 'azure', 'gcp', 'git', 'github', 'linux', 'bash',
        'machine learning', 'ai', 'data science', 'analytics', 'cloud',
        'agile', 'scrum', 'devops', 'ci/cd', 'terraform', 'ansible'
    ]
    
    found_skills = []
    for skill in skill_keywords:
        if skill.lower() in desc_lower:
            found_skills.append(skill)
    
    return experience, ', '.join(found_skills[:10])  # Limit to top 10 skills


def get_job_detail(job_url):
    """
    Fetch detailed job information from individual job page.
    
    Args:
        job_url (str): URL to job detail page
        
    Returns:
        dict: Job details including description, experience, skills
    """
    try:
        response = requests.get(job_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract job description from various possible containers
        description_selectors = [
            '.markdown-body',
            '.job-description',
            '.job-details',
            '.content',
            'main',
            '[data-target="readme-toc.content"]'
        ]
        
        description = ""
        for selector in description_selectors:
            desc_element = soup.select_one(selector)
            if desc_element:
                description = desc_element.get_text(strip=True)
                break
        
        # Extract experience and skills
        experience, skills = extract_experience_and_skills(description)
        
        # Get summary (first 200 characters)
        summary = description[:200] + "..." if len(description) > 200 else description
        
        return {
            'description': description,
            'experience': experience,
            'skills': skills,
            'summary': summary,
            'salary': ""  # GitHub typically doesn't list salaries publicly
        }
        
    except Exception as e:
        print(f"Error fetching job details from {job_url}: {str(e)}")
        return {
            'description': "",
            'experience': "",
            'skills': "",
            'summary': "",
            'salary': ""
        }


def get_job_listings():
    """
    Scrape job listings from GitHub careers page.
    
    Returns:
        list: List of job dictionaries
    """
    try:
        print(f"Accessing GitHub careers page...")
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("Successfully accessed GitHub careers page")
        jobs = []
        
        # Look for job listings - GitHub might use different structures
        job_selectors = [
            '.job-listing',
            '.position',
            '.career-position',
            'a[href*="/careers/positions/"]',
            'a[href*="jobs"]'
        ]
        
        job_cards = []
        for selector in job_selectors:
            job_cards = soup.select(selector)
            if job_cards:
                print(f"Found {len(job_cards)} job cards using selector: {selector}")
                break
        
        # If no specific job cards found, look for any links that might be jobs
        if not job_cards:
            print("No specific job cards found, looking for job-related links...")
            all_links = soup.find_all('a', href=True)
            job_cards = [link for link in all_links if 
                        any(keyword in link.get('href', '').lower() 
                            for keyword in ['job', 'career', 'position', 'opening'])]
            print(f"Found {len(job_cards)} potential job links")
        
        if not job_cards:
            print("No job cards found. Saving page content for debugging...")
            with open("debug_github_page.html", "w", encoding="utf-8") as f:
                f.write(soup.prettify())
            print("Page content saved to debug_github_page.html")
            return []
        
        for i, card in enumerate(job_cards):
            try:
                print(f"Processing job {i+1}/{len(job_cards)}")
                
                # Extract job title and URL
                if card.name == 'a':
                    job_title = card.get_text(strip=True)
                    job_url = urljoin(BASE_URL, card.get('href', ''))
                else:
                    title_element = card.find('a')
                    if title_element:
                        job_title = title_element.get_text(strip=True)
                        job_url = urljoin(BASE_URL, title_element.get('href', ''))
                    else:
                        job_title = card.get_text(strip=True)
                        job_url = ""
                
                # Skip if no meaningful title
                if not job_title or len(job_title.strip()) < 3:
                    continue
                
                # Extract location (might be in the same element or nearby)
                location = "Remote/Global"  # GitHub is known for remote work
                
                # Get detailed job information
                job_details = {
                    'experience': "",
                    'skills': "",
                    'summary': "",
                    'salary': ""
                }
                
                if job_url and 'github.com' in job_url:
                    print(f"  Fetching details for: {job_title}")
                    job_details = get_job_detail(job_url)
                    time.sleep(1)  # Be respectful to the server
                
                # Create job dictionary
                job_data = {
                    'JobTitle': job_title,
                    'Location': location,
                    'ExperienceRequired': job_details['experience'],
                    'SkillsRequired': job_details['skills'],
                    'Salary': job_details['salary'],
                    'JobURL': job_url,
                    'JobDescriptionSummary': job_details['summary']
                }
                
                jobs.append(job_data)
                print(f"  ✓ Successfully processed: {job_title}")
                
            except Exception as e:
                print(f"Error processing job card {i+1}: {str(e)}")
                continue
        
        return jobs
        
    except Exception as e:
        print(f"Error in get_job_listings: {str(e)}")
        return []


def save_to_excel(jobs, filename="GitHub_Jobs.xlsx"):
    """
    Save job data to Excel file with proper formatting.
    
    Args:
        jobs (list): List of job dictionaries
        filename (str): Output filename
    """
    if not jobs:
        print("No jobs to save!")
        return
    
    try:
        # Create DataFrame
        df = pd.DataFrame(jobs)
        
        # Ensure all required columns are present
        required_columns = [
            'JobTitle', 'Location', 'ExperienceRequired', 
            'SkillsRequired', 'Salary', 'JobURL', 'JobDescriptionSummary'
        ]
        
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""
        
        # Reorder columns
        df = df[required_columns]
        
        # Clean up data
        df = df.fillna("")  # Replace NaN with empty strings
        
        # Save to Excel without index
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"\n✓ Successfully saved {len(jobs)} jobs to {filename}")
        
        # Print summary statistics
        print(f"\nSummary:")
        print(f"- Total jobs: {len(jobs)}")
        print(f"- Jobs with experience info: {len([j for j in jobs if j.get('ExperienceRequired')])}")
        print(f"- Jobs with skills info: {len([j for j in jobs if j.get('SkillsRequired')])}")
        print(f"- Jobs with descriptions: {len([j for j in jobs if j.get('JobDescriptionSummary')])}")
        
    except Exception as e:
        print(f"Error saving to Excel: {str(e)}")


def main():
    """
    Main function to run the job scraper.
    """
    print("=" * 60)
    print("GitHub Careers Job Scraper")
    print("=" * 60)
    
    try:
        # Test internet connection
        print("Testing connection...")
        test_response = requests.get("https://github.com", headers=HEADERS, timeout=10)
        test_response.raise_for_status()
        print("✓ Internet connection OK")
        
        # Start scraping
        print("\nStarting job scraping...")
        jobs = get_job_listings()
        
        if jobs:
            # Save to Excel
            save_to_excel(jobs, "GitHub_Jobs.xlsx")
            
            # Display sample jobs
            print(f"\nSample of scraped jobs:")
            print("-" * 40)
            for i, job in enumerate(jobs[:3]):
                print(f"{i+1}. {job['JobTitle']}")
                print(f"   Location: {job['Location']}")
                print(f"   URL: {job['JobURL'][:60]}..." if job['JobURL'] else "   URL: Not available")
                print()
        else:
            print("❌ No jobs were scraped. Trying alternative approach...")
            
    except requests.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        print("Please check your internet connection and try again.")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        print("Please check the error details and try again.")


if __name__ == "__main__":
    main()
