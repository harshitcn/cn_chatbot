"""
Example usage of the comprehensive scraping chatbot system.
This demonstrates how to use the scraper, cleaner, query engine, and chatbot.
"""
import json
from app.utils.chatbot import ScrapingChatbot, answer_query


def example_basic_usage():
    """Basic example of using the chatbot."""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)
    
    # Initialize chatbot with a base URL
    chatbot = ScrapingChatbot(base_url="https://example.com")
    
    # Answer a query
    response = chatbot.answer_query("What camps do you offer?")
    
    print(f"Status: {response['status']}")
    print(f"Query: {response['query']}")
    print(f"Category: {response.get('category', 'N/A')}")
    print(f"\nFormatted Answer:\n{response['formatted']}")
    print(f"\nResults Count: {len(response['results'])}")


def example_convenience_function():
    """Example using the convenience function."""
    print("\n" + "=" * 60)
    print("Example 2: Convenience Function")
    print("=" * 60)
    
    # Use the convenience function
    response = answer_query(
        "What are the prices for your programs?",
        url="https://example.com"
    )
    
    print(f"Status: {response['status']}")
    print(f"Query: {response['query']}")
    print(f"\nFormatted Answer:\n{response['formatted']}")


def example_multiple_queries():
    """Example of handling multiple queries with caching."""
    print("\n" + "=" * 60)
    print("Example 3: Multiple Queries (with caching)")
    print("=" * 60)
    
    chatbot = ScrapingChatbot(base_url="https://example.com")
    
    queries = [
        "What camps do you offer?",
        "What are the age groups?",
        "What is your contact information?",
        "What are your prices?"
    ]
    
    for query in queries:
        response = chatbot.answer_query(query)
        print(f"\nQuery: {query}")
        print(f"Answer: {response['formatted'][:200]}...")
    
    print(f"\nCached URLs: {chatbot.get_cached_urls()}")


def example_detailed_response():
    """Example showing detailed response structure."""
    print("\n" + "=" * 60)
    print("Example 4: Detailed Response Structure")
    print("=" * 60)
    
    response = answer_query(
        "Tell me about your summer camps",
        url="https://example.com"
    )
    
    print("Full Response JSON:")
    print(json.dumps(response, indent=2, default=str))


def example_custom_url():
    """Example with a custom URL per query."""
    print("\n" + "=" * 60)
    print("Example 5: Custom URL per Query")
    print("=" * 60)
    
    chatbot = ScrapingChatbot()
    
    # Use different URL for each query
    response1 = chatbot.answer_query(
        "What programs are available?",
        url="https://example.com/programs"
    )
    
    response2 = chatbot.answer_query(
        "What camps are available?",
        url="https://example.com/camps"
    )
    
    print(f"Query 1: {response1['query']}")
    print(f"Answer: {response1['formatted'][:150]}...")
    print(f"\nQuery 2: {response2['query']}")
    print(f"Answer: {response2['formatted'][:150]}...")


if __name__ == "__main__":
    print("Comprehensive Scraping Chatbot - Example Usage\n")
    print("Note: These examples use placeholder URLs.")
    print("Replace 'https://example.com' with actual URLs to test.\n")
    
    # Run examples
    try:
        example_basic_usage()
        example_convenience_function()
        example_multiple_queries()
        example_detailed_response()
        example_custom_url()
    except Exception as e:
        print(f"\nError running examples: {str(e)}")
        print("Make sure to replace placeholder URLs with actual URLs to test.")

