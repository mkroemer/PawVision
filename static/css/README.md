# PawVision CSS Architecture

## Overview
This document explains the modular CSS architecture used in PawVision and the responsibilities of each file.

## File Structure and Responsibilities

### Core Files
- **`main.css`** - Main entry point that imports all other CSS files
- **`base.css`** - CSS variables, reset styles, basic typography, and global styles

### Layout and Components
- **`layout.css`** - Core layout components (header, sections, navigation, footer) - **SINGLE SOURCE OF TRUTH** for layout
- **`buttons.css`** - Button styles and variants
- **`forms.css`** - Form elements and styling
- **`components.css`** - Reusable UI components (video items, statistics cards, etc.)
- **`modals.css`** - Modal system (general, progress, delete modals)

### Page-Specific Styles
- **`config.css`** - Configuration page specific styles only
- **`control.css`** - Control center page specific styles
- **`statistics.css`** - Statistics dashboard page specific styles

## Important Rules

### No Duplication
- Each CSS class should be defined in **only one file**
- Common layout classes (`.header`, `.logo`, `.section`, `.menu`) are defined in `layout.css` only
- Page-specific files should only contain styles unique to that page

### Variable Usage
- All CSS variables are defined in `base.css`
- Use CSS variables for consistency: `var(--primary)`, `var(--spacing-lg)`, etc.
- Fallback values are provided for compatibility: `var(--spacing-lg, 1.5rem)`

### Responsive Design
- Core responsive styles are in `layout.css`
- Page-specific responsive styles can be in their respective files
- Use consistent breakpoints: `768px` (tablet) and `480px` (mobile)

## Recently Fixed Issues

### Duplicate Definitions Removed
- **Logo**: Consolidated from `layout.css` and `config.css` to `layout.css` only
- **Header**: Removed duplicates from `config.css`, kept in `layout.css`
- **Section**: Removed duplicates from `config.css`, kept in `layout.css`
- **Menu**: Removed duplicates from `config.css`, kept in `layout.css`
- **Settings Card**: Removed duplicates from `components.css`, kept in `config.css` with proper styling
- **Stats Grid**: Removed duplicates from `statistics.css`, kept in `components.css` as reusable component
- **Stat Card**: Removed duplicates from `statistics.css`, kept in `components.css` as reusable component
- **Stat Value/Label**: Removed duplicates from `statistics.css`, kept in `components.css`
- **Responsive styles**: Consolidated media queries to reduce conflicts

### Media Query Consolidation
- **768px breakpoint**: Consolidated duplicate responsive styles across files
- **480px breakpoint**: Removed duplicate mobile styles
- **Component-specific responsiveness**: Kept only in their respective component files
- **Layout responsiveness**: Centralized in `layout.css`

### Architecture Improvements
- Added missing CSS variables to `base.css` for consistency
- Separated Jekyll theme styles (in `docs/`) from application styles
- Clear separation between layout and page-specific styles

## Development Guidelines

1. **Before adding new styles**: Check if the class already exists in another file
2. **For layout changes**: Modify `layout.css` only
3. **For page-specific styling**: Use the appropriate page-specific CSS file
4. **For new components**: Add to `components.css` if reusable, or page-specific file if unique
5. **Always use CSS variables** from `base.css` for colors, spacing, and other design tokens

## File Import Order
The import order in `main.css` is important for CSS specificity:
1. Base styles and variables
2. Layout (general structure)
3. Forms and buttons (interactive elements)
4. Modals and components
5. Page-specific styles (highest specificity)
