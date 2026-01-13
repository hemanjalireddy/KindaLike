# KindaLike - Restaurant Recommender Chatbot

A niche-based restaurant recommendation system that uses user preferences to provide personalized restaurant suggestions through a chatbot interface.

## Project Overview

KindaLike is a web application that collects detailed user preferences through an interactive survey and uses this information to recommend restaurants that match their taste. The system creates user profiles based on cuisine preferences, price range, dining style, dietary restrictions, and atmosphere preferences.

## Features (Current Implementation)

### Frontend
- **User Authentication**
  - Login page with username and password
  - Signup page with password confirmation
  - Client-side form validation

- **Preference Survey**
  - Multi-step survey (5 categories)
  - Clean, intuitive radio button interface
  - Progress tracking
  - Categories covered:
    - Cuisine Type (Italian, Chinese, Mexican, Indian, Japanese, American)
    - Price Range (Budget, Moderate, Upscale, Fine Dining)
    - Dining Style (Dine-in, Takeout, Delivery, No Preference)
    - Dietary Restrictions (None, Vegetarian, Vegan, Gluten-Free, Halal, Kosher)
    - Atmosphere (Casual, Romantic, Family-Friendly, Trendy, Quiet)

- **Modern UI**
  - Responsive design
  - Gradient styling with smooth animations
  - Progress indicators
  - Mobile-friendly interface

## Tech Stack

### Frontend
- **React** - UI library
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **CSS3** - Styling with gradients and animations

### Current State (MVP)
- User data temporarily stored in localStorage
- No backend integration yet
- No database persistence yet

## Project Structure

```
KindaLike/
├── src/
│   ├── pages/
│   │   ├── Login.jsx          # User login page
│   │   ├── Signup.jsx         # User registration page
│   │   └── Survey.jsx         # Multi-step preference survey
│   ├── components/            # (Empty - for future components)
│   ├── App.jsx               # Main app with routing
│   ├── App.css               # Global styles
│   └── main.jsx              # Application entry point
├── index.html                # HTML template
├── vite.config.js            # Vite configuration
├── package.json              # Dependencies and scripts
├── .gitignore               # Git exclusions
└── README.md                # Project documentation
```

## Getting Started

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone https://github.com/hemanjalireddy/KindaLike.git
cd KindaLike
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open your browser and navigate to:
```
http://localhost:5173
```

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## How It Works (Current Flow)

1. **User Registration/Login**
   - User creates an account or logs in
   - Username is stored in localStorage (temporary)

2. **Preference Survey**
   - User is redirected to a 5-step survey
   - Each step collects one category of preferences
   - Progress bar shows completion status
   - User can navigate back and forth between steps

3. **Profile Completion**
   - All preferences are collected
   - Data is logged to console (for now)
   - Ready for backend integration

## Future Implementation

### Phase 2 - Backend Integration
- [ ] Set up Node.js/Express backend
- [ ] Implement database (MongoDB/PostgreSQL)
- [ ] Create API endpoints for user authentication
- [ ] Store user profiles in database
- [ ] Implement secure password hashing

### Phase 3 - Chatbot Service
- [ ] Integrate AI/NLP service for chatbot
- [ ] Connect chatbot to user preference data
- [ ] Implement restaurant database/API
- [ ] Build recommendation algorithm
- [ ] Create chat interface

### Phase 4 - Enhanced Features
- [ ] User dashboard
- [ ] Edit preferences
- [ ] Restaurant favorites
- [ ] Review system
- [ ] Location-based recommendations

## Current Limitations

- **No Backend**: User data is not persisted
- **No Authentication**: Login/signup don't verify credentials
- **No Database**: All data is temporary (localStorage)
- **No Chatbot**: Recommendation system not yet implemented

## What to Push to GitHub

**Include:**
- All source code (`src/` folder)
- Configuration files (`vite.config.js`, `package.json`)
- HTML template (`index.html`)
- Documentation (`README.md`)
- `.gitignore` file

**Exclude (already in .gitignore):**
- `node_modules/` - Dependencies (can be installed via npm)
- `dist/` - Build output
- `.env` - Environment variables
- Log files
- Editor-specific files

## Contributing

This is a personal project, but suggestions and feedback are welcome!

## License

ISC

## Author

Hemanjali Reddy

## Repository

https://github.com/hemanjalireddy/KindaLike
