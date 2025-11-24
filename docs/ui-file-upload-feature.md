# File Upload & Directory Selection Feature

## Overview

The TBCV system now supports user-friendly file and directory selection for batch validations and workflows. Users can choose between uploading files from their local computer or entering server-side file paths.

## Features

### 1. Batch Validation File Upload

**Location:** Dashboard → Validations → Run Validation → Batch Files

**Modes:**
- **Upload Files** (Default): Upload files from your computer
- **Server Paths**: Enter file paths from the server filesystem

#### Upload Files Mode

**Features:**
- Multiple file selection via browse dialog
- Drag-and-drop file upload
- Real-time file list preview
- Individual file removal
- Clear all files option
- File size display (KB/MB format)
- Total file count and size
- Supported file types: `.md`, `.txt`, `.html`, `.json`, `.yaml`, `.yml`

**How to Use:**
1. Click "Run Validation" button
2. Select "Batch Files" from Validation Mode
3. Choose "Upload Files" from Batch Mode (default)
4. Either:
   - Click "Browse Files..." and select multiple files
   - Drag and drop files into the drop zone
5. Review selected files in the list
6. Remove unwanted files using "Remove" button
7. Select family and validation types
8. Click "Start Validation"

#### Server Paths Mode

**Use Case:** When files are already on the server

**How to Use:**
1. Click "Run Validation" button
2. Select "Batch Files" from Validation Mode
3. Change Batch Mode to "Server Paths"
4. Enter file paths (one per line) in the textarea
5. Click "Start Validation"

### 2. Directory Validation Workflow

**Location:** Dashboard → Workflows → Run Workflow → Directory Validation

**Modes:**
- **Upload Directory**: Select and upload an entire directory
- **Server Path**: Enter server directory path with file pattern

#### Upload Directory Mode

**Features:**
- Directory selection dialog
- Automatic file filtering by extension
- Directory file count and total size
- File path preview (with relative paths)
- Clear directory selection

**How to Use:**
1. Click "Run Workflow" button
2. Select "Directory Validation"
3. Choose "Upload Directory" (default)
4. Click "Browse Directory..." button
5. Select a directory containing your files
6. Review the file list (shows all valid files in directory)
7. Select family and max workers
8. Click "Start Workflow"

**Note:** Directory selection uses the `webkitdirectory` HTML attribute, which is supported in modern browsers (Chrome, Edge, Firefox, Safari).

#### Server Path Mode

**Use Case:** When directory is on the server

**How to Use:**
1. Click "Run Workflow" button
2. Select "Directory Validation"
3. Change Directory Mode to "Server Path"
4. Enter directory path (e.g., `/path/to/docs`)
5. Enter file pattern (e.g., `*.md`, `*.txt`)
6. Click "Start Workflow"

### 3. Batch Workflow File Upload

**Location:** Dashboard → Workflows → Run Workflow → Batch Validation

Similar to batch validation, with the same upload capabilities.

## Technical Details

### Frontend Implementation

**File Selection:**
- Uses HTML5 `<input type="file" multiple>` for file selection
- Uses `webkitdirectory` attribute for directory selection
- FileReader API reads file contents client-side
- Drag-and-drop uses HTML5 Drag and Drop API

**File Validation:**
- Client-side file type checking by extension
- Duplicate detection (same name and size)
- Warning messages for unsupported file types

**UI Components:**
- Drop zones with visual feedback (hover effects)
- File list with file names, sizes, and remove buttons
- Progress indicators during file reading
- Summary statistics (count, total size)

### Backend Implementation

**API Endpoint:** `POST /api/validate/batch`

**Request Payload (Upload Mode):**
```json
{
  "files": ["file1.md", "file2.md"],
  "file_contents": [
    {"file_path": "file1.md", "content": "..."},
    {"file_path": "file2.md", "content": "..."}
  ],
  "family": "words",
  "validation_types": ["yaml", "markdown", "code"],
  "max_workers": 4,
  "upload_mode": true
}
```

**Request Payload (Server Mode):**
```json
{
  "files": ["/path/to/file1.md", "/path/to/file2.md"],
  "family": "words",
  "validation_types": ["yaml", "markdown"],
  "max_workers": 4,
  "upload_mode": false
}
```

**Data Models:**
```python
class FileContent(BaseModel):
    file_path: str
    content: str

class BatchValidationRequest(BaseModel):
    files: List[str]
    family: str = "words"
    validation_types: List[str]
    max_workers: int = 4
    upload_mode: bool = False
    file_contents: Optional[List[FileContent]] = None
```

### File Processing

**Upload Mode:**
1. Files are selected on client
2. FileReader API reads file contents
3. Contents sent to server in JSON payload
4. Server processes contents directly (no filesystem access needed)

**Server Mode:**
1. File paths entered by user
2. Server reads files from filesystem
3. Processes files using existing logic

## Browser Compatibility

| Feature | Chrome | Firefox | Edge | Safari |
|---------|--------|---------|------|--------|
| File Upload (multiple) | ✅ | ✅ | ✅ | ✅ |
| Drag and Drop | ✅ | ✅ | ✅ | ✅ |
| Directory Selection | ✅ | ✅ | ✅ | ✅ (iOS 13.4+) |

