let socket;
let isTyping = false;
let typingTimer;
let isRecording = false;
let mediaRecorder;
let audioChunks = [];

function initializeChat() {
  // Connect to SocketIO
  socket = io();

  // Socket event listeners
  socket.on("connect", function () {
    console.log("Connected to chat server");
  });

  socket.on("new_message", function (data) {
    addMessage(data, "received");
    playNotificationSound();
    scrollToBottom();
  });

  socket.on("user_typing", function (data) {
    showTypingIndicator(data.user_name);
  });

  socket.on("user_stop_typing", function (data) {
    hideTypingIndicator();
  });

  socket.on("virtual_hug", function (data) {
    showVirtualHugAnimation(data.from_user_name);
  });

  socket.on("mood_update", function (data) {
    showMoodNotification(data);
  });

  // NEW: Partner connection events
  socket.on("partner_connected", function (data) {
    showPartnerConnectedNotification(data);
    // Refresh the page to show the new partner after 3 seconds
    setTimeout(() => {
      window.location.reload();
    }, 3000);
  });

  socket.on("user_online", function (data) {
    if (data.user_id === PARTNER_ID) {
      updatePartnerStatus("online", data.user_name);
    }
  });

  socket.on("user_offline", function (data) {
    if (data.user_id === PARTNER_ID) {
      updatePartnerStatus("offline");
    }
  });

  socket.on("error", function (data) {
    showNotification(data.message, "error");
  });
}

// NEW: Partner connection notification
function showPartnerConnectedNotification(data) {
  const notification = document.createElement("div");
  notification.className = "partner-connected-notification";
  notification.innerHTML = `
    <div class="partner-connected-content">
      <div class="partner-connected-icon">
        <i class="fas fa-heart"></i>
      </div>
      <div class="partner-connected-text">
        <h4>🎉 Connected with ${data.partner_name}!</h4>
        <p>You can now start chatting together!</p>
      </div>
      <button class="partner-connected-close" onclick="this.parentElement.parentElement.remove()">
        <i class="fas fa-times"></i>
      </button>
    </div>
  `;

  // Add styles if not already added
  if (!document.querySelector("#partnerConnectedStyles")) {
    const styles = document.createElement("style");
    styles.id = "partnerConnectedStyles";
    styles.textContent = `
      .partner-connected-notification {
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideDown 0.5s ease-out;
        max-width: 400px;
        width: 90%;
      }
      .partner-connected-content {
        display: flex;
        align-items: center;
        gap: 15px;
      }
      .partner-connected-icon {
        font-size: 24px;
        animation: pulse 2s infinite;
      }
      .partner-connected-text h4 {
        margin: 0 0 5px 0;
        font-size: 16px;
      }
      .partner-connected-text p {
        margin: 0;
        opacity: 0.9;
        font-size: 14px;
      }
      .partner-connected-close {
        background: none;
        border: none;
        color: white;
        font-size: 16px;
        cursor: pointer;
        margin-left: auto;
      }
      @keyframes slideDown {
        from { transform: translateX(-50%) translateY(-100px); opacity: 0; }
        to { transform: translateX(-50%) translateY(0); opacity: 1; }
      }
      @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
      }
      @keyframes slideUp {
        from { transform: translateX(-50%) translateY(0); opacity: 1; }
        to { transform: translateX(-50%) translateY(-100px); opacity: 0; }
      }
    `;
    document.head.appendChild(styles);
  }

  document.body.appendChild(notification);

  // Auto remove after 5 seconds
  setTimeout(() => {
    if (notification.parentElement) {
      notification.style.animation = "slideUp 0.5s ease-out forwards";
      setTimeout(() => notification.remove(), 500);
    }
  }, 5000);
}

