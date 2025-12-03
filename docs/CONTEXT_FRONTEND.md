# Frontend Context: EnergyApp LLM Platform

**Purpose:** Comprehensive reference for the Next.js frontend, React components, state management, and UI architecture.

## Frontend Technology Stack

- **Framework:** Next.js 14 (App Router)
- **UI Library:** React 18 with TypeScript
- **Styling:** Tailwind CSS (utility-first)
- **State Management:** Zustand (auth), React Query (API data)
- **HTTP Client:** Custom wrapper around fetch
- **Build System:** Turbopack (via Next.js)
- **Node Version:** 20 or 22 LTS

---

## Project Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Auth routes (public)
│   │   ├── login/
│   │   │   └── page.tsx         # Login page (SSR)
│   │   └── register/
│   │       └── page.tsx         # Register page (SSR)
│   ├── (dashboard)/              # Protected routes
│   │   ├── dashboard/
│   │   │   └── page.tsx         # Main chat dashboard
│   │   ├── admin/
│   │   │   └── page.tsx         # Admin panel (admin only)
│   │   └── settings/
│   │       └── page.tsx         # User settings
│   ├── layout.tsx               # Root layout
│   ├── middleware.ts            # Route protection
│   └── globals.css
├── components/                   # Reusable React components
│   ├── ChatWindow.tsx           # Main chat interface
│   ├── ConversationsList.tsx    # Sidebar conversation list
│   ├── AdminUsersList.tsx       # Admin users table
│   ├── AdminConversationsList.tsx
│   ├── AdminMessagesViewer.tsx
│   ├── SystemPromptsManager.tsx
│   └── ReassignConversationModal.tsx
├── hooks/                        # Custom React hooks
│   ├── useAuthCheck.ts          # Auth validation
│   ├── useAdmin.ts              # Admin hooks
│   ├── useConversations.ts      # Conversation data
│   └── ... (other hooks)
├── lib/                          # Utilities & libraries
│   ├── api.ts                   # HTTP client wrapper
│   └── ... (utilities)
├── store/                        # State management
│   ├── useAuthStore.ts          # Zustand auth store
│   └── ... (other stores)
├── providers/                    # Context providers
│   └── QueryProvider.tsx        # React Query setup
├── next.config.ts               # Next.js configuration
├── tailwind.config.ts           # Tailwind CSS config
├── tsconfig.json               # TypeScript config
└── package.json
```

---

## Key Components

### 1. **ChatWindow.tsx**
Main chat interface with message display, input, and streaming.

**Features:**
- Real-time message streaming
- System prompt auto-selection (default prompt loads on mount)
- Message history display
- Typing indicator ("escribiendo...")
- Input form with send button
- Conversation sidebar integration

**Key States:**
```typescript
const [selectedPromptId, setSelectedPromptId] = useState<number | null>(null);
const [messages, setMessages] = useState<Message[]>([]);
const [isLoading, setIsLoading] = useState(false);
const [userInput, setUserInput] = useState("");
const [systemPrompts, setSystemPrompts] = useState([]);
```

**Auto-Select Logic:**
```typescript
// ChatWindow.tsx lines 44-52
useEffect(() => {
  if (systemPrompts.length > 0) {
    const defaultPrompt = systemPrompts.find((p: any) => p.is_default);
    if (defaultPrompt) {
      setSelectedPromptId(defaultPrompt.id);
    }
  }
}, [systemPrompts]);
```

**Message Streaming:**
```typescript
const sendMessage = async () => {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      conversation_id: conversationId,
      message: userInput,
      system_prompt_id: selectedPromptId
    })
  });

  // Stream response as Server-Sent Events
  const reader = response.body.getReader();
  let assistantMessage = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const text = new TextDecoder().decode(value);
    // Parse SSE format: "data: {...}\n\n"
    assistantMessage += extractTokenFromSSE(text);
    setMessages(prev => [...prev, { role: 'assistant', content: assistantMessage }]);
  }
};
```

---

### 2. **ConversationsList.tsx**
Sidebar listing user's conversations.

**Props:**
```typescript
interface ConversationsListProps {
  selectedId?: number | null;
  onSelect: (id: number) => void;
}
```

**Fetches:** `GET /api/conversations?limit=50&offset=0`

**Features:**
- Ordered by `updated_at DESC` (most recent first)
- Click to select conversation
- Visual highlight for selected conversation
- Empty state if no conversations

---

### 3. **Admin Components**
Suite of components for admin panel:

#### **AdminUsersList.tsx**
- Displays all active users
- Shows user count, role
- Click to select for viewing conversations

#### **AdminConversationsList.tsx**
- Shows conversations for selected user
- Filters by `user_id`
- Click to select conversation for viewing messages

#### **AdminMessagesViewer.tsx**
- Displays all messages in selected conversation
- Shows user role indicator
- Includes "Mover" (reassign) button

#### **ReassignConversationModal.tsx**
- Modal dialog for reassigning conversation
- Lists available users (excludes current owner, only active)
- POST to `/api/admin/conversations/{id}/reassign`

---

### 4. **SystemPromptsManager.tsx**
Admin tool for managing system prompts.

**Features:**
- List all system prompts
- Create new prompt
- Edit existing prompts
- Delete prompts
- Mark one as default
- Real-time validation

**APIs:**
- `GET /api/admin/system-prompts`
- `POST /api/admin/system-prompts`
- `PATCH /api/admin/system-prompts/{id}`
- `DELETE /api/admin/system-prompts/{id}`

---

## Authentication & Authorization

### Auth Flow

**1. Login Page**
```typescript
// frontend/app/(auth)/login/page.tsx
const handleLogin = async (email: string, password: string) => {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    credentials: 'include',  // Send cookies
    body: JSON.stringify({ email, password })
  });

  // If 2FA is required
  if (response.status === 202) {
    // Show TOTP input screen
    return;
  }

  // Success: session_token cookie is set
  router.push('/dashboard');
};
```

**2. Auth Check (Protected Routes)**
```typescript
// frontend/hooks/useAuthCheck.ts
export function useAuthCheck() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await fetch('/api/auth/me', {
          credentials: 'include'
        });
        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        } else {
          // Not authenticated
          setUser(null);
        }
      } catch (error) {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  return { user, loading };
}
```

**3. Route Protection (Next.js Middleware)**
```typescript
// frontend/middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function middleware(request: NextRequest) {
  const token = request.cookies.get('session_token');

  // Public routes
  if (request.nextUrl.pathname.startsWith('/login') ||
      request.nextUrl.pathname.startsWith('/register')) {
    return NextResponse.next();
  }

  // Protected routes
  if (!token) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Admin routes
  if (request.nextUrl.pathname.startsWith('/admin')) {
    // Check user role via /api/auth/me
    const user = await fetchUserRole(token);
    if (user?.role !== 'admin') {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

---

## State Management

### 1. **Zustand Auth Store**
```typescript
// frontend/store/useAuthStore.ts
interface AuthState {
  user: User | null;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  logout: () => set({ user: null })
}));
```

### 2. **React Query (TanStack Query)**
```typescript
// frontend/providers/QueryProvider.tsx
export function QueryProvider({ children }) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes
        gcTime: 10 * 60 * 1000,    // 10 minutes
      }
    }
  });

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

**Custom Query Hooks:**
```typescript
// frontend/hooks/useConversations.ts
export function useConversations() {
  return useQuery({
    queryKey: ['conversations'],
    queryFn: async () => {
      const res = await api.get('/conversations');
      return res.json();
    },
    enabled: !!user  // Only fetch if user is logged in
  });
}

// frontend/hooks/useAdmin.ts
export function useAdminUsers() {
  return useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => api.get('/admin/users')
  });
}

