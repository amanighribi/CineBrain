import json

reviews = [json.loads(l) for l in open('data/reviews.jsonl', encoding='utf-8')]
print(f'Total reviews: {len(reviews)}')
print(f'Avg review length: {sum(len(r["review_text"]) for r in reviews) // len(reviews)} chars')

r = reviews[0]
print(f'\nSample:')
print(f'  Title:    {r["title"]}')
print(f'  Reviewer: {r["reviewer"]}')
print(f'  Rating:   {r["rating"]}')
print(f'  Text:     {r["review_text"][:200]}...')