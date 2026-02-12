#!/usr/bin/env python3
"""
AI Agentic Wallet - LabLab Hackathon: Agentic Commerce on Arc
=============================================================

An autonomous AI agent that manages USDC payments on Arc Network using Circle's
Programmable Wallets, integrated with Google Gemini for intelligent orchestration.

Tech Stack:
- AI: Google Gemini 1.5 Flash/Pro
- Blockchain: Arc Network (Circle's L1, USDC native gas)
- Payments: Circle Developer-Controlled Wallets
- SDK: circle-developer-controlled-wallets

Author: LabLab Hackathon Team
Circle Developer Email: [YOUR_CIRCLE_DEV_EMAIL@example.com]
"""

import logging
import os
import asyncio
import json
import re
import sqlite3
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal

logger = logging.getLogger(__name__)

# Try to import Circle SDK
try:
    from circle.developer_controlled_wallets import DeveloperControlledWalletsClient
    from circle.developer_controlled_wallets.models import CreateWalletInput
    CIRCLE_SDK_AVAILABLE = True
except ImportError:
    CIRCLE_SDK_AVAILABLE = False
    logger.warning("Circle SDK not installed. Run: pip install circle-developer-controlled-wallets")

# Try to import Google AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google AI SDK not installed. Run: pip install google-generativeai")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CIRCLE_API_KEY = os.getenv("CIRCLE_API_KEY", "")
CIRCLE_ENTITY_SECRET = os.getenv("CIRCLE_ENTITY_SECRET", "")

# Arc Network RPC (testnet)
ARC_TESTNET_RPC = "https://rpc.testnet.arc.network"
ARC_MAINNET_RPC = "https://rpc.arc.network"


# ============================================================================
# RATE LIMITER
# ============================================================================

class RateLimiter:
    """Simple token-bucket rate limiter for API calls."""

    def __init__(self, max_calls: int = 10, period_seconds: float = 60.0):
        self.max_calls = max_calls
        self.period = period_seconds
        self._calls: List[float] = []

    def _prune(self):
        now = time.monotonic()
        self._calls = [t for t in self._calls if now - t < self.period]

    def allow(self) -> bool:
        """Return True if the call is allowed under the rate limit."""
        self._prune()
        if len(self._calls) < self.max_calls:
            self._calls.append(time.monotonic())
            return True
        return False

    @property
    def remaining(self) -> int:
        self._prune()
        return max(0, self.max_calls - len(self._calls))


# ============================================================================
# PERSISTENCE LAYER (SQLite)
# ============================================================================

