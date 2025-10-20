# Claude Instructions for Camera Project

## Git Commit Guidelines

**IMPORTANT**: Do NOT add Claude marketing or attribution to git commits.

❌ **DO NOT include**:
- "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
- "Co-Authored-By: Claude <noreply@anthropic.com>"
- Any Claude branding or marketing messages
- Emoji in commit messages unless explicitly requested

✅ **DO include**:
- Clear, concise commit message describing changes
- Technical details relevant to the change
- Breaking changes or important notes
- Professional, standard git commit format

## Example Good Commit Message

```
Implement working camera demo with face detection

- Flask + SocketIO implementation with real-time metadata
- OpenCV Haar Cascade face detection (CPU-based, 30 FPS)
- MJPEG video streaming with canvas overlay
- Docker containerized with NVIDIA GPU runtime
- Threading-based async mode fixes SocketIO blocking
- Tested on Jetson AGX Orin
```

## General Guidelines

- Keep commits professional and focused on technical content
- Follow standard git commit message conventions
- No marketing or branding in technical documentation
- Be concise but informative
