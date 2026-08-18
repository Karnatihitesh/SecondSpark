/**
 * SecondSpark — Authentication Scripts
 * Handles real-time password strength meter and form validation
 */

document.addEventListener('DOMContentLoaded', () => {
  const regForm = document.getElementById('register-form');
  const passwordInput = document.getElementById('password');
  const confirmInput = document.getElementById('confirm_password');
  const strengthBar = document.getElementById('password-strength-bar');
  const strengthText = document.getElementById('password-strength-text');

  if (passwordInput && strengthBar) {
    passwordInput.addEventListener('input', () => {
      const val = passwordInput.value;
      let score = 0;

      if (val.length >= 8) score++;
      if (/[A-Z]/.test(val)) score++;
      if (/[a-z]/.test(val)) score++;
      if (/[0-9]/.test(val)) score++;
      if (/[^A-Za-z0-9]/.test(val)) score++;

      strengthBar.style.width = `${(score / 5) * 100}%`;

      if (score <= 2) {
        strengthBar.style.backgroundColor = '#EF4444';
        if (strengthText) strengthText.textContent = 'Weak (add letters & numbers)';
      } else if (score <= 4) {
        strengthBar.style.backgroundColor = '#F59E0B';
        if (strengthText) strengthText.textContent = 'Medium';
      } else {
        strengthBar.style.backgroundColor = '#35C98A';
        if (strengthText) strengthText.textContent = 'Strong password';
      }
    });
  }

  if (regForm) {
    regForm.addEventListener('submit', (e) => {
      if (passwordInput && confirmInput && passwordInput.value !== confirmInput.value) {
        e.preventDefault();
        alert('Passwords do not match. Please verify and try again.');
      }
    });
  }
});