// NEW: Update partner status
function updatePartnerStatus(status, userName = "") {
  const statusDot = document.querySelector(".status-dot");
  const statusText = document.querySelector(".partner-status");

  if (statusDot && statusText) {
    if (status === "online") {
      statusDot.className = "status-dot online";
      statusText.innerHTML = '<span class="status-dot online"></span> Online';
      // Update typing indicator name if partner comes online
      const typingIndicator = document.getElementById("typingIndicator");
      if (typingIndicator) {
        typingIndicator.querySelector(
          "span:last-child"
        ).textContent = `${userName} is typing...`;
      }
    } else {
      statusDot.className = "status-dot offline";
      // Keep the existing last seen text
      const currentText = statusText.textContent.replace("Online", "").trim();
      statusText.innerHTML = `<span class="status-dot offline"></span> ${currentText}`;
    }
  }
}

// NEW: Check for partner connection on page load
function checkForPartnerConnection() {
  if (!PARTNER_ID) {
    // Check if we just got connected (via URL parameter or session)
    const urlParams = new URLSearchParams(window.location.search);
    const justConnected = urlParams.get("connected");

    if (justConnected) {
      showNotification(
        "🎉 You're now connected with your partner! Start chatting!",
        "success"
      );
      // Remove the parameter from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }
}

function loadMessages() {
  const container = document.getElementById("messagesContainer");
  const loading = document.getElementById("messagesLoading");

  fetch(`/chat/messages?partner_id=${PARTNER_ID}`)
    .then((response) => response.json())
    .then((data) => {
      loading.style.display = "none";

      if (data.messages && data.messages.length > 0) {
        data.messages.forEach((message) => {
          addMessage(
            message,
            message.sender_id == CURRENT_USER_ID ? "sent" : "received"
          );
        });
        scrollToBottom();
      } else {
        container.innerHTML = `
                    <div class="no-messages">
                        <i class="fas fa-comments"></i>
                        <h3>No messages yet</h3>
                        <p>Start the conversation with your partner!</p>
                    </div>
                `;
      }
    })
    .catch((error) => {
      console.error("Error loading messages:", error);
      loading.style.display = "none";
      showNotification("Error loading messages", "error");
    });
}

function addMessage(messageData, type) {
  const container = document.getElementById("messagesContainer");

  // Remove no messages placeholder if it exists
  const noMessages = container.querySelector(".no-messages");
  if (noMessages) {
    noMessages.remove();
  }

  const messageElement = document.createElement("div");
  messageElement.className = `message ${type}`;

  const timestamp = new Date(messageData.timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  let contentHtml = "";

  if (messageData.type === "text") {
    contentHtml = `
            <div class="message-content">${formatMessage(
              messageData.content
            )}</div>
            <div class="message-time">${timestamp}</div>
        `;
  } else if (messageData.type === "image") {
    contentHtml = `
            <div class="media-message">
                <div class="media-content" onclick="openMedia('${
                  messageData.media.file_path
                }')">
                    <img src="${
                      messageData.media.thumbnail_path ||
                      messageData.media.file_path
                    }" 
                         alt="Shared image">
                </div>
                <div class="message-time">${timestamp}</div>
            </div>
        `;
  } else if (messageData.type === "video") {
    contentHtml = `
            <div class="media-message">
                <div class="media-content" onclick="openMedia('${messageData.media.file_path}')">
                    <video controls>
                        <source src="${messageData.media.file_path}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                </div>
                <div class="message-time">${timestamp}</div>
            </div>
        `;
  } else if (messageData.type === "voice") {
    contentHtml = `
            <div class="audio-message">
                <audio controls>
                    <source src="${messageData.media.file_path}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
                <div class="message-time">${timestamp}</div>
            </div>
        `;
  }

  messageElement.innerHTML = contentHtml;
  container.appendChild(messageElement);
}

function formatMessage(content) {
  // Convert URLs to links
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  content = content.replace(urlRegex, '<a href="$1" target="_blank">$1</a>');

  // Convert line breaks
  content = content.replace(/\n/g, "<br>");

  return content;
}

function sendMessage() {
  const input = document.getElementById("messageInput");
  const content = input.value.trim();

  if (!content) return;

  const messageData = {
    message: content,
    type: "text",
    partner_id: PARTNER_ID,
  };

  fetch("/chat/send-message", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(messageData),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Add the sent message to the chat immediately
        addMessage(data.message, "sent");
        input.value = "";
        stopTyping();
        scrollToBottom();
      } else {
        showNotification(data.error, "error");
      }
    })
    .catch((error) => {
      console.error("Error sending message:", error);
      showNotification("Error sending message", "error");
    });
}

function handleFileUpload(file) {
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);
  formData.append("type", getFileType(file.type));
  formData.append("partner_id", PARTNER_ID);

  fetch("/chat/send-message", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        addMessage(data.message, "sent");
        scrollToBottom();
      } else {
        showNotification(data.error, "error");
      }
    })
    .catch((error) => {
      console.error("Error uploading file:", error);
      showNotification("Error uploading file", "error");
    });
}

