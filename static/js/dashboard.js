// Dashboard functionality
let currentMood = null;

function setMood(mood, emoji) {
  currentMood = { mood, emoji };

  // Visual feedback
  const buttons = document.querySelectorAll(".mood-btn");
  buttons.forEach((btn) => btn.classList.remove("active"));
  event.target.classList.add("active");

  // Send to server
  fetch("/dashboard/add-mood", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      mood_text: mood,
      emoji: emoji,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification("Mood updated! 💫", "success");
        // Refresh recent moods after a short delay
        setTimeout(() => {
          location.reload();
        }, 1000);
      } else {
        showNotification("Error updating mood", "error");
      }
    })
    .catch((error) => {
      console.error("Error setting mood:", error);
      showNotification("Error updating mood", "error");
    });
}

function showAddNoteModal() {
  const modal = document.getElementById("addNoteModal");
  modal.style.display = "block";
}

function closeAddNoteModal() {
  const modal = document.getElementById("addNoteModal");
  modal.style.display = "none";
  document.getElementById("addNoteForm").reset();
}

function addAnniversary() {
  const modal = document.getElementById("addAnniversaryModal");
  modal.style.display = "block";
}

function closeAddAnniversaryModal() {
  const modal = document.getElementById("addAnniversaryModal");
  modal.style.display = "none";
  document.getElementById("addAnniversaryForm").reset();
}

// Note form handling
document.getElementById("addNoteForm").addEventListener("submit", function (e) {
  e.preventDefault();

  const title = document.getElementById("noteTitle").value;
  const content = document.getElementById("noteContent").value;
  const isShared = document.getElementById("noteShared").checked;

  if (!content.trim()) {
    showNotification("Note content is required", "error");
    return;
  }

  fetch("/dashboard/add-note", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      title: title,
      content: content,
      is_shared: isShared,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification("Note added successfully! 📝", "success");
        closeAddNoteModal();
        // Refresh the page to show new note
        setTimeout(() => {
          location.reload();
        }, 1000);
      } else {
        showNotification(data.error, "error");
      }
    })
    .catch((error) => {
      console.error("Error adding note:", error);
      showNotification("Error adding note", "error");
    });
});

// Anniversary form handling
document
  .getElementById("addAnniversaryForm")
  .addEventListener("submit", function (e) {
    e.preventDefault();

    const title = document.getElementById("anniversaryTitle").value;
    const date = document.getElementById("anniversaryDate").value;
    const recurring = document.getElementById("anniversaryRecurring").checked;

    fetch("/dashboard/add-anniversary", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: title,
        date: date,
        recurring: recurring,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showNotification("Anniversary added! 📅", "success");
          closeAddAnniversaryModal();
          // Refresh the page to show new anniversary
          setTimeout(() => {
            location.reload();
          }, 1000);
        } else {
          showNotification(data.error, "error");
        }
      })
      .catch((error) => {
        console.error("Error adding anniversary:", error);
        showNotification("Error adding anniversary", "error");
      });
  });

function loadRecentMemories() {
  const container = document.querySelector(".memories-preview");

  fetch("/dashboard/memories")
    .then((response) => response.text())
    .then((html) => {
      // Extract memory items from the full page
      const tempDiv = document.createElement("div");
      tempDiv.innerHTML = html;
      const memoryItems = tempDiv.querySelectorAll(".memory-item");

      container.innerHTML = "";

      if (memoryItems.length > 0) {
        const timeline = document.createElement("div");
        timeline.className = "memory-timeline";

        // Take only the first 3 memories for preview
        Array.from(memoryItems)
          .slice(0, 3)
          .forEach((item) => {
            timeline.appendChild(item.cloneNode(true));
          });

        container.appendChild(timeline);
      } else {
        container.innerHTML = `
                    <div class="no-data">
                        <i class="fas fa-history"></i>
                        <p>No memories yet</p>
                        <p class="small">Start chatting to create memories!</p>
                    </div>
                `;
      }
    })
    .catch((error) => {
      console.error("Error loading memories:", error);
      container.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error loading memories</p>
                </div>
            `;
    });
}

function sendVirtualHug() {
  fetch("/dashboard/virtual-hug", {
    method: "POST",
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification(data.message, "success");
        createFloatingHearts();
      } else {
        showNotification(data.error, "error");
      }
    })
    .catch((error) => {
      console.error("Error sending virtual hug:", error);
      showNotification("Error sending virtual hug", "error");
    });
}

function createFloatingHearts() {
  for (let i = 0; i < 15; i++) {
    setTimeout(() => {
      createFloatingHeart();
    }, i * 100);
  }
}

function createFloatingHeart() {
  const heart = document.createElement("div");
  heart.innerHTML = "💖";
  heart.style.position = "fixed";
  heart.style.fontSize = Math.random() * 24 + 16 + "px";
  heart.style.left = Math.random() * 100 + "vw";
  heart.style.top = "100vh";
  heart.style.zIndex = "10000";
  heart.style.pointerEvents = "none";
  heart.style.animation = `floatUp ${Math.random() * 3 + 2}s ease-in forwards`;
  heart.style.opacity = "0.8";

  document.body.appendChild(heart);

  setTimeout(() => {
    heart.remove();
  }, 5000);
}

function invitePartner() {
  const email = prompt("Enter your partner's email address:");
  if (email && email.includes("@")) {
    // In a real implementation, you would send an invitation email
    showNotification(`Invitation sent to ${email}! 💌`, "success");

    // Simulate sending invitation
    fetch("/auth/invite-partner", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email: email }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showNotification("Invitation sent successfully!", "success");
        }
      })
      .catch((error) => {
        console.error("Error sending invitation:", error);
      });
  } else if (email) {
    showNotification("Please enter a valid email address", "error");
  }
}

function showNotification(message, type) {
  // Create or use existing flash container
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
    flashMessage.remove();
  }, 5000);

  // Close button functionality
  flashMessage.querySelector(".flash-close").onclick = () => {
    flashMessage.remove();
  };
}

// Close modals when clicking outside
document.addEventListener("click", function (event) {
  const modals = document.querySelectorAll(".modal");
  modals.forEach((modal) => {
    if (event.target === modal) {
      modal.style.display = "none";
    }
  });
});

// Add CSS for floating animation
const style = document.createElement("style");
style.textContent = `
    @keyframes floatUp {
        0% {
            transform: translateY(0) rotate(0deg);
            opacity: 0.8;
        }
        50% {
            opacity: 1;
        }
        100% {
            transform: translateY(-100vh) rotate(360deg);
            opacity: 0;
        }
    }
    
    .small {
        font-size: 0.8rem;
    }
`;
document.head.appendChild(style);

// Initialize dashboard features
document.addEventListener("DOMContentLoaded", function () {
  // Set current date as default for anniversary form
  const today = new Date().toISOString().split("T")[0];
  const anniversaryDate = document.getElementById("anniversaryDate");
  if (anniversaryDate) {
    anniversaryDate.value = today;
  }

  // Add animation to stat cards on scroll
  const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px",
  };

  const observer = new IntersectionObserver(function (entries) {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.style.animation = "fadeInUp 0.6s ease forwards";
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // Observe all dashboard cards
  document.querySelectorAll(".dashboard-card").forEach((card) => {
    card.style.opacity = "0";
    observer.observe(card);
  });
});
