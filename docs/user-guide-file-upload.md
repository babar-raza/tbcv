# Quick Start Guide: File Upload Features

## What's New?

TBCV now makes it easy to validate multiple files and entire directories! You can upload files directly from your computer instead of typing file paths.

## Quick Start

### Validate Multiple Files

1. **Go to Validations** page
2. Click **"Run Validation"**
3. Select **"Batch Files"**
4. **Upload files:**
   - Click "Browse Files..." OR
   - Drag files into the drop zone
5. Click **"Start Validation"**

That's it! ✅

### Validate an Entire Directory

1. **Go to Workflows** page
2. Click **"Run Workflow"**
3. Select **"Directory Validation"**
4. Click **"Browse Directory..."**
5. Select your folder
6. Click **"Start Workflow"**

Done! ✅

## Common Tasks

### Upload Files for Validation

**Step-by-step:**

1. Open the **Validations** page from the dashboard
2. Click the green **"▶ Run Validation"** button
3. Choose **"Batch Files"** from the dropdown
4. You'll see two options:
   - **"Upload Files"** - for files on your computer (recommended)
   - **"Server Paths"** - for files already on the server

5. With **"Upload Files"** selected:
   - Click **"Browse Files..."** button
   - Select one or more files (hold Ctrl/Cmd for multiple)
   - OR drag and drop files into the drop zone

6. Review your files:
   - See file names and sizes
   - Remove unwanted files with "Remove" button
   - Click "Clear All" to start over

7. Choose settings:
   - **Family**: words, cells, slides, or pdf
   - **Validation Types**: Check the types you want
   - **Max Workers**: How many files to process at once (1-16)

8. Click **"Start Validation"**

### Upload a Directory

**Step-by-step:**

1. Open the **Workflows** page
2. Click **"▶ Run Workflow"**
3. Select **"Directory Validation"**
4. Two options available:
   - **"Upload Directory"** - from your computer
   - **"Server Path"** - directory on the server

5. With **"Upload Directory"** selected:
   - Click **"Browse Directory..."**
   - Select a folder
   - All valid files will be shown

6. Review the directory:
   - See total file count
   - See total size
   - Review all files that will be validated

7. Choose settings:
   - **Family**: words, cells, slides, or pdf
   - **Max Workers**: 1-16 (4 is recommended)

8. Click **"Start Workflow"**

## Tips & Tricks

### 💡 Drag and Drop

- Drag files from your file explorer directly into the drop zone
- The drop zone will highlight when files are over it
- Works with multiple files at once

### 💡 File Types

Supported file types:
- `.md` - Markdown files
- `.txt` - Text files
- `.html` - HTML files
- `.json` - JSON files
- `.yaml` / `.yml` - YAML files

Unsupported files will be skipped with a warning.

### 💡 Removing Files

- **Individual**: Click "Remove" next to any file
- **All**: Click "Clear All" button
- Files are only removed from the upload list, not deleted from your computer

### 💡 File Sizes

- File sizes are shown in KB or MB
- Total size is calculated automatically
- Large files may take longer to upload

### 💡 Progress Tracking

After starting a validation or workflow:
- Check the **"Active Validation Runs"** / **"Active Workflow Runs"** section
- Real-time progress updates via WebSocket
- Click "View" to see detailed results

## When to Use Each Mode

### Upload Files Mode

**Use when:**
- ✅ Files are on your local computer
- ✅ You want quick validation
- ✅ Working with less than 50 files
- ✅ Files are small to medium size (<10MB each)

**Advantages:**
- Easy file selection
- No need to know file paths
- Visual file management
- Drag and drop support

### Server Paths Mode

**Use when:**
- ✅ Files are already on the server
- ✅ Working with large batches (50+ files)
- ✅ Files are very large
- ✅ Automating validations

**Advantages:**
- No file upload needed
- Faster for large batches
- Can use wildcards/patterns (in directory mode)

## Troubleshooting

### "Please select at least one file"

**Problem:** Clicked "Start Validation" without selecting files

**Solution:**
1. Click "Browse Files..." or drag files to drop zone
2. Ensure files appear in the list
3. Try again

### Files Don't Appear After Selection

**Problem:** Selected files but list is empty

**Possible Causes:**
- Files are not supported types
- Files are duplicates
- Browser permission issue

**Solutions:**
- Check file extensions (.md, .txt, .html, .json, .yaml)
- Try different files
- Check browser console (F12) for errors

### Directory Selection Not Working

**Problem:** Can't select directory

**Possible Causes:**
- Browser doesn't support directory selection
- Need to update browser

**Solutions:**
- Use Chrome, Firefox, Edge, or Safari (latest version)
- Try "Server Path" mode instead
- Update your browser

### Upload Takes Too Long

**Problem:** Files take forever to upload

**Possible Causes:**
- Files are very large
- Too many files selected
- Slow network connection

**Solutions:**
- Upload fewer files at once
- Use "Server Path" mode for large batches
- Check network connection
- Split into multiple smaller batches

## Keyboard Shortcuts

When selecting files:
- **Ctrl + Click** (Windows/Linux) or **Cmd + Click** (Mac): Select multiple files
- **Ctrl + A** (Windows/Linux) or **Cmd + A** (Mac): Select all files in dialog

## Video Tutorial

*(Coming soon)*

## FAQ

**Q: How many files can I upload at once?**
A: There's no hard limit, but we recommend batches of 10-20 files for best performance. For larger batches, use "Server Path" mode.

**Q: What's the maximum file size?**
A: Depends on browser and server settings. Typically 50-100MB per file. For larger files, use "Server Path" mode.

**Q: Can I upload folders?**
A: Yes! Use "Directory Validation" in the Workflows page. Select a directory and all valid files will be included.

**Q: Are my files stored on the server?**
A: In "Upload Files" mode, file contents are processed but not permanently stored. Validation results are stored in the database.

**Q: Can I upload files from cloud storage?**
A: Currently no. You need to download files to your computer first, or use "Server Path" mode if files are on the server.

**Q: Does drag and drop work on mobile?**
A: Drag and drop is limited on mobile devices. Use the "Browse" button instead.

**Q: Can I validate files in subfolders?**
A: Yes! When you select a directory, all files in subfolders are included (filtered by supported types).

**Q: What happens if validation fails?**
A: Failed validations are marked with error status. Check the validation details for specific error messages.

## Getting Help

If you encounter issues:

1. **Check this guide** for common solutions
2. **Browser console**: Press F12 and check for errors
3. **Server logs**: Check `data/logs/tbcv.log`
4. **Report issue**: Create an issue on GitHub with:
   - Browser and version
   - Steps to reproduce
   - Console errors
   - File types and sizes

## Next Steps

- Learn about [Validation Types](./validation-types.md)
- Explore [Workflow Features](./workflows.md)
- Read [API Documentation](./api-reference.md)
- Check [Advanced Features](./ui-file-upload-feature.md)
