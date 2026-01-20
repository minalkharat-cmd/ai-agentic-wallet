#!/usr/bin/env python3
"""
Quick Demo Script for AI Agentic Wallet
Run this to test the project in demo mode.
"""

import asyncio
import sys
sys.path.insert(0, '.')

async def demo():
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║         🤖 AI AGENTIC WALLET - Quick Demo                             ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)
    
    from main import CircleWallet, PaidAPIService, AgenticOrchestrator
    
    # Initialize
    wallet = CircleWallet()
    api_service = PaidAPIService(wallet)
    orchestrator = AgenticOrchestrator(wallet, api_service)
    
    # Demo queries
    queries = [
        "Check my wallet balance",
        "What's the weather in Tokyo?",
        "Get TSLA stock price",
        "Show transaction history"
    ]
    
    print("Running demo queries...\n")
    
    for query in queries:
        print(f"📝 Query: {query}")
        response = await orchestrator.process(query)
        print(f"🤖 Response: {response}\n")
    
    print("✅ Demo complete!")

if __name__ == "__main__":
    asyncio.run(demo())
