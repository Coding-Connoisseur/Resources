# Fixing the issue by removing the invalid triple backticks from the script

import os
import sys
import ast
import json
import argparse
import re
import time
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from ~/.env
load_dotenv(dotenv_path=os.path.expanduser("~/.env"))

if not os.getenv("OPENAI_API_KEY") or "your-api-key" in os.getenv("OPENAI_API_KEY"):
    print("❌ ERROR: OPENAI_API_KEY is missing or placeholder. Set a valid key in your .env file.")
    sys.exit(1)


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader



# Constants
ALLOWED_EXTS = {
    '.py', '.js', '.ts', '.tsx', '.jsx',
    '.md', '.toml', '.nix'
}
SPECIAL_FILES = {'Dockerfile', 'Makefile'}
EXCLUDE_DIRS = {'node_modules', '.git', '.venv', 'venv', 'uploads'}
INPUT_FILE = "master_index.json"
OUTPUT_FILE = "master_index_enhanced.json"

# Tag rules
TAG_RULES = {
    "auth": "#auth",
    "user": "#user",
    "login": "#auth",
    "signup": "#auth",
    "schema": "#db",
    "query": "#db",
    "toast": "#notification",
    "inventory": "#inventory",
    "equipment": "#equipment",
    "workorder": "#work",
    "task": "#task",
    "form": "#form",
    "card": "#ui",
    "dialog": "#ui",
    "react": "#react",
    "vite": "#vite",
    "api": "#api",
    "notification": "#notification",
}

master_index = []

def extract_tags_and_summary(name, docstring):
    tags = set()
    summary = ""
    if docstring:
        summary = docstring.strip().split("\n")[0]
        lower = docstring.lower()
        for keyword, tag in TAG_RULES.items():
            if keyword in lower:
                tags.add(tag)
    return list(tags), summary

def parse_python_file_ast(path, source, rel_path):
    try:
        tree = ast.parse(source, filename=rel_path)
    except Exception:
        return []

    components = []
    tags, summary = extract_tags_and_summary(os.path.basename(rel_path), ast.get_docstring(tree))
    components.append({
        "type": "file",
        "name": os.path.basename(rel_path),
        "path": rel_path,
        "lineno": 1,
        "tags": tags,
        "summary": summary,
        "excerpt": source[:500]
    })

    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            tags, summary = extract_tags_and_summary(node.name, ast.get_docstring(node))
            components.append({
                "type": "class" if isinstance(node, ast.ClassDef) else "function",
                "name": node.name,
                "path": rel_path,
                "lineno": node.lineno,
                "tags": tags,
                "summary": summary,
                "excerpt": source[:500]
            })

    return components

def load_documents_and_index(src_dir: str):
    docs = []
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if fname in SPECIAL_FILES or ext in ALLOWED_EXTS:
                path = os.path.join(root, fname)
                rel_path = os.path.relpath(path, src_dir)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        source = f.read()
                        excerpt = source[:500]
                        if ext == ".py":
                            components = parse_python_file_ast(path, source, rel_path)
                            master_index.extend(components)
                        else:
                            master_index.append({
                                "type": "file",
                                "name": fname,
                                "path": rel_path,
                                "lineno": 1,
                                "tags": [],
                                "summary": "",
                                "excerpt": excerpt
                            })
                except Exception as e:
                    print(f"⚠️ Failed to parse {rel_path}: {e}")
                try:
                    docs.extend(TextLoader(path, encoding='utf-8').load())
                except Exception as e:
                    print(f"⚠️ Failed to load for embedding: {path}: {e}")
    return docs

def auto_tag(entry):
    tags = set(entry.get("tags", []))
    content = (entry.get("excerpt", "") + entry.get("name", "")).lower()
    for key, tag in TAG_RULES.items():
        if key in content:
            tags.add(tag)
    return sorted(list(tags))

def detect_frameworks(entry):
    excerpt = entry.get("excerpt", "").lower()
    frameworks = []
    if "react" in excerpt or entry["name"].endswith(".tsx"):
        frameworks.append("React")
    if "vite" in excerpt:
        frameworks.append("Vite")
    if "@radix-ui" in excerpt:
        frameworks.append("Radix UI")
    if "tailwind" in excerpt:
        frameworks.append("Tailwind")
    return frameworks

def detect_language(filename):
    ext = os.path.splitext(filename)[1]
    return {
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".js": "JavaScript",
        ".py": "Python"
    }.get(ext, "Unknown")

def summarize_entry(entry):
    prompt = f"""Summarize the following code excerpt in one natural sentence suitable for developers reviewing a project structure. Be specific about what the file or function does.

Excerpt:
{entry.get("excerpt", "")}
"""
    try:
        response = client.chat.completions.create(model="gpt-4",
        messages=[{
            "role": "user",
            "content": prompt
        }],
        temperature=0.5,
        max_tokens=80)
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ OpenAI error for {entry.get('name')}: {e}")
        return ""

def enhance_index(entries):
    enhanced = []
    for entry in entries:
        print(f"🔍 Enhancing {entry['path']}:{entry.get('name')}")
        entry["tags"] = auto_tag(entry)
        entry["frameworks"] = detect_frameworks(entry)
        entry["lang"] = detect_language(entry["name"])
        entry["summary"] = entry["summary"] or summarize_entry(entry)
        if "component" not in entry:
            entry["component"] = re.sub(r"[-_]", " ", os.path.splitext(entry["name"])[0]).title()
        enhanced.append(entry)
        time.sleep(0.5)
    return enhanced

def build_ai_index(src_dir: str, idx_dir: str):
    if not os.path.isdir(src_dir):
        print(f"ERROR: Source directory not found: '{src_dir}'")
        sys.exit(1)

    print(f"\n🔍 Scanning: {src_dir}")
    docs = load_documents_and_index(src_dir)
    print(f"✔️ Master index has {len(master_index)} components")

    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(master_index, f, indent=2)
        print(f"📄 Saved base index to {INPUT_FILE}")

    enhanced = enhance_index(master_index)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enhanced, f, indent=2)
        print(f"🎯 Saved enhanced index to {OUTPUT_FILE}")

    if not docs:
        print("❌ No documents found to embed.")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    print(f"✔️ Split into {len(chunks)} embedding chunks.")

    embedder = OpenAIEmbeddings()
    store = FAISS.from_documents(chunks, embedder)
    os.makedirs(idx_dir, exist_ok=True)
    store.save_local(idx_dir)
    print(f"🎉 FAISS vector index saved to {idx_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build and enhance AI-readable project index")
    parser.add_argument("--src", "-s", default=".", help="Source project directory to scan")
    parser.add_argument("--index", "-i", default="faiss_index", help="Output directory for FAISS index")
    args = parser.parse_args()

    build_ai_index(args.src, args.index)