**Notes:**
- Directory selection requires modern browser (2018+)
- Drag and drop may have limitations in some browsers
- File size limits may vary by browser

## Performance Considerations

**Client-Side:**
- Large files (>10MB) may take time to read
- Progress indicator shows "Reading files..." during processing
- Memory usage increases with number/size of files

**Server-Side:**
- Batch processing uses configurable worker threads
- Default max_workers: 4 (adjustable 1-16)
- Workflow progress tracked via WebSocket

**Recommendations:**
- For large batches (50+ files), use server path mode
- For quick uploads (<10 files), use upload mode
- Monitor browser memory with developer tools

## Security Considerations

**File Type Validation:**
- Client-side validation by extension
- Server-side validation recommended
- Only text files should be processed

**File Size Limits:**
- Browser limits: Typically 500MB-2GB per file
- Server limits: Configurable (check server settings)
- Network limits: Upload time increases with size

**Content Validation:**
- Files are validated before processing
- Malicious content detection via validation agents
- Server-side sanitization recommended

## Troubleshooting

### Files Not Appearing in List

**Possible Causes:**
- Unsupported file type
- Duplicate file (same name and size)
- Browser permissions

**Solutions:**
- Check file extension is in supported list
- Try different files
- Check browser console for errors

### Directory Selection Not Working

**Possible Causes:**
- Browser doesn't support `webkitdirectory`
- Browser permissions denied

**Solutions:**
- Use modern browser (Chrome, Firefox, Edge, Safari)
- Grant file access permissions
- Try server path mode instead

### Upload Fails or Hangs

**Possible Causes:**
- Large file size
- Network timeout
- Browser memory limit

**Solutions:**
- Reduce file size or number of files
- Check network connection
- Clear browser cache
- Use server path mode for large batches

### Drag and Drop Not Working

**Possible Causes:**
- Browser restrictions
- File type not supported
- JavaScript errors

**Solutions:**
- Use browse button instead
- Check browser console for errors
- Ensure drag source is valid (not from restricted areas)

## Examples

### Example 1: Upload 5 Documentation Files

```
1. Click "Run Validation"
2. Select "Batch Files"
3. Drag and drop 5 .md files
4. Review file list
5. Select "words" family
6. Check validation types: YAML, Markdown, Links
7. Click "Start Validation"
8. Monitor progress in Active Validation Runs
```

### Example 2: Validate Entire Documentation Directory

```
1. Click "Run Workflow"
2. Select "Directory Validation"
3. Click "Browse Directory..."
4. Select your documentation folder
5. Review file list (should show all .md files)
6. Select "words" family
7. Set max workers to 4
8. Click "Start Workflow"
9. View progress in Active Workflow Runs
```

### Example 3: Server-Side Batch Validation

```
1. Click "Run Validation"
2. Select "Batch Files"
3. Change to "Server Paths"
4. Enter paths:
   /docs/api/endpoints.md
   /docs/guides/setup.md
   /docs/reference/config.md
5. Select validation types
6. Click "Start Validation"
```

## API Integration

### JavaScript Example (Client-Side)

```javascript
// Read files and create payload
async function uploadBatchValidation(files) {
    const fileContents = await Promise.all(
        files.map(async (file) => ({
            file_path: file.name,
            content: await readFileContent(file)
        }))
    );

    const payload = {
        files: files.map(f => f.name),
        file_contents: fileContents,
        family: 'words',
        validation_types: ['yaml', 'markdown'],
        max_workers: 4,
        upload_mode: true
    };

    const response = await fetch('/api/validate/batch', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });

    return await response.json();
}

function readFileContent(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = reject;
        reader.readAsText(file);
    });
}
```

### Python Example (Server-Side)

```python
from pathlib import Path

# Server path mode
files = [
    "/path/to/doc1.md",
    "/path/to/doc2.md"
]

payload = {
    "files": files,
    "family": "words",
    "validation_types": ["yaml", "markdown"],
    "max_workers": 4,
    "upload_mode": False
}

response = requests.post(
    "http://localhost:8000/api/validate/batch",
    json=payload
)
```

## Future Enhancements

Potential improvements for future versions:

1. **Folder Filtering**: Allow filtering by file type when selecting directory
2. **File Preview**: Show content preview before upload
3. **Chunked Upload**: Support for very large files
4. **Resume Upload**: Resume interrupted uploads
5. **Compression**: Compress files before upload
6. **Parallel Upload**: Upload files in parallel
7. **Progress Bar**: Individual file upload progress
8. **Recent Files**: Quick access to recently uploaded files
9. **Favorites**: Save common file/directory paths
10. **Cloud Integration**: Upload from Google Drive, Dropbox, etc.

## Related Documentation

- [API Reference](./api-reference.md)
- [Validation Types](./validation-types.md)
- [Workflow Management](./workflows.md)
- [Testing Guide](../tests/ui/test_file_upload_ui.md)
