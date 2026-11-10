(() => {
  // Owner/staff dashboard navigation (independent of the public-site menu).
  const adminToggle = document.getElementById("adminMenuToggle");
  const sidebar = document.getElementById("admin-sidebar");
  if (adminToggle && sidebar) {
    const label = adminToggle.querySelector("span:last-child");
    adminToggle.addEventListener("click", () => {
      const isOpen = sidebar.classList.toggle("is-open");
      adminToggle.setAttribute("aria-expanded", String(isOpen));
      if (label) label.textContent = isOpen ? "Close menu" : "Menu";
    });
    sidebar.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        sidebar.classList.remove("is-open");
        adminToggle.setAttribute("aria-expanded", "false");
        if (label) label.textContent = "Menu";
      });
    });
  }

  // Public website mobile navigation. Do not return early when no admin menu exists.
  const publicToggle = document.querySelector(".menu-toggle");
  const publicNav = document.getElementById("public-nav") || document.querySelector(".nav-links");
  if (publicToggle && publicNav) {
    const closeMenu = () => {
      publicNav.classList.remove("open");
      publicToggle.setAttribute("aria-expanded", "false");
      publicToggle.setAttribute("aria-label", "Open navigation");
    };
    publicToggle.addEventListener("click", () => {
      const isOpen = publicNav.classList.toggle("open");
      publicToggle.setAttribute("aria-expanded", String(isOpen));
      publicToggle.setAttribute("aria-label", isOpen ? "Close navigation" : "Open navigation");
    });
    publicNav.querySelectorAll('a[href^="#"]').forEach((link) => {
      link.addEventListener("click", closeMenu);
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeMenu();
    });
  }
})();
