# Quick Fix: Enhancement Button Error

## Problem
The "Enhance" button in the web UI fails with an error because the `enhancements` variable is never initialized in the `_enhance()` method of the MCP server.

## Location
**File:** `svc/mcp_server.py`  
**Line:** 263  
**Method:** `_enhance()`

## Current Broken Code

```python
def _enhance(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance approved validation records.
    """
    ids = params.get("ids", [])
    if not ids:
        raise ValueError("ids parameter is required")
    
    enhanced_count = 0
    errors = []
    # ❌ BUG: Missing initialization of 'enhancements' list
    
    for validation_id in ids:
        try:
            # ... validation and enhancement logic ...
            
            enhanced_count += 1
            enhancements.append(audit_entry)  # ❌ NameError: 'enhancements' is not defined
            
        except Exception as e:
            errors.append(f"Error enhancing {validation_id}: {str(e)}")
    
    return {
        "success": True,
        "enhanced_count": enhanced_count,
        "errors": errors
        # ❌ Missing 'enhancements' key in return value
    }
```

## Fixed Code

```python
def _enhance(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance approved validation records.
    Args:
        params: Parameters containing ids list
    Returns:
        Enhancement results
    """
    ids = params.get("ids", [])
    if not ids:
        raise ValueError("ids parameter is required")
    
    enhanced_count = 0
    errors = []
    enhancements = []  # ✅ FIX: Initialize the list
    
    for validation_id in ids:
        try:
            # Get validation record
            records = self.db_manager.list_validation_results(limit=1000)
            validation = None
            for record in records:
                if record.id == validation_id:
                    validation = record
                    break
            
            if not validation:
                errors.append(f"Validation {validation_id} not found")
                continue
            
            # Check if validation is approved
            if validation.status != ValidationStatus.APPROVED:
                errors.append(f"Validation {validation_id} not approved (status: {validation.status})")
                continue
            
            # Load original markdown file
            file_path = Path(validation.file_path)
            if not file_path.exists():
                errors.append(f"File not found: {file_path}")
                continue
            
            # Read original content
            from core.io_win import read_text, write_text_crlf
            original_content = read_text(file_path)
            
            # Get enhancement prompts
            from core.prompt_loader import get_prompt
            try:
                enhancement_prompt = get_prompt("enhancer", "enhance_markdown")
            except Exception:
                # Fallback prompt if loader fails
                enhancement_prompt = """Please enhance this markdown document by:
1. Improving clarity and readability
2. Fixing any grammatical issues
3. Ensuring proper formatting
4. Adding missing sections if needed
5. Maintaining the original meaning and structure

Original content:
{content}

Enhanced content:"""
            
            # Call Ollama for enhancement
            from core.ollama import chat
            try:
                messages = [
                    {"role": "system", "content": "You are a technical writing assistant. Enhance markdown documents while preserving their structure and meaning."},
                    {"role": "user", "content": enhancement_prompt.format(content=original_content)}
                ]
                
                # Get model from environment or use default
                import os
                model = os.getenv("OLLAMA_MODEL", "llama2")
                response = chat(model, messages)
                enhanced_content = response.strip()
                
                # Write enhanced content atomically
                write_text_crlf(file_path, enhanced_content, atomic=True)
                
                # Create audit log entry
                audit_entry = {
                    "validation_id": validation_id,
                    "action": "enhance",
                    "timestamp": datetime.utcnow().isoformat(),
                    "original_size": len(original_content),
                    "enhanced_size": len(enhanced_content),
                    "model_used": model
                }
                
                # Update validation status to enhanced
                with self.db_manager.get_session() as session:
                    db_record = session.query(ValidationResult).filter(ValidationResult.id == validation_id).first()
                    if db_record:
                        db_record.status = ValidationStatus.ENHANCED
                        db_record.updated_at = datetime.utcnow()
                        # Store enhancement details in notes
                        current_notes = db_record.notes or ""
                        db_record.notes = f"{current_notes}\n\nEnhanced: {audit_entry}"
                        session.commit()
                
                enhanced_count += 1
                enhancements.append(audit_entry)  # ✅ FIX: Now this works
                
            except Exception as ollama_error:
                errors.append(f"Enhancement failed for {validation_id}: {str(ollama_error)}")
                
        except Exception as e:
            errors.append(f"Error enhancing {validation_id}: {str(e)}")
    
    return {
        "success": True,
        "enhanced_count": enhanced_count,
        "errors": errors,
        "enhancements": enhancements  # ✅ FIX: Return the enhancements list
    }
```

## Changes Made

1. **Line ~188:** Add `enhancements = []` to initialize the list
2. **Line ~263:** The `enhancements.append(audit_entry)` now works correctly
3. **Return statement:** Added `"enhancements": enhancements` to the return dictionary

## How to Apply the Fix

### Option 1: Manual Edit
1. Open `svc/mcp_server.py`
2. Find the `_enhance` method (around line 177)
3. Add `enhancements = []` after `errors = []` (around line 189)
4. Add `"enhancements": enhancements` to the return dict (around line 271)

### Option 2: Use str_replace (if using the system)
```python
# This would be done programmatically
str_replace(
    path="svc/mcp_server.py",
    old_str="""    enhanced_count = 0
    errors = []
    for validation_id in ids:""",
    new_str="""    enhanced_count = 0
    errors = []
    enhancements = []
    for validation_id in ids:"""
)
```

## Testing the Fix

After applying the fix, test with:

```bash
# Start the server
python main.py --mode api --port 8080

# In another terminal, test the enhancement endpoint
curl -X POST http://localhost:8080/api/enhance/val_abc123 \
  -H "Content-Type: application/json"
```

Or via the web UI:
1. Navigate to http://localhost:8080/dashboard
2. Find a validation with status "APPROVED"
3. Click the "Enhance" button
4. Should now work without errors

## Expected Behavior After Fix

1. Enhancement button click → Success
2. File gets enhanced via Ollama LLM
3. Original file is overwritten with enhanced content
4. Validation status changes to "ENHANCED"
5. Audit log is stored in notes field
6. Response includes list of enhancements made

## Additional Notes

### Known Limitation
The current enhancement logic:
- Overwrites original files directly (no backup)
- Uses Ollama LLM for enhancement
- Doesn't use the ContentEnhancerAgent (architectural inconsistency)

### Recommended Follow-up
After fixing this bug, consider:
1. Creating backups before enhancement
2. Refactoring to use ContentEnhancerAgent instead of direct Ollama calls
3. Adding unit tests for the _enhance method
4. Implementing batch enhancement capability
5. Adding rollback functionality

## Verification Checklist

- [ ] Fix applied to `svc/mcp_server.py`
- [ ] Server restarted
- [ ] Enhancement button tested in web UI
- [ ] No NameError appears in logs
- [ ] Enhanced content is written to file
- [ ] Database status updates to "ENHANCED"
- [ ] Audit log is created correctly
