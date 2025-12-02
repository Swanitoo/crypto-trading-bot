#!/usr/bin/env python3
"""
Test script to verify configuration and API connectivity
"""

import os
import sys
from dotenv import load_dotenv
from colorama import init as colorama_init, Fore, Style

colorama_init(autoreset=True)

def print_section(title):
    print(f"\n{Fore.CYAN}{'='*50}")
    print(f"{title}")
    print(f"{'='*50}{Style.RESET_ALL}")

def check_env_file():
    """Check if .env file exists and is configured"""
    print_section("📋 Checking Environment Configuration")

    env_path = 'config/.env'
    if not os.path.exists(env_path):
        print(f"{Fore.RED}❌ .env file not found at {env_path}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Run: cp config/.env.example config/.env{Style.RESET_ALL}")
        return False

    print(f"{Fore.GREEN}✅ .env file found{Style.RESET_ALL}")
    load_dotenv(env_path)
    return True

def check_openai_key():
    """Check OpenAI API key"""
    print_section("🤖 Checking OpenAI Configuration")

    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key:
        print(f"{Fore.RED}❌ OPENAI_API_KEY not set{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Add your key to config/.env{Style.RESET_ALL}")
        return False

    if api_key.startswith('sk-'):
        print(f"{Fore.GREEN}✅ OpenAI API key found (sk-...{api_key[-4:]}){Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠️  OpenAI API key format looks unusual{Style.RESET_ALL}")

    # Test OpenAI connection
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        print(f"{Fore.GREEN}✅ OpenAI API connection successful{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}❌ OpenAI API connection failed: {e}{Style.RESET_ALL}")
        return False

def check_binance_config():
    """Check Binance configuration"""
    print_section("💱 Checking Binance Configuration")

    mode = os.getenv('MODE', 'paper')
    print(f"Trading Mode: {Fore.YELLOW}{mode.upper()}{Style.RESET_ALL}")

    api_key = os.getenv('BINANCE_API_KEY', '')
    api_secret = os.getenv('BINANCE_API_SECRET', '')

    if mode == 'paper':
        print(f"{Fore.GREEN}✅ Paper trading mode - Binance keys not required{Style.RESET_ALL}")
        return True

    if not api_key or not api_secret:
        print(f"{Fore.RED}❌ Binance API keys not set (required for live trading){Style.RESET_ALL}")
        return False

    print(f"{Fore.GREEN}✅ Binance API keys found{Style.RESET_ALL}")

    # Test connection
    try:
        import ccxt
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True
        })
        balance = exchange.fetch_balance()
        print(f"{Fore.GREEN}✅ Binance API connection successful{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}❌ Binance API connection failed: {e}{Style.RESET_ALL}")
        return False

def check_dependencies():
    """Check if all dependencies are installed"""
    print_section("📦 Checking Dependencies")

    required = [
        'ccxt',
        'openai',
        'flask',
        'pandas',
        'ta',
        'sqlalchemy',
        'yaml',
        'colorama'
    ]

    all_ok = True
    for package in required:
        try:
            if package == 'yaml':
                __import__('yaml')
            else:
                __import__(package)
            print(f"{Fore.GREEN}✅ {package}{Style.RESET_ALL}")
        except ImportError:
            print(f"{Fore.RED}❌ {package} not installed{Style.RESET_ALL}")
            all_ok = False

    return all_ok

def check_config_file():
    """Check config.yaml"""
    print_section("⚙️  Checking Configuration File")

    config_path = 'config/config.yaml'
    if not os.path.exists(config_path):
        print(f"{Fore.RED}❌ config.yaml not found{Style.RESET_ALL}")
        return False

    print(f"{Fore.GREEN}✅ config.yaml found{Style.RESET_ALL}")

    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        print(f"\nTrading Configuration:")
        print(f"  Mode: {config['trading']['mode']}")
        print(f"  Initial Balance: ${config['trading']['initial_balance']}")
        print(f"  Trade Amount: ${config['trading']['trade_amount']}")
        print(f"  Take Profit: {config['trading']['take_profit_percent']}%")
        print(f"  Stop Loss: {config['trading']['stop_loss_percent']}%")
        print(f"  AI Enabled: {config['strategy']['use_ai']}")

        return True
    except Exception as e:
        print(f"{Fore.RED}❌ Error reading config: {e}{Style.RESET_ALL}")
        return False

def main():
    """Main test function"""
    print(f"{Fore.GREEN}")
    print("╔════════════════════════════════════════════════╗")
    print("║   Crypto Trading Bot - Configuration Test     ║")
    print("╚════════════════════════════════════════════════╝")
    print(f"{Style.RESET_ALL}")

    results = []

    results.append(("Environment File", check_env_file()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Config File", check_config_file()))
    results.append(("OpenAI API", check_openai_key()))
    results.append(("Binance Config", check_binance_config()))

    # Summary
    print_section("📊 Summary")

    all_passed = True
    for name, passed in results:
        status = f"{Fore.GREEN}✅ PASS" if passed else f"{Fore.RED}❌ FAIL"
        print(f"{status}{Style.RESET_ALL} - {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print(f"{Fore.GREEN}🎉 All checks passed! You're ready to run the bot.{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}Start the bot with:{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  python main.py{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  # or{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  ./start.sh{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ Some checks failed. Please fix the issues above.{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
