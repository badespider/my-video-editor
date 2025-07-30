# AI Video Editor Frontend

A modern React.js frontend application for the AI Video Editor system, providing a comprehensive user interface for video editing and creation with AI assistance.

## Features

### Core Functionality
- **Video Upload**: Drag-and-drop interface with progress tracking
- **Script-to-Video Generation**: AI-powered video creation from text scripts
- **Real-time Editing**: WebSocket-based live editing with instant feedback
- **Video Processing**: Upload and process videos with AI analysis
- **Preview & Playback**: Full-featured video player with streaming support
- **AI Analysis**: Detailed video content analysis with visualizations

### User Interface
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Material-UI Components**: Modern, accessible UI components
- **Dark/Light Theme**: Toggle between themes
- **Real-time Status**: Live API connection and session status
- **Progress Indicators**: Visual feedback for long-running operations
- **Error Handling**: Comprehensive error messages and recovery

### Technical Features
- **TypeScript**: Full type safety and better development experience
- **Axios Integration**: Robust API communication with interceptors
- **WebSocket Support**: Real-time bidirectional communication
- **Session Management**: Persistent session state with localStorage
- **File Streaming**: Support for large video files with range requests
- **Chart Visualizations**: Interactive charts for analysis results

## Getting Started

### Prerequisites
- Node.js 16+ and npm
- Backend API server running on `http://localhost:8000`

### Installation

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm start
   ```

3. **Open your browser:**
   Navigate to `http://localhost:3000`

### Backend Connection

The frontend is configured to connect to the backend API at `http://localhost:8000`. Make sure your backend server is running before using the frontend.

## Application Structure

### Pages and Routes

- **Home (`/`)**: Welcome page with feature overview
- **Upload (`/upload`)**: Video file upload with drag-and-drop
- **Generate (`/generate`)**: Create videos from text scripts
- **Process (`/process`)**: Upload and process videos with AI
- **Edit (`/edit`)**: Real-time video editing with WebSocket
- **Preview (`/preview`)**: Video playback and thumbnail generation
- **Analyze (`/analyze`)**: AI-powered video analysis and insights

### Key Components

#### API Service (`src/services/api.ts`)
Centralized API communication with:
- Axios configuration with base URL and interceptors
- Type-safe API methods for all backend endpoints
- Progress tracking for file uploads
- Error handling and logging

#### WebSocket Hook (`src/hooks/useWebSocket.ts`)
Custom React hook for WebSocket communication:
- Automatic connection management
- Message parsing and error handling
- Connection status tracking
- Automatic reconnection on failures

#### App Context (`src/context/AppContext.tsx`)
Global state management for:
- Current session ID persistence
- API connection status
- User preferences and theme
- Authentication state (future)

### UI Components

#### Layout Components
- **Header**: Navigation with status indicators
- **Footer**: API status and session information
- **LoadingSpinner**: Consistent loading states
- **ErrorAlert**: Standardized error display
- **ProgressBar**: Upload and processing progress

#### Page-Specific Features
- **Drag-and-Drop Upload**: File validation and preview
- **Real-time Chat Interface**: WebSocket command interface
- **Video Player Integration**: ReactPlayer with custom controls
- **Chart Visualizations**: Recharts for analysis data
- **Timeline Editor**: Visual editing interface

## API Integration

### Endpoints Covered

#### Core Operations
- `GET /` - Welcome message
- `GET /health` - API health check
- `POST /upload/video` - File upload with progress
- `POST /generate` - Script-to-video generation
- `POST /process_video` - Video processing

#### Session Management
- `GET /session/{session_id}` - Session information
- `POST /apply_edits/{session_id}` - Batch edit operations
- `POST /trim/{session_id}` - Video trimming
- `POST /finalize/{session_id}` - Finalize editing

#### Media Serving
- `GET /preview/{session_id}` - Video preview streaming
- `GET /file/{filename}` - File serving for downloads
- `POST /thumbnail/{session_id}` - Thumbnail generation

#### AI Features
- `POST /analyze/{session_id}` - Video content analysis
- `POST /suggestions/{session_id}` - AI editing suggestions
- `POST /optimize/{session_id}` - Optimization recommendations

