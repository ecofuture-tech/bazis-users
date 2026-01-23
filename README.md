# Bazis Users

[![PyPI version](https://img.shields.io/pypi/v/bazis-users.svg)](https://pypi.org/project/bazis-users/)
[![Python Versions](https://img.shields.io/pypi/pyversions/bazis-users.svg)](https://pypi.org/project/bazis-users/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

An extension package for Bazis that provides advanced capabilities for user management and authentication.

## Quick Start

```bash
# Install the package
uv add bazis-users

# Create user model
from bazis.contrib.users.models_abstract import UserAbstract
from bazis.core.models_abstract import DtMixin, UuidMixin, JsonApiMixin

class User(UserAbstract, DtMixin, UuidMixin, JsonApiMixin):
    """Custom user model"""
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

# Create user route
from bazis.contrib.users.routes import UserRouteSet
from django.apps import apps

class MyUserRouteSet(UserRouteSet):
    model = apps.get_model('myapp.User')
```

## Table of Contents

- [Description](#description)
- [Requirements](#requirements)
- [Installation](#installation)
- [Core Components](#core-components)
  - [Abstract Models](#abstract-models)
  - [Mixins](#mixins)
  - [Base Routes](#base-routes)
  - [Built-in Routes](#built-in-routes)
  - [Services](#services)
- [Usage](#usage)
  - [Creating User Model](#creating-user-model)
  - [Creating User Route](#creating-user-route)
  - [Using Authentication Services](#using-authentication-services)
  - [Linking Models to Users](#linking-models-to-users)
- [API Authentication](#api-authentication)
- [Examples](#examples)
- [License](#license)
- [Links](#links)

## Description

**Bazis Users** is an extension package for the Bazis framework that provides a complete toolkit for user management and authentication. The package includes:

- Abstract user models with JWT authentication support
- Ready-to-use routes for user operations
- Services for token and authentication management
- Mixins for linking models to users
- Integration with Swagger UI for API testing

**This package requires the base `bazis` package to be installed.**

## Requirements

- **Python**: 3.12+
- **bazis**: latest version
- **PostgreSQL**: 12+
- **Redis**: For caching

## Installation

### Using uv (recommended)

```bash
uv add bazis-users
```

### Using pip

```bash
pip install bazis-users
```

## Core Components

### Abstract Models

#### UserAbstract

Abstract user model implementing methods required for extended work with Bazis.

**Location**: `bazis.contrib.users.models_abstract.UserAbstract`

**Methods**:

- `get_full_name()` - returns user's full name
- `jwt_build()` - creates JWT token for the user
- `find_or_create()` - finds or creates a user
- `raw_password` - works with raw password

**Example usage**:

```python
from bazis.contrib.users.models_abstract import UserAbstract
from bazis.core.models_abstract import DtMixin, UuidMixin, JsonApiMixin

class User(UserAbstract, DtMixin, UuidMixin, JsonApiMixin):
    """Application user model"""
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.get_full_name()
```

#### AnonymousUserAbstract

Abstract anonymous user model for handling unauthenticated requests.

**Location**: `bazis.contrib.users.models_abstract.AnonymousUserAbstract`

**Methods**:

- `get_full_name()` - returns name for anonymous user

### Mixins

#### UserMixin

Mixin for entity models that should be associated with a user.

**Location**: `bazis.contrib.users.models_abstract.UserMixin`

**Features**:

- User is stored in context variable `CTX_USER_REQUEST`
- Automatically links model to current user from request

**Example usage**:

```python
from bazis.contrib.users.models_abstract import UserMixin
from bazis.core.models_abstract import DtMixin, UuidMixin, JsonApiMixin
from django.db import models

class Article(UserMixin, DtMixin, UuidMixin, JsonApiMixin):
    """Article linked to a user"""
    title = models.CharField(max_length=255)
    content = models.TextField()
    
    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'
```

### Base Routes

#### UserRouteBase

Base class for routes associated with users.

**Location**: `bazis.contrib.users.routes_abstract.UserRouteBase`

Provides base functionality for creating routes that work with user models.

### Built-in Routes

#### token_auth

Basic token authentication (JWT), applied in Swagger UI.

**Location**: `bazis.contrib.users.routes.token_auth`

Enables JWT token authentication in Swagger UI.

#### UserRouteSet

Base route class for working with users.

**Location**: `bazis.contrib.users.routes.UserRouteSet`

Provides ready-to-use endpoints for user operations:
- List users
- Get specific user information
- Create user
- Update user
- Delete user

**Example usage**:

```python
from bazis.contrib.users.routes import UserRouteSet
from django.apps import apps

class MyUserRouteSet(UserRouteSet):
    model = apps.get_model('myapp.User')
```

### Services

Services for working with users and tokens.

**Location**: `bazis.contrib.users.services`

#### get_token_data

Extracts data from JWT token.

```python
from bazis.contrib.users.services import get_token_data

def my_endpoint(token: str = Depends(get_token_data)):
    user_id = token.get('user_id')
    # Work with token data
```

#### get_user_from_token

Gets user from token.

```python
from bazis.contrib.users.services import get_user_from_token

def my_endpoint(user = Depends(get_user_from_token)):
    # user - user object or AnonymousUser
    print(user.get_full_name())
```

#### get_user_required

Gets user from request (authentication required).

```python
from bazis.contrib.users.services import get_user_required

def my_endpoint(user = Depends(get_user_required)):
    # user - authenticated user
    # Returns 401 if token is invalid
    return {"user": user.get_full_name()}
```

#### get_user_optional

Gets user from request (authentication optional).

```python
from bazis.contrib.users.services import get_user_optional

def my_endpoint(user = Depends(get_user_optional)):
    # user - user or AnonymousUser
    if user.is_authenticated:
        return {"user": user.get_full_name()}
    return {"user": "Anonymous"}
```

## Usage

### Creating User Model

```python
from bazis.contrib.users.models_abstract import UserAbstract
from bazis.core.models_abstract import DtMixin, UuidMixin, JsonApiMixin
from django.db import models

class User(UserAbstract, DtMixin, UuidMixin, JsonApiMixin):
    """Custom user model"""
    
    # Additional fields
    phone = models.CharField('Phone', max_length=20, null=True, blank=True)
    department = models.CharField('Department', max_length=100, null=True, blank=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.get_full_name()
```

### Creating User Route

```python
# routes.py
from bazis.contrib.users.routes import UserRouteSet
from bazis.core.schemas.fields import SchemaField, SchemaFields
from django.apps import apps

class MyUserRouteSet(UserRouteSet):
    model = apps.get_model('myapp.User')
    
    # Add additional fields to schema
    fields = {
        None: SchemaFields(
            include={
                'phone': None,
                'department': None,
            },
        ),
    }
```

```python
# router.py
from bazis.core.routing import BazisRouter
from . import routes

router = BazisRouter(tags=['Users'])
router.register(routes.MyUserRouteSet.as_router())
```

### Using Authentication Services

#### Required Authentication

Use `get_user_required` for endpoints that require authentication:

```python
from bazis.contrib.users.services import get_user_required
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()

class NewPasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.post('/user/change_password/', response_model=dict)
def change_password(
    data: NewPasswordRequest,
    user: User = Depends(get_user_required)
):
    # user - guaranteed authenticated user
    # Returns 401 if token is invalid
    return user.change_password(data)
```

#### Optional Authentication

Use `get_user_optional` for endpoints available to everyone:

```python
from bazis.contrib.users.services import get_user_optional, get_token_data
from fastapi import Depends

@router.get('/auth/', response_model=AuthResponse)
def auth(
    auth_store: AuthStore = Depends(),
    user: User = Depends(get_user_optional),
    token_data: dict = Depends(get_token_data),
):
    # user can be AnonymousUser
    if user.is_anonymous:
        if user_id := auth_store.user_id:
            user = User.objects.filter(id=user_id).first()
    
    # Logic for working with user or anonymous
    return {"user": user.get_full_name() if not user.is_anonymous else "Anonymous"}
```

#### Using get_token_data

Getting data from JWT token without loading the user:

```python
from bazis.contrib.users.services import get_token_data
from fastapi import Depends

@router.get('/token-info/')
def token_info(token_data: dict = Depends(get_token_data)):
    # token_data contains decoded data from JWT
    return {
        "user_id": token_data.get("user_id"),
        "exp": token_data.get("exp"),
    }
```

### Linking Models to Users

```python
from bazis.contrib.users.models_abstract import UserMixin
from bazis.core.models_abstract import DtMixin, UuidMixin, JsonApiMixin
from django.db import models

class Document(UserMixin, DtMixin, UuidMixin, JsonApiMixin):
    """Document automatically linked to user"""
    title = models.CharField(max_length=255)
    content = models.TextField()
    
    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
```

## API Authentication

### Getting Token

After setting up routes, users can obtain JWT tokens through the authentication endpoint.

**Example request**:
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

**Example response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using Token in Requests

```bash
GET /api/v1/protected-resource
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Authentication in Swagger UI

1. Open `/api/swagger/`
2. Click "Authorize" button
3. Enter token in format: `Bearer <your_token>`
4. Click "Authorize"
5. Now all requests will be executed with authentication

## Examples

### Complete Application Example with Users

**models.py**:
```python
from bazis.contrib.users.models_abstract import UserAbstract, UserMixin
from bazis.core.models_abstract import DtMixin, UuidMixin, JsonApiMixin
from django.db import models

class User(UserAbstract, DtMixin, UuidMixin, JsonApiMixin):
    """System user"""
    phone = models.CharField('Phone', max_length=20, null=True, blank=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

class Task(UserMixin, DtMixin, UuidMixin, JsonApiMixin):
    """Task linked to user"""
    title = models.CharField('Title', max_length=255)
    description = models.TextField('Description')
    is_completed = models.BooleanField('Completed', default=False)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Assigned To'
    )
    
    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
```

**routes.py**:
```python
from bazis.contrib.users.routes import UserRouteSet
from bazis.contrib.users.services import get_user_required
from django.apps import apps
from fastapi import APIRouter, Depends
from pydantic import BaseModel

class MyUserRouteSet(UserRouteSet):
    model = apps.get_model('myapp.User')

# Additional endpoints for working with tasks
router = APIRouter()

class TaskCreateRequest(BaseModel):
    title: str
    description: str

@router.get('/my-tasks/')
def get_my_tasks(user: User = Depends(get_user_required)):
    # Return only current user's tasks
    tasks = Task.objects.filter(assigned_to=user)
    return {"tasks": [{"id": str(t.id), "title": t.title} for t in tasks]}

@router.post('/tasks/')
def create_task(
    data: TaskCreateRequest,
    user: User = Depends(get_user_required)
):
    # Create task for current user
    task = Task.objects.create(
        title=data.title,
        description=data.description,
        assigned_to=user
    )
    return {"id": str(task.id), "title": task.title}
```

**router.py**:
```python
from bazis.core.routing import BazisRouter
from . import routes

# Register user routes
user_router = BazisRouter(tags=['Users'])
user_router.register(routes.MyUserRouteSet.as_router())

# Register additional task endpoints
user_router.include_router(routes.router, prefix='/api/v1')
```

**admin.py**:
```python
from django.contrib import admin
from bazis.core.admin_abstract import DtAdminMixin
from .models import User, Task

@admin.register(User)
class UserAdmin(DtAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'phone', 'is_active')
    search_fields = ('username', 'email', 'phone')
    list_filter = ('is_active', 'is_staff')

@admin.register(Task)
class TaskAdmin(DtAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'title', 'assigned_to', 'is_completed')
    search_fields = ('title', 'description')
    list_filter = ('is_completed',)
    raw_id_fields = ('assigned_to',)
```

## License

Apache License 2.0

See [LICENSE](LICENSE) file for details.

## Links

- [Bazis Documentation](https://github.com/ecofuture-tech/bazis) — main repository
- [Bazis Users Repository](https://github.com/ecofuture-tech/bazis-users) — package repository
- [Issue Tracker](https://github.com/ecofuture-tech/bazis-users/issues) — report bugs or request features

## Support

If you have questions or issues:
- Check the [Bazis documentation](https://github.com/ecofuture-tech/bazis)
- Search [existing issues](https://github.com/ecofuture-tech/bazis-users/issues)
- Create a [new issue](https://github.com/ecofuture-tech/bazis-users/issues/new) with detailed information

---

Made with ❤️ by the Bazis team