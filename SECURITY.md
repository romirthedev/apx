# Cluely Security Features

## Overview
Cluely implements comprehensive security measures to ensure safe operation while maintaining full system control capabilities.

## Security Architecture

### 1. Permission Management
- **Full Disk Access**: Required for comprehensive file operations
- **Accessibility Access**: Enables keyboard/mouse control
- **Screen Recording**: Allows screen analysis and automation
- **Automation Access**: Permits AppleScript execution

### 2. Command Validation
- **Risk Assessment**: All commands are categorized by risk level
- **Pattern Matching**: Dangerous command patterns are blocked or require confirmation
- **Path Validation**: File operations are restricted to safe directories
- **Sandboxing**: Operations are contained within allowed boundaries

### 3. Confirmation System
- **High-Risk Operations**: Require explicit user confirmation
- **Confirmation Cache**: Recent confirmations are cached to avoid repetition
- **Timeout Protection**: Confirmations expire after a set time
- **Default Deny**: Unknown operations default to denial

### 4. Logging and Monitoring
- **Comprehensive Logging**: All actions are logged with timestamps
- **Action Audit**: Complete audit trail of system interactions
- **Error Tracking**: Failed operations and security violations are tracked
- **Log Rotation**: Automatic log cleanup and rotation

## Permission Setup

### Automated Setup
Run the setup script to automatically configure permissions:
```bash
./scripts/setup.sh
```

### Manual Setup
1. **Full Disk Access**
   - System Settings → Privacy & Security → Full Disk Access
   - Click "+" and add Cluely.app

2. **Accessibility**
   - System Settings → Privacy & Security → Accessibility
   - Enable Cluely.app

3. **Screen Recording**
   - System Settings → Privacy & Security → Screen & System Audio Recording
   - Enable Cluely.app

### Verification
Check permissions status:
```bash
npm run permissions-check
# or
./scripts/check-permissions.py
```

## Security Configuration

### Configuration File
Security settings are managed in `backend/config/security_config.json`:

```json
{
  "security": {
    "confirmation_required": {
      "file_operations": {
        "delete": true,
        "modify_system_files": true
      },
      "system_operations": {
        "admin_commands": true,
        "automation_scripts": true
      }
    },
    "sandboxing": {
      "enabled": true,
      "allowed_directories": ["~/Desktop", "~/Documents"],
      "blocked_directories": ["/System", "/usr/bin"]
    }
  }
}
```

### Risk Levels
- **Low**: Read operations, information gathering
- **Medium**: File creation, non-destructive modifications
- **High**: File deletion, script execution
- **Critical**: System-level changes, admin operations

## Safe Operation Guidelines

### Recommended Practices
1. **Start with Low-Risk Commands**: Test basic functionality first
2. **Review Confirmations**: Always read confirmation dialogs carefully
3. **Use Specific Paths**: Provide explicit file paths rather than wildcards
4. **Monitor Logs**: Regularly check action logs for unexpected activity

### Dangerous Operations
The following operations require extra caution:
- File deletion with `rm -rf`
- Permission changes with `chmod`
- Admin commands with `sudo`
- System service management
- Network operations

## Daemon Mode Security

### Background Service
When running as a daemon:
- Process runs with user privileges (not root)
- Network access limited to localhost by default
- Automatic restart on crashes
- Comprehensive logging to dedicated files

### Installation
```bash
# Install daemon
npm run install-daemon

# Check daemon status
launchctl list | grep cluely

# Uninstall daemon
npm run uninstall-daemon
```

## Troubleshooting

### Permission Denied Errors
1. Verify all required permissions are granted
2. Restart the application after granting permissions
3. Check system logs for security violations

### "Operation Not Permitted"
- Usually indicates missing accessibility or full disk access
- Re-run permission checker: `npm run permissions-check`
- Grant missing permissions in System Settings

### Unexpected Confirmations
- Commands may be flagged as high-risk due to pattern matching
- Review the command for dangerous patterns
- Use more specific, safer alternatives when possible

## Security Updates

### Regular Maintenance
- Update dependencies regularly
- Review security configuration quarterly
- Audit action logs monthly
- Test permission requirements after system updates

### Reporting Security Issues
If you discover security vulnerabilities:
1. Do not post publicly
2. Email security concerns to the development team
3. Provide detailed reproduction steps
4. Allow time for patches before disclosure

## Advanced Security Features

### AI Safety
- Content filtering for AI responses
- Prompt injection detection
- Command validation before execution
- Response length limits

### Rate Limiting
- Maximum commands per minute
- File operation throttling
- Network request limits
- Automatic cooldown periods

### Audit Trail
Complete audit trail includes:
- Command text and timestamp
- Risk level assessment
- User confirmations
- Execution results
- Error conditions
- System state changes

## Development Security

### Testing Mode
For development, enable safe testing:
```json
{
  "development": {
    "mock_dangerous_operations": true,
    "enable_testing_commands": true
  }
}
```

### Security Testing
- Test permission boundaries
- Verify confirmation dialogs
- Check logging completeness
- Validate sandboxing effectiveness
