# UI File Upload Manual Test Guide

This document provides manual testing steps for the new batch file upload and directory selection features.

## Test Environment Setup

1. Start the TBCV server:
   ```bash
   python main.py
   ```

2. Open a web browser and navigate to `http://localhost:8000/dashboard`

3. Navigate to the Validations page

## Test Cases

### Test 1: Batch Validation - File Upload Mode

**Steps:**
1. Click "Run Validation" button
2. Select "Batch Files" from the Validation Mode dropdown
3. Verify "Batch Mode" dropdown appears with "Upload Files (from your computer)" selected
4. Click "Browse Files..." button
5. Select 2-3 markdown files from your computer
6. Verify selected files appear in the file list with:
   - File names
   - File sizes
   - Remove buttons
   - Total file count
   - Total size

**Expected Results:**
- Files are listed correctly
- File sizes are displayed in human-readable format (KB/MB)
- Total count and size are accurate
- Each file has a functional "Remove" button

### Test 2: Batch Validation - Drag and Drop

**Steps:**
1. Click "Run Validation" button
2. Select "Batch Files" from the Validation Mode dropdown
3. Drag and drop 2-3 markdown files into the drop zone
4. Verify files appear in the file list

**Expected Results:**
- Drop zone highlights when files are dragged over it
- Files are added to the list after dropping
- Duplicate files (same name and size) are not added twice
- Unsupported file types show a warning message

### Test 3: Batch Validation - Server Paths Mode

**Steps:**
1. Click "Run Validation" button
2. Select "Batch Files" from the Validation Mode dropdown
3. Change "Batch Mode" to "Server Paths (files on server)"
4. Verify textarea appears for entering file paths
5. Enter valid server file paths (one per line)
6. Click "Start Validation"

**Expected Results:**
- Textarea is shown for server paths
- File upload UI is hidden
- Validation starts successfully with server paths

### Test 4: Directory Workflow - Upload Mode

**Steps:**
1. Navigate to Workflows page
2. Click "Run Workflow" button
3. Select "Directory Validation" from Workflow Type dropdown
4. Verify "Directory Mode" shows "Upload Directory (from your computer)"
5. Click "Browse Directory..." button
6. Select a directory containing markdown files
7. Verify directory file list shows:
   - Directory name
   - Total file count
   - Total size
   - List of all files with paths and sizes

**Expected Results:**
- Directory selection dialog opens
- All valid files (.md, .txt, .html, .json, .yaml, .yml) are listed
- File paths show relative paths from directory root
- Total count and size are accurate
- Clear button works

### Test 5: Directory Workflow - Server Path Mode

**Steps:**
1. Click "Run Workflow" button
2. Select "Directory Validation"
3. Change "Directory Mode" to "Server Path (directory on server)"
4. Verify text input appears for directory path
5. Enter a valid server directory path
6. Enter a file pattern (e.g., "*.md")
7. Click "Start Workflow"

**Expected Results:**
- Text inputs are shown
- Directory upload UI is hidden
- Workflow starts successfully

### Test 6: Workflow Batch - Upload Mode

**Steps:**
1. Click "Run Workflow" button
2. Select "Batch Validation"
3. Verify "Upload Files" mode is selected by default
4. Upload 3-5 files using either:
   - Browse button
   - Drag and drop
5. Verify file list displays correctly
6. Click "Start Workflow"
7. Monitor workflow progress

**Expected Results:**
- Files upload successfully
- Workflow starts and shows progress
- Active runs section shows the workflow
- WebSocket updates show real-time progress

### Test 7: File Removal

**Steps:**
1. Upload multiple files to batch validation or workflow
2. Click "Remove" button on individual files
3. Verify file is removed from list
4. Verify counts and sizes update
5. Click "Clear All" button
6. Verify all files are removed

**Expected Results:**
- Individual remove works correctly
- List updates immediately
- Counts and sizes recalculate
- Clear All removes everything

### Test 8: File Type Validation

**Steps:**
1. Try to upload unsupported file types:
   - .exe
   - .zip
   - .png
   - .pdf (if not in supported list)
2. Verify warning messages appear
3. Verify unsupported files are not added to the list

**Expected Results:**
- Warning message: "Skipped [filename]: Unsupported file type"
- Only supported files are added to the list

### Test 9: Modal Close/Cancel

**Steps:**
1. Open validation/workflow modal
2. Upload some files
3. Click "Cancel" button
4. Reopen modal
5. Verify file list is empty

**Expected Results:**
- Selected files are cleared when modal closes
- Modal resets to initial state
- No files are retained from previous session

### Test 10: Large File Handling

**Steps:**
1. Upload a large file (> 1MB)
2. Verify file size is displayed correctly
3. Click "Start Validation/Workflow"
4. Monitor "Reading files..." progress indicator

**Expected Results:**
- Large files are handled without crashing
- Progress indicator shows while files are being read
- File size displays in MB
- Validation/workflow completes successfully

### Test 11: Multiple File Selection

**Steps:**
1. Click "Browse Files..." button
2. Use Ctrl+Click (Windows/Linux) or Cmd+Click (Mac) to select multiple files
3. Click Open
4. Verify all selected files are added

**Expected Results:**
- Multiple file selection works
- All selected files appear in the list
- No duplicates are added

### Test 12: Empty Submission Validation

**Steps:**
1. Open batch validation modal
2. Don't select any files
3. Keep "Upload Files" mode selected
4. Click "Start Validation"
5. Verify error message appears

**Expected Results:**
- Alert: "Please select at least one file to upload"
- Validation does not start
- Modal remains open

## Browser Compatibility Testing

Test all features in:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

Verify:
- File input works
- Drag and drop works
- Directory selection works (webkitdirectory attribute)
- Styling is consistent

## Performance Testing

**Test with:**
- 1 file
- 10 files
- 50 files
- 100 files

**Monitor:**
- UI responsiveness
- File reading time
- Upload progress
- Memory usage

## Notes

- Directory selection uses `webkitdirectory` attribute, which may have limited support in older browsers
- File reading is done client-side using FileReader API
- Large files may take time to read - ensure progress indicator is visible
- Drag and drop should work with both files and directories (browser dependent)

## Reporting Issues

When reporting issues, include:
1. Browser and version
2. File types and sizes tested
3. Number of files uploaded
4. Console errors (F12 Developer Tools)
5. Network requests (F12 Network tab)
6. Steps to reproduce
