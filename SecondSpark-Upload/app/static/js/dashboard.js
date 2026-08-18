/**
 * SecondSpark — Dashboard Scripts
 * Handles counter animations and interactive widgets
 */

document.addEventListener('DOMContentLoaded', () => {
  // Animate numbers on stats cards
  const statNumbers = document.querySelectorAll('.stat-val');
  statNumbers.forEach(el => {
    const target = parseInt(el.textContent, 10);
    if (isNaN(target)) return;

    let current = 0;
    const duration = 1000;
    const step = Math.max(1, Math.ceil(target / (duration / 25)));

    const timer = setInterval(() => {
      current += step;
      if (current >= target) {
        el.textContent = target;
        clearInterval(timer);
      } else {
        el.textContent = current;
      }
    }, 25);
  });
});
