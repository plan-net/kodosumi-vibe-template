#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up kodosumi-vibe-template environment...${NC}"

# Check if Python 3.12.2 is installed
if command -v python3.12 &>/dev/null; then
    python_version=$(python3.12 --version 2>&1 | awk '{print $2}')
    if [ "$python_version" = "3.12.2" ]; then
        echo -e "${GREEN}Python $python_version detected${NC}"
    else
        echo -e "${RED}Error: Python 3.12.2 is required but found $python_version${NC}"
        echo -e "${YELLOW}Please install Python 3.12.2 specifically and try again${NC}"
        exit 1
    fi
else
    echo -e "${RED}Error: Python 3.12.2 is required but not found${NC}"
    echo -e "${YELLOW}Please install Python 3.12.2 specifically and try again${NC}"
    exit 1
fi

# Create and activate virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3.12 -m venv venv
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install the project in development mode
echo -e "${YELLOW}Installing project in development mode...${NC}"
pip install -e .

# Install development dependencies
echo -e "${YELLOW}Installing development dependencies...${NC}"
pip install -e ".[dev]"

# Install dependencies with specific versions
echo -e "${YELLOW}Installing dependencies with specific versions...${NC}"
pip install "crewai==0.105.0" "ray>=2.6.0" "langchain>=0.0.267" "langchain-openai>=0.0.2" "langchain-community>=0.0.10"

# Install Kodosumi from GitHub
echo -e "${BLUE}NOTE: Kodosumi is not available on PyPI and must be installed from GitHub${NC}"
echo -e "${YELLOW}Installing Kodosumi from GitHub (dev branch)...${NC}"
pip install git+https://github.com/masumi-network/kodosumi.git@dev

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env file with your API keys${NC}"
fi

echo -e "${GREEN}Installation complete!${NC}"
echo -e "${GREEN}To activate the environment, run:${NC}"
echo -e "${YELLOW}source venv/bin/activate${NC}" 