// Authentication JavaScript functionality

function togglePassword(button) {
  const input = button.parentElement.querySelector("input");
  const icon = button.querySelector("i");

  if (input.type === "password") {
    input.type = "text";
    icon.className = "fas fa-eye-slash";
    button.setAttribute("aria-label", "Hide password");
  } else {
    input.type = "password";
    icon.className = "fas fa-eye";
    button.setAttribute("aria-label", "Show password");
  }
}

function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

function validatePassword(password) {
  const requirements = {
    length: password.length >= 8,
    lowercase: /[a-z]/.test(password),
    uppercase: /[A-Z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[^a-zA-Z0-9]/.test(password),
  };

  return requirements;
}

function updatePasswordStrength(password) {
  const requirements = validatePassword(password);
  const metCount = Object.values(requirements).filter(Boolean).length;
  const strength = (metCount / 5) * 100;

  const strengthFill = document.getElementById("strengthFill");
  const strengthText = document.getElementById("strengthText");

  if (strengthFill && strengthText) {
    strengthFill.style.width = strength + "%";

    // Update colors and text based on strength
    if (strength < 40) {
      strengthFill.style.background = "#f44336";
      strengthText.textContent = "Weak";
      strengthText.style.color = "#f44336";
    } else if (strength < 70) {
      strengthFill.style.background = "#ff9800";
      strengthText.textContent = "Medium";
      strengthText.style.color = "#ff9800";
    } else {
      strengthFill.style.background = "#4caf50";
      strengthText.textContent = "Strong";
      strengthText.style.color = "#4caf50";
    }
  }

  return strength;
}

function checkPasswordMatch() {
  const password = document.getElementById("password");
  const confirmPassword = document.getElementById("confirmPassword");
  const matchElement = document.getElementById("passwordMatch");

  if (!password || !confirmPassword || !matchElement) return;

  if (confirmPassword.value === "") {
    matchElement.style.display = "none";
  } else if (password.value === confirmPassword.value) {
    matchElement.style.display = "flex";
    matchElement.innerHTML =
      '<i class="fas fa-check"></i><span>Passwords match</span>';
    matchElement.style.color = "#4caf50";
  } else {
    matchElement.style.display = "flex";
    matchElement.innerHTML =
      '<i class="fas fa-times"></i><span>Passwords do not match</span>';
    matchElement.style.color = "#f44336";
  }
}

// Form submission handling
document.addEventListener("DOMContentLoaded", function () {
  const signupForm = document.getElementById("signupForm");
  const loginForm = document.querySelector('form[action*="login"]');

  // Password strength and match checking for signup form
  if (signupForm) {
    const passwordInput = document.getElementById("password");
    const confirmInput = document.getElementById("confirmPassword");

    if (passwordInput) {
      passwordInput.addEventListener("input", function () {
        updatePasswordStrength(this.value);
        checkPasswordMatch();
      });
    }

    if (confirmInput) {
      confirmInput.addEventListener("input", checkPasswordMatch);
    }

    // Enhanced form validation
    signupForm.addEventListener("submit", function (e) {
      const password = document.getElementById("password")?.value;
      const confirmPassword = document.getElementById("confirmPassword")?.value;

      if (password && confirmPassword && password !== confirmPassword) {
        e.preventDefault();
        showNotification("Passwords do not match!", "error");
        return;
      }

      const strength = updatePasswordStrength(password);
      if (strength < 40) {
        e.preventDefault();
        showNotification("Please choose a stronger password", "error");
        return;
      }

      // Add loading state
      const submitBtn = this.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.classList.add("loading");
        submitBtn.disabled = true;
        submitBtn.innerHTML =
          '<i class="fas fa-spinner fa-spin"></i> Creating Account...';
      }
    });
  }

  // Login form enhancement
  if (loginForm) {
    loginForm.addEventListener("submit", function (e) {
      const submitBtn = this.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.classList.add("loading");
        submitBtn.disabled = true;
        submitBtn.innerHTML =
          '<i class="fas fa-spinner fa-spin"></i> Signing In...';
      }
    });
  }

  // Auto-focus first input in forms
  const firstInput = document.querySelector("form .form-input");
  if (firstInput) {
    firstInput.focus();
  }
});

