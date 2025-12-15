# Smart Heating Frontend

React + TypeScript frontend for the Smart Heating system with Material-UI components.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## 🛠 Development

### Available Scripts

- `npm run dev` - Start development server (http://localhost:5173)
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run test` - Run unit tests
- `npm run test:watch` - Run tests in watch mode
- `npm run test:coverage` - Run tests with coverage report
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Run ESLint with auto-fix
- `npm run format` - Format code with Prettier
- `npm run format:check` - Check code formatting
- `npm run type-check` - TypeScript type checking

### Tech Stack

- **React 19** with TypeScript
- **Material-UI v7** for components
- **Vite** for build tooling
- **Vitest** for testing
- **React Router** for navigation
- **i18next** for internationalization
- **Recharts** for data visualization
- **ESLint + Prettier** for code quality

### Code Quality

The project enforces code quality through:

- **ESLint** - Static code analysis with React and TypeScript rules
- **Prettier** - Consistent code formatting
- **TypeScript** - Static type checking
- **Vitest** - Unit testing with coverage reporting
- **Pre-commit hooks** - Automatic linting and formatting

#### ESLint Configuration

- TypeScript and React rules enabled
- No unused variables (except `_` prefixed)
- Console warnings (not errors)
- Single quotes and no semicolons
- React 17+ JSX transform

#### Prettier Configuration

- 100 character line width
- Single quotes for strings
- No semicolons
- Trailing commas for multiline
- 2 space indentation

### Testing

Unit tests use Vitest and React Testing Library with comprehensive coverage:

```bash
# Run tests once
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage (70% threshold)
npm run test:coverage
```

#### Coverage Thresholds

- **Lines:** 70%
- **Functions:** 70%
- **Branches:** 70%
- **Statements:** 70%

#### Test Structure

- Component tests in `__tests__` directories
- API tests for client functions
- Hook tests for custom hooks
- Mock external dependencies
- Use `data-testid` for reliable selectors

### API Integration

The frontend connects to the Home Assistant API through the Smart Heating integration:

- Base URL: `http://homeassistant.local:8123`
- API endpoints: `/api/smart_heating/*`
- WebSocket for real-time updates

## 🏗 Architecture

### Component Structure

```
src/
├── components/     # Reusable UI components
├── pages/         # Route components
├── hooks/         # Custom React hooks
├── api/          # API client functions
├── types/        # TypeScript type definitions
└── locales/      # Translation files
```

### Key Features

- **Responsive design** - Works on desktop and mobile
- **Dark/light theme** - User preference with system detection
- **Internationalization** - English and Dutch support
- **Real-time updates** - WebSocket integration
- **Data visualization** - Temperature charts and metrics
- **Accessibility** - ARIA labels and keyboard navigation
- **Test coverage** - Comprehensive `data-testid` attributes

### State Management

- React hooks for local state
- Context API for theme and language
- WebSocket for real-time data sync
- No external state management library needed

## 🎯 Development Guidelines

### Code Style

- Use TypeScript strict mode
- Follow React best practices
- Implement proper error boundaries
- Add comprehensive test coverage
- Use semantic HTML and ARIA labels
- Include `data-testid` for all interactive elements

### Testing Strategy

- Unit tests for all components
- Integration tests for user flows
- Mock external dependencies
- Aim for >70% code coverage
- Use reliable test selectors (`data-testid`)

### Performance

- Lazy load route components
- Optimize bundle size
- Use React.memo for expensive components
- Implement proper loading states

### Pre-commit Quality Checks

The project uses pre-commit hooks to ensure code quality:

- ESLint with auto-fix
- Prettier formatting
- TypeScript type checking
- Python linting (ruff)

Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

## 📱 Mobile Support

The frontend is fully responsive and optimized for mobile devices:

- Touch-friendly interface
- Responsive Material-UI components
- Mobile-first CSS approach
- Progressive Web App ready

## 🔧 CI/CD

### GitHub Actions

The project includes comprehensive CI/CD workflows:

- **Main CI** (`ci.yml`) - Full test suite for all code
- **Frontend Quality** (`frontend.yml`) - Frontend-specific checks
- **Release** (`release.yml`) - Automated releases

### Quality Checks

- TypeScript compilation
- ESLint linting
- Prettier formatting
- Unit test execution
- Coverage reporting
- Build verification

## 🚀 Getting Started

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd smart_heating
   ```

2. **Install dependencies**
   ```bash
   cd smart_heating/frontend
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Run tests**
   ```bash
   npm run test:coverage
   ```

5. **Check code quality**
   ```bash
   npm run lint
   npm run format:check
   npm run type-check
   ```

The frontend will be available at `http://localhost:5173` and proxy API requests to your Home Assistant instance.