function getFileType(mimeType) {
  if (mimeType.startsWith("image/")) return "image";
  if (mimeType.startsWith("video/")) return "video";
  if (mimeType.startsWith("audio/")) return "voice";
  return "file";
}

function handleKeyPress(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

function handleTyping() {
  if (!isTyping) {
    isTyping = true;
    socket.emit("typing", {
      typing: true,
      partner_id: PARTNER_ID,
      user_name:
        document.querySelector(".partner-info h3")?.textContent ||
        "Your partner",
    });
  }

  clearTimeout(typingTimer);
  typingTimer = setTimeout(stopTyping, 1000);
}

function stopTyping() {
  if (isTyping) {
    isTyping = false;
    socket.emit("stop_typing", {
      typing: false,
      partner_id: PARTNER_ID,
    });
  }
}

function showTypingIndicator(userName) {
  const indicator = document.getElementById("typingIndicator");
  indicator.querySelector(
    "span:last-child"
  ).textContent = `${userName} is typing...`;
  indicator.style.display = "flex";
}

function hideTypingIndicator() {
  const indicator = document.getElementById("typingIndicator");
  indicator.style.display = "none";
}

function toggleEmojiPicker() {
  const picker = document.getElementById("emojiPicker");
  picker.style.display = picker.style.display === "none" ? "block" : "none";
}

function addEmoji(emoji) {
  const input = document.getElementById("messageInput");
  input.value += emoji;
  input.focus();
  toggleEmojiPicker();
}

function startVoiceRecording() {
  if (!navigator.mediaDevices || !window.MediaRecorder) {
    showNotification("Voice recording not supported in your browser", "error");
    return;
  }

  if (isRecording) {
    stopVoiceRecording();
    return;
  }

  navigator.mediaDevices
    .getUserMedia({ audio: true })
    .then((stream) => {
      isRecording = true;
      audioChunks = [];
      mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
        sendVoiceMessage(audioBlob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      showNotification("Recording... Click again to stop", "info");

      // Update button appearance
      const recordBtn = document
        .querySelector(".action-btn .fa-microphone")
        .closest(".action-btn");
      recordBtn.innerHTML = '<i class="fas fa-stop"></i>';
      recordBtn.style.color = "#ff4444";
    })
    .catch((error) => {
      console.error("Error accessing microphone:", error);
      showNotification(
        "Cannot access microphone. Please check permissions.",
        "error"
      );
    });
}

function stopVoiceRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    isRecording = false;

    // Reset button appearance
    const recordBtn = document
      .querySelector(".action-btn .fa-stop")
      .closest(".action-btn");
    recordBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    recordBtn.style.color = "";

    showNotification("Recording stopped", "info");
  }
}

function sendVoiceMessage(audioBlob) {
  const formData = new FormData();
  formData.append("audio", audioBlob, "voice-message.wav");
  formData.append("type", "voice");
  formData.append("partner_id", PARTNER_ID);

  fetch("/chat/send-message", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        addMessage(data.message, "sent");
        scrollToBottom();
      } else {
        showNotification(data.error, "error");
      }
    })
    .catch((error) => {
      console.error("Error sending voice message:", error);
      showNotification("Error sending voice message", "error");
    });
}

