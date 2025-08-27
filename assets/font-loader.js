// Load saved font preference on page load
window.addEventListener('DOMContentLoaded', (event) => {
    const savedFont = localStorage.getItem('preferredFont');
    if (savedFont) {
        // Apply the saved font
        document.body.style.fontFamily = `'${savedFont}', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`;
        
        // Apply to all text elements after a short delay to ensure they're loaded
        setTimeout(() => {
            const elements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, a, div, span, button, input, textarea, .nav-link, td, th');
            elements.forEach(el => {
                el.style.fontFamily = `'${savedFont}', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`;
            });
            
            // Update the dropdown if it exists
            const fontSelector = document.getElementById('font-selector');
            if (fontSelector) {
                // Find the React input element and update its value
                const reactProps = Object.keys(fontSelector).find(key => key.startsWith('__reactProps'));
                if (reactProps && fontSelector[reactProps]) {
                    fontSelector[reactProps].value = savedFont;
                }
            }
        }, 100);
    }
});

// Also apply font changes to dynamically added elements
const observer = new MutationObserver((mutations) => {
    const savedFont = localStorage.getItem('preferredFont');
    if (savedFont) {
        mutations.forEach((mutation) => {
            if (mutation.addedNodes.length) {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) { // Element node
                        node.style.fontFamily = `'${savedFont}', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`;
                        const childElements = node.querySelectorAll('h1, h2, h3, h4, h5, h6, p, a, div, span, button, input, textarea, .nav-link, td, th');
                        childElements.forEach(el => {
                            el.style.fontFamily = `'${savedFont}', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`;
                        });
                    }
                });
            }
        });
    }
});

// Start observing the document for changes
observer.observe(document.body, {
    childList: true,
    subtree: true
});