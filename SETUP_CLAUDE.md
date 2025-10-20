# Claude API Setup for EdgeMind

## Quick Setup

1. **Get your Anthropic API key:**

   - Go to https://console.anthropic.com/
   - Create an account or sign in
   - Go to API Keys section
   - Create a new API key

2. **Configure the API key:**

   ```bash
   # Edit the .env file
   ANTHROPIC_API_KEY=your-actual-api-key-here
   ```

3. **Test the setup:**
   ```bash
   python test_claude_strands.py
   ```

## Current Status ✅

- ✅ Strands agents framework installed with Anthropic support
- ✅ All 5 MEC agents configured with Claude models
- ✅ Swarm coordination system ready
- ✅ Integration tests passing

## Next Steps

1. Set your Claude API key in `.env`
2. Build the Streamlit dashboard (Phase 2)
3. Create demo scenarios (Phase 3)
4. AWS integration (Phase 4)

## Agent Configuration

Each agent uses Claude 3.5 Sonnet with:

- Temperature: 0.3 (consistent decision making)
- Max tokens: 2048
- Model: claude-3-5-sonnet-20241022

## Ready for Demo! 🚀

Your EdgeMind project is now properly configured with Claude-powered Strands agents. The swarm coordination system is ready for the AWS hackathon demonstration.