function showMediaGallery() {
  const modal = document.getElementById("mediaGalleryModal");
  const grid = document.getElementById("mediaGrid");

  fetch(`/chat/media?partner_id=${PARTNER_ID}`)
    .then((response) => response.json())
    .then((data) => {
      grid.innerHTML = "";

      if (data.media && data.media.length > 0) {
        data.media.forEach((media) => {
          const mediaItem = document.createElement("div");
          mediaItem.className = "media-item";
          mediaItem.onclick = () => openMedia(media.file_path);

          if (media.file_type.startsWith("image/")) {
            mediaItem.innerHTML = `<img src="${
              media.thumbnail_path || media.file_path
            }" alt="Media">`;
          } else if (media.file_type.startsWith("video/")) {
            mediaItem.innerHTML = `
                            <div class="video-thumbnail">
                                <i class="fas fa-play"></i>
                                <video>
                                    <source src="${media.file_path}">
                                </video>
                            </div>
                        `;
          } else if (media.file_type.startsWith("audio/")) {
            mediaItem.innerHTML = `
                            <div class="audio-thumbnail">
                                <i class="fas fa-music"></i>
                                <p>Audio Message</p>
                            </div>
                        `;
          }

          grid.appendChild(mediaItem);
        });
      } else {
        grid.innerHTML = "<p class='no-media'>No media shared yet</p>";
      }

      modal.style.display = "block";
    })
    .catch((error) => {
      console.error("Error loading media:", error);
      showNotification("Error loading media", "error");
    });
}

function closeMediaGallery() {
  const modal = document.getElementById("mediaGalleryModal");
  modal.style.display = "none";
}

function openMedia(filePath) {
  window.open(filePath, "_blank");
}

function sendVirtualHug() {
  fetch("/dashboard/virtual-hug", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ partner_id: PARTNER_ID }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification(data.message, "success");
        // Also emit via socket for real-time effect
        socket.emit("send_virtual_hug", {
          partner_id: PARTNER_ID,
          from_user_name: "You",
        });
      } else {
        showNotification(data.error, "error");
      }
    })
    .catch((error) => {
      console.error("Error sending virtual hug:", error);
      showNotification("Error sending virtual hug", "error");
    });
}

function showVirtualHugAnimation(fromUser) {
  // Create floating hearts animation
  for (let i = 0; i < 20; i++) {
    createFloatingHeart();
  }

  showNotification(`${fromUser} sent you a virtual hug! 💞`, "success");
}

function createFloatingHeart() {
  const heart = document.createElement("div");
  heart.innerHTML = "💖";
  heart.style.position = "fixed";
  heart.style.fontSize = Math.random() * 20 + 10 + "px";
  heart.style.left = Math.random() * 100 + "vw";
  heart.style.top = "100vh";
  heart.style.zIndex = "1000";
  heart.style.pointerEvents = "none";
  heart.style.animation = `floatUp ${Math.random() * 3 + 2}s linear forwards`;

  document.body.appendChild(heart);

  setTimeout(() => {
    heart.remove();
  }, 5000);
}

function toggleBackgroundMusic() {
  const music = document.getElementById("backgroundMusic");
  const musicBtn = document.querySelector(".fa-music").closest(".feature-btn");

  if (music.paused) {
    music
      .play()
      .then(() => {
        showNotification("Background music started", "success");
        musicBtn.innerHTML = '<i class="fas fa-pause"></i> Background Music';
      })
      .catch((e) => {
        console.log("Audio play failed:", e);
        showNotification(
          "Cannot play music. Please interact with the page first.",
          "error"
        );
      });
  } else {
    music.pause();
    showNotification("Background music paused", "info");
    musicBtn.innerHTML = '<i class="fas fa-music"></i> Background Music';
  }
}

function playNotificationSound() {
  const audio = new Audio("/static/sounds/notification.mp3");
  audio.volume = 0.3;
  audio.play().catch((e) => console.log("Notification sound play failed:", e));
}

