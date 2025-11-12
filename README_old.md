# ContextBridge Web Application

A multilingual idiom translation and management system with PostgreSQL database integration.

## 🚀 Quick Start

### 1. Start PostgreSQL Database
```bash
# Make sure PostgreSQL is running
brew services start postgresql
```

### 2. Install Python Dependencies
```bash
pip3 install -r idiom_requirements.txt
```

### 3. Start the Idiom API Server
```bash
python3 idiom_api_server.py
```
Server runs on: http://127.0.0.1:5001

### 4. Start the Translation API Server (Optional)
```bash
cd "Context Bridge"
python3 api_server.py
```
Server runs on: http://127.0.0.1:5000

### 5. Open the Web Application
Open `index.html` in your web browser to start using the application.

## 📁 Project Structure

```
BACAPSTONE/
├── index.html                  # Landing page
├── signin.html                 # Sign in page
├── playground.html             # Translation playground
├── analogies.html              # Idiom management page
├── analogies.js                # Frontend logic for idioms
├── styles.css                  # Global styles
├── logo.jpeg                   # Logo asset
├── unnamed.png                 # Background asset
├── idiom_api_server.py         # Flask API for idiom management
├── database_config.py          # PostgreSQL database operations
├── idiom_requirements.txt      # Python dependencies
├── README.md                   # This file
├── admin_tools/                # Admin tools & documentation
│   ├── README.md              # Admin tools guide
│   ├── view_idioms_html.py    # Generate HTML report of all idioms
│   ├── admin_panel.py         # Interactive admin panel
│   ├── idiom_training_manager.py  # Export for training
│   ├── setup_database.py      # Database setup script
│   └── *.md                   # Documentation files
└── Context Bridge/             # ML translation models
```

## 🗄️ Database Structure

The application uses PostgreSQL with the following tables:
- `english_idioms`
- `hindi_idioms`
- `telugu_idioms`
- `chinese_idioms`
- `german_idioms`
- `idiom_statistics`

Each idiom is stored privately with username, meaning, and timestamps.

## 🎯 Features

- **Add Idioms**: Users can add idioms in 5 languages
- **Search Idioms**: Search for specific idioms (private to user)
- **Statistics**: View count statistics by language
- **Translation**: Contextual translation between languages
- **Privacy**: Idioms are private - no public listing

## 🔧 Admin Access

For administrative tasks (viewing all idioms, exporting training data), see the tools in the `admin_tools/` folder:

```bash
# Generate HTML view of all idioms
cd admin_tools
python3 view_idioms_html.py
```

This creates `idioms_database_view.html` with all stored idioms for admin review.

## 🔐 Privacy Note

User-submitted idioms are stored privately. Only the admin can access all idioms for model training purposes using the tools in `admin_tools/`.

## 📝 License

Educational project for BA Capstone.
