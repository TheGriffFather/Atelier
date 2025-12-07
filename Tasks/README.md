# Atelier Development Tasks

This folder contains detailed specifications for implementing new features in Atelier, a Digital Catalogue Raisonné Platform.

## Purpose

These documents serve as comprehensive guides for AI agents (or human developers) implementing features across multiple sessions. Each specification includes:

- **Feature Overview**: What the feature does and why it matters
- **Success Criteria**: Measurable outcomes that define "done"
- **Database Schema**: Exact table/column definitions for consistency
- **API Endpoints**: RESTful endpoints to implement
- **UI/UX Requirements**: User interface specifications
- **Implementation Steps**: Ordered tasks with dependencies
- **Testing Requirements**: What to test and how
- **Edge Cases**: Potential issues to handle

## Architecture Principles

All implementations must follow these principles:

### 1. Database Conventions
- Use SQLAlchemy 2.0 async style with `Mapped` type hints
- All tables use `id: Mapped[int]` as primary key
- Include `created_at` and `updated_at` timestamps
- Use Enums for status fields (defined in `src/database/models.py`)
- Foreign keys reference table name, not model class

### 2. API Conventions
- FastAPI with async routes
- Pydantic models for request/response validation
- Routes organized in `src/api/routes/`
- Consistent error handling with HTTPException
- JSON responses with snake_case keys

### 3. Frontend Conventions
- Jinja2 templates in `src/api/templates/`
- Tailwind CSS for styling (build with `npm run css:build`)
- Vanilla JavaScript (no frameworks)
- Dark theme with gold accents (Digital Atelier aesthetic)
- Mobile-responsive design

### 4. File Organization
```
src/
├── api/
│   ├── routes/          # API endpoints
│   ├── templates/       # Jinja2 templates
│   └── static/          # CSS, JS, images
├── database/
│   ├── models.py        # SQLAlchemy models
│   └── session.py       # Database session management
├── services/            # Business logic
├── scrapers/            # Data collection
└── filters/             # Confidence scoring
```

## Development Phases

### Phase 1: Foundation (Prerequisites)
Foundational features that other phases depend on.

| Task | File | Priority | Dependencies |
|------|------|----------|--------------|
| Enhanced Image Management | `Phase1-Foundation/01-enhanced-image-management.md` | High | None |
| Import/Migration Tools | `Phase1-Foundation/02-import-migration-tools.md` | High | None |
| Duplicate Detection | `Phase1-Foundation/03-duplicate-detection.md` | High | Enhanced Images |
| Data Completeness Dashboard | `Phase1-Foundation/04-data-completeness-dashboard.md` | Medium | None |

### Phase 2: Professional (Core Catalog Features)
Features essential for scholarly catalogue raisonné work.

| Task | File | Priority | Dependencies |
|------|------|----------|--------------|
| Provenance Chain Builder | `Phase2-Professional/01-provenance-chain-builder.md` | High | None |
| Exhibition History Module | `Phase2-Professional/02-exhibition-history-module.md` | High | None |
| Literature & Bibliography | `Phase2-Professional/03-literature-bibliography.md` | High | None |
| Catalog Numbering System | `Phase2-Professional/04-catalog-numbering-system.md` | Medium | None |

### Phase 3: Collaboration (Team Features)
Features for teams and external collaboration.

| Task | File | Priority | Dependencies |
|------|------|----------|--------------|
| Multi-User Support | `Phase3-Collaboration/01-multi-user-support.md` | High | None |
| Authentication Workflow | `Phase3-Collaboration/02-authentication-workflow.md` | High | Multi-User |
| Print-Ready Export | `Phase3-Collaboration/03-print-ready-export.md` | Medium | None |
| Public Tip Submission | `Phase3-Collaboration/04-public-tip-submission.md` | Medium | None |

### Phase 4: Discovery (External Integration)
Features for discovering and monitoring artworks.

| Task | File | Priority | Dependencies |
|------|------|----------|--------------|
| Auction House Integrations | `Phase4-Discovery/01-auction-house-integrations.md` | High | None |
| Price History Tracking | `Phase4-Discovery/02-price-history-tracking.md` | Medium | Auction Houses |
| Museum Collection Search | `Phase4-Discovery/03-museum-collection-search.md` | Low | None |
| Online Catalog Portal | `Phase4-Discovery/04-online-catalog-portal.md` | Low | Phase 2 Complete |

## How to Use These Specs

### For AI Agents

1. **Read the SCHEMA.md first** - Understand the database conventions
2. **Check dependencies** - Ensure prerequisite features are implemented
3. **Follow the implementation steps** - They're ordered for a reason
4. **Run migrations** - Create migration scripts, don't modify models.py directly without backup
5. **Test thoroughly** - Follow the testing requirements
6. **Update documentation** - Keep CLAUDE.md and other docs current

### Starting a Task

```
1. Read the full specification document
2. Review SCHEMA.md for database conventions
3. Check existing models.py for current schema
4. Create a migration script if adding tables/columns
5. Implement API endpoints
6. Build UI components
7. Write tests
8. Update CLAUDE.md with new features
```

### Completing a Task

Before marking complete, verify:
- [ ] All success criteria met
- [ ] Database migrations work on fresh DB
- [ ] API endpoints return correct responses
- [ ] UI matches design specifications
- [ ] Tests pass
- [ ] No regressions in existing features
- [ ] Documentation updated

## Important Files to Know

| File | Purpose |
|------|---------|
| `src/database/models.py` | All SQLAlchemy models |
| `src/database/session.py` | Database session management |
| `src/api/main.py` | FastAPI app and route registration |
| `config/settings.py` | Environment configuration |
| `CLAUDE.md` | Project documentation for AI agents |
| `Tasks/SCHEMA.md` | Master schema reference |

## Questions?

If a specification is unclear or you need to make architectural decisions not covered in the docs, consider:

1. Following existing patterns in the codebase
2. Prioritizing simplicity over cleverness
3. Maintaining backwards compatibility
4. Documenting your decisions in the code

---

*Last updated: December 5, 2025*