function showNotification(message, type) {
  // Create or find flash container
  let flashContainer = document.querySelector(".flash-container");
  if (!flashContainer) {
    flashContainer = document.createElement("div");
    flashContainer.className = "flash-container";
    document.body.appendChild(flashContainer);
  }

  const flashMessage = document.createElement("div");
  flashMessage.className = `flash-message ${type}`;
  flashMessage.innerHTML = `
        <div class="flash-content">
            <span class="flash-icon">
                ${type === "success" ? "✓" : type === "error" ? "✕" : "ℹ"}
            </span>
            ${message}
            <span class="flash-close">&times;</span>
        </div>
    `;

  flashContainer.appendChild(flashMessage);

  // Auto remove after 5 seconds
  setTimeout(() => {
    if (flashMessage.parentElement) {
      flashMessage.style.animation = "slideOut 0.3s ease-out forwards";
      setTimeout(() => flashMessage.remove(), 300);
    }
  }, 5000);

  // Close button functionality
  flashMessage.querySelector(".flash-close").onclick = () => {
    flashMessage.style.animation = "slideOut 0.3s ease-out forwards";
    setTimeout(() => flashMessage.remove(), 300);
  };
}

function scrollToBottom() {
  const container = document.getElementById("messagesContainer");
  container.scrollTop = container.scrollHeight;
}

// Partner Invitation Functions
function invitePartner() {
  showInvitationModal();
}

