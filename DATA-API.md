# Data Management API

This document describes the data file management endpoints that allow you to upload, list, download, update, and delete data files without needing to redeploy the application.

## Overview

The API provides full CRUD (Create, Read, Update, Delete) operations for managing data files:

- **Upload** new data files via HTTP
- **List** all available data files
- **Download** data files
- **Get metadata** about files (size, modification time, etc.)
- **Update/Replace** existing files
- **Delete** files you no longer need

**No redeployment required** - manage your datasets dynamically!

## Supported File Types

The following file types are supported:
- CSV (`.csv`)
- JSON (`.json`)
- Text (`.txt`)
- Excel (`.xlsx`)
- TSV (`.tsv`)

Maximum file size: **100MB**

## API Endpoints

### 1. List All Data Files

**Endpoint:** `GET /data`

**Description:** Returns a list of all data files with metadata.

**Example Request:**
```bash
curl http://localhost:5001/data
```

**Example Response:**
```json
{
  "files": [
    {
      "filename": "sales-data.csv",
      "size_bytes": 2048,
      "size_human": "2.00 KB",
      "modified": 1698624000.0,
      "created": 1698620000.0
    },
    {
      "filename": "customer-data.json",
      "size_bytes": 15360,
      "size_human": "15.00 KB",
      "modified": 1698625000.0,
      "created": 1698621000.0
    }
  ],
  "count": 2,
  "data_dir": "/app/data"
}
```

---

### 2. Upload a New Data File

**Endpoint:** `POST /data`

**Description:** Upload a new data file. Optionally overwrite if file exists.

**Parameters:**
- `file` (required): The file to upload (multipart/form-data)
- `overwrite` (optional): Set to `true` to overwrite existing files (default: `false`)

**Example Request:**
```bash
# Upload a new file
curl -X POST http://localhost:5001/data \
  -F "file=@/path/to/your/data.csv"

# Upload and overwrite if exists
curl -X POST http://localhost:5001/data \
  -F "file=@/path/to/your/data.csv" \
  -F "overwrite=true"
```

**Example Response (Success):**
```json
{
  "message": "File uploaded successfully",
  "file": {
    "filename": "data.csv",
    "size_bytes": 4096,
    "size_human": "4.00 KB",
    "modified": 1698626000.0,
    "created": 1698626000.0
  }
}
```

**Example Response (File Exists):**
```json
{
  "error": "File 'data.csv' already exists. Use overwrite=true to replace it."
}
```

---

### 3. Get File Information

**Endpoint:** `GET /data/<filename>/info`

**Description:** Get metadata about a specific file without downloading it.

**Example Request:**
```bash
curl http://localhost:5001/data/sales-data.csv/info
```

**Example Response:**
```json
{
  "filename": "sales-data.csv",
  "size_bytes": 2048,
  "size_human": "2.00 KB",
  "modified": 1698624000.0,
  "created": 1698620000.0
}
```

---

### 4. Download a Data File

**Endpoint:** `GET /data/<filename>`

**Description:** Download a specific data file.

**Example Request:**
```bash
# Download and save to local file
curl http://localhost:5001/data/sales-data.csv -O

# Download with custom name
curl http://localhost:5001/data/sales-data.csv -o my-local-copy.csv
```

---

### 5. Update/Replace a Data File

**Endpoint:** `PUT /data/<filename>`

**Description:** Replace an existing data file with new content.

**Parameters:**
- `file` (required): The new file content (multipart/form-data)

**Example Request:**
```bash
curl -X PUT http://localhost:5001/data/sales-data.csv \
  -F "file=@/path/to/updated-data.csv"
```

**Example Response:**
```json
{
  "message": "File updated successfully",
  "file": {
    "filename": "sales-data.csv",
    "size_bytes": 3072,
    "size_human": "3.00 KB",
    "modified": 1698627000.0,
    "created": 1698620000.0
  }
}
```

---

### 6. Delete a Data File

**Endpoint:** `DELETE /data/<filename>`

**Description:** Delete a data file.

**Example Request:**
```bash
curl -X DELETE http://localhost:5001/data/old-data.csv
```

**Example Response:**
```json
{
  "message": "File 'old-data.csv' deleted successfully"
}
```

---

## Complete Workflow Example

### 1. Upload a new dataset
```bash
curl -X POST http://localhost:5001/data \
  -F "file=@quarterly-sales.csv"
```

### 2. List all files to confirm upload
```bash
curl http://localhost:5001/data
```

### 3. Analyze the data
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the total revenue?",
    "filename": "quarterly-sales.csv"
  }'
```

### 4. Update the dataset with new data
```bash
curl -X PUT http://localhost:5001/data/quarterly-sales.csv \
  -F "file=@quarterly-sales-updated.csv"
```

### 5. Delete when no longer needed
```bash
curl -X DELETE http://localhost:5001/data/quarterly-sales.csv
```

---

## Python Client Example

```python
import requests

