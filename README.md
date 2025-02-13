# Raycast AI Assistant Service

A backend service that improve responsivity of all the dictate features for the Raycast AI Assistant extention, providing intelligent responses and task automation through natural language processing.
See: https://github.com/pezzos/raycast-ai-assistant

## Features

- ⚡️ Reduce response times when using the Raycast AI Assistant extension

## Getting Started

### Prerequisites

- Python 3.8+
- Docker (optional)
- Raycast installed

### Installation

1. Clone the repository
```bash
git clone https://github.com/pezzos/raycast-ai-assistant-service.git
cd raycast-ai-assistant-service
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

Start the service:
```bash
python main.py
```

Or with Docker:
```bash
docker-compose up
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Alexandre "Pezzos" Pezzotta
- GitHub: [https://github.com/pezzos](https://github.com/pezzos)

## Acknowledgments

- Raycast team for their amazing platform
- Contributors who help improve this service
