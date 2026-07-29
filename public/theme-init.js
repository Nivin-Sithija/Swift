(() => {
  const saved = localStorage.getItem("swift-theme");
  const theme = saved || "dark";
  const dark =
    theme === "dark" ||
    (theme === "system" &&
      matchMedia("(prefers-color-scheme: dark)").matches);

  document.documentElement.classList.toggle("dark", dark);
  document.documentElement.dataset.theme = theme;
})();
