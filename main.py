#!/usr/bin/env python3
"""
Crypto Trading Bot - Main Entry Point

A sophisticated cryptocurrency trading bot with:
- AI-powered market analysis using OpenAI
- Technical analysis with multiple indicators
- Risk management with stop-loss and take-profit
- Real-time web dashboard
- Paper trading mode for safe testing
"""

import os
import sys
import yaml
import logging
import argparse
from dotenv import load_dotenv
from colorama import init as colorama_init, Fore, Style

# Initialize colorama for colored terminal output
colorama_init(autoreset=True)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.bot.trader import TradingBot
from src.web.app import create_app, set_trading_bot


def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Set library loggers to WARNING to reduce noise
    logging.getLogger('ccxt').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)


def load_config(config_path='config/config.yaml'):
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"{Fore.RED}Error loading config: {e}{Style.RESET_ALL}")
        sys.exit(1)


def load_api_keys():
    """Load API keys from environment variables"""
    # Load .env file
    env_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()  # Try loading from current directory

    api_keys = {
        'binance_api_key': os.getenv('BINANCE_API_KEY', ''),
        'binance_api_secret': os.getenv('BINANCE_API_SECRET', ''),
        'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
    }

    # Check required keys
    if not api_keys['openai_api_key']:
        print(f"{Fore.RED}Error: OPENAI_API_KEY not found in environment{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please set it in config/.env file{Style.RESET_ALL}")
        sys.exit(1)

    # Binance keys are optional for paper trading
    mode = os.getenv('MODE', 'paper')
    if mode == 'live' and (not api_keys['binance_api_key'] or not api_keys['binance_api_secret']):
        print(f"{Fore.RED}Error: Binance API keys required for live trading{Style.RESET_ALL}")
        sys.exit(1)

    return api_keys


def print_banner():
    """Print welcome banner"""
    banner = f"""
{Fore.CYAN}{'='*70}
{Fore.GREEN}
   ███████╗██████╗ ██╗   ██╗██████╗ ████████╗ ██████╗     ██████╗  ██████╗ ████████╗
   ██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗╚══██╔══╝██╔═══██╗    ██╔══██╗██╔═══██╗╚══██╔══╝
   ██║     ██████╔╝ ╚████╔╝ ██████╔╝   ██║   ██║   ██║    ██████╔╝██║   ██║   ██║
   ██║     ██╔══██╗  ╚██╔╝  ██╔═══╝    ██║   ██║   ██║    ██╔══██╗██║   ██║   ██║
   ╚██████╗██║  ██║   ██║   ██║        ██║   ╚██████╔╝    ██████╔╝╚██████╔╝   ██║
    ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝        ╚═╝    ╚═════╝     ╚═════╝  ╚═════╝    ╚═╝
{Fore.CYAN}
   AI-Powered Cryptocurrency Trading Bot
   Version 1.0.0
{'='*70}{Style.RESET_ALL}
"""
    print(banner)


def print_config_summary(config, api_keys):
    """Print configuration summary"""
    mode = config['trading']['mode']
    mode_color = Fore.YELLOW if mode == 'paper' else Fore.RED

    print(f"\n{Fore.CYAN}Configuration:{Style.RESET_ALL}")
    print(f"  Trading Mode: {mode_color}{mode.upper()}{Style.RESET_ALL}")
    print(f"  Initial Balance: {Fore.GREEN}${config['trading']['initial_balance']}{Style.RESET_ALL}")
    print(f"  Trading Pairs: {Fore.CYAN}{', '.join(config['trading']['pairs'])}{Style.RESET_ALL}")
    print(f"  Trade Amount: {Fore.GREEN}${config['trading']['trade_amount']}{Style.RESET_ALL}")
    print(f"  Take Profit: {Fore.GREEN}+{config['trading']['take_profit_percent']}%{Style.RESET_ALL}")
    print(f"  Stop Loss: {Fore.RED}-{config['trading']['stop_loss_percent']}%{Style.RESET_ALL}")
    print(f"  AI Analysis: {Fore.MAGENTA}{'Enabled' if config['strategy']['use_ai'] else 'Disabled'}{Style.RESET_ALL}")
    print(f"  Dashboard Port: {Fore.CYAN}http://localhost:{os.getenv('FLASK_PORT', 5000)}{Style.RESET_ALL}")
    print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Crypto Trading Bot')
    parser.add_argument('--config', default='config/config.yaml', help='Path to config file')
    parser.add_argument('--mode', choices=['dashboard', 'cli', 'both'], default='both',
                       help='Run mode: dashboard only, CLI only, or both')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(log_level)

    # Print banner
    print_banner()

    # Load configuration
    config = load_config(args.config)
    api_keys = load_api_keys()

    # Print config summary
    print_config_summary(config, api_keys)

    # Initialize trading bot
    print(f"{Fore.CYAN}Initializing trading bot...{Style.RESET_ALL}")
    bot = TradingBot(config, api_keys)

    if args.mode in ['dashboard', 'both']:
        # Create Flask app
        print(f"{Fore.CYAN}Starting web dashboard...{Style.RESET_ALL}")
        app, socketio = create_app(config)
        set_trading_bot(bot)

        # Get port
        port = int(os.getenv('FLASK_PORT', 5000))

        print(f"\n{Fore.GREEN}✅ Dashboard available at: http://localhost:{port}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Open your browser and navigate to the URL above{Style.RESET_ALL}\n")

        if args.mode == 'both':
            # Start bot in a separate thread
            import threading
            bot_thread = threading.Thread(target=bot.start)
            bot_thread.daemon = True
            bot_thread.start()

        # Run Flask app (sans SocketIO pour éviter les crashs)
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True, use_reloader=False)

    else:  # CLI mode
        print(f"{Fore.GREEN}Starting bot in CLI mode...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Press Ctrl+C to stop{Style.RESET_ALL}\n")
        bot.start()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Bot stopped by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Fatal error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
