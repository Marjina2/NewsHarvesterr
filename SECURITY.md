# Security Implementation

## Authentication System

### Master Token Protection
- **Environment Variable**: `MASTER_TOKEN` (required)
- **Storage**: Secure environment variables only
- **Validation**: Server-side token comparison
- **Frontend**: Secure localStorage storage

### Rate Limiting
- **Failed Attempts**: Max 5 attempts per IP
- **Reset Window**: 15 minutes
- **Protection**: Brute force prevention

### API Security
- **Protected Endpoints**: All CRUD operations
- **Authentication**: Bearer token in headers
- **Authorization**: Master token validation
- **Error Handling**: Generic error messages

## Protected Endpoints

### News Management
- `GET /api/sources` - News sources list
- `POST /api/sources` - Add news source  
- `DELETE /api/sources/:id` - Remove source
- `GET /api/news` - Articles list
- `POST /api/articles` - Create article

### Scraper Operations
- `GET /api/config` - Scraper configuration
- `POST /api/config` - Update configuration
- `POST /api/scraper/start` - Start scraping
- `POST /api/scraper/stop` - Stop scraping
- `GET /api/scraper/status` - Scraper status

### Data Access
- `GET /api/stats` - Dashboard statistics
- `GET /api/articles/:id/json` - Article JSON export
- `GET /api/articles/all` - All articles export

## Public Endpoints

### Health & Auth
- `GET /api/health` - Health check
- `POST /api/auth/verify` - Token verification

## Frontend Security

### Authentication Flow
1. User enters master token
2. Token sent to `/api/auth/verify`
3. On success, token stored in localStorage
4. All API requests include Bearer token
5. Logout clears stored credentials

### Session Management
- **Storage**: localStorage (auth_token)
- **Persistence**: Survives browser restart
- **Logout**: Complete credential removal
- **Auto-logout**: On authentication errors

### Request Security
- **Headers**: Authorization Bearer token
- **Validation**: Server-side verification
- **Error Handling**: Automatic logout on 401

## Security Headers

### CORS Configuration
- **Origin**: Configured for production domain
- **Methods**: Limited to required HTTP methods
- **Headers**: Content-Type, Authorization

### Content Security
- **Input Validation**: Zod schema validation
- **SQL Injection**: Prevented by ORM
- **XSS Protection**: React built-in escaping

## Environment Security

### Required Secrets
```env
MASTER_TOKEN=your_secure_master_token
DATABASE_URL=postgresql://...
```

### Optional Secrets
```env
OPENROUTER_API_KEY=your_api_key
```

## Deployment Security

### Render Configuration
- **Environment Variables**: Secure secret storage
- **HTTPS**: Automatic SSL certificates
- **Database**: Encrypted connections
- **Build Process**: Secure dependency installation

### Production Checklist
- [ ] MASTER_TOKEN set to strong value
- [ ] Database URL uses SSL connection
- [ ] All environment variables configured
- [ ] HTTPS enforced in production
- [ ] CORS configured for production domain

## Token Security

### Best Practices
- **Length**: Minimum 32 characters
- **Complexity**: Alphanumeric + symbols
- **Uniqueness**: Random generation
- **Rotation**: Regular token updates

### Example Strong Token
```bash
# Generate secure token
openssl rand -base64 32
```

## Monitoring & Logging

### Security Events
- Authentication failures
- Rate limit violations
- Unauthorized access attempts
- Configuration changes

### Log Information
- IP addresses of failed attempts
- Request timestamps
- Error types and frequencies
- Suspicious activity patterns

## Incident Response

### Authentication Bypass
1. Rotate MASTER_TOKEN immediately
2. Check logs for unauthorized access
3. Verify data integrity
4. Update deployment with new token

### Brute Force Attack
1. Monitor rate limiting effectiveness
2. Consider IP blocking if needed
3. Review authentication logs
4. Strengthen token if compromised

## Compliance & Privacy

### Data Protection
- No personal data collection
- News articles from public sources
- Secure credential handling
- Database encryption at rest

### Access Control
- Single master token system
- Role-based access (admin only)
- Audit trail for all operations
- Secure session management