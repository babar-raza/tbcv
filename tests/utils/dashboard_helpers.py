# file: tests/utils/dashboard_helpers.py
"""
Dashboard test helper utilities.

Provides HTML parsing and verification utilities for dashboard tests.
Uses BeautifulSoup for robust HTML handling.
"""

import re
from typing import Optional, List, Dict, Any, Tuple
from bs4 import BeautifulSoup


def verify_html_contains_element(html: str, tag: str, attrs: Optional[Dict[str, Any]] = None) -> bool:
    """
    Verify that HTML content contains an element with the specified tag and attributes.

    Args:
        html: HTML content to search
        tag: HTML tag name to find (e.g., 'div', 'a', 'button')
        attrs: Optional dictionary of attributes to match (e.g., {'class': 'btn'})

    Returns:
        True if matching element found, False otherwise

    Example:
        >>> html = '<div class="container"><button id="submit">Click</button></div>'
        >>> verify_html_contains_element(html, 'button', {'id': 'submit'})
        True
    """
    if not html:
        return False

    try:
        soup = BeautifulSoup(html, 'html.parser')
        elements = soup.find_all(tag, attrs=attrs or {})
        return len(elements) > 0
    except Exception:
        return False


def verify_html_contains_link(html: str, href: str) -> bool:
    """
    Verify that HTML content contains a link (anchor tag) with the specified href.

    Args:
        html: HTML content to search
        href: The href value to find (can be partial match)

    Returns:
        True if matching link found, False otherwise

    Example:
        >>> html = '<a href="/dashboard/validations/123">View</a>'
        >>> verify_html_contains_link(html, '/dashboard/validations/123')
        True
    """
    if not html or not href:
        return False

    try:
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', href=True)
        for link in links:
            if href in link.get('href', ''):
                return True
        return False
    except Exception:
        return False


def extract_form_action(html: str, form_id: str) -> Optional[str]:
    """
    Extract the action attribute from a form with the specified ID.

    Args:
        html: HTML content containing the form
        form_id: The ID of the form element

    Returns:
        The form's action URL, or None if not found

    Example:
        >>> html = '<form id="review-form" action="/api/review" method="post"></form>'
        >>> extract_form_action(html, 'review-form')
        '/api/review'
    """
    if not html or not form_id:
        return None

    try:
        soup = BeautifulSoup(html, 'html.parser')
        form = soup.find('form', id=form_id)
        if form:
            return form.get('action')
        return None
    except Exception:
        return None


def extract_table_rows(html: str, table_class: Optional[str] = None) -> List[List[str]]:
    """
    Extract all rows from a table, optionally filtered by class.

    Args:
        html: HTML content containing the table
        table_class: Optional class name to filter tables

    Returns:
        List of rows, where each row is a list of cell text values

    Example:
        >>> html = '<table class="data"><tr><td>A</td><td>B</td></tr></table>'
        >>> extract_table_rows(html, 'data')
        [['A', 'B']]
    """
    if not html:
        return []

    try:
        soup = BeautifulSoup(html, 'html.parser')

        if table_class:
            table = soup.find('table', class_=table_class)
        else:
            table = soup.find('table')

        if not table:
            return []

        rows = []
        for tr in table.find_all('tr'):
            cells = []
            for cell in tr.find_all(['td', 'th']):
                cells.append(cell.get_text(strip=True))
            if cells:
                rows.append(cells)

        return rows
    except Exception:
        return []


def verify_badge_status(html: str, status: str) -> bool:
    """
    Verify that HTML contains a badge element with the specified status.

    Looks for common badge patterns: .badge, .status-badge, .label classes
    with status text or status-specific classes.

    Args:
        html: HTML content to search
        status: Status text to find (e.g., 'approved', 'pending', 'rejected')

    Returns:
        True if matching badge found, False otherwise

    Example:
        >>> html = '<span class="badge badge-success">approved</span>'
        >>> verify_badge_status(html, 'approved')
        True
    """
    if not html or not status:
        return False

    try:
        soup = BeautifulSoup(html, 'html.parser')
        status_lower = status.lower()

        # Look for badge elements with matching text
        badge_classes = ['badge', 'status-badge', 'label', 'tag', 'chip']
        for badge_class in badge_classes:
            badges = soup.find_all(class_=re.compile(badge_class, re.I))
            for badge in badges:
                badge_text = badge.get_text(strip=True).lower()
                if status_lower in badge_text:
                    return True
                # Check for status in class name
                badge_classes_str = ' '.join(badge.get('class', []))
                if status_lower in badge_classes_str.lower():
                    return True

        # Also check for status in any element with status-related classes
        status_elements = soup.find_all(class_=re.compile(f'status.*{status_lower}|{status_lower}.*status', re.I))
        if status_elements:
            return True

        return False
    except Exception:
        return False


