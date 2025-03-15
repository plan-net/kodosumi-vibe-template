#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up kodosumi-vibe-template environment...${NC}"

# Check if Python 3.8+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}')
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 8 ]); then
    echo -e "${RED}Error: Python 3.8 or higher is required (found $python_version)${NC}"
    exit 1
fi

echo -e "${GREEN}Python $python_version detected${NC}"

# Create and activate virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv
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

# Install Kodosumi from GitHub
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