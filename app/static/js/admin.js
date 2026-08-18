/**
 * SecondSpark — Admin Panel Scripts
 * Handles table filtering, report moderation modals, and confirmation dialogues
 */

document.addEventListener('DOMContentLoaded', () => {
  // Confirm sensitive actions
  document.querySelectorAll('.confirm-action').forEach(btn => {
    btn.addEventListener('click', function (e) {
      const msg = this.getAttribute('data-confirm-message') || 'Are you sure you want to perform this action?';
      if (!confirm(msg)) {
        e.preventDefault();
      }
    });
  });
});
