# Wishlist Frontend

Modern React frontend for the Wishlist API built with TypeScript, Vite, and Tailwind CSS.

## Features

- 🔐 **Authentication** - Register, login, and secure session management
- ✨ **CRUD Operations** - Create, read, update, and delete wishes
- 🎨 **Modern UI** - Beautiful interface with Tailwind CSS
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🔍 **Filtering** - Filter wishes by price
- 📄 **Pagination** - Navigate through large lists of wishes
- ⚡ **Fast** - Built with Vite for lightning-fast development
- 🛡️ **Type-Safe** - Full TypeScript coverage
- 🎯 **React Query** - Efficient data fetching and caching

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **React Query** - Data fetching
- **React Hook Form** - Form handling
- **Axios** - HTTP client

## Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on `http://localhost:8000`

## Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Create `.env` file:
```bash
echo "VITE_API_URL=http://localhost:8000" > .env
```

## Development

Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Build

Build for production:
```bash
npm run build
```

Preview production build:
```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and endpoints
│   │   ├── client.ts     # Axios instance with interceptors
│   │   ├── auth.ts       # Authentication API
│   │   └── wishes.ts     # Wishes API
│   ├── components/       # Reusable components
│   │   ├── Header.tsx    # Navigation header
│   │   ├── PrivateRoute.tsx # Protected route wrapper
│   │   ├── WishCard.tsx  # Wish display card
│   │   └── WishModal.tsx # Create/Edit modal
│   ├── contexts/         # React contexts
│   │   └── AuthContext.tsx # Authentication state
│   ├── pages/            # Page components
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   └── WishlistPage.tsx
│   ├── types/            # TypeScript types
│   │   └── index.ts
│   ├── App.tsx           # Main app component
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Features Overview

### Authentication
- User registration with validation
- Secure login with JWT tokens
- Automatic token refresh
- Protected routes

### Wishlist Management
- Add new wishes with title, link, price, and notes
- Edit existing wishes
- Delete wishes with confirmation
- View all wishes in a grid layout

### Filtering & Pagination
- Filter wishes by maximum price
- Paginate through results
- Clear filters easily

### UI/UX
- Loading states for all async operations
- Error handling with user-friendly messages
- Responsive design for all screen sizes
- Smooth animations and transitions
- Confirmation dialogs for destructive actions

## API Integration

The frontend communicates with the backend API at `http://localhost:8000/api/v1/`:

- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user
- `GET /wishes/` - Get wishes list
- `POST /wishes/` - Create wish
- `GET /wishes/{id}` - Get single wish
- `PATCH /wishes/{id}` - Update wish
- `DELETE /wishes/{id}` - Delete wish

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |

## Contributing

1. Follow TypeScript best practices
2. Use Tailwind CSS for styling
3. Maintain consistent code formatting
4. Add proper error handling
5. Test all functionality

## License

MIT