class TransactionStore:
    """SQLite-backed persistence for wallet state and transaction history."""

    def __init__(self, db_path: str = "wallet_data.db"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._ensure_schema()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _ensure_schema(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT NOT NULL,
                params TEXT NOT NULL,
                cost_usdc REAL NOT NULL,
                tx_hash TEXT,
                result TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS wallet_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        conn.commit()

    def record_transaction(self, service: str, params: Dict, cost: float,
                           tx_hash: str, result: Any) -> int:
        conn = self._get_conn()
        cur = conn.execute(
            "INSERT INTO transactions (service, params, cost_usdc, tx_hash, result, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (service, json.dumps(params), cost, tx_hash,
             json.dumps(result), datetime.now().isoformat()),
        )
        conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_recent_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM transactions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_total_spent(self) -> float:
        conn = self._get_conn()
        row = conn.execute("SELECT COALESCE(SUM(cost_usdc), 0) AS total FROM transactions").fetchone()
        return float(row["total"])

    def set_state(self, key: str, value: str):
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO wallet_state (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()

    def get_state(self, key: str, default: str = "") -> str:
        conn = self._get_conn()
        row = conn.execute("SELECT value FROM wallet_state WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


# ============================================================================
# CIRCLE WALLET INTEGRATION
# ============================================================================

class CircleWallet:
    """
    Circle Programmable Wallet integration for Arc Network.
    Uses Developer-Controlled Wallets for seamless UX.
    """

    _ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
    _VALID_BLOCKCHAINS = {"ARC-TESTNET", "ARC-MAINNET"}

    def __init__(self):
        self.client = None
        self.wallet_id: Optional[str] = None
        self.wallet_address: Optional[str] = None
        self.wallet_set_id: Optional[str] = None

        if CIRCLE_SDK_AVAILABLE and CIRCLE_API_KEY:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize the Circle SDK client."""
        try:
            self.client = DeveloperControlledWalletsClient(
                api_key=CIRCLE_API_KEY,
                entity_secret=CIRCLE_ENTITY_SECRET
            )
            logger.info("Circle SDK client initialized")
        except Exception as e:
            logger.error("Failed to initialize Circle client: %s", e)
            self.client = None

    async def create_wallet_set(self, name: str = "agentic-commerce-wallets"):
        """Create a wallet set for organizing agent wallets."""
        if not self.client:
            return None

        try:
            response = self.client.create_wallet_set(
                name=name,
                idempotency_key=str(uuid.uuid4())
            )
            self.wallet_set_id = response.data.wallet_set.id
            logger.info("Created wallet set: %s", self.wallet_set_id)
            return self.wallet_set_id
        except Exception as e:
            logger.error("Wallet set creation failed: %s", e)
            return None

    async def create_wallet(self, blockchain: str = "ARC-TESTNET"):
        """Create a new programmable wallet on Arc Network."""
        if blockchain not in self._VALID_BLOCKCHAINS:
            raise ValueError(f"Invalid blockchain: {blockchain}. Must be one of {self._VALID_BLOCKCHAINS}")

        if not self.client:
            return self._demo_wallet()

        try:
            response = self.client.create_wallets(
                wallet_set_id=self.wallet_set_id,
                blockchains=[blockchain],
                count=1,
                idempotency_key=str(uuid.uuid4())
            )

            wallet = response.data.wallets[0]
            self.wallet_id = wallet.id
            self.wallet_address = wallet.address

            logger.info("Created wallet: %s", self.wallet_address)
            return {
                "id": self.wallet_id,
                "address": self.wallet_address,
                "blockchain": blockchain
            }
        except Exception as e:
            logger.error("Wallet creation failed: %s", e)
            return self._demo_wallet()

    async def get_balance(self) -> Dict[str, Any]:
        """Get wallet USDC balance."""
        if not self.client or not self.wallet_id:
            return {"usdc": 10.0, "native": 0.1}  # Demo values

        try:
            response = self.client.get_wallet_token_balances(wallet_id=self.wallet_id)
            balances = {}
            for token in response.data.token_balances:
                balances[token.token.symbol.lower()] = float(token.amount)
            return balances
        except Exception as e:
            logger.warning("Balance fetch failed: %s", e)
            return {"usdc": 10.0, "native": 0.1}

    async def transfer_usdc(
        self,
        to_address: str,
        amount: float,
        description: str = ""
    ) -> Dict[str, Any]:
        """Transfer USDC to another address (pay for API service)."""
        if not self._ADDRESS_RE.match(to_address):
            return {"success": False, "error": f"Invalid address format: {to_address}"}
        if amount <= 0:
            return {"success": False, "error": "Amount must be positive"}

        if not self.client or not self.wallet_id:
            return self._demo_transfer(to_address, amount, description)

        try:
            response = self.client.create_transaction(
                wallet_id=self.wallet_id,
                token_id="usdc",
                destination_address=to_address,
                amounts=[str(amount)],
                idempotency_key=str(uuid.uuid4()),
                fee_level="MEDIUM"
            )

            tx = response.data.transaction
            return {
                "success": True,
                "tx_hash": tx.txHash,
                "amount": amount,
                "to": to_address,
                "description": description,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error("Transfer failed: %s", e)
            return {"success": False, "error": str(e)}

    def _demo_wallet(self) -> Dict[str, Any]:
        """Return demo wallet for testing without API keys."""
        return {
            "id": "demo-wallet-001",
            "address": "0xDEMO..." + str(uuid.uuid4())[:8],
            "blockchain": "ARC-TESTNET",
            "mode": "demo"
        }

    def _demo_transfer(self, to: str, amount: float, desc: str) -> Dict[str, Any]:
        """Simulate transfer for demo mode."""
        return {
            "success": True,
            "tx_hash": f"0xDEMO{uuid.uuid4().hex[:56]}",
            "amount": amount,
            "to": to,
            "description": desc,
            "timestamp": datetime.now().isoformat(),
            "mode": "demo"
        }


# ============================================================================
# PAID API SERVICES (Pay-per-Request Framework)
# ============================================================================

class PaidAPIService:
    """
    Framework for paid API services that integrate with the agentic wallet.
    Each API call costs USDC, enabling true pay-per-request economics.
    """

    # Service addresses on Arc Network (demo addresses)
    SERVICE_ADDRESSES = {
        "weather": "0x1234567890abcdef1234567890abcdef12345678",
        "stock": "0xabcdef1234567890abcdef1234567890abcdef12",
        "news": "0xfedcba0987654321fedcba0987654321fedcba09",
        "translation": "0x1111111111111111111111111111111111111111",
    }

    # Service costs in USDC
    SERVICE_COSTS = {
        "weather": 0.001,
        "stock": 0.002,
        "news": 0.003,
        "translation": 0.005,
    }

    # Input length limits
    _MAX_PARAM_LEN = 200

    def __init__(self, wallet: CircleWallet, store: Optional[TransactionStore] = None,
                 rate_limiter: Optional[RateLimiter] = None):
        self.wallet = wallet
        self.store = store or TransactionStore()
        self.rate_limiter = rate_limiter or RateLimiter(max_calls=30, period_seconds=60)
        self.call_history: List[Dict[str, Any]] = []

    @staticmethod
    def _sanitize(value: str) -> str:
        """Strip control characters and limit length."""
        cleaned = re.sub(r"[^\w\s.,!?'-]", "", value)
        return cleaned[: PaidAPIService._MAX_PARAM_LEN]

    async def call_service(
        self,
        service_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a paid API service after processing payment."""

        if service_name not in self.SERVICE_COSTS:
            return {"error": f"Unknown service: {service_name}"}

        if not self.rate_limiter.allow():
            logger.warning("Rate limit exceeded for service %s", service_name)
            return {"error": "Rate limit exceeded. Please try again later."}

        # Sanitize string params
        sanitized_params = {
            k: self._sanitize(v) if isinstance(v, str) else v
            for k, v in params.items()
        }

        cost = self.SERVICE_COSTS[service_name]
        address = self.SERVICE_ADDRESSES[service_name]

        # Process payment
        payment = await self.wallet.transfer_usdc(
            to_address=address,
            amount=cost,
            description=f"{service_name} API call"
        )

        if not payment.get("success"):
            return {"error": "Payment failed", "details": payment}

        # Execute the service call
        result = self._execute_service(service_name, sanitized_params)

        tx_hash = payment.get("tx_hash", "")

        # Persist to SQLite
        self.store.record_transaction(
            service=service_name,
            params=sanitized_params,
            cost=cost,
            tx_hash=tx_hash,
            result=result,
        )

        # Keep in-memory history too (for backwards compatibility)
        call_record = {
            "service": service_name,
            "params": sanitized_params,
            "cost": cost,
            "payment_tx": tx_hash,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.call_history.append(call_record)

        logger.info("Service %s called successfully, cost=%.4f USDC, tx=%s",
                     service_name, cost, tx_hash)

        return {
            "success": True,
            "result": result,
            "cost_usdc": cost,
            "tx_hash": tx_hash
        }

    def _execute_service(self, service: str, params: Dict) -> Any:
        """Execute the actual service call (simulated for demo)."""
        import random

        if service == "weather":
            city = params.get("city", "Unknown")
            return {
                "city": city,
                "temperature": "22°C",
                "condition": "Sunny",
                "humidity": "45%",
                "wind": "12 km/h"
            }

        elif service == "stock":
            symbol = params.get("symbol", "AAPL")
            return {
                "symbol": symbol.upper(),
                "price": round(random.uniform(100, 500), 2),
                "change": round(random.uniform(-5, 5), 2),
                "volume": random.randint(1000000, 50000000)
            }

        elif service == "news":
            topic = params.get("topic", "technology")
            return {
                "topic": topic,
                "headlines": [
                    f"Breaking: AI makes breakthrough in {topic}",
                    f"Market update: {topic} sector sees major growth",
                    f"Experts predict future of {topic}"
                ]
            }

        elif service == "translation":
            text = params.get("text", "")
            target = params.get("target_language", "es")
            return {
                "original": text,
                "translated": f"[{target}] {text}",  # Simulated
                "language_pair": f"en-{target}"
            }

        return {"error": "Service not implemented"}


# ============================================================================
# GEMINI AI ORCHESTRATION
# ============================================================================

class AgenticOrchestrator:
    """
    The AI brain that orchestrates paid API calls with cost awareness.
    Uses Gemini for intent understanding and multi-step reasoning.
    """

    SYSTEM_PROMPT = """You are an autonomous AI agent managing a USDC wallet on Arc Network.
You can pay for API services in real-time using your Circle Programmable Wallet.

## Available Paid Services:
- weather(city): Get weather data. Cost: 0.001 USDC
- stock(symbol): Get stock price. Cost: 0.002 USDC
- news(topic): Get latest news. Cost: 0.003 USDC
- translation(text, target_language): Translate text. Cost: 0.005 USDC

## Free Actions:
- check_balance(): View your USDC wallet balance
- get_history(): View recent transaction history

## Important Rules:
1. ALWAYS consider the cost before calling paid services
2. Inform the user of the cost BEFORE making the call
3. If multiple services are needed, explain the total cost
4. Be efficient - don't make unnecessary API calls

Respond naturally while being cost-conscious. Format responses clearly."""

    _QUERY_MAX_LEN = 500

    def __init__(self, wallet: CircleWallet, api_service: PaidAPIService):
        self.wallet = wallet
        self.api_service = api_service
        self.model = None

        if GEMINI_AVAILABLE and GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel(
                'gemini-1.5-flash',
                system_instruction=self.SYSTEM_PROMPT
            )

    async def process(self, user_query: str) -> str:
        """Process user query with AI reasoning and cost-aware actions."""
        if not user_query or not user_query.strip():
            return "Please enter a query."

        user_query = user_query[: self._QUERY_MAX_LEN]

        # Get current wallet state
        balance = await self.wallet.get_balance()

        context = (
            f"Current Wallet State:\n"
            f"- USDC Balance: {balance.get('usdc', 0):.4f}\n"
            f"- Recent calls: {len(self.api_service.call_history)}\n\n"
            f"User Query: {user_query}\n"
        )

        if self.model:
            try:
                response = self.model.generate_content(context)
                ai_response = response.text
            except Exception as e:
                logger.error("Gemini API call failed: %s", e)
                ai_response = ""

            result = await self._execute_from_ai_response(ai_response, user_query)
            return result
        else:
            return await self._basic_routing(user_query, balance)

    async def _execute_from_ai_response(self, ai_response: str, query: str) -> str:
        """Parse AI response and execute detected intents."""
        query_lower = query.lower()

        if "weather" in query_lower:
            city = self._extract_city(query)
            result = await self.api_service.call_service("weather", {"city": city})
            if result.get("success"):
                data = result["result"]
                return (f"Weather in {data['city']}: {data['temperature']}, "
                        f"{data['condition']} | Cost: {result['cost_usdc']} USDC")
            return result.get("error", str(result))

        elif any(w in query_lower for w in ["stock", "price", "ticker"]):
            symbol = self._extract_symbol(query)
            result = await self.api_service.call_service("stock", {"symbol": symbol})
            if result.get("success"):
                data = result["result"]
                return (f"{data['symbol']}: ${data['price']:.2f} "
                        f"({data['change']:+.2f}%) | Cost: {result['cost_usdc']} USDC")
            return result.get("error", str(result))

        elif "news" in query_lower:
            topic = self._extract_topic(query)
            result = await self.api_service.call_service("news", {"topic": topic})
            if result.get("success"):
                data = result["result"]
                headlines = "\n".join([f"  - {h}" for h in data['headlines']])
                return (f"News on {data['topic']}:\n{headlines}\n\n"
                        f"Cost: {result['cost_usdc']} USDC")
            return result.get("error", str(result))

        elif "balance" in query_lower or "wallet" in query_lower:
            balance = await self.wallet.get_balance()
            total_spent = self.api_service.store.get_total_spent()
            return (f"Wallet Balance: {balance.get('usdc', 0):.4f} USDC | "
                    f"Total Spent: {total_spent:.4f} USDC")

        elif "history" in query_lower:
            # Pull from persistent store
            recent = self.api_service.store.get_recent_transactions(5)
            if not recent:
                return "No transactions yet."
            lines = [f"  - {c['service']}: {c['cost_usdc']} USDC @ {c['created_at'][:19]}"
                     for c in recent]
            return "Recent Transactions:\n" + "\n".join(lines)

        return ai_response if ai_response else "I can help with weather, stocks, news, or check your wallet balance!"

    async def _basic_routing(self, query: str, balance: Dict) -> str:
        """Basic keyword-based routing when Gemini is unavailable."""
        query_lower = query.lower()

        if "balance" in query_lower:
            total_spent = self.api_service.store.get_total_spent()
            return (f"Balance: {balance.get('usdc', 0):.4f} USDC | "
                    f"Total Spent: {total_spent:.4f} USDC")
        elif "weather" in query_lower:
            city = self._extract_city(query)
            result = await self.api_service.call_service("weather", {"city": city})
            if result.get("success"):
                data = result["result"]
                return (f"{data['city']}: {data['temperature']}, "
                        f"{data['condition']} | {result['cost_usdc']} USDC")
            return result.get("error", str(result))
        elif "stock" in query_lower:
            symbol = self._extract_symbol(query)
            result = await self.api_service.call_service("stock", {"symbol": symbol})
            if result.get("success"):
                data = result["result"]
                return f"{data['symbol']}: ${data['price']:.2f} | {result['cost_usdc']} USDC"
            return result.get("error", str(result))
        elif "news" in query_lower:
            topic = self._extract_topic(query)
            result = await self.api_service.call_service("news", {"topic": topic})
            if result.get("success"):
                data = result["result"]
                headlines = "\n".join([f"  - {h}" for h in data["headlines"]])
                return f"News on {data['topic']}:\n{headlines}\n\nCost: {result['cost_usdc']} USDC"
            return result.get("error", str(result))
        elif "history" in query_lower:
            recent = self.api_service.store.get_recent_transactions(5)
            if not recent:
                return "No transactions yet."
            lines = [f"  - {c['service']}: {c['cost_usdc']} USDC @ {c['created_at'][:19]}"
                     for c in recent]
            return "Recent Transactions:\n" + "\n".join(lines)

        return "Try: weather [city], stock [symbol], news [topic], or check balance"

    def _extract_city(self, query: str) -> str:
        """Extract city name from query."""
        words = query.split()
        for i, word in enumerate(words):
            if word.lower() in ["in", "for", "at"] and i + 1 < len(words):
                return words[i + 1].strip("?.,!")
        for word in words:
            if word and word[0].isupper() and word.lower() not in ["what", "how", "get", "check", "show"]:
                return word.strip("?.,!")
        return "Mumbai"

    def _extract_symbol(self, query: str) -> str:
        """Extract stock symbol from query."""
        words = query.upper().split()
        for word in words:
            clean = word.strip("?.,!")
            if 1 <= len(clean) <= 5 and clean.isalpha() and clean not in [
                "GET", "STOCK", "PRICE", "THE", "WHAT", "SHOW", "CHECK"
            ]:
                return clean
        return "AAPL"

    def _extract_topic(self, query: str) -> str:
        """Extract topic from query."""
        words = query.lower().split()
        for i, word in enumerate(words):
            if word in ["about", "on", "for"] and i + 1 < len(words):
                return words[i + 1].strip("?.,!")
        return "technology"


# ============================================================================
# MAIN APPLICATION
# ============================================================================

async def main():
    """Main entry point for the AI Agentic Wallet."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    print("""
    ===================================================================
             AI AGENTIC WALLET - Agentic Commerce on Arc
    ===================================================================
       An autonomous AI that pays for APIs with USDC on Arc Network

       Tech Stack:
          AI Engine: Google Gemini 1.5 Flash
          Blockchain: Arc Network (Circle L1)
          Payments: Circle Programmable Wallets
          Token: USDC (Native Gas)
    ===================================================================
    """)

    # Initialize components
    logger.info("Initializing wallet...")
    wallet = CircleWallet()
    store = TransactionStore()

    if wallet.client:
        await wallet.create_wallet_set()
        await wallet.create_wallet()
    else:
        logger.info("Running in demo mode (no Circle API key)")

    api_service = PaidAPIService(wallet, store=store)
    orchestrator = AgenticOrchestrator(wallet, api_service)

    # Display initial state
    balance = await wallet.get_balance()
    print(f"\nWallet Balance: {balance.get('usdc', 0):.4f} USDC")
    print(f"Total Spent: {store.get_total_spent():.4f} USDC")
    print("\nExamples:")
    print("   'What's the weather in Tokyo?'")
    print("   'Get TSLA stock price'")
    print("   'Latest news about AI'")
    print("   'Check my wallet balance'")
    print("   'Show transaction history'")
    print("   Type 'exit' to quit\n")

    # Main loop
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\nGoodbye!")
                break

            response = await orchestrator.process(user_input)
            print(f"\nAgent: {response}\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            logger.error("Unhandled error: %s", e)
            print(f"\nError: {e}\n")

    store.close()


if __name__ == "__main__":
    asyncio.run(main())
