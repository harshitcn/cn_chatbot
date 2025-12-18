"""
Test script to validate the fully dynamic scraper system.
Tests various queries to ensure it works for any question.
"""
import logging
from scraper import DynamicScraper
from chatbot import DynamicChatbot

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Test URL
TEST_URL = "https://codeninjas-39646145.hs-sites.com/tx-alamo-ranch/"

def test_scraper():
    """Test the scraper to extract all content."""
    print("\n" + "="*80)
    print("TEST 1: Testing Dynamic Scraper")
    print("="*80)
    
    scraper = DynamicScraper()
    chunks = scraper.scrape(TEST_URL)
    
    print(f"\n[OK] Extracted {len(chunks)} chunks from {TEST_URL}")
    
    if chunks:
        print(f"\nSample chunks:")
        for i, chunk in enumerate(chunks[:5], 1):
            print(f"\n  Chunk {i}:")
            print(f"    Section: {chunk.get('section', 'Unknown')}")
            print(f"    Text: {chunk.get('text', '')[:150]}...")
            print(f"    Length: {len(chunk.get('text', ''))} chars")
    
    # Show section distribution
    sections = {}
    for chunk in chunks:
        section = chunk.get('section', 'Unknown')
        sections[section] = sections.get(section, 0) + 1
    
    print(f"\n[OK] Section distribution:")
    for section, count in sorted(sections.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"    {section}: {count} chunks")
    
    return chunks

def test_queries(chunks):
    """Test various queries to ensure the system works for any question."""
    print("\n" + "="*80)
    print("TEST 2: Testing Dynamic Query Engine with Various Queries")
    print("="*80)
    
    chatbot = DynamicChatbot(base_url=TEST_URL, use_cache=True)
    
    # Scrape first
    chatbot.scrape_website()
    
    # Test queries
    test_queries_list = [
        "camps",
        "programs",
        "academies",
        "parent's night out",
        "address",
        "mission",
        "careers",
        "faq",
        "after school",
        "robotics",
        "what do you offer",
        "what is Code Ninjas",
        "what ages do you serve",
        "refund policy",
        "contact information"
    ]
    
    results = []
    for query in test_queries_list:
        print(f"\n--- Testing query: '{query}' ---")
        try:
            response = chatbot.answer_query(query)
            status = response.get('status', 'unknown')
            answer = response.get('answer', 'No answer')
            sources_count = len(response.get('sources', []))
            
            print(f"  Status: {status}")
            print(f"  Answer length: {len(answer)} chars")
            print(f"  Sources: {sources_count}")
            print(f"  Answer preview: {answer[:150]}...")
            
            results.append({
                'query': query,
                'status': status,
                'has_answer': len(answer) > 50,
                'sources': sources_count
            })
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            results.append({
                'query': query,
                'status': 'error',
                'has_answer': False,
                'sources': 0
            })
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results if r['status'] == 'success' and r['has_answer'])
    total = len(results)
    
    print(f"\n[OK] Successful queries: {successful}/{total} ({successful/total*100:.1f}%)")
    print(f"\nQuery Results:")
    for r in results:
        status_icon = "[OK]" if r['status'] == 'success' and r['has_answer'] else "[FAIL]"
        print(f"  {status_icon} {r['query']}: {r['status']} ({r['sources']} sources)")
    
    return results

if __name__ == "__main__":
    print("\n" + "="*80)
    print("DYNAMIC SCRAPER SYSTEM VALIDATION")
    print("="*80)
    
    # Test scraper
    chunks = test_scraper()
    
    if not chunks:
        print("\n[ERROR] No chunks extracted. Cannot proceed with query tests.")
        exit(1)
    
    # Test queries
    results = test_queries(chunks)
    
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)

