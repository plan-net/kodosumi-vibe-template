# Installation Guide

## Prerequisites

- Python 3.12.2 (exact version required)
- Git
- A terminal or command prompt

## Important Note About Kodosumi

**Kodosumi is not available on PyPI** and must be installed directly from GitHub. Our installation scripts handle this automatically, but if you're installing manually, you'll need to run:

```bash
pip install git+https://github.com/masumi-network/kodosumi.git@dev
```

## Installation Methods

### 1. Using Installation Scripts (Recommended)

#### Linux/macOS
```bash
# Make the script executable
chmod +x install.sh

# Run the installation script
./install.sh
```

#### Windows
```bash
# Run the installation script
install.bat
```

The scripts will:
1. Create a virtual environment
2. Install the project in development mode
3. Install development dependencies
4. Install Kodosumi from GitHub (dev branch)
5. Create a .env file from .env.example if it doesn't exist

### 2. Manual Installation with pip

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Install Kodosumi from GitHub (dev branch)
pip install git+https://github.com/masumi-network/kodosumi.git@dev
```

### 3. Using requirements.txt (Legacy)

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Manual Kodosumi Installation

If you need more control over the Kodosumi installation:

```bash
# Clone the Kodosumi repository
git clone https://github.com/masumi-network/kodosumi.git

# Change to the Kodosumi directory
cd kodosumi

# Checkout the dev branch
git checkout dev

# Install in development mode
pip install -e .

# Return to your project directory
cd ..
```

## Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your settings:
   ```bash
   # Ray configuration
   RAY_TASK_NUM_CPUS=0.1
   RAY_TASK_MAX_RETRIES=3
   RAY_TASK_TIMEOUT=10.0
   RAY_BATCH_SIZE=1
   RAY_INIT_NUM_CPUS=2
   RAY_DASHBOARD_PORT=None

   # OpenAI configuration
   OPENAI_API_KEY=your_openai_api_key_here

   # Environment type
   KODOSUMI_ENVIRONMENT=false
   ```

## Verification

To verify your installation:

1. Run the tests:
   ```bash
   python -m pytest tests/
   ```

2. Try the example workflow:
   ```bash
   python -m workflows.crewai_flow.main
   ```

## Troubleshooting

### Common Issues

1. **Python Version Mismatch**
   - Error: "Python version must be 3.12.2"
   - Solution: Install Python 3.12.2 exactly

2. **Ray Connection Issues**
   - Error: "Failed to connect to Ray"
   - Solution: Start Ray with `ray start --head`

3. **Kodosumi Installation Fails**
   - Error: "Could not find a version that satisfies the requirement kodosumi"
   - Solution: Ensure you're installing from GitHub with the correct URL

4. **Environment Variables Missing**
   - Error: "OPENAI_API_KEY not found"
   - Solution: Copy `.env.example` to `.env` and fill in your API keys

For more help, check our [troubleshooting guide](troubleshooting.md) or open an issue on GitHub. 