export function useReassignConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ conversationId, targetUserId }) =>
      api.post(`/admin/conversations/${conversationId}/reassign`, {
        target_user_id: targetUserId
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin'] });
    }
  });
}
```

---

## HTTP Client

### API Wrapper
```typescript
// frontend/lib/api.ts
export const api = {
  baseUrl: '/api',

  async get(path: string) {
    return fetch(`${this.baseUrl}${path}`, {
      credentials: 'include',  // Send cookies
      headers: { 'Content-Type': 'application/json' }
    });
  },

  async post(path: string, body: any) {
    return fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
  },

  async patch(path: string, body: any) {
    return fetch(`${this.baseUrl}${path}`, {
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
  },

  async delete(path: string) {
    return fetch(`${this.baseUrl}${path}`, {
      method: 'DELETE',
      credentials: 'include'
    });
  },

  // Specialized for streaming
  async stream(path: string, body: any) {
    return fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
  }
};
```

### Error Handling
```typescript
// All API calls should check response.ok
const response = await api.get('/conversations');
if (!response.ok) {
  if (response.status === 401) {
    // Not authenticated - redirect to login
    router.push('/login');
  } else if (response.status === 403) {
    // Forbidden - insufficient permissions
    toast.error('No tienes permisos para acceder a esto');
  } else {
    const error = await response.json();
    toast.error(error.detail || 'Error en la solicitud');
  }
}
```

---

## UI & Styling

### Tailwind Configuration
```typescript
// frontend/tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        slate: { /* gray color palette */ },
        sky: { /* blue color palette */ },
      },
      spacing: { /* custom spacing if needed */ },
    },
  },
  plugins: [],
}
```

### Color Scheme
- **Background:** `bg-slate-950` (very dark), `bg-slate-900` (dark)
- **Borders:** `border-slate-800` (dark borders)
- **Text:** `text-slate-300` (dim), `text-white` (primary)
- **Accent:** `bg-sky-600` (primary action), `text-sky-300` (highlight)
- **Error:** `text-red-400` (errors/destructive)

### Responsive Design
```typescript
// Mobile-first with Tailwind
<div className="w-full lg:w-72">  {/* Full width on mobile, 288px on desktop */}
<button className="hidden sm:inline">  {/* Hidden on mobile, visible on small screens and up */}
```

---

## Build & Deployment

### Development
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
# Auto-reloads on file changes
# Proxies /api to http://localhost:8000 (via next.config.ts)
```