def verify_toast_container_present(html: str) -> bool:
    """
    Verify that HTML contains a toast notification container.

    Looks for common toast container patterns used by notification systems.

    Args:
        html: HTML content to search

    Returns:
        True if toast container found, False otherwise

    Example:
        >>> html = '<div id="toast-container" class="toast-notifications"></div>'
        >>> verify_toast_container_present(html)
        True
    """
    if not html:
        return False

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Common toast container patterns
        toast_patterns = [
            {'id': re.compile('toast', re.I)},
            {'class_': re.compile('toast', re.I)},
            {'id': re.compile('notification', re.I)},
            {'class_': re.compile('notification.*container', re.I)},
            {'id': re.compile('alert.*container', re.I)},
            {'class_': re.compile('snackbar', re.I)},
        ]

        for pattern in toast_patterns:
            if soup.find(attrs=pattern):
                return True

        return False
    except Exception:
        return False


def extract_websocket_url(html: str) -> Optional[str]:
    """
    Extract WebSocket URL from HTML content.

    Looks for WebSocket URLs in script tags and data attributes.

    Args:
        html: HTML content to search

    Returns:
        WebSocket URL if found, None otherwise

    Example:
        >>> html = '<script>const ws = new WebSocket("ws://localhost:8000/ws");</script>'
        >>> extract_websocket_url(html)
        'ws://localhost:8000/ws'
    """
    if not html:
        return None

    try:
        # Pattern to match WebSocket URLs
        ws_pattern = re.compile(r'(wss?://[^\s\'"<>]+)', re.I)

        # Search in raw HTML for ws:// or wss:// URLs
        matches = ws_pattern.findall(html)
        if matches:
            # Return first match, cleaned up
            url = matches[0].rstrip('")\'};')
            return url

        # Also check data attributes
        soup = BeautifulSoup(html, 'html.parser')
        for element in soup.find_all(attrs={'data-ws-url': True}):
            return element.get('data-ws-url')
        for element in soup.find_all(attrs={'data-websocket-url': True}):
            return element.get('data-websocket-url')
        for element in soup.find_all(attrs={'data-socket-url': True}):
            return element.get('data-socket-url')

        return None
    except Exception:
        return None


def verify_filter_selected(html: str, filter_name: str, value: str) -> bool:
    """
    Verify that a filter option is selected in HTML form/select elements.

    Checks for selected options in select elements and checked inputs.

    Args:
        html: HTML content to search
        filter_name: Name of the filter (used for input/select name attribute)
        value: Expected selected value

    Returns:
        True if filter is selected with the specified value, False otherwise

    Example:
        >>> html = '<select name="status"><option value="pending" selected>Pending</option></select>'
        >>> verify_filter_selected(html, 'status', 'pending')
        True
    """
    if not html or not filter_name:
        return False

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Check select elements
        select = soup.find('select', {'name': filter_name})
        if select:
            selected_option = select.find('option', selected=True)
            if selected_option:
                option_value = selected_option.get('value', selected_option.get_text(strip=True))
                if str(value).lower() == str(option_value).lower():
                    return True

        # Check radio buttons
        radio = soup.find('input', {'type': 'radio', 'name': filter_name, 'value': value, 'checked': True})
        if radio:
            return True

        # Check checkboxes
        checkbox = soup.find('input', {'type': 'checkbox', 'name': filter_name, 'value': value, 'checked': True})
        if checkbox:
            return True

        # Check for active filter buttons/links
        filter_patterns = [
            {'class_': re.compile(f'{filter_name}.*active|active.*{filter_name}', re.I)},
            {'data-filter': filter_name, 'class_': re.compile('active', re.I)},
        ]
        for pattern in filter_patterns:
            elements = soup.find_all(attrs=pattern)
            for elem in elements:
                if value.lower() in elem.get_text(strip=True).lower():
                    return True
                if value.lower() in str(elem.get('data-value', '')).lower():
                    return True

        return False
    except Exception:
        return False


# Export all helper functions
__all__ = [
    'verify_html_contains_element',
    'verify_html_contains_link',
    'extract_form_action',
    'extract_table_rows',
    'verify_badge_status',
    'verify_toast_container_present',
    'extract_websocket_url',
    'verify_filter_selected',
]
