"""
Predefined Q&A data storage and exact matching.
Contains a list of predefined question-answer pairs for exact/precise matching.
This is checked BEFORE semantic search in the FAQ list.
"""
from typing import List, Dict, Optional
import re

# Predefined Q&A data structure: List of dictionaries with 'question' and 'answer' keys
# Static predefined questions - do not edit
PREDEFINED_QA: List[Dict[str, str]] = [
    {
        "question": "Welcome to Code Ninjas! Are you interested in a Program or a Franchisee? Which role fits you the best?",
        "answer": ['Parent/Guardian', 'Existing Franchise Owner', 'Franchise Staff', 'Potential Franchisee Owner ',
                   'Something else/just browsing']
    },
    {
        "question": "Parent/Guardian",
        "answer": ['Enroll or learn about programs for my kids', 'Know more about CAMPS', 'Know more about Clubs',
                   'Know more about Academies', 'Know more about CREATE', 'Know more about JR', 'Know more about Parent Night Out',
                   'Know more about Birthday Parties', 'Know more about Home Schooling', 'Know more about After School Programs',
                   'Know more about PTO / PTA', 'Know more about Upcoming Events / Programs',
                   'Ask a general question about a program', 'Go back to Main Menu']
    },
    {
        "question": "Existing Franchise Owner",
        "answer": ['I want to know more about Franchise Ownership', 'I want to sell my Franchise',
                   'I want to own a new Franchise', 'I want to raise a support issue', 'I have another concern',
                   'Ask a general question regarding Franchisee cost, ownership and returns', 'Go back to Main Menu']
    },
    {
        "question": "Franchise Staff",
        "answer": ['I want to raise a support issue', 'I have another concern', 'I want to know about Program timings',
                   'Go back to Main Menu']
    },
    {
        "question": "Potential Franchise Owner",
        "answer": ['I want to know more about Franchise Ownership', 'I want to own a Franchise',
                   'I want to raise a support issue', 'I have another concern', 'Go back to Main Menu']
    },
    {
        "question": "Something else/just browsing ",
        "answer": [
            'I want to know about career opportunities',
            'I have a question regarding available programs and timings',
            'I want to know about my nearby Centers',
            'I want to know more about Franchise Ownership',
            'I want to own a Franchise',
            'I want to raise a support issue',
            'I have another concern',
            'Go back to Main Menu'
        ]

    },
    {
        "question": "I want to raise a support issue",
        "answer": "To raise a support issue, please contact your Franchise Business Partner (FBP) or reach out to the Code Ninjas support team. You can submit a support ticket through the franchise portal, email the support team directly, or call the support hotline. For urgent issues, please contact your FBP immediately. The support team will assist you with technical issues, operational questions, system access problems, and other concerns related to your franchise operations."
    },
    {
        "question": "I have another concern",
        "answer": "Please tell us what you are looking for or describe your concern, and we'll do our best to help you."
    }
]


def normalize_question(question: str) -> str:
    """
    Normalize a question for comparison.
    - Convert to lowercase
    - Remove extra whitespace
    - Remove punctuation
    - Remove common question words
    
    Args:
        question: Original question string
        
    Returns:
        str: Normalized question string
    """
    if not question:
        return ""

    # Convert to lowercase
    normalized = question.lower().strip()

    # Remove punctuation
    normalized = re.sub(r'[^\w\s]', '', normalized)

    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)

    return normalized.strip()


def normalize_for_matching(text: str) -> str:
    """
    Normalize text for flexible matching.
    Removes common question words and articles.
    
    Args:
        text: Text to normalize
        
    Returns:
        str: Normalized text
    """
    if not text:
        return ""

    # Common words to remove for matching
    stop_words = {
        'what', 'is', 'are', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
        'to', 'for', 'of', 'with', 'by', 'does', 'do', 'how', 'can', 'will', 'would',
        'should', 'could', 'tell', 'me', 'about', 'i', 'you', 'your', 'my', 'this', 'that'
    }

    normalized = normalize_question(text)
    words = normalized.split()

    # Remove stop words
    filtered_words = [w for w in words if w not in stop_words]

    return ' '.join(filtered_words)


def find_exact_match(user_question: str, predefined_qa: List[Dict[str, str]]) -> Optional[str]:
    """
    Find exact or very close match in predefined Q&A.
    
    Matching strategies:
    1. Exact normalized match
    2. User question contains predefined question (or vice versa)
    3. High keyword overlap (>= 80%)
    
    Args:
        user_question: User's question
        predefined_qa: List of predefined Q&A pairs
        
    Returns:
        Optional[str]: Answer if match found, None otherwise
    """
    if not user_question or not predefined_qa:
        return None

    user_normalized = normalize_question(user_question)
    user_keywords = set(normalize_for_matching(user_question).split())

    best_match = None
    best_score = 0.0

    for qa_pair in predefined_qa:
        predefined_q = qa_pair.get("question", "")
        predefined_a = qa_pair.get("answer", "")

        if not predefined_q or not predefined_a:
            continue

        predefined_normalized = normalize_question(predefined_q)
        predefined_keywords = set(normalize_for_matching(predefined_q).split())

        # Strategy 1: Exact normalized match
        if user_normalized == predefined_normalized:
            return predefined_a

        # Strategy 2: Substring match (user question contains predefined or vice versa)
        if (user_normalized in predefined_normalized or
                predefined_normalized in user_normalized):
            # Calculate overlap score
            if predefined_keywords:
                overlap = len(user_keywords.intersection(predefined_keywords))
                overlap_ratio = overlap / len(predefined_keywords)
                if overlap_ratio >= 0.8:  # 80% keyword overlap
                    return predefined_a

        # Strategy 3: High keyword overlap
        if user_keywords and predefined_keywords:
            common_keywords = user_keywords.intersection(predefined_keywords)
            if common_keywords:
                # Calculate overlap ratio (both directions)
                overlap_ratio_user = len(common_keywords) / len(user_keywords) if user_keywords else 0
                overlap_ratio_predefined = len(common_keywords) / len(predefined_keywords) if predefined_keywords else 0

                # Use the average overlap
                avg_overlap = (overlap_ratio_user + overlap_ratio_predefined) / 2

                # Require at least 80% overlap and at least 3 common keywords
                if avg_overlap >= 0.8 and len(common_keywords) >= 3:
                    if avg_overlap > best_score:
                        best_match = predefined_a
                        best_score = avg_overlap

    return best_match


def get_predefined_answer(user_question: str) -> Optional[str]:
    """
    Get answer from predefined Q&A if exact match is found.
    
    Args:
        user_question: User's question
        
    Returns:
        Optional[str]: Answer if match found, None otherwise
    """
    return find_exact_match(user_question, PREDEFINED_QA)
