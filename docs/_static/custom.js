// The Read the Docs theme scrolls the sidebar navigation to keep the current
// section link in view, which pushes the SourceSpec logo out of sight.
// Disable that behaviour so the sidebar never auto-scrolls.
(function() {
  const original = Element.prototype.scrollIntoView;
  Element.prototype.scrollIntoView = function() {
    if (this.closest(".wy-menu-vertical")) {
      return;
    }
    original.apply(this, arguments);
  };
})();

document.addEventListener("DOMContentLoaded", function() {
  // Stop the theme's sticky navigation from syncing the sidebar scroll
  // position with the main content scroll position.
  const nav = window.SphinxRtdTheme && window.SphinxRtdTheme.Navigation;
  if (nav) {
    nav.onScroll = function() {};
  }

  document.querySelectorAll("a.external").forEach(function(link) {
    link.setAttribute("target", "_blank");
    link.setAttribute("rel", "noopener noreferrer");
  });
});
