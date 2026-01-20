document.addEventListener("DOMContentLoaded", function() {
  const sidebar = document.getElementById('side-nav');
  const main = document.getElementById('main-content');
  const toggle = document.getElementById('sidebar-toggle');

  if (!sidebar || !toggle || !main) return;

  toggle.addEventListener('click', function() {
    sidebar.classList.toggle('collapsed');
    main.classList.toggle('collapsed');
  });
});
