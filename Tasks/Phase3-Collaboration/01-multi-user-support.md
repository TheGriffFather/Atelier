# Multi-User Support

> Phase 3, Task 1 | Priority: High | Dependencies: None

## Overview

Add user management and authentication to enable team collaboration on the catalogue raisonné. Supports multiple user roles (admin, editor, viewer), tracks all changes with audit logging, and enables threaded comments on artworks.

## Success Criteria

- [ ] User registration and login system
- [ ] Three user roles: Admin, Editor, Viewer
- [ ] Session management with JWT tokens
- [ ] Password hashing with secure algorithms
- [ ] Activity logging for all data changes
- [ ] Comments/discussions on artworks
- [ ] User profile management
- [ ] Admin dashboard for user management
- [ ] Protected API routes based on role

## Database Changes

### New `users` Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT,
    password_hash TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    role TEXT DEFAULT 'viewer',
    avatar_url TEXT,
    bio TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
```

### New `activity_log` Table

```sql
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    changes TEXT,  -- JSON
    notes TEXT,
    ip_address TEXT,
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_activity_user ON activity_log(user_id);
CREATE INDEX idx_activity_entity ON activity_log(entity_type, entity_id);
CREATE INDEX idx_activity_created ON activity_log(created_at);
```

### New `artwork_comments` Table

```sql
CREATE TABLE artwork_comments (
    id INTEGER PRIMARY KEY,
    artwork_id INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    parent_comment_id INTEGER REFERENCES artwork_comments(id),
    is_resolved INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comments_artwork ON artwork_comments(artwork_id);
CREATE INDEX idx_comments_user ON artwork_comments(user_id);
CREATE INDEX idx_comments_parent ON artwork_comments(parent_comment_id);
```

### New `sessions` Table

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(token_hash);
```

### Enums

```python
class UserRole(str, Enum):
    ADMIN = "admin"     # Full access, user management
    EDITOR = "editor"   # Create, edit, delete content
    VIEWER = "viewer"   # Read-only access
```

## Role Permissions

| Action | Admin | Editor | Viewer |
|--------|-------|--------|--------|
| View artworks | Yes | Yes | Yes |
| Create artwork | Yes | Yes | No |
| Edit artwork | Yes | Yes | No |
| Delete artwork | Yes | No | No |
| Verify artwork | Yes | Yes | No |
| Import data | Yes | Yes | No |
| Export data | Yes | Yes | Yes |
| Manage users | Yes | No | No |
| View activity log | Yes | Yes | No |
| Add comments | Yes | Yes | Yes |
| Delete comments | Yes | Own only | Own only |

## API Endpoints

### Authentication

#### POST /api/auth/register
Register new user.

**Request:**
```json
{
  "email": "user@example.com",
  "username": "jsmith",
  "password": "SecurePassword123!",
  "display_name": "John Smith"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "jsmith",
    "display_name": "John Smith",
    "role": "viewer"
  },
  "token": "eyJhbG...",
  "expires_at": "2025-12-12T10:00:00"
}
```

#### POST /api/auth/login
Login user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** Same as register

#### POST /api/auth/logout
Logout (invalidate token).

**Headers:** `Authorization: Bearer <token>`

#### POST /api/auth/refresh
Refresh token.

**Response:** New token

#### GET /api/auth/me
Get current user.

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "jsmith",
  "display_name": "John Smith",
  "role": "editor",
  "avatar_url": "/uploads/avatars/1.jpg",
  "bio": "Art historian specializing in American trompe l'oeil",
  "created_at": "2025-12-01T10:00:00",
  "last_login": "2025-12-05T08:30:00"
}
```

#### PATCH /api/auth/me
Update current user profile.

#### POST /api/auth/change-password
Change password.

**Request:**
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewSecurePassword456!"
}
```

### User Management (Admin only)

#### GET /api/users
List all users.

**Response:**
```json
{
  "users": [
    {
      "id": 1,
      "email": "admin@example.com",
      "username": "admin",
      "display_name": "Administrator",
      "role": "admin",
      "is_active": true,
      "last_login": "2025-12-05T08:30:00"
    }
  ],
  "total": 5
}
```

#### POST /api/users
Create user (admin only).

#### GET /api/users/{id}
Get user details.

#### PATCH /api/users/{id}
Update user (admin only).

#### DELETE /api/users/{id}
Deactivate user (admin only).

