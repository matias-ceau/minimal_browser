# External Browser Integration

The Minimal Browser now includes comprehensive external browser integration that allows you to seamlessly open pages in your preferred system browsers while maintaining the vim-like workflow.

## Features

### 🔧 **Configurable Browser Preferences**
- Set your preferred default browser
- Define ordered browser preferences for fallback
- Enable/disable browser detection caching for performance
- Configurable timeouts for browser operations

### 🌐 **Intelligent Browser Management**
- **Smart Detection**: Automatically discovers available browsers on your system
- **Health Caching**: Tracks browser failures to avoid repeatedly trying broken browsers
- **Graceful Fallbacks**: Falls back to system default when preferred browser fails
- **Cross-Platform**: Works on Windows, macOS, and Linux

### ⌨️ **Rich Command Interface**
- **Vim Commands**: Full integration with the vim-style command system
- **Keyboard Shortcuts**: Quick access via dedicated keybindings
- **URL Validation**: Automatic protocol addition and data URL protection

## Configuration

Create or edit `~/.config/minimal_browser/config.toml`:

```toml
[browser]
# Set your preferred external browser
default_external_browser = "firefox"  # Options: firefox, chrome, chromium, safari, edge, opera

# Define browser preference order (first available is used)
preferred_browsers = ["firefox", "chrome", "chromium", "safari", "edge", "opera"]

# Performance settings
external_browser_timeout = 5.0  # Timeout in seconds
cache_browser_detection = true  # Cache browser availability
```

## Usage

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `e` | Open current page in external browser |
| `Ctrl+Shift+O` | Open current page in external browser |

### Vim Commands

| Command | Description | Example |
|---------|-------------|---------|
| `:browser` | Open current page in default external browser | `:browser` |
| `:browser <name>` | Open current page in specific browser | `:browser firefox` |
| `:browser <name> <url>` | Open specific URL in specific browser | `:browser chrome https://github.com` |
| `:browser-list` | List available browsers on system | `:browser-list` |
| `:ext` | Shorthand for external browser opening | `:ext` |

### Supported Browsers

The integration automatically detects these browsers when available:

- **Firefox** (`firefox`)
- **Google Chrome** (`chrome`)
- **Chromium** (`chromium`) 
- **Safari** (`safari`) - macOS only
- **Microsoft Edge** (`edge`)
- **Opera** (`opera`)

## Advanced Features

### Browser Health Monitoring

The system tracks browser failures and temporarily avoids browsers that consistently fail:

- Tracks up to 3 failures per browser within a 5-minute window
- Automatically retries browsers after the failure window expires
- Falls back to system default when preferred browsers are unhealthy

### Data URL Protection

The integration prevents opening AI-generated content (data URLs) in external browsers:

```
Cannot open data URLs in external browser
```

This protects against sending locally-generated AI responses to external browsers.

### URL Validation

URLs are automatically validated and corrected:

- Missing protocols are automatically prefixed with `https://`
- Invalid URLs are rejected with helpful error messages
- Proper encoding is maintained for complex URLs

## Examples

### Basic Usage
```bash
# In minimal browser, press 'e' to open current page in your default external browser
# Or use the command:
:browser
```

### Specific Browser
```bash
# Open current page in Firefox
:browser firefox

# Open GitHub in Chrome
:browser chrome https://github.com
```

### Browser Discovery
```bash
# See what browsers are available
:browser-list
# Output: "Available: firefox, chrome, chromium | Preferred: firefox"
```

## Troubleshooting

### Browser Not Found
If you see "Browser 'name' not found":
1. Check that the browser is installed and in your system PATH
2. Try using the full browser name (e.g., 'google-chrome' instead of 'chrome')
3. Use `:browser-list` to see detected browsers

### No Browsers Detected
If no browsers are detected:
1. The system will fall back to the OS default browser
2. Check your browser installations
3. Ensure browsers are properly registered with the system

### Configuration Issues
If configuration changes aren't taking effect:
1. Check the config file syntax with a TOML validator
2. Restart the minimal browser
3. Verify the config file location: `~/.config/minimal_browser/config.toml`

## Integration with Main Browser

This feature integrates seamlessly with the existing minimal browser workflow:

- Preserves current page state and buffer management
- Maintains vim-like command syntax and behavior
- Uses consistent notification system for user feedback
- Respects existing keybinding patterns and modal interface

## Technical Implementation

The external browser integration consists of:

- **`ExternalBrowserManager`**: Core management class with configuration support
- **`BrowserCache`**: Health and availability caching system
- **Enhanced Configuration**: Extended browser configuration options
- **Command Integration**: Vim command parser extensions
- **UI Integration**: Keybinding and help system updates

The implementation follows the established architectural patterns of the minimal browser while adding robust external browser capabilities.