function showInvitationModal() {
  const modal = document.createElement("div");
  modal.className = "invitation-modal";
  modal.innerHTML = `
        <div class="invitation-modal-content">
            <div class="invitation-modal-header">
                <h3>Invite Your Partner</h3>
                <button class="invitation-close-btn" onclick="this.closest('.invitation-modal').remove()">&times;</button>
            </div>
            <div class="invitation-modal-body">
                <div class="invitation-options">
                    <div class="invitation-option">
                        <h4>🔗 Share Invitation Link</h4>
                        <p>Send this link to your partner to connect</p>
                        <div class="link-container">
                            <input type="text" id="invitationLink" readonly value="${window.location.origin}/auth/signup?invite=${CURRENT_USER_ID}">
                            <button class="invitation-btn invitation-btn-secondary" onclick="copyInvitationLink()">
                                <i class="fas fa-copy"></i> Copy
                            </button>
                        </div>
                    </div>
                    
                    <div class="invitation-option">
                        <h4>📧 Send Email Invitation</h4>
                        <p>Invite via email</p>
                        <div class="email-invite">
                            <input type="email" id="partnerEmail" placeholder="Enter partner's email">
                            <button class="invitation-btn invitation-btn-primary" onclick="sendEmailInvitation()">
                                <i class="fas fa-paper-plane"></i> Send
                            </button>
                        </div>
                    </div>
                    
                    <div class="invitation-option">
                        <h4>🔧 Test Email Configuration</h4>
                        <p>Check if email is properly configured</p>
                        <button class="invitation-btn invitation-btn-secondary" onclick="testEmailConfig()">
                            <i class="fas fa-cog"></i> Test Configuration
                        </button>
                    </div>
                    
                    <div class="invitation-option">
                        <h4>👥 Connect Existing User</h4>
                        <p>If your partner already has an account</p>
                        <button class="invitation-btn invitation-btn-secondary" onclick="connectExistingUser()">
                            <i class="fas fa-user-plus"></i> Connect
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

  document.body.appendChild(modal);

  // Close modal when clicking outside
  modal.onclick = function (event) {
    if (event.target === modal) {
      modal.remove();
    }
  };

  // Focus on the first input field for better UX
  setTimeout(() => {
    const emailInput = document.getElementById("partnerEmail");
    if (emailInput) {
      emailInput.focus();
    }
  }, 100);
}

function copyInvitationLink() {
  const linkInput = document.getElementById("invitationLink");
  linkInput.select();
  linkInput.setSelectionRange(0, 99999);

  navigator.clipboard
    .writeText(linkInput.value)
    .then(() => {
      showNotification("Invitation link copied to clipboard!", "success");
    })
    .catch((err) => {
      // Fallback for older browsers
      document.execCommand("copy");
      showNotification("Invitation link copied!", "success");
    });
}

function sendEmailInvitation() {
  const emailInput = document.getElementById("partnerEmail");
  const email = emailInput.value.trim();

  if (!email) {
    showNotification("Please enter a valid email address", "error");
    return;
  }

  if (!validateEmail(email)) {
    showNotification("Please enter a valid email address", "error");
    return;
  }

  // Show loading state
  const sendBtn = emailInput.nextElementSibling;
  const originalText = sendBtn.innerHTML;
  sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
  sendBtn.disabled = true;

  fetch("/chat/send-invitation", {
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
        emailInput.value = "";

        // Close modal after successful send
        const modal = document.querySelector(".invitation-modal");
        if (modal) modal.remove();
      } else {
        showNotification(data.error || "Failed to send invitation", "error");
      }
    })
    .catch((error) => {
      console.error("Error sending invitation:", error);
      showNotification(
        "Network error. Please check your connection and try again.",
        "error"
      );
    })
    .finally(() => {
      sendBtn.innerHTML = originalText;
      sendBtn.disabled = false;
    });
}

function testEmailConfig() {
  // Show loading state
  showNotification("Checking email configuration...", "info");

  fetch("/chat/email-status")
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (data.configured) {
        showNotification(
          "✓ Email is properly configured! Sending test email...",
          "success"
        );

        // Automatically send test email to the configured email address
        sendTestEmail();
      } else {
        const missing = data.missing_configs
          ? data.missing_configs.join(", ")
          : "configuration issues";
        showNotification(`❌ Email configuration issues: ${missing}`, "error");

        // Show detailed help message
        setTimeout(() => {
          showNotification(
            "Please check your environment variables in .env file",
            "error"
          );
        }, 1000);
      }
    })
    .catch((error) => {
      console.error("Error checking email config:", error);
      showNotification(
        "Error checking email configuration. The endpoint might not be available.",
        "error"
      );
    });
}

function sendTestEmail() {
  // Use the current user's email or prompt for one
  const userEmail =
    "{{ current_user.email }}" ||
    prompt("Enter your email address to send a test email:");

  if (!userEmail) {
    showNotification("No email address available for testing", "error");
    return;
  }

  showNotification("Sending test email...", "info");

  fetch("/chat/send-test-email", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ test_email: userEmail }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification(
          "✓ Test email sent successfully! Please check your inbox.",
          "success"
        );
      } else {
        showNotification(data.error || "Failed to send test email", "error");
      }
    })
    .catch((error) => {
      console.error("Error sending test email:", error);
      showNotification("Error sending test email", "error");
    });
}

function connectExistingUser() {
  // Redirect to partner connection page
  window.location.href = "/dashboard/connect-partner";
}

function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

function showMoodNotification(moodData) {
  showNotification(
    `${moodData.user_name} is feeling ${moodData.mood_text} ${moodData.emoji}`,
    "info"
  );
}

// Utility Functions
function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

function getCurrentTimestamp() {
  return new Date().toISOString();
}

// Event Listeners
document.addEventListener("click", function (event) {
  const emojiPicker = document.getElementById("emojiPicker");
  const emojiButton = document
    .querySelector(".action-btn .fa-smile")
    ?.closest(".action-btn");

  if (emojiPicker && emojiButton) {
    if (
      emojiPicker.style.display !== "none" &&
      !emojiPicker.contains(event.target) &&
      !emojiButton.contains(event.target)
    ) {
      emojiPicker.style.display = "none";
    }
  }
});

// Add CSS for animations and invitation modal
const style = document.createElement("style");
style.textContent = `
    @keyframes floatUp {
        0% {
            transform: translateY(0) rotate(0deg);
            opacity: 1;
        }
        100% {
            transform: translateY(-100vh) rotate(360deg);
            opacity: 0;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .flash-container {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        max-width: 400px;
    }
    
    .flash-message {
        background: var(--card-bg-color);
        border-left: 4px solid;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-radius: 4px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        animation: slideIn 0.3s ease-out;
    }
    
    .flash-message.success {
        border-left-color: #4CAF50;
    }
    
    .flash-message.error {
        border-left-color: #f44336;
    }
    
    .flash-message.info {
        border-left-color: #2196F3;
    }
    
    .flash-content {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .flash-icon {
        font-weight: bold;
    }
    
    .flash-close {
        margin-left: auto;
        cursor: pointer;
        font-size: 18px;
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    /* Invitation Modal Styles - Unique class names */
    .invitation-modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    }

    .invitation-modal-content {
        background: white;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        width: 90%;
        max-width: 500px;
        max-height: 90vh;
        overflow-y: auto;
    }

    .invitation-modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 24px;
        border-bottom: 1px solid #eee;
    }

    .invitation-modal-header h3 {
        margin: 0;
        color: #333;
        font-size: 1.5rem;
        font-weight: 600;
    }

    .invitation-close-btn {
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: #666;
        padding: 0;
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: background-color 0.3s ease;
    }

    .invitation-close-btn:hover {
        background: #f5f5f5;
        color: #333;
    }

    .invitation-modal-body {
        padding: 24px;
    }

    .invitation-options {
        display: flex;
        flex-direction: column;
        gap: 20px;
    }
    
    .invitation-option {
        padding: 20px;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        background: #fafafa;
        transition: all 0.3s ease;
    }

    .invitation-option:hover {
        border-color: #c0c0c0;
        background: #f5f5f5;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .invitation-option h4 {
        margin: 0 0 8px 0;
        color: #333;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    .invitation-option p {
        margin: 0 0 16px 0;
        color: #666;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    
    .link-container {
        display: flex;
        gap: 10px;
        align-items: center;
    }
    
    .link-container input {
        flex: 1;
        padding: 12px 16px;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        background: #fff;
        font-size: 14px;
        font-family: inherit;
        transition: border-color 0.3s ease;
        color: #333;
    }

    .link-container input:focus {
        outline: none;
        border-color: #4a90e2;
        box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
    }
    
    .email-invite {
        display: flex;
        gap: 10px;
        align-items: center;
    }
    
    .email-invite input {
        flex: 1;
        padding: 12px 16px;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        font-size: 14px;
        font-family: inherit;
        transition: border-color 0.3s ease;
        color: #333;
    }

    .email-invite input:focus {
        outline: none;
        border-color: #4a90e2;
        box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
    }

    .email-invite input::placeholder {
        color: #999;
    }

    /* Invitation Button Styles */
    .invitation-btn {
        padding: 12px 20px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.3s ease;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        text-decoration: none;
        font-family: inherit;
    }

    .invitation-btn-primary {
        background: #4a90e2;
        color: white;
    }

    .invitation-btn-primary:hover {
        background: #357abd;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
    }

    .invitation-btn-secondary {
        background: #f0f0f0;
        color: #333;
        border: 1px solid #ddd;
    }

    .invitation-btn-secondary:hover {
        background: #e0e0e0;
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    .invitation-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
        transform: none !important;
        box-shadow: none !important;
    }
`;
document.head.appendChild(style);

// Update the DOMContentLoaded event listener
document.addEventListener("DOMContentLoaded", function () {
  if (PARTNER_ID) {
    initializeChat();
    loadMessages();
  }
  checkForPartnerConnection();
});

// Export functions for global access
window.invitePartner = invitePartner;
window.sendMessage = sendMessage;
window.startVoiceRecording = startVoiceRecording;
window.toggleBackgroundMusic = toggleBackgroundMusic;
window.sendEmailInvitation = sendEmailInvitation;
window.testEmailConfig = testEmailConfig;
window.copyInvitationLink = copyInvitationLink;
window.connectExistingUser = connectExistingUser;
window.showMediaGallery = showMediaGallery;
window.closeMediaGallery = closeMediaGallery;
window.openMedia = openMedia;
window.sendVirtualHug = sendVirtualHug;
window.toggleEmojiPicker = toggleEmojiPicker;
window.addEmoji = addEmoji;
window.handleFileUpload = handleFileUpload;
window.handleKeyPress = handleKeyPress;
window.showPartnerConnectedNotification = showPartnerConnectedNotification;
window.updatePartnerStatus = updatePartnerStatus;
window.checkForPartnerConnection = checkForPartnerConnection;
