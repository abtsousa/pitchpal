# TODO
# Get a simple Python script running
# Add logging and observability
# Get a streaming response going
# Import tools
# Test it out

from phoenix.otel import register
from datetime import datetime
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessageChunk, AIMessage
from tools import get_all_tools
from agent import get_agent, create_agent_config
from termcolor import colored, cprint

import getpass
import os
import logging
import argparse
import time

# Global variables
APP_NAME = "Tonibot"

# Logging
logging.basicConfig(level=logging.INFO, 
                    format="[%(levelname)s] (%(asctime)s) %(name)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)

# Phoenix tracing
def start_phoenix(phoenix_endpoint : str):
    register(
    project_name=APP_NAME,
    auto_instrument=True,
    endpoint=phoenix_endpoint,
    )
    logging.getLogger("openinference").setLevel(logging.CRITICAL)

# QA loop
def qa_loop(agent, config):
    while True:
        try:
            user_input = input("> ").strip()
            if user_input.lower() in {"exit", "quit"}:
                break

            #print(f"{APP_NAME}: ", end="", flush=True)

            start_time = time.time()
            
            for mode, chunk in agent.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config,
                stream_mode=["messages", "custom"],
            ):
                if mode == "messages" and isinstance(chunk[0], (AIMessageChunk, AIMessage)):
                    cprint(chunk[0].content, color="light_grey", attrs=["dark"], end="", flush=True)
                elif mode == "custom":
                    cprint(chunk, color="green", end="", flush=True)
            end_time = time.time()
            print()  # New line after the response
            logger.info(f"Response time: {(end_time - start_time)*1000:.0f} ms")
            
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

def main():
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument(
        "--phoenix-endpoint", 
        help="Phoenix endpoint URL (optional)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Enable logging (critical level if off, info/debug if on)"
    )
    parser.add_argument(
        "--model",
        choices=["google", "openai"],
        default="openai",
        help="Choose the model to use (default: openai)"
    )
    args = parser.parse_args()
    
    # Set logging level based on arguments
    if not args.log:
        logging.getLogger().setLevel(logging.CRITICAL)
    elif args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    else:
        logging.getLogger().setLevel(logging.INFO)
    
    if args.phoenix_endpoint:
        start_phoenix(args.phoenix_endpoint)
    
    


    # Use our custom agent
    agent = get_agent()
    
    # Create configuration
    config = create_agent_config(
        model_name=args.model,
        app_name=APP_NAME
    )

    # Run it
    qa_loop(agent, config)



if __name__ == "__main__":
    main()
