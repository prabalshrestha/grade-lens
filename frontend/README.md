# Grade Lens Frontend

Modern React web interface for the Grade Lens AI grading system.

## Overview

A responsive web UI for:
- Creating assignments with AI-generated configs
- Uploading and managing student submissions
- Grading assignments with AI
- Viewing detailed results and statistics

## Installation

```bash
npm install
```

## Running

### Development Mode

```bash
npm run dev
# Opens on http://localhost:5173
```

### Production Build

```bash
npm run build
# Output in dist/
```

### Preview Build

```bash
npm run preview
```

## Configuration

### Environment Variables

Create `.env` file (optional):

```env
VITE_API_BASE_URL=http://localhost:8000
```

### API Connection

Edit `src/api/client.js` to change backend URL:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

## Features

### 1. Dashboard
- View all assignments
- See statistics (questions, points, submissions)
- Quick access to grading and results
- Delete assignments

### 2. Create Assignment
Three-step wizard:

**Step 1: Upload Files**
- Upload questions PDF (required)
- Upload answer key PDF (optional)

**Step 2: Assignment Details**
- Set assignment ID and name
- Add course code and term
- Generate config with AI

**Step 3: Review & Edit**
- Edit questions and points
- Customize rubrics
- Modify grading criteria
- Add/remove criteria dynamically
- Edit general grading instructions
- Save configuration

### 3. Assignment Detail
- View assignment information
- Edit configuration (click "Edit Config")
- Upload student submissions
- Select grading mode
- Start grading
- View submissions list

### 4. Results
- Summary statistics
- Grade distribution chart
- Per-student detailed results
- Expandable question-by-question feedback
- Export to CSV or JSON
- Switch between grading modes

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.js           # API integration layer
│   ├── components/
│   │   └── Layout.jsx          # Main layout with nav
│   ├── pages/
│   │   ├── Dashboard.jsx       # Assignment list
│   │   ├── CreateAssignment.jsx # Create assignment wizard
│   │   ├── AssignmentDetail.jsx # Manage submissions
│   │   └── Results.jsx         # View grading results
│   ├── App.jsx                 # Main app with routing
│   ├── main.jsx                # Entry point
│   └── index.css               # Global styles
├── index.html                   # HTML template
├── package.json                 # Dependencies
├── vite.config.js              # Vite configuration
├── tailwind.config.js          # Tailwind CSS config
└── postcss.config.js           # PostCSS config
```

## Technology Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Lucide React** - Icon library

## Key Components

### Layout Component
Main layout with:
- Header with branding
- Navigation bar
- Footer
- Responsive design

### Dashboard
- Grid of assignment cards
- Statistics display
- Action buttons
- Empty state handling

### CreateAssignment
- Multi-step form wizard
- File upload with validation
- AI config generation
- Comprehensive rubric editing
- Criteria management
- Instructions editing

### AssignmentDetail
- Two modes: View and Edit
- Assignment info display
- Submission management
- Grading controls
- Config editing with rubrics

### Results
- Data table with sorting
- Expandable row details
- Summary statistics
- Grade distribution chart
- Export functionality

## API Integration

All API calls are in `src/api/client.js`:

```javascript
// Assignments
listAssignments()
getAssignment(id)
saveAssignmentConfig(id, config)
deleteAssignment(id)

// File uploads
uploadAssignmentFiles(formData)
generateConfig(formData)
uploadSubmissions(id, formData)

// Grading
gradeAssignment(id, gradingMode)
getResults(id, gradingMode)
downloadResults(id, format, gradingMode)
```

## Styling

### Tailwind CSS

All styling uses Tailwind utility classes:

```jsx
<button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
  Click Me
</button>
```

### Color Scheme

- **Primary:** Blue (`bg-blue-600`)
- **Success:** Green (`bg-green-600`)
- **Warning:** Amber (`bg-amber-500`)
- **Error:** Red (`bg-red-600`)
- **Neutral:** Gray shades

### Responsive Design

Mobile-first approach:

```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
```

## Development Tips

### Hot Module Replacement

Vite provides instant HMR - save files to see changes immediately.

### Console Logging

Open browser DevTools (F12) to see:
- API request/response logs
- React component errors
- Network activity

### React DevTools

Install React DevTools browser extension for:
- Component tree inspection
- Props and state viewing
- Performance profiling

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
```

### API Connection Failed

1. Check backend is running on port 8000
2. Verify `API_BASE_URL` in `src/api/client.js`
3. Check browser console for CORS errors

### Build Errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Styling Not Working

```bash
# Rebuild Tailwind
npm run dev
```

## Building for Production

### 1. Build

```bash
npm run build
```

### 2. Test Build Locally

```bash
npm run preview
```

### 3. Deploy

Deploy the `dist/` folder to:
- Netlify
- Vercel
- AWS S3 + CloudFront
- Any static hosting

### Environment Variables

For production, set `VITE_API_BASE_URL` to your backend URL.

## Performance

### Optimization

- Code splitting with React.lazy()
- Image optimization
- Minification via Vite
- Tree shaking

### Bundle Size

Check bundle size:

```bash
npm run build
```

Vite will show gzipped sizes.

## Accessibility

- Semantic HTML elements
- ARIA labels where needed
- Keyboard navigation support
- Focus management
- Screen reader friendly

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Test thoroughly
5. Submit a pull request

## Testing

### Manual Testing

1. Start dev server
2. Test all pages
3. Try error scenarios
4. Check responsive design
5. Test in different browsers

### Automated Testing (Future)

Can add:
- Jest for unit tests
- React Testing Library
- Cypress for E2E tests

## Common Tasks

### Add a New Page

1. Create component in `src/pages/`
2. Add route in `App.jsx`
3. Add navigation link in `Layout.jsx`

### Add New API Endpoint

1. Add function to `src/api/client.js`
2. Use in component with `useState` and `useEffect`

### Modify Styling

1. Use Tailwind classes
2. Check `tailwind.config.js` for theme
3. Use `className` prop

## Support

For issues:
1. Check browser console (F12)
2. Review network requests
3. Check API responses
4. See main README: ../README.md

## License

CS 557 AI Final Project, Boise State University

---

**Live Dev Server:** http://localhost:5173  
**Backend API:** http://localhost:8000  
**Main README:** ../README.md