function showNotification(message, type) {
  // Create flash message container if it doesn't exist
  let flashContainer = document.querySelector(".flash-container");
  if (!flashContainer) {
    flashContainer = document.createElement("div");
    flashContainer.className = "flash-container";
    document.body.appendChild(flashContainer);
  }

  const flashMessage = document.createElement("div");
  flashMessage.className = `flash-message ${type}`;
  flashMessage.innerHTML = `
        ${message}
        <span class="flash-close">&times;</span>
    `;

  flashContainer.appendChild(flashMessage);

  // Auto remove after 5 seconds
  setTimeout(() => {
    if (flashMessage.parentElement) {
      flashMessage.remove();
    }
  }, 5000);

  // Close button functionality
  flashMessage.querySelector(".flash-close").onclick = () => {
    flashMessage.remove();
  };
}

// Handle OTP input functionality
function handleOtpInput() {
  const otpInputs = document.querySelectorAll(".otp-input");
  if (otpInputs.length === 0) return;

  otpInputs.forEach((input, index) => {
    input.addEventListener("input", function (e) {
      // Only allow numbers
      this.value = this.value.replace(/[^0-9]/g, "");

      if (this.value.length === 1) {
        // Move to next input
        if (index < otpInputs.length - 1) {
          otpInputs[index + 1].focus();
        }
      }

      checkOtpComplete();
    });

    input.addEventListener("keydown", function (e) {
      if (e.key === "Backspace" && this.value === "" && index > 0) {
        otpInputs[index - 1].focus();
      } else if (e.key === "ArrowLeft" && index > 0) {
        otpInputs[index - 1].focus();
        e.preventDefault();
      } else if (e.key === "ArrowRight" && index < otpInputs.length - 1) {
        otpInputs[index + 1].focus();
        e.preventDefault();
      }
    });
  });
}

function checkOtpComplete() {
  const otpInputs = document.querySelectorAll(".otp-input");
  const isComplete = Array.from(otpInputs).every(
    (input) => input.value.length === 1
  );
  const verifyBtn = document.getElementById("verifyBtn");

  if (verifyBtn) {
    verifyBtn.disabled = !isComplete;
  }

  if (isComplete) {
    // Auto-submit after a short delay
    setTimeout(() => {
      const form = document.getElementById("otpForm");
      if (form) {
        // Combine OTP values
        const otp = Array.from(otpInputs)
          .map((input) => input.value)
          .join("");
        const hiddenInput = document.createElement("input");
        hiddenInput.type = "hidden";
        hiddenInput.name = "otp";
        hiddenInput.value = otp;
        form.appendChild(hiddenInput);

        form.submit();
      }
    }, 500);
  }
}

// Initialize OTP functionality if on OTP page
if (window.location.pathname.includes("verify-otp")) {
  document.addEventListener("DOMContentLoaded", function () {
    handleOtpInput();

    // Start OTP expiration timer
    startOtpTimer(300); // 5 minutes
  });
}

function startOtpTimer(duration) {
  const timerDisplay = document.getElementById("countdown");
  const resendLink = document.getElementById("resendLink");

  if (!timerDisplay) return;

  let time = duration;
  const timerInterval = setInterval(function () {
    const minutes = Math.floor(time / 60);
    const seconds = time % 60;

    timerDisplay.textContent = `${minutes.toString().padStart(2, "0")}:${seconds
      .toString()
      .padStart(2, "0")}`;

    if (time <= 30) {
      timerDisplay.parentElement.classList.add("expiring");
    }

    if (time <= 0) {
      clearInterval(timerInterval);
      timerDisplay.textContent = "00:00";
      if (resendLink) {
        resendLink.style.display = "inline";
      }
    }

    time--;
  }, 1000);
}

// Password reset functionality
function requestPasswordReset() {
  const email = document.getElementById("email")?.value;

  if (!email || !validateEmail(email)) {
    showNotification("Please enter a valid email address", "error");
    return;
  }

  const btn = document.querySelector(".auth-btn");
  if (btn) {
    btn.classList.add("loading");
    btn.disabled = true;
    btn.innerHTML =
      '<i class="fas fa-spinner fa-spin"></i> Sending Reset Link...';
  }

  // Simulate API call - replace with actual implementation
  setTimeout(() => {
    showNotification(
      "If the email exists, a reset link has been sent!",
      "success"
    );
    if (btn) {
      btn.classList.remove("loading");
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-paper-plane"></i> Send Reset Link';
    }
  }, 2000);
}

// Export functions for global access
window.togglePassword = togglePassword;
window.showNotification = showNotification;
window.requestPasswordReset = requestPasswordReset;