class DataAnalysisClient:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
    
    def list_files(self):
        """List all data files."""
        response = requests.get(f"{self.base_url}/data")
        response.raise_for_status()
        return response.json()
    
    def upload_file(self, filepath, overwrite=False):
        """Upload a new data file."""
        with open(filepath, 'rb') as f:
            files = {'file': f}
            data = {'overwrite': str(overwrite).lower()}
            response = requests.post(
                f"{self.base_url}/data",
                files=files,
                data=data
            )
            response.raise_for_status()
            return response.json()
    
    def get_file_info(self, filename):
        """Get file metadata."""
        response = requests.get(f"{self.base_url}/data/{filename}/info")
        response.raise_for_status()
        return response.json()
    
    def download_file(self, filename, save_path):
        """Download a data file."""
        response = requests.get(f"{self.base_url}/data/{filename}")
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(response.content)
    
    def update_file(self, filename, filepath):
        """Update/replace an existing file."""
        with open(filepath, 'rb') as f:
            files = {'file': f}
            response = requests.put(
                f"{self.base_url}/data/{filename}",
                files=files
            )
            response.raise_for_status()
            return response.json()
    
    def delete_file(self, filename):
        """Delete a data file."""
        response = requests.delete(f"{self.base_url}/data/{filename}")
        response.raise_for_status()
        return response.json()
    
    def analyze(self, question, filename):
        """Run analysis on a data file."""
        response = requests.post(
            f"{self.base_url}/analyze",
            json={"question": question, "filename": filename}
        )
        response.raise_for_status()
        return response.json()

# Usage
client = DataAnalysisClient()

# Upload a file
result = client.upload_file("my-data.csv")
print(result)

# List all files
files = client.list_files()
print(f"Total files: {files['count']}")
for file in files['files']:
    print(f"  - {file['filename']} ({file['size_human']})")

# Analyze the data
task = client.analyze(
    question="What is the median value?",
    filename="my-data.csv"
)
print(f"Task ID: {task['task_id']}")

# Update the file
client.update_file("my-data.csv", "my-data-v2.csv")

# Delete when done
client.delete_file("my-data.csv")
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "No file provided"
}
```

### 404 Not Found
```json
{
  "error": "File 'nonexistent.csv' not found"
}
```

### 409 Conflict
```json
{
  "error": "File 'data.csv' already exists. Use overwrite=true to replace it."
}
```

### 500 Internal Server Error
```json
{
  "error": "Detailed error message here"
}
```

---

## Security Considerations

1. **Filename Sanitization**: All filenames are sanitized using `secure_filename()` to prevent path traversal attacks.

2. **File Type Restrictions**: Only allowed file extensions can be uploaded (CSV, JSON, TXT, XLSX, TSV).

3. **File Size Limits**: Maximum file size is 100MB to prevent resource exhaustion.

4. **Directory Isolation**: Files are restricted to the designated data directory (`/app/data`).

### Production Recommendations:

- **Add Authentication**: Implement API keys or OAuth for production use
- **Add Authorization**: Control which users can upload/delete files
- **Virus Scanning**: Scan uploaded files for malware
- **Rate Limiting**: Prevent abuse with rate limits
- **Audit Logging**: Log all file operations for security audits
- **Encryption**: Encrypt sensitive data at rest and in transit (HTTPS)

---

## Kubernetes/Container Considerations

### Volume Mounts
The data directory is mounted as a volume, so uploaded files persist across container restarts:

```yaml
# In your deployment
volumeMounts:
  - name: data
    mountPath: /app/data
```

### Multiple Replicas
When running multiple Flask API pods:
- Use **ReadWriteMany** (RWX) storage class
- Or use object storage (S3, GCS, Azure Blob) instead of local files
- Consider implementing file locking for concurrent writes

### Storage Class
Choose appropriate storage:
```yaml
# k8s/pvc.yaml
spec:
  accessModes:
    - ReadWriteMany  # Required for multiple pods
  storageClassName: nfs  # Or efs, azurefile, etc.
```

---

## Limitations

1. **File Size**: Maximum 100MB per file (configurable)
2. **File Types**: Only CSV, JSON, TXT, XLSX, TSV supported
3. **Concurrent Access**: Basic implementation - consider file locking for production
4. **No Versioning**: Overwrites replace files completely (consider adding versioning)
5. **No Folders**: Flat file structure only (all files in `/app/data`)

---

## Future Enhancements

Potential improvements for future versions:

- [ ] Folder/directory support
- [ ] File versioning and history
- [ ] Batch upload/delete
- [ ] File compression/decompression
- [ ] Data validation on upload
- [ ] Preview/sampling endpoints
- [ ] Search/filter files by metadata
- [ ] Direct S3/GCS integration
- [ ] Streaming upload for large files
- [ ] Authentication and authorization
