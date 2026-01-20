# 🤖 AI Agentic Wallet - Agentic Commerce on Arc

> **LabLab.ai Hackathon Submission - January 2026**

An autonomous AI agent that manages USDC payments on Arc Network using Circle's Programmable Wallets, powered by Google Gemini for intelligent orchestration.

![Demo](docs/demo.gif)

## 🌟 Features

- **Pay-per-Request AI** - Agent automatically pays for API services in real-time with USDC
- **Cost-Conscious Reasoning** - Gemini-powered logic considers costs before making API calls
- **Real Blockchain Payments** - Uses Circle Programmable Wallets on Arc Network
- **Native USDC Gas** - Leverages Arc's unique USDC-native gas mechanism

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| **AI Engine** | Google Gemini 1.5 Flash |
| **Blockchain** | Arc Network (Circle L1) |
| **Wallet Infrastructure** | Circle Programmable Wallets |
| **Gas Token** | USDC (Native) |

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd lablab_agentic_commerce
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
# Edit .env with your credentials:
# - GEMINI_API_KEY (from https://aistudio.google.com/)
# - CIRCLE_API_KEY (from https://console.circle.com/)
# - CIRCLE_ENTITY_SECRET
```

### 3. Run the Agent

```bash
python main.py
```

## 💬 Usage Examples

```
You: What's the weather in Tokyo?
🤖 Agent: 🌤️ Weather in Tokyo: 22°C, Sunny | Cost: 0.001 USDC

You: Get TSLA stock price
🤖 Agent: 📈 TSLA: $248.50 (+2.3%) | Cost: 0.002 USDC

You: Check my wallet balance
🤖 Agent: 💰 Wallet Balance: 9.9970 USDC
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query                               │
│                        ↓                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │            Gemini Orchestrator                          │ │
│ │  • Intent Detection                                     │ │
│ │  • Cost Analysis                                        │ │
│ │  • Multi-step Planning                                  │ │
│ └─────────────────────────────────────────────────────────┘ │
│                        ↓                                    │
│ ┌──────────────────┐   ┌──────────────────────────────────┐ │
│ │  Circle Wallet   │ → │     Paid API Services            │ │
│ │  (Developer-     │   │  • Weather API (0.001 USDC)      │ │
│ │   Controlled)    │   │  • Stock API (0.002 USDC)        │ │
│ │                  │   │  • News API (0.003 USDC)         │ │
│ └──────────────────┘   └──────────────────────────────────┘ │
│         ↓                                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │              Arc Network (USDC Gas)                     │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Submission Details

**Circle Developer Console Email**: [YOUR_EMAIL@example.com]

> **⚠️ Required**: Update this email before submission!

## 🔗 Links

- [Arc Network Docs](https://docs.arc.network/)
- [Circle Developer Console](https://console.circle.com/)  
- [Google AI Studio](https://aistudio.google.com/)
- [LabLab.ai Hackathon](https://lablab.ai/event/agentic-commerce-on-arc)

## 📄 License

MIT License - Built for the LabLab.ai Agentic Commerce Hackathon 2026
