"""
🤖 AI Agentic Wallet - Streamlit Demo App
LabLab Hackathon: Agentic Commerce on Arc

Deploy with: streamlit run app.py
"""

import streamlit as st
import asyncio
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="AI Agentic Wallet",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .wallet-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 16px;
        padding: 20px;
        color: white;
        margin: 10px 0;
    }
    .balance-amount {
        font-size: 2.5rem;
        font-weight: 700;
        color: #00d4aa;
    }
    .transaction-item {
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
    }
    .cost-badge {
        background: #ff6b6b;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'wallet_balance' not in st.session_state:
    st.session_state.wallet_balance = 10.0
if 'transactions' not in st.session_state:
    st.session_state.transactions = []
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Service costs
SERVICE_COSTS = {
    "weather": 0.001,
    "stock": 0.002,
    "news": 0.003,
}

def process_payment(amount: float, description: str) -> bool:
    """Process a USDC payment."""
    if st.session_state.wallet_balance >= amount:
        st.session_state.wallet_balance -= amount
        st.session_state.transactions.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "amount": amount,
            "description": description,
            "tx_hash": f"0x{hash(datetime.now().isoformat()) % (10**16):016x}"
        })
        return True
    return False

def get_weather(city: str) -> str:
    """Simulated weather API."""
    import random
    temps = ["18°C", "22°C", "25°C", "28°C", "15°C"]
    conditions = ["Sunny ☀️", "Cloudy ☁️", "Rainy 🌧️", "Clear 🌤️"]
    return f"**{city}**: {random.choice(temps)}, {random.choice(conditions)}"

def get_stock(symbol: str) -> str:
    """Simulated stock API."""
    import random
    price = round(random.uniform(100, 500), 2)
    change = round(random.uniform(-5, 5), 2)
    arrow = "📈" if change > 0 else "📉"
    return f"**{symbol.upper()}**: ${price} ({change:+.2f}%) {arrow}"

def get_news(topic: str) -> str:
    """Simulated news API."""
    headlines = [
        f"Breaking: Major developments in {topic} sector",
        f"Experts predict growth in {topic} industry",
        f"New innovations emerging in {topic}"
    ]
    return "\n".join([f"• {h}" for h in headlines])

# Header
st.markdown('<h1 class="main-header">🤖 AI Agentic Wallet</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center;color:#888;">Autonomous AI that pays for APIs with USDC on Arc Network</p>', unsafe_allow_html=True)

# Sidebar - Wallet Info
with st.sidebar:
    st.markdown("### 💰 Circle Wallet")
    st.markdown(f"""
    <div class="wallet-card">
        <p style="color:#888;margin:0;">Balance</p>
        <p class="balance-amount">{st.session_state.wallet_balance:.4f} USDC</p>
        <p style="color:#888;font-size:0.8rem;margin:0;">🔗 Arc Network (Testnet)</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📋 API Pricing")
    st.markdown("""
    | Service | Cost |
    |---------|------|
    | 🌤️ Weather | 0.001 USDC |
    | 📈 Stock | 0.002 USDC |
    | 📰 News | 0.003 USDC |
    """)
    
    st.markdown("### 🔧 Tech Stack")
    st.markdown("""
    - **AI**: Gemini 1.5 Flash
    - **Blockchain**: Arc Network
    - **Wallet**: Circle SDK
    - **Token**: USDC (Native Gas)
    """)
    
    if st.button("🔄 Reset Wallet"):
        st.session_state.wallet_balance = 10.0
        st.session_state.transactions = []
        st.session_state.messages = []
        st.rerun()

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 💬 Chat with Agent")
    
    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about weather, stocks, or news..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Process query
        prompt_lower = prompt.lower()
        response = ""
        
        if "weather" in prompt_lower:
            # Extract city
            words = prompt.split()
            city = "Mumbai"
            for i, word in enumerate(words):
                if word.lower() in ["in", "for", "at"] and i + 1 < len(words):
                    city = words[i + 1].strip("?.,!")
                    break
            
            if process_payment(SERVICE_COSTS["weather"], f"Weather API: {city}"):
                response = f"🌤️ {get_weather(city)}\n\n💳 *Paid 0.001 USDC*"
            else:
                response = "❌ Insufficient USDC balance!"
                
        elif any(w in prompt_lower for w in ["stock", "price", "ticker"]):
            # Extract symbol
            words = prompt.upper().split()
            symbol = "AAPL"
            for word in words:
                clean = word.strip("?.,!")
                if len(clean) <= 5 and clean.isalpha() and clean not in ["GET", "STOCK", "PRICE", "THE"]:
                    symbol = clean
                    break
            
            if process_payment(SERVICE_COSTS["stock"], f"Stock API: {symbol}"):
                response = f"📈 {get_stock(symbol)}\n\n💳 *Paid 0.002 USDC*"
            else:
                response = "❌ Insufficient USDC balance!"
                
        elif "news" in prompt_lower:
            words = prompt.lower().split()
            topic = "technology"
            for i, word in enumerate(words):
                if word in ["about", "on", "for"] and i + 1 < len(words):
                    topic = words[i + 1].strip("?.,!")
                    break
            
            if process_payment(SERVICE_COSTS["news"], f"News API: {topic}"):
                response = f"📰 **Latest on {topic}**:\n{get_news(topic)}\n\n💳 *Paid 0.003 USDC*"
            else:
                response = "❌ Insufficient USDC balance!"
                
        elif "balance" in prompt_lower or "wallet" in prompt_lower:
            response = f"💰 **Wallet Balance**: {st.session_state.wallet_balance:.4f} USDC"
            
        elif "history" in prompt_lower or "transactions" in prompt_lower:
            if st.session_state.transactions:
                tx_list = "\n".join([
                    f"• {tx['time']}: -{tx['amount']} USDC ({tx['description']})"
                    for tx in st.session_state.transactions[-5:]
                ])
                response = f"📋 **Recent Transactions**:\n{tx_list}"
            else:
                response = "📋 No transactions yet."
        else:
            response = "🤖 I can help with:\n- Weather: *'What's the weather in Tokyo?'*\n- Stocks: *'Get TSLA stock price'*\n- News: *'Latest news about AI'*\n- Balance: *'Check my wallet'*"
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

with col2:
    st.markdown("### 📜 Transaction History")
    
    if st.session_state.transactions:
        for tx in reversed(st.session_state.transactions[-10:]):
            st.markdown(f"""
            <div class="transaction-item">
                <span style="color:#888;">{tx['time']}</span><br>
                <span style="color:#ff6b6b;">-{tx['amount']}</span> USDC<br>
                <span style="font-size:0.8rem;">{tx['description']}</span><br>
                <span style="font-size:0.7rem;color:#666;">tx: {tx['tx_hash'][:20]}...</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No transactions yet. Try asking the agent a question!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#666;font-size:0.8rem;">
    Built for LabLab.ai Hackathon: Agentic Commerce on Arc | 
    <a href="https://github.com/your-repo">GitHub</a> |
    Powered by 🔵 Circle + 🤖 Gemini
</div>
""", unsafe_allow_html=True)
