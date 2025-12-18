from scraper import DynamicScraper

s = DynamicScraper()
html = s.fetch_html('https://codeninjas-39646145.hs-sites.com/tx-alamo-ranch/')
if not html:
    print("No HTML fetched")
    exit(1)

soup = s.parse_html(html)
print(f'Before cleaning - p tags: {len(soup.find_all("p"))}')
print(f'Before cleaning - h tags: {len(soup.find_all(["h1", "h2", "h3"]))}')

s._remove_unwanted_elements(soup)

print(f'After cleaning - p tags: {len(soup.find_all("p"))}')
print(f'After cleaning - h tags: {len(soup.find_all(["h1", "h2", "h3"]))}')
print(f'After cleaning - div tags: {len(soup.find_all("div"))}')

# Test text extraction on a sample
p_tags = soup.find_all("p")
if p_tags:
    sample = p_tags[0]
    text = s._extract_text_from_element(sample)
    print(f'Sample p tag text length: {len(text)}')
    print(f'Sample text: {text[:100]}')

elements = s._extract_content_elements(soup)
print(f'Content elements found: {len(elements)}')

if elements:
    print(f'First element type: {elements[0].name}')
    print(f'First element text: {s._extract_text_from_element(elements[0])[:200]}')

# Test full scraping
print("\nTesting full scrape:")
chunks = s.scrape('https://codeninjas-39646145.hs-sites.com/tx-alamo-ranch/')
print(f'Total chunks extracted: {len(chunks)}')
if chunks:
    print(f'\nSample chunks (first 3):')
    for i, chunk in enumerate(chunks[:3], 1):
        print(f'\nChunk {i}:')
        print(f'  Section: {chunk["section"]}')
        print(f'  Text length: {len(chunk["text"])}')
        print(f'  Text: {chunk["text"][:150]}...')

