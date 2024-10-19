import json
import re
import requests
from PyPDF2 import PdfFileReader
import docx
from datetime import datetime
import re
import pdfplumber
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import namedtuple
import os
from docx import Document
import pypandoc
import fitz
import unicodedata
import docx2txt

nltk.download('punkt')
nltk.download('stopwords')

stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()

def preprocess_text(text):
    tokens = word_tokenize(text)
    tokens = [token.lower() for token in tokens if token.isalnum() and token.lower() not in stop_words]
    tokens = [stemmer.stem(token) for token in tokens]
    return ' '.join(tokens)

Resume = namedtuple('Resume', ['content', 'experience_level', 'rate_card'])

def read_resume(op_path):
    text = extract_text(op_path)
    # experience_level = extract_experience_level(text)
    # rate_card = extract_rate_card(text)
    experience_level = None
    rate_card = None
    return Resume(text, experience_level, rate_card)

def extract_text_from_pdf(file_path):
    
    document = fitz.open(file_path)
    text = ""
    
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda block: (block[1], block[0]))  # Sort by y, then by x
         
        for block in blocks:
            text += block[4] + "\n"
            
    return text


def read_pdf(file_path):
    with open(file_path, 'rb') as f:
        file_data = f.read()

    # Use fitz to open the byte stream
    document = fitz.open(stream=file_data, filetype='pdf')
    
    text = ""
    
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda block: (block[1], block[0]))  # Sort by y, then by x
         
        for block in blocks:
            text += block[4] + "\n"
            
    return text

def extract_text_from_docx(file_path):
    text = docx2txt.process(file_path)
    # print(text.encode('ascii', 'ignore').decode('ascii'))
    return text

def extract_text(file_path):
    if file_path.endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith('.docx'):
        return extract_text_from_docx(file_path)
    elif file_path.endswith('.doc'):
        return extract_text_from_doc(file_path)
    else:
        raise ValueError('Unsupported file type')

def extract_text_from_doc(doc_path):
    output = pypandoc.convert_file(doc_path, 'plain', format='doc')
    return output

def extract_education_section(content):
    pattern = r'(Education|Educational Summary|Educational Qualifications|Educational Qualification|Academic Background|Qualifications|Academic Credentials|Educational Details|Academic Qualification)[\s\S]+?(Experience|Certifications|Project|Achievements|Awards|Skills|Projects|$)'
    education_section = re.search(pattern, content, re.IGNORECASE)
    print(education_section)
    if education_section:
        section_text = education_section.group(0)
        section_text= section_text.encode('ascii', 'ignore').decode('ascii')
        print(section_text)

        return section_text
    else:
        return ''


def extract_college_name(text):
    college_pattern = re.compile(
        r"Indian\sInstitute\sof\sTechnology\s(?:Madras|Delhi|Bombay|Kanpur|Roorkee|Kharagpur|Guwahati|Hyderabad|Indore|Varanasi|Gandhinagar|Ropar|Jodhpur|Mandi|Palakkad|Patna|Bhilai|Bhubaneswar|Jammu|Dharwad|Tirupati|ISM)|"
        r"National\sInstitute\sof\sTechnology\s(?:Tiruchirappalli|Karnataka,\sSurathkal|Rourkela|Warangal|Calicut|Durgapur|Kurukshetra|Raipur|Silchar|Delhi|Goa|Agartala|Srinagar|Manipur|Jaipur|Meghalaya|Nagpur|Surat|Patna|Bhopal|Jalandhar)|"
        r"(?:Jadavpur|Vellore\sInstitute\sof|Anna|Amrita\sVishwa|Thapar\sInstitute\sof\sEngineering\sand|Jamia\sMillia\sIslamia|Siksha\s`O`\sAnusandhan|S\.R\.M\.\sInstitute\sof|Delhi\sTechnological|Amity|Aligarh\sMuslim|Shanmugha\sArts\sScience\sTechnology\s&\sResearch|Indian\sInstitute\sof\sEngineering\sScience\sand\sTechnology,\sShibpur|Kalasalingam\sAcademy\sof\sResearch\sand|Chandigarh|Kalinga\sInstitute\sof\sIndustrial|Institute\sof\sChemical|Manipal|Graphic\sEra|PSG\sCollege\sof|Saveetha\sInstitute\sof|Banasthali|College\sof\sEngineering,\sPune|Vel\sTech\sRangarajan\sDr.\sSagunthala\sR\s&\sD|Rajalakshmi|Jawaharlal\sNehru|Guru\sGobind|Vignan's\sFoundation\sfor\sScience,\sTechnology\sand|M\.\sS\.\sRamaiah|Atal\sBihari\sVajpayee\sIndian\sInstitute\sof\sInformation\sTechnology\sand\sManagement|Indian\sInstitute\sof\sInformation\sTechnology\sAllahabad|Pandit\sDwarka\sPrasad\sMishra\sIndian\sInstitute\sof\sInformation\sTechnology,\sDesign\sand\sManufacturing\s(?:IIITDM)|Sri\sKrishna|Netaji\sSubhas\sUniversity\sof|Lovely\sProfessional|Chitkara|SR\sUniversity|AU\sCollege\sof\sEngineering\s\(A\)|C\.V\.\sRaman\sGlobal\sUniversity,\sOdisha|Visvesvaraya\sTechnological|International\sInstitute\sof\sInformation\sTechnology\s(?:Bangalore|Hyderabad)|Indraprastha\sInstitute\sof\sInformation\sTechnology\sDelhi|Manipal\sUniversity\sJaipur|Rajiv\sGandhi\sInstitute\sof\sPetroleum|University\sof\sHyderabad|Visvesvaraya\sNational\sInstitute\sof\sTechnology|UPES)"
    )
    
    matches = college_pattern.findall(text)
    return matches



def get_resume_paths(directory_path):
    supported_extensions = ('.pdf', '.docx','.doc')
    resume_paths = [os.path.join(directory_path, filename) for filename in os.listdir(directory_path) if filename.endswith(supported_extensions)]
    return resume_paths
    # return [os.path.join(directory, filename) for file in os.listdir(directory,filename) if file.endswith(('.docx', '.pdf','.doc'))]

resume_directory = 'new_samples'
resume_paths = get_resume_paths(resume_directory)
resumes = [read_resume(path) for path in resume_paths]

# Extract education sections from resumes
education_sections = [extract_education_section(resume.content) for resume in resumes]

# Extract college names from education sections
college_names = [extract_college_name(education_section) for education_section in education_sections]

print(college_names)

def get_nirf_ranking(college_name, rankings_file='engineering_ranking.json'):
    with open(rankings_file, 'r') as file:
        nirf_rankings = json.load(file)
    
    college_name = college_name.strip('| ')
    for college in nirf_rankings:
        if college_name == college["name"].strip('| '):
            return college["rank"]
    
    return f"Ranking not found for {college_name}"

def get_nirf_rankings(college_names, rankings_file='engineering_ranking.json'):
    results = {}
    score = {}
    for college_name in college_names:
        for name in college_name:
            ranking = get_nirf_ranking(name, rankings_file)
            s = 2
            if isinstance(ranking, int):
                if ranking > 0 and ranking <= 10:
                    s = 10
                elif ranking > 10 and ranking <= 20:
                    s = 8
                elif ranking > 20 and ranking <= 40:
                    s = 6
                elif ranking > 40 and ranking <= 50:
                    s = 4
            results[name] = ranking
            score[name] = s
    
    return results, score

nirf_ranking, scores = get_nirf_rankings(college_names)
print(f"NIRF Ranking: {nirf_ranking}")
print(f"Scores: {scores}")
