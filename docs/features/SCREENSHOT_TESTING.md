# Screenshot Analysis Feature - Testing Guide

## Feature Overview
The AI Screenshot Analysis feature (FR-006) allows users to capture a screenshot of the current webpage and ask questions about it using a vision-capable AI model.

## How to Use

### Basic Usage
1. Navigate to any webpage
2. Press `Ctrl+Shift+S` to capture a screenshot
3. A notification will appear: "Screenshot captured! Ask a question about it."
4. The command palette will open with a 📷 icon
5. Type your question about the screenshot (e.g., "What is the main topic of this page?")
6. Press Enter to submit
7. The AI will analyze the screenshot and provide a response

### Example Questions
- "What is the main content on this page?"
- "Describe the layout and design of this webpage"
- "What colors are prominently used?"
- "Are there any forms or interactive elements?"
- "What text is visible in this screenshot?"
- "Summarize what this page is about"

## Technical Details

### Architecture
1. **Screenshot Capture**: Uses QWebEngineView.grab() to capture the visible webpage
2. **Image Encoding**: Converts QPixmap → QImage → PNG bytes → base64 encoding
3. **API Integration**: Sends to OpenRouter with GPT-4o vision model
4. **Response Processing**: Returns analysis as HTML content

### Key Components

#### 1. Base Engine Interface
```python
# src/minimal_browser/engines/base.py
@abstractmethod
def capture_screenshot(self, callback: Callable[[bytes], None]):
    """Capture a screenshot of the current page asynchronously"""
```

#### 2. Qt Implementation
```python
# src/minimal_browser/engines/qt_engine.py
def capture_screenshot(self, callback: Callable[[bytes], None]):
    pixmap = self._widget.grab()
    image = pixmap.toImage()
    # Convert to PNG bytes and call callback
```

#### 3. AI Worker Extension
```python
# src/minimal_browser/minimal_browser.py (AIWorker)
def __init__(self, query, current_url, history, screenshot_data=None):
    self.screenshot_data = screenshot_data

def _get_vision_response(self, query, current_url):
    # Sends multimodal request to OpenRouter API
    # with base64-encoded screenshot
```

#### 4. Browser Integration
```python
# src/minimal_browser/minimal_browser.py (VimBrowser)
def screenshot_analysis_mode(self):
    # Captures screenshot and prompts for question

def _start_screenshot_analysis(self, query):
    # Initiates AI worker with screenshot data
```

## Manual Testing Checklist

### Prerequisites
- [ ] OpenRouter API key configured
- [ ] Browser running with display (not headless)
- [ ] Test on different webpage types

### Test Cases

#### Test 1: Basic Screenshot Capture
- [ ] Open any webpage (e.g., https://github.com)
- [ ] Press `Ctrl+Shift+S`
- [ ] Verify notification: "Capturing screenshot..."
- [ ] Verify notification: "Screenshot captured! Ask a question about it."
- [ ] Verify command palette opens with 📷 icon

#### Test 2: Simple Question
- [ ] After capturing screenshot, type: "What is this page about?"
- [ ] Press Enter
- [ ] Verify loading overlay: "📷 Analyzing screenshot..."
- [ ] Verify AI response appears as HTML content
- [ ] Verify response is relevant to the captured page

#### Test 3: Detailed Analysis
- [ ] Capture screenshot of a complex page (e.g., Wikipedia article)
- [ ] Ask: "Describe the layout and main sections of this page"
- [ ] Verify response includes layout details
- [ ] Verify response mentions visible elements

#### Test 4: Empty Query Handling
- [ ] Press `Ctrl+Shift+S` to capture screenshot
- [ ] Press Enter without typing anything
- [ ] Verify notification: "Please provide a question about the screenshot"
- [ ] Verify returns to normal mode

#### Test 5: Multiple Screenshots
- [ ] Capture screenshot on page A, ask a question
- [ ] Navigate to page B
- [ ] Capture new screenshot, ask different question
- [ ] Verify each response corresponds to its respective screenshot

#### Test 6: Error Handling
- [ ] Disconnect from internet or use invalid API key
- [ ] Try to analyze a screenshot
- [ ] Verify error message is shown
- [ ] Verify browser doesn't crash

#### Test 7: Help Documentation
- [ ] Press F1 to open help
- [ ] Scroll to "Developer Tools" section
- [ ] Verify "Ctrl+Shift+S - Screenshot analysis with AI vision" is listed
- [ ] Scroll to "AI Integration" section
- [ ] Verify screenshot feature is mentioned

#### Test 8: Escape Key
- [ ] Press `Ctrl+Shift+S` to capture screenshot
- [ ] Command palette opens
- [ ] Press Escape
- [ ] Verify returns to normal mode without processing

## Vision Model Configuration

The feature uses OpenRouter with GPT-4o (gpt-4o has built-in vision capabilities).

### API Request Format
```python
{
    "model": "openai/gpt-4o",
    "messages": [
        {
            "role": "system",
            "content": "You are analyzing a screenshot of a webpage..."
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "User's question"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,..."
                    }
                }
            ]
        }
    ]
}
```

## Known Limitations

1. **Screenshot Size**: Large screenshots may result in larger API payloads
2. **Vision Model Availability**: Requires OpenRouter API key and vision-capable model
3. **No Screenshot Preview**: Screenshot is not shown to user before analysis
4. **Single Screenshot**: Only one screenshot can be pending at a time
5. **Browser Display Required**: Screenshots won't work in headless mode

## Future Enhancements

- [ ] Add screenshot preview before analysis
- [ ] Support multiple screenshots in conversation
- [ ] Allow screenshot annotation
- [ ] Add screenshot history/gallery
- [ ] Support OCR for text extraction
- [ ] Add screenshot cropping/region selection
- [ ] Support different vision models (Claude Vision, etc.)

## Troubleshooting

### Screenshot capture fails
- Ensure browser widget is initialized
- Check console for error messages
- Verify display is available (not headless)

### Vision API returns errors
- Verify OpenRouter API key is valid
- Check internet connection
- Ensure GPT-4o model is available
- Check API rate limits

### Response is irrelevant
- Try more specific questions
- Ensure webpage was fully loaded before screenshot
- Verify screenshot captured the intended content

## Code Review Points

1. ✅ Abstract method added to base engine
2. ✅ Qt implementation uses proper Qt image handling
3. ✅ AIWorker properly extended with optional parameter
4. ✅ Vision API call uses correct multimodal format
5. ✅ Error handling for screenshot capture failures
6. ✅ Error handling for API failures
7. ✅ UI feedback during capture and analysis
8. ✅ Help documentation updated
9. ✅ Keybinding properly registered
10. ✅ Command palette styling added

## Performance Considerations

- Screenshot capture: ~100-500ms (depends on page size)
- Base64 encoding: ~50-100ms
- API call: ~2-5 seconds (depends on network and model)
- Total time: ~3-6 seconds for typical workflow

## Security Considerations

- Screenshots may contain sensitive information
- Screenshots are sent to OpenRouter API (third-party service)
- No local caching of screenshots
- API key should be properly secured
