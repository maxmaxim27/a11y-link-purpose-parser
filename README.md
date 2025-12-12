# a11y-link-purpose-parser

This tool parses an HTML file, extracts all `<a>` elements, collects their contextual information, and evaluates each link using OpenAI to determine whether it satisfies **WCAG 2.4.4 – Link Purpose (In Context)**.

The script classifies links into:
- **clear** – the link text clearly describes its purpose  
- **needs-context** – generic link text, but the surrounding context clarifies it  
- **unclear** – neither text nor context make the purpose understandable  

A final JSON report is generated with classification, pass/fail status, and explanation.

---

## 💥 Features

- Parses all links in an HTML page
- Extracts:
  - aria-label
  - link text
  - parent `<p>` context
- Sends all links to OpenAI in a single batch
- Classifies accessibility clarity following **WCAG 2.4.4**
- Returns structured JSON with:
  - AI classification
  - pass/fail
  - explanation
- Outputs `results.json`

---

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/maxmaxim27/a11y-link-purpose-parser.git
cd a11y-link-purpose-parser
```

### 2. Install dependencies
```bash
pip install beautifulsoup4
pip install openai
pip install python-dotenv
```

### 3. Set your OpenAI API key

Create a .env file in the project root with the following content:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Run the script

```bash
cd src/
python3 parse_html.py
```

**Note**: The script may take some time to complete depending on the number of <a> links in the HTML.

---

## 🚨 Limitations

- The analysis depends on the quality of the provided HTML.  
- Current implementation sends all links in a single OpenAI request, which may not scale efficiently for hundreds of links.  
- The classification is heuristic and AI-based, edge cases may require human review.  
- Links inside dynamically loaded content (e.g., via JavaScript) are not captured. 

---

## 🚀 Future Improvements & Features

Currently, the script evaluates links primarily based on their visible text or `aria-label` if the text is empty. Some potential enhancements include:

- **Use OpenAI Batch API for large HTML files** – When processing hundreds or thousands of links, a single request may exceed token limits. The Batch API could be used to split classification tasks efficiently and reduce cost at scale.
- **Check links containing images** – evaluate `alt` text or contextual description.  
- **Processing a specific url** – allow scanning a specific url instead of a .html file.  
- **Advanced contextual analysis** – consider surrounding headings, sections, or navigation landmarks for better classification.  
- **Performance optimizations** – cache results.  
