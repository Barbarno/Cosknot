(() => {
  const bar = document.querySelector("[data-filter-bar]");
  const grid = document.querySelector("[data-creator-grid]");
  if (!bar || !grid) return;

  const chips = Array.from(bar.querySelectorAll("[data-filter]"));
  const cards = Array.from(grid.querySelectorAll("[data-specialty]"));
  const status = bar.querySelector("[data-filter-status]");
  const empty = document.querySelector("[data-empty-state]");

  const apply = (value) => {
    let visible = 0;

    for (const card of cards) {
      const match = value === "todas" || card.dataset.specialty === value;
      card.hidden = !match;
      if (match) visible += 1;
    }

    for (const chip of chips) {
      const active = chip.dataset.filter === value;
      chip.classList.toggle("is-active", active);
      chip.setAttribute("aria-pressed", String(active));
    }

    if (status) {
      status.textContent =
        value === "todas"
          ? `${visible} creadores`
          : `${visible} creadores en ${value}`;
    }

    if (empty) empty.hidden = visible !== 0;
  };

  bar.addEventListener("click", (event) => {
    const chip = event.target.closest("[data-filter]");
    if (!chip || !bar.contains(chip)) return;
    apply(chip.dataset.filter);
  });

  apply("todas");
})();
