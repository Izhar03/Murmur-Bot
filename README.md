# Murmur Bot

An asynchronous WhatsApp affiliate bot that provides personalized product recommendations through intelligent message processing and affiliate link management.

## 🎯 Overview

Async Affbot is designed to optimize affiliate marketing strategies by automatically engaging with users in WhatsApp groups. It captures product inquiries, generates tailored recommendations, and manages affiliate links through an intuitive admin dashboard.

### Core Features

- **Asynchronous WhatsApp Integration**: Automated message capture and response using Selenium WebDriver
- **Smart Recommendation Engine**: Integration with Groq and Perplexity APIs for intelligent product suggestions
- **Admin Dashboard**: FastAPI-powered interface for managing affiliate links and responses
- **Database Management**: Robust SQLite database with asynchronous operations via aiosqlite
- **Customizable Configuration**: Easy setup through environment variables and configuration files

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- pip
- ChromeDriver (for Selenium automation)
- WhatsApp Web access

### Installation

1. Clone the repository
```bash
git clone https://github.com/YourRepo/AsyncAffbot.git
cd AsyncAffbot
```

2. Create and activate virtual environment
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment variables
```bash
# Create .env file and add your configurations
cp .env.example .env
```

## 💻 Usage

### Initialize Database
```bash
python initialize_db.py
```

### Start WhatsApp Automation
```bash
python whatsapp_automation.py
```

### Launch Admin Dashboard
```bash
uvicorn admin.main:app --reload
```

## 🔄 Workflow

1. **Message Detection**: The bot monitors WhatsApp groups for product inquiries
2. **Processing**: Captures relevant messages and analyzes product needs
3. **Recommendation Generation**: Fetches product suggestions via API integration
4. **Admin Review**: Dashboard allows review and affiliate link addition
5. **Response**: Sends personalized recommendations back to the group


## 🔜 Future Enhancements

- Multi-platform messaging support
- Additional product recommendation API integrations
- Enhanced analytics and reporting tools
- Machine learning-based recommendation improvements

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


## 📞 Contact

Email me at: izharhamdan@gmail.com

## 🙏 Acknowledgments

- Thanks to all contributors who have helped shape Async Affbot
- Special thanks to the open-source community for the tools and libraries used in this project
