# Messenger Chatbot

A basic Facebook Messenger chatbot built with FastAPI and uv package manager. This chatbot can handle text messages, provide automated responses, and maintain simple conversation context.

## Features

- ✅ Facebook Messenger webhook integration
- ✅ Webhook signature verification for security
- ✅ Basic conversation flow with context awareness
- ✅ Name recognition and personalized responses  
- ✅ Multiple response types (greetings, help, questions, etc.)
- ✅ Postback handling for buttons and quick replies
- ✅ Environment-based configuration
- ✅ FastAPI with automatic API documentation

## Prerequisites

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Facebook Developer Account
- Facebook App with Messenger integration
- ngrok or similar tool for local development (optional)

## Installation

### 1. Clone and Navigate to the Project

```bash
cd messenger-chatbot
```

### 2. Install uv (if not already installed)

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using pip
pip install uv
```

### 3. Install Dependencies

```bash
# Install all dependencies using uv
uv sync

# Or install in development mode with dev dependencies
uv sync --dev
```

### 4. Environment Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your Facebook App credentials:
```bash
VERIFY_TOKEN=your_custom_verify_token_here
PAGE_ACCESS_TOKEN=your_page_access_token_here  
APP_SECRET=your_app_secret_here
```

## Facebook App Setup

### 1. Create a Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click "Create App" → "Business" → "Next"
3. Fill in app details and create the app

### 2. Add Messenger Product

1. In your app dashboard, click "Add Product"
2. Find "Messenger" and click "Set Up"
3. Generate a Page Access Token for your Facebook page
4. Copy the token to your `.env` file as `PAGE_ACCESS_TOKEN`

### 3. Set Up Webhook

1. In Messenger settings, click "Add Callback URL"
2. Callback URL: `https://your-domain.com/webhook` (use ngrok for local development)
3. Verify Token: Use the same value as `VERIFY_TOKEN` in your `.env` file
4. Subscribe to webhook fields: `messages`, `messaging_postbacks`

### 4. Get App Secret

1. Go to App Settings → Basic
2. Copy the App Secret to your `.env` file as `APP_SECRET`

## Running the Application

### Development Mode

```bash
# Using uv
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the configured script
uv run start
```

### Production Mode

```bash
# Using uvicorn directly
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or using gunicorn (install first: uv add gunicorn)
uv run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

The application will be available at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Local Development with ngrok

For local testing with Facebook Messenger:

1. Install ngrok: https://ngrok.com/download
2. Start your FastAPI application:
```bash
uv run start
```
3. In another terminal, expose your local server:
```bash
ngrok http 8000
```
4. Use the ngrok HTTPS URL as your webhook URL in Facebook App settings

## API Endpoints

### Health Check
- **GET** `/` - Health check endpoint

### Webhook Endpoints
- **GET** `/webhook` - Webhook verification endpoint
- **POST** `/webhook` - Message handling endpoint

### API Documentation
- **GET** `/docs` - Swagger UI documentation
- **GET** `/redoc` - ReDoc documentation

## Project Structure

```
messenger-chatbot/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application and webhook handlers
│   └── chatbot.py       # Chatbot service and message processing logic
├── config/
│   ├── __init__.py
│   └── settings.py      # Application settings and environment variables
├── tests/               # Test files (create as needed)
├── .env.example         # Example environment variables
├── .env                 # Your environment variables (not in git)
├── .gitignore          # Git ignore rules
├── pyproject.toml      # Project configuration and dependencies
└── README.md           # This file
```

## Chatbot Features

### Supported Message Types

1. **Greetings**: Responds to hello, hi, hey, etc.
2. **Name Collection**: Asks for and remembers user names
3. **Help Requests**: Provides help information
4. **Product Inquiries**: Handles product/service questions
5. **Questions**: Responds to question formats
6. **Thanks**: Acknowledges gratitude
7. **Goodbyes**: Provides farewell messages
8. **Default Responses**: Handles unrecognized messages

### Conversation Context

The chatbot maintains simple conversation state including:
- User names
- Current conversation state
- Basic context for follow-up responses

## Customization

### Adding New Response Types

Edit `app/chatbot.py` and modify the `generate_response` method to add new message patterns and responses.

### Adding New Postback Handlers

Edit the `handle_postback` method in `app/chatbot.py` to handle new button clicks and quick replies.

### Configuration

Modify `config/settings.py` to add new environment variables and configuration options.

## Development Tools

### Code Quality

```bash
# Format code with Black
uv run black .

# Sort imports with isort  
uv run isort .

# Lint with flake8
uv run flake8 .
```

### Testing

```bash
# Run tests with pytest
uv run pytest

# Run tests with coverage
uv run pytest --cov=app
```

## Deployment

### Using Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml ./
COPY app/ ./app/
COPY config/ ./config/

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production

Set these environment variables in your production environment:

```bash
VERIFY_TOKEN=your_production_verify_token
PAGE_ACCESS_TOKEN=your_production_page_access_token
APP_SECRET=your_production_app_secret
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

## Security Considerations

1. **Webhook Signature Verification**: Always verify webhook signatures in production
2. **Environment Variables**: Never commit sensitive tokens to version control
3. **HTTPS**: Use HTTPS for all webhook URLs
4. **Rate Limiting**: Implement rate limiting for production applications
5. **Input Validation**: Validate all incoming message data

## Troubleshooting

### Common Issues

1. **Webhook Verification Failed**
   - Check that VERIFY_TOKEN matches in both .env and Facebook App settings
   - Ensure your webhook URL is accessible and returns the challenge

2. **Messages Not Being Received**
   - Verify webhook is subscribed to 'messages' field
   - Check APP_SECRET for signature verification
   - Ensure PAGE_ACCESS_TOKEN is correct

3. **Messages Not Being Sent**
   - Verify PAGE_ACCESS_TOKEN has send message permissions
   - Check Facebook API response for error details
   - Ensure recipient is subscribed to your page

### Debug Mode

Set `DEBUG=true` in your `.env` file to enable verbose logging.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the [Facebook Messenger Platform documentation](https://developers.facebook.com/docs/messenger-platform/)
- Review FastAPI documentation: https://fastapi.tiangolo.com/
- Create an issue in this repository