#### POST /api/users/{id}/change-role
Change user role.

**Request:**
```json
{
  "role": "editor"
}
```

### Activity Log

#### GET /api/activity
Get activity log.

**Query Parameters:**
- `user_id`: Filter by user
- `entity_type`: artwork, exhibition, etc.
- `entity_id`: Specific entity
- `action`: create, update, delete, verify
- `from_date`, `to_date`: Date range
- `limit`, `offset`: Pagination

**Response:**
```json
{
  "activities": [
    {
      "id": 1,
      "user": {
        "id": 1,
        "username": "jsmith",
        "display_name": "John Smith"
      },
      "action": "update",
      "entity_type": "artwork",
      "entity_id": 42,
      "entity_title": "The Harbor",
      "changes": {
        "title": {"old": "Harbor", "new": "The Harbor"},
        "year_created": {"old": null, "new": 1985}
      },
      "created_at": "2025-12-05T10:30:00"
    }
  ],
  "total": 150
}
```

#### GET /api/artworks/{id}/activity
Get activity for specific artwork.

### Comments

#### GET /api/artworks/{id}/comments
Get comments for artwork.

**Response:**
```json
{
  "comments": [
    {
      "id": 1,
      "user": {
        "id": 1,
        "username": "jsmith",
        "display_name": "John Smith",
        "avatar_url": null
      },
      "content": "Should we verify the signature attribution?",
      "is_resolved": false,
      "created_at": "2025-12-05T10:30:00",
      "replies": [
        {
          "id": 2,
          "user": {
            "id": 2,
            "username": "admin",
            "display_name": "Admin"
          },
          "content": "Yes, I'll check the gallery records.",
          "created_at": "2025-12-05T11:00:00"
        }
      ]
    }
  ],
  "total": 5
}
```

#### POST /api/artworks/{id}/comments
Add comment.

**Request:**
```json
{
  "content": "Should we verify the signature attribution?",
  "parent_comment_id": null
}
```

#### PATCH /api/comments/{id}
Edit comment (own comments only).

#### DELETE /api/comments/{id}
Delete comment (own or admin).

#### POST /api/comments/{id}/resolve
Mark comment thread as resolved.

## UI Requirements

### Login Page

Location: `/login`

**Layout:**
- Logo/branding
- Email input
- Password input
- Login button
- "Forgot password" link
- "Register" link (if allowed)

### Registration Page

Location: `/register` (if enabled)

**Layout:**
- Email input
- Username input
- Display name input
- Password input
- Confirm password input
- Register button
- "Login" link

### User Profile Page

Location: `/profile`

**Layout:**
1. **Profile Header**
   - Avatar (upload)
   - Display name
   - Username
   - Role badge

2. **Edit Profile Form**
   - Display name
   - Bio
   - Avatar upload

3. **Change Password Section**
   - Current password
   - New password
   - Confirm password

4. **Activity Summary**
   - Recent actions count
   - Comments count

### Admin - User Management

Location: `/admin/users`

**Layout:**
1. **User List**
   - Table with columns: User, Email, Role, Status, Last Login, Actions
   - Role change dropdown
   - Activate/Deactivate toggle

2. **Add User Modal**
   - Full user form
   - Initial role assignment

### Activity Log Page

Location: `/admin/activity`

**Layout:**
- Filter bar (user, entity, action, date)
- Activity timeline
- Entity links

### Artwork Comments Section

On `/artwork/{id}`:

1. **Comments Panel**
   - Thread list
   - Reply buttons
   - Resolve button
   - Add comment form

### Navigation Updates

- Login/Logout button
- User menu with:
  - Profile link
  - Admin link (if admin)
  - Logout

## Implementation Steps

### Step 1: Database Migration

```python
# scripts/migrations/008_multi_user.py
"""
Migration: Multi-User Support
Date: YYYY-MM-DD
"""
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path("data/artworks.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            username TEXT NOT NULL UNIQUE,
            display_name TEXT,
            password_hash TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            role TEXT DEFAULT 'viewer',
            avatar_url TEXT,
            bio TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    """)

    # Create activity_log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            changes TEXT,
            notes TEXT,
            ip_address TEXT,
            user_agent TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create artwork_comments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artwork_comments (
            id INTEGER PRIMARY KEY,
            artwork_id INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id),
            content TEXT NOT NULL,
            parent_comment_id INTEGER REFERENCES artwork_comments(id),
            is_resolved INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at DATETIME NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_log(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_entity ON activity_log(entity_type, entity_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_artwork ON artwork_comments(artwork_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token_hash)")

    conn.commit()
    conn.close()
    print("Migration completed successfully")

if __name__ == "__main__":
    migrate()
```