#### Real-time Communication
- `WS /ws/edit/{session_id}` - WebSocket editing interface

### Error Handling

The application implements comprehensive error handling:

- **Network Errors**: Automatic retry and user feedback
- **API Errors**: Detailed error messages from backend
- **Validation Errors**: Client-side validation with helpful messages
- **WebSocket Errors**: Connection status and automatic reconnection
- **File Errors**: Upload validation and size/type checking

### State Management

#### Session Persistence
- Session IDs stored in localStorage
- Automatic session restoration on page reload
- Session cleanup on logout/reset

#### API Status Monitoring
- Real-time API health checking
- Visual status indicators in header/footer
- Automatic reconnection attempts

## Development

### Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run test suite
- `npm run eject` - Eject from Create React App

### Environment Configuration

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_WS_BASE_URL=ws://localhost:8000
REACT_APP_VERSION=1.0.0
```

### TypeScript Configuration

The application uses strict TypeScript configuration with:
- Full type coverage for API responses
- Interface definitions for all data structures
- Type-safe component props and state
- Strict null checks and error handling

### Styling and Theming

#### Material-UI Theme
- Custom color palette with primary/secondary colors
- Typography scale with consistent font weights
- Component style overrides for consistent appearance
- Dark/light theme support with user preference

#### Responsive Design
- Mobile-first approach with breakpoints
- Flexible grid layouts using Material-UI Grid
- Responsive typography and spacing
- Touch-friendly interface elements

## Production Deployment

### Build Process

1. **Create production build:**
   ```bash
   npm run build
   ```

2. **Serve static files:**
   The build folder contains optimized static files ready for deployment.

### Deployment Options

#### Static Hosting
- **Netlify**: Drag-and-drop deployment
- **Vercel**: Git-based deployment
- **AWS S3**: Static website hosting
- **GitHub Pages**: Free hosting for public repos

#### Server Deployment
- **Nginx**: Serve static files with proxy to backend
- **Apache**: Traditional web server setup
- **Docker**: Containerized deployment

### Environment Variables

For production, set these environment variables:

```env
REACT_APP_API_BASE_URL=https://your-api-domain.com
REACT_APP_WS_BASE_URL=wss://your-api-domain.com
REACT_APP_VERSION=1.0.0
```

### Performance Optimization

The application includes several performance optimizations:

- **Code Splitting**: Automatic route-based code splitting
- **Lazy Loading**: Components loaded on demand
- **Image Optimization**: Responsive images with proper sizing
- **Bundle Analysis**: Use `npm run build` to analyze bundle size
- **Caching**: Service worker for offline functionality

## Browser Support

- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

### Required Features
- **WebSocket Support**: For real-time editing
- **File API**: For drag-and-drop uploads
- **Video Element**: For video playback
- **Fetch API**: For HTTP requests
- **LocalStorage**: For session persistence

## Troubleshooting

### Common Issues

#### CORS Errors
If you see CORS errors, ensure the backend is configured to allow requests from `http://localhost:3000`:

```python
# In backend/api.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### WebSocket Connection Issues
- Check that the backend WebSocket endpoint is accessible
- Verify the session ID is valid
- Check browser console for connection errors

#### Video Playback Issues
- Ensure video files are in supported formats (MP4, WebM)
- Check that the backend file serving is working
- Verify CORS headers for media files

#### Upload Failures
- Check file size limits (default 100MB)
- Verify file type restrictions
- Ensure backend upload directory is writable

### Debug Mode

Enable debug logging by setting:
```javascript
localStorage.setItem('debug', 'true');
```

This will show additional console logs for API calls and WebSocket messages.

## Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-feature`
3. **Make your changes** with proper TypeScript types
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Submit a pull request**

### Code Style

- Use TypeScript for all new code
- Follow Material-UI design patterns
- Implement proper error handling
- Add loading states for async operations
- Write descriptive component and function names
- Use proper semantic HTML elements

## License

This project is licensed under the MIT License - see the LICENSE file for details.