# 🤝 Skill Swap Platform

A web application that connects people who want to exchange skills - learn something new while teaching something you know!

## 📋 Features

- **User Authentication**: Secure registration and login system
- **Skill Management**: Add skills you can teach and want to learn
- **User Discovery**: Browse and search for other users by skills
- **Swap Requests**: Send and receive skill exchange requests
- **Real-time Notifications**: Get notified about pending requests
- **Profile Management**: Update your profile and change passwords
- **Responsive Design**: Works on desktop and mobile devices

## 🛠️ Tech Stack

- **Backend**: Flask, SQLAlchemy, Flask-JWT-Extended
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: JWT tokens
- **Styling**: Custom CSS with modern animations

## 📁 Project Structure

```
skill-swap-platform/
├── app/                    # Modular Flask application
│   ├── __init__.py        # App factory
│   ├── simple_app.py      # Core app with models
│   ├── models/            # Database models
│   ├── routes/            # API route blueprints
│   ├── services/          # Business logic
│   └── utils/             # Helper functions
├── templates/             # HTML templates
│   └── index.html        # Main frontend
├── static/               # Static files
├── instance/             # Instance-specific files
├── app_standalone.py     # Standalone version
├── app.py               # Main app runner
├── create_test_users.py # Test data generator
├── delete_data.py       # Data cleanup utility
└── requirements.txt     # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone or download the project**
   ```bash
   cd path/to/your/project
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables (optional)**
   Create a `.env` file in the project root:
   ```
   DATABASE_URL=sqlite:///skillswap.db
   JWT_SECRET_KEY=your-secret-key-here
   FRONTEND_URL=http://localhost:3000
   ```

### Running the Application

You have two options to run the app:

#### Option 1: Modular Version (Recommended)
```bash
python app.py
```

#### Option 2: Standalone Version
```bash
python app_standalone.py
```

The application will be available at `http://127.0.0.1:5000`

## 📊 Test Data

### Create Test Users
To populate the database with sample users for testing:

```bash
# Create 10 test users (default)
python create_test_users.py

# Create a specific number of users
python create_test_users.py 25
```

**Default test user credentials:**
- Password for all test users: `password123`
- Emails follow the pattern: `user1@example.com`, `user2@example.com`, etc.

### Clean Database
To remove all data from the database:

```bash
python delete_data.py
```

## 🎯 Usage Guide

### Getting Started

1. **Register**: Create a new account with your name, email, and skills
2. **Browse Users**: Explore other users and their skills
3. **Send Requests**: Click "Connect & Swap Skills" to send exchange requests
4. **Manage Requests**: View and respond to requests in the "My Requests" tab
5. **Update Profile**: Modify your skills and information in "My Profile"

### API Endpoints

The application provides a REST API:

- **Authentication**: `/api/auth/*`
  - `POST /api/auth/register` - User registration
  - `POST /api/auth/login` - User login
  - `GET /api/auth/profile` - Get user profile
  - `PUT /api/auth/profile` - Update profile
  - `PUT /api/auth/change-password` - Change password

- **Users**: `/api/users/*`
  - `GET /api/users` - Get all users

- **Swap Requests**: `/api/swap-requests/*`
  - `POST /api/swap-requests` - Create request
  - `GET /api/swap-requests/my-requests` - Get sent requests
  - `GET /api/swap-requests/received` - Get received requests
  - `PUT /api/swap-requests/{id}` - Update request status

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///skillswap.db` |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | `your-secret-key-change-in-production` |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:3000` |

### Database

The app uses SQLite by default for development. To use PostgreSQL in production:

```bash
pip install psycopg2-binary
```

Set the `DATABASE_URL` environment variable:
```
DATABASE_URL=postgresql://username:password@localhost/skillswap
```

## 🐛 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database connection issues**
   - Ensure the database file is writable
   - Check the `DATABASE_URL` in your `.env` file

3. **Port already in use**
   ```bash
   # Kill process using port 5000
   # On Windows
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F
   
   # On macOS/Linux
   lsof -ti:5000 | xargs kill -9
   ```

4. **CORS issues**
   - Make sure you're accessing the app via `http://127.0.0.1:5000` not `localhost:5000`

### Debug Mode

The application runs in debug mode by default. To disable for production:

```python
# In app.py or app_standalone.py
app.run(debug=False, host='0.0.0.0', port=5000)
```

## 📝 Development

### Project Structure Explanation

- **[app_standalone.py](app_standalone.py)**: Complete application in a single file
- **[app/simple_app.py](app/simple_app.py)**: Core application with models and app factory
- **[app/routes/](app/routes/)**: Modular route blueprints for different features
- **[templates/index.html](templates/index.html)**: Single-page application frontend
- **[create_test_users.py](create_test_users.py)**: Utility to generate realistic test data

### Adding New Features

1. Add models to [`app/simple_app.py`](app/simple_app.py)
2. Create new route blueprints in [`app/routes/`](app/routes/)
3. Register blueprints in [`app/__init__.py`](app/__init__.py)
4. Update frontend in [`templates/index.html`](templates/index.html)

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Review the console/browser logs for error details
3. Ensure all dependencies are properly installed
4. Verify your Python version is 3.8 or higher

---

**Happy Skill Swapping! 🎉**