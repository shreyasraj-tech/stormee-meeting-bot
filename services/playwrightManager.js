
/**
 * Playwright Manager
 * ==================
 * Manages access to the active Playwright page object.
 * This module provides a centralized way to retrieve the current page instance
 * used for interacting with Google Meet.
 */

let activePage = null;

/**
 * Sets the active Playwright page object
 * @param {Page} page - The Playwright page object to set as active
 */
function setActiveMeetPage(page) {
  activePage = page;
}

/**
 * Gets the currently active Playwright page object
 * @returns {Page|null} The active page object or null if no page is active
 */
function getActiveMeetPage() {
  return activePage;
}

export { getActiveMeetPage, setActiveMeetPage };
