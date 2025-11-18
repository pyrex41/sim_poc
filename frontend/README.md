# Client & Campaign Management UI

A simple, clean web interface for managing clients and campaigns using Alpine.js and Tailwind CSS.

## Features

### Client Management
- ✅ Create new clients with name, description, and brand guidelines
- ✅ List all clients with search functionality
- ✅ Edit existing clients
- ✅ Delete clients (with cascade warning)
- ✅ View campaigns for a specific client

### Campaign Management
- ✅ Create new campaigns linked to clients
- ✅ List all campaigns with filters (status, client, search)
- ✅ Edit existing campaigns
- ✅ Delete campaigns
- ✅ Status badges (Active, Draft, Archived)

## Tech Stack

- **Alpine.js** - Lightweight reactive framework (loaded from CDN)
- **Tailwind CSS** - Utility-first CSS framework (loaded from CDN)
- **Vanilla JavaScript** - No build step required

## Usage

1. Start the v3 backend server:
   ```bash
   python -m backend.main_v3
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000/app/clients-campaigns.html
   ```

## API Integration

The interface connects to the v3 API at `http://localhost:8000/api/v3`:

- `/clients` - Client CRUD operations
- `/campaigns` - Campaign CRUD operations

## No Build Required

This is a standalone HTML file with no build process. All dependencies are loaded from CDNs:
- Alpine.js from `cdn.jsdelivr.net`
- Tailwind CSS from `cdn.tailwindcss.com`

## Features Details

### Search & Filter
- Real-time search for clients and campaigns (300ms debounce)
- Filter campaigns by status (Active/Draft/Archived)
- Filter campaigns by client

### Modals
- Clean modal dialogs for creating/editing
- Form validation
- Cancel/Save actions

### User Experience
- Loading states
- Empty states with helpful messages
- Confirmation dialogs for destructive actions
- Responsive design
- Smooth transitions

### Data Flow
```
User Action → Alpine.js Method → Fetch API → Backend API → Database
                                                  ↓
User Interface ← Alpine.js Reactive Update ← JSON Response
```

## Customization

### Change API URL
Edit the `apiBase` property in the Alpine.js app:

```javascript
apiBase: 'http://your-api-server:8000/api/v3',
```

### Styling
The interface uses Tailwind CSS utility classes. You can:
- Customize colors by changing class names (e.g., `bg-blue-600` → `bg-purple-600`)
- Add custom styles in a `<style>` block
- Use Tailwind's configuration for more advanced theming

## Browser Support

Works in all modern browsers that support:
- ES6 JavaScript
- Fetch API
- CSS Grid & Flexbox