### Step 2: Update Models

Add to `src/database/models.py`:
- `UserRole` enum
- `User` model
- `ActivityLog` model
- `ArtworkComment` model
- `Session` model

### Step 3: Create Auth Service

Create `src/services/auth_service.py`:

```python
from datetime import datetime, timedelta
import hashlib
import secrets
from passlib.context import CryptContext
import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Handle authentication and authorization."""

    SECRET_KEY = "your-secret-key"  # Move to config
    ALGORITHM = "HS256"
    TOKEN_EXPIRE_HOURS = 24

    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        """Verify a password."""
        return pwd_context.verify(plain, hashed)

    def create_token(self, user_id: int) -> tuple[str, datetime]:
        """Create JWT token."""
        expires = datetime.utcnow() + timedelta(hours=self.TOKEN_EXPIRE_HOURS)
        payload = {
            "user_id": user_id,
            "exp": expires
        }
        token = jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token, expires

    def verify_token(self, token: str) -> int:
        """Verify JWT token, return user_id."""
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload["user_id"]
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

    async def register(
        self,
        email: str,
        username: str,
        password: str,
        display_name: str = None
    ) -> dict:
        """Register new user."""
        pass

    async def login(self, email: str, password: str) -> dict:
        """Login user."""
        pass

    async def logout(self, token: str) -> None:
        """Invalidate token."""
        pass

    async def get_current_user(self, token: str) -> User:
        """Get user from token."""
        pass

    async def update_profile(self, user_id: int, data: dict) -> User:
        """Update user profile."""
        pass

    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> None:
        """Change user password."""
        pass

    def check_permission(self, user: User, action: str, entity_type: str) -> bool:
        """Check if user has permission."""
        permissions = {
            'admin': ['*'],
            'editor': ['create', 'update', 'verify', 'comment'],
            'viewer': ['read', 'comment']
        }
        allowed = permissions.get(user.role, [])
        return '*' in allowed or action in allowed
```

### Step 4: Create Activity Service

Create `src/services/activity_service.py`:

```python
class ActivityService:
    """Track user activity."""

    async def log_activity(
        self,
        user_id: int,
        action: str,
        entity_type: str,
        entity_id: int,
        changes: dict = None,
        notes: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> ActivityLog:
        """Log an activity."""
        pass

    async def get_activities(
        self,
        user_id: int = None,
        entity_type: str = None,
        entity_id: int = None,
        action: str = None,
        from_date: datetime = None,
        to_date: datetime = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """Get activities with filters."""
        pass

    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: int
    ) -> list:
        """Get all activity for an entity."""
        pass

    def track_changes(self, old_data: dict, new_data: dict) -> dict:
        """Compare and return changed fields."""
        changes = {}
        for key in new_data:
            if key in old_data and old_data[key] != new_data[key]:
                changes[key] = {
                    'old': old_data[key],
                    'new': new_data[key]
                }
        return changes
```

### Step 5: Create API Routes

Create `src/api/routes/auth.py`:

```python
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    display_name: str = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current user from token."""
    pass

async def require_admin(user = Depends(get_current_user)):
    """Dependency to require admin role."""
    if user.role != 'admin':
        raise HTTPException(403, "Admin access required")
    return user

async def require_editor(user = Depends(get_current_user)):
    """Dependency to require editor or admin role."""
    if user.role not in ['admin', 'editor']:
        raise HTTPException(403, "Editor access required")
    return user

@router.post("/register")
async def register(request: RegisterRequest):
    pass

@router.post("/login")
async def login(request: LoginRequest):
    pass

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    pass

@router.post("/refresh")
async def refresh(credentials: HTTPAuthorizationCredentials = Depends(security)):
    pass

@router.get("/me")
async def get_me(user = Depends(get_current_user)):
    pass

@router.patch("/me")
async def update_me(data: dict, user = Depends(get_current_user)):
    pass

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    user = Depends(get_current_user)
):
    pass
```

Create `src/api/routes/users.py`:

```python
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("")
async def list_users(admin = Depends(require_admin)):
    pass

@router.post("")
async def create_user(user_data: dict, admin = Depends(require_admin)):
    pass

@router.get("/{id}")
async def get_user(id: int, admin = Depends(require_admin)):
    pass

@router.patch("/{id}")
async def update_user(id: int, data: dict, admin = Depends(require_admin)):
    pass

@router.delete("/{id}")
async def deactivate_user(id: int, admin = Depends(require_admin)):
    pass

@router.post("/{id}/change-role")
async def change_role(id: int, role: str, admin = Depends(require_admin)):
    pass
```

### Step 6: Create Protected Route Decorator

```python
# src/api/dependencies.py

from functools import wraps
from fastapi import HTTPException

def require_role(*roles):
    """Decorator to require specific roles."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user=None, **kwargs):
            if user is None or user.role not in roles:
                raise HTTPException(403, "Insufficient permissions")
            return await func(*args, user=user, **kwargs)
        return wrapper
    return decorator
```

### Step 7: Create Templates

Create `src/api/templates/login.html`
Create `src/api/templates/register.html`
Create `src/api/templates/profile.html`
Create `src/api/templates/admin/users.html`
Create `src/api/templates/admin/activity.html`

Update `src/api/templates/base.html`:
- Add user menu
- Add login/logout links

Update `src/api/templates/artwork.html`:
- Add comments section

### Step 8: Add JavaScript

Create `src/api/static/js/auth.js`:
- Token storage (localStorage)
- Auth headers for API calls
- Login/logout handlers

Create `src/api/static/js/comments.js`:
- Comment threading
- Reply functionality
- Resolve toggle

## Testing Requirements

### Unit Tests

```python
# tests/test_auth_service.py

def test_password_hashing():
    """Password hashes correctly."""

def test_password_verify():
    """Password verification works."""

def test_token_creation():
    """Token creates with correct payload."""

def test_token_verification():
    """Token verifies and returns user_id."""

def test_expired_token():
    """Expired token raises error."""

def test_role_permissions():
    """Permission checks work correctly."""
```

### Integration Tests

```python
# tests/test_auth_api.py

def test_register():
    """Registration creates user."""

def test_login():
    """Login returns token."""

def test_protected_route():
    """Protected route requires token."""

def test_admin_only_route():
    """Admin route rejects non-admin."""

def test_change_password():
    """Password change works."""
```

### Manual Testing Checklist

- [ ] Register new user
- [ ] Login with credentials
- [ ] View protected pages
- [ ] Update profile
- [ ] Change password
- [ ] Admin: list users
- [ ] Admin: change user role
- [ ] Admin: deactivate user
- [ ] Add comment to artwork
- [ ] Reply to comment
- [ ] Resolve comment thread
- [ ] View activity log
- [ ] Logout

## Security Considerations

1. **Password Storage**: Use bcrypt with cost factor 12
2. **Token Security**: JWT with short expiry, refresh tokens
3. **Rate Limiting**: Limit login attempts
4. **Input Validation**: Sanitize all inputs
5. **CSRF Protection**: Use CSRF tokens for forms
6. **XSS Prevention**: Escape user content
7. **SQL Injection**: Use parameterized queries (SQLAlchemy handles)
8. **Secure Cookies**: HttpOnly, Secure, SameSite flags

## Dependencies

- `passlib[bcrypt]` - Password hashing
- `python-jose[cryptography]` or `PyJWT` - JWT handling

```bash
pip install passlib[bcrypt] python-jose[cryptography]
```

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/migrations/008_multi_user.py` | Create | Database migration |
| `src/database/models.py` | Modify | Add models |
| `src/services/auth_service.py` | Create | Auth logic |
| `src/services/activity_service.py` | Create | Activity logging |
| `src/api/routes/auth.py` | Create | Auth endpoints |
| `src/api/routes/users.py` | Create | User management |
| `src/api/routes/comments.py` | Create | Comments endpoints |
| `src/api/dependencies.py` | Create | Auth dependencies |
| `src/api/main.py` | Modify | Register routes |
| `src/api/templates/login.html` | Create | Login page |
| `src/api/templates/profile.html` | Create | Profile page |
| `src/api/templates/admin/users.html` | Create | User management |
| `src/api/templates/base.html` | Modify | User menu |
| `src/api/static/js/auth.js` | Create | Client auth |
| `tests/test_auth_service.py` | Create | Unit tests |
| `tests/test_auth_api.py` | Create | API tests |

---

*Last updated: December 5, 2025*
