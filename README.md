# DocCrawler

**DocCrawler** is a document acquisition module designed to automate the discovery, extraction, and downloading of unstructured documents from the web and other sources. It serves as the first stage in the document understanding pipeline.

## 🚀 Purpose

- Crawl public or private sources for documents (PDFs, HTML, DOCX, etc.)
- Apply domain specific filtering rules.
- Store documents in a structured format for downstream processing.


## ☁️ Azure Blob Storage

Crawled documents are stored in a centralized Azure Blob Storage container.

### 📂 Structure

| Purpose        | Blob Path Prefix | Description                                |
|----------------|------------------|--------------------------------------------|
| Crawled Docs   | `raw-docs/`      | PDFs or HTML documents downloaded by crawlers |
| Logs           | `logs/`          | Crawl reports, summaries, and errors       |

### 🔐 Access Configuration

```env
AZURE_STORAGE_ACCOUNT=multimodel
AZURE_STORAGE_KEY=<your-storage-key>
AZURE_CONTAINER_NAME=docunderstanding
```

### 🗂️ Example Upload Path

- Azure ML Job Output File: `outputs/my_crawled_file.pdf`  
- Upload to: `raw-docs/outputs/my_crawled_file.pdf`  
- Full URL:  https://multimodel.blob.core.windows.net/docunderstanding/raw-docs/outputs/my_crawled_file.pdf

> ✅ Use timestamped or UUID-based filenames to avoid overwriting. Organize documents in subfolders when appropriate (e.g., `raw-docs/batch-001/`).