### Production Build
```bash
npm run build
# Creates optimized Next.js build in .next/
# Generates static chunks with hashing
```

### Starting Production Server
```bash
npm start
# Runs optimized server on port 3000
# Serves pre-built .next/ directory
```

### Chunk Verification (CRITICAL)
After rebuild, always verify chunks are loading:
```bash
# 1. Check build generated chunks
curl http://localhost:3000/_next/static/chunks/main.js -I | grep "HTTP"

# 2. Check admin page loads
curl http://localhost:3000/admin | grep "next/static/chunks" | head -3

# 3. Verify chunks are status 200 (not 404 or 500)
```

---

## Environment Variables

### Next.js Config (.env.local or next.config.ts)
```typescript
// next.config.ts - API proxy configuration
const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/:path*',  // Proxy to FastAPI
      },
    ];
  },
};
```

---

## Performance Optimization

### Code Splitting
- Next.js automatically splits routes into separate chunks
- Each page loads only its required code
- Shared code (React, utils) goes to vendor bundle

### Image Optimization
```typescript
// Use next/image for automatic optimization
import Image from 'next/image';

<Image
  src="/logo.png"
  alt="Logo"
  width={32}
  height={32}
/>
```

### Data Fetching
- **React Query:** Caches API responses, deduplicates requests
- **Stale Time:** 5 minutes (configurable)
- **Background Refetch:** Automatically re-fetches when user returns to tab

---

## Common Issues & Solutions

### Issue: Chunks returning 500 errors
**Solution:**
1. Ensure port 3000 is not in use: `lsof -i :3000`
2. Kill old processes: `pkill -9 node`
3. Clean build cache: `rm -rf .next .turbo node_modules/.cache`
4. Rebuild: `npm run build`
5. Test: `curl http://localhost:3000/_next/static/chunks/main.js -I`

### Issue: Routes not protected
**Solution:** Check middleware.ts is matching correct paths and authenticating properly

### Issue: Components not re-rendering
**Solution:** Check React Query cache (use `queryClient.invalidateQueries`) or Zustand store updates

---

## Related Files & References

- `frontend/next.config.ts` → Next.js configuration & API proxy
- `frontend/app/` → All pages and routes
- `frontend/components/` → Reusable components
- `frontend/hooks/` → Custom React hooks
- `frontend/lib/api.ts` → HTTP client
- `frontend/store/useAuthStore.ts` → Zustand auth store
- `docs/CONTEXT_BACKEND.md` → Backend API endpoints
