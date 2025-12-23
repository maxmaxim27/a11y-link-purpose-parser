from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
import json
import re
import os

HTML_FILE = "pizza-blog.html"
HEURISTIC_TEXTS = ["clicca qui", "qui", "leggi di più", "scopri", "scopri di più"]

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# check if text is heuristic
def is_heuristic_text(text):
    if not text:
        return False
    return text.lower().strip() in HEURISTIC_TEXTS


# remove extra whitespace and normalize text
def normalize(text):
    if not text:
        return text
    return re.sub(r"\s+", " ", text).strip()


# extract the accessible name following WCAG priority
# 1 - aria-label
# 2 - text    
# 3 - title
def get_accessible_name(link):

    aria_label = link.get("aria-label")
    if aria_label and aria_label.strip():
        return normalize(aria_label), "aria-label"
    
    def extract_text(element):
        text = []
        for child in element.children:
            # check if child is a string
            if isinstance(child, str):
                text.append(child)
            elif hasattr(child, 'name'):
                if child.get("aria-hidden") != "true":
                    text.append(extract_text(child))
        return "".join(text)
    
    text_content = normalize(extract_text(link))
    if text_content:
        return text_content, "text"
    
    title = link.get("title")
    if title and title.strip():
        return normalize(title), "title"
    
    return "none", "none"

# extract parent p for context
def get_context_simple(link):
    parent_p = link.find_parent("p")
    if parent_p:
        return normalize(parent_p.get_text())
    return ""

# ask openai to classify links based on their purpose
def classify_links(links):

    def extract_json(text):
        t = text.strip()
        if t.startswith("```"):
            t = re.sub(r"^```(?:json)?", "", t)
            t = re.sub(r"```$", "", t)
            t = t.strip()
        return t
    
    prompt = """
    You are a helpful assistant that will classify links in a web page.
    For each provided link, classify it under one of these categories, 
    if text is empty, use aria-label instead:

    - "clear": the link purpose is clear from the link text or aria-label alone.
    - "needs-context": the link text or aria-label is generic, but the surrounding context makes the purpose understandable.
    - "unclear": the link text or aria-label is vague and even the context does not clarify its purpose.

    You will receive:
    - "text": the accessible name
    - "source": where it comes from:
      - "aria-label": explicit label
      - "text": visible text content
      - "title": tooltip attribute
      - "none": no accessible name
    - "context": surrounding text

    This is the WCAG 2.4.4 "Link Purpose (In Context)" guideline:
    https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-in-context.html

    For each link:
    - If the rule is satisfied, set "pass" = true.
    - If the rule is not satisfied, set "pass" = false.
    - Always include a "reason" explaining the decision.

    Respond ONLY with a raw JSON array. Example:

    [
      {
        "id": 0,
        "href": "...",
        "text": "...",
        "classification": "clear | needs-context | unclear",
        "pass": true | false,
        "reason": "..."
      }
    ]

    Here are the links to analyze:
    """

    prompt += json.dumps(links, ensure_ascii=False, indent=2)

    response = client.chat.completions.create(
        model = "gpt-4o",
        messages = [
            {"role": "system", "content": "You are a WCAG accessibility expert."},
            {"role": "user", "content": prompt}
        ]
    )

    raw = response.choices[0].message.content
    clean = extract_json(raw)
    return json.loads(clean)


# analyze html
with open(HTML_FILE, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

results = {
    "rule": "wcag-2.4.4-link-purpose-in-context",
    "links": []
}

all_links_for_ai = []
for i, link in enumerate(soup.find_all("a")):
    href = link.get("href", "")
    text, source = get_accessible_name(link)
    context = get_context_simple(link)
    is_heuristic = is_heuristic_text(text)
    
    results["links"].append({
        "id": i,
        "href": href,
        "text": text,
        "context_excerpt": context,
        "heuristic_flag": is_heuristic
    })
    all_links_for_ai.append({
        "id": i,
        "href": href,
        "text": text,
        "source": source, 
        "context": context
    })

try:
    classification_result = classify_links(all_links_for_ai)
except Exception as e:
    print("Error calling OpenAI API:", e)
    classification_result = []

for link in results["links"]:
    link_id = link["id"]
    for cls in classification_result:
        if cls.get("id") == link_id:
            link["ai_classification"] = cls.get("classification")
            link["pass"] = cls.get("pass")
            link["reason"] = cls.get("reason")
            break
    del link["id"]

with open("results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("✓ Analisys completed")