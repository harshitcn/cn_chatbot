"""Test script to validate the dynamic scraper system."""
import logging
from scraper import DynamicScraper
from chatbot import DynamicChatbot

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test URL
url = 'https://codeninjas-39646145.hs-sites.com/tx-alamo-ranch/'

print("=" * 80)
print("TESTING DYNAMIC SCRAPER SYSTEM")
print("=" * 80)

# Initialize chatbot
print("\n1. Initializing DynamicChatbot...")
chatbot = DynamicChatbot(base_url=url, use_cache=False)

# Scrape website
print(f"\n2. Scraping website: {url}")
chunks = chatbot.scrape_website(url)

print(f"\n3. EXTRACTION RESULTS:")
print(f"   Total chunks extracted: {len(chunks)}")

# Show chunk statistics
stats = chatbot.get_chunk_stats()
print(f"\n4. CHUNK STATISTICS:")
print(f"   Total chunks: {stats['total_chunks']}")
print(f"   Sections found: {len(stats['sections'])}")
print(f"   Top sections:")
for section, count in sorted(stats['sections'].items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"     - {section}: {count} chunks")

# Show sample chunks
print(f"\n5. SAMPLE CHUNKS:")
for i, chunk in enumerate(chunks[:5], 1):
    print(f"\n   Chunk {i}:")
    print(f"     Section: {chunk.get('section', 'Unknown')}")
    print(f"     Text: {chunk.get('text', '')[:200]}...")
    print(f"     Length: {len(chunk.get('text', ''))} chars")

# Test various queries
test_queries = [
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
    "what ages do you serve",
    "contact information",
    "hours",
    "location"
]

print(f"\n6. TESTING QUERIES:")
print("=" * 80)

for query in test_queries:
    print(f"\nQuery: '{query}'")
    print("-" * 80)
    try:
        response = chatbot.answer_query(query)
        status = response.get('status', 'unknown')
        answer = response.get('answer', 'No answer')
        sources = response.get('sources', [])
        
        print(f"Status: {status}")
        if status == 'success':
            print(f"Answer: {answer[:300]}...")
            print(f"Sources: {len(sources)} chunks found")
            if sources:
                print(f"Top source section: {sources[0].get('section', 'Unknown')}")
        else:
            print(f"Answer: {answer}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("TESTING COMPLETE")
print("=" * 80)
