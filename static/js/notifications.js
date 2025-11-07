// Notifications and Web Push functionality
class NotificationManager {
  constructor() {
    this.permission = null;
    this.socket = null;
    this.isSubscribed = false;
    this.registration = null;

    this.init();
  }

  async init() {
    // Check if browser supports notifications
    if (!("Notification" in window)) {
      console.log("This browser does not support notifications");
      return;
    }

    // Check current permission
    this.permission = Notification.permission;

    // Initialize service worker for push notifications
    if ("serviceWorker" in navigator && "PushManager" in window) {
      try {
        this.registration = await navigator.serviceWorker.register("/sw.js");
        console.log("Service Worker registered successfully");

        // Check current subscription
        const subscription =
          await this.registration.pushManager.getSubscription();
        this.isSubscribed = !(subscription === null);
      } catch (error) {
        console.error("Service Worker registration failed:", error);
      }
    }

    // Initialize SocketIO for real-time notifications
    this.initSocketIO();

    // Request permission if not already granted
    if (this.permission === "default") {
      this.requestPermission();
    }
  }

  async requestPermission() {
    if (this.permission !== "default") return;

    try {
      const permission = await Notification.requestPermission();
      this.permission = permission;

      if (permission === "granted") {
        this.showNotification("Welcome to LunaLink!", {
          body: "You will now receive notifications for new messages and activities.",
          icon: "/static/images/icons/icon-192x192.png",
        });

        // Subscribe to push notifications
        await this.subscribeToPush();
      }
    } catch (error) {
      console.error("Error requesting notification permission:", error);
    }
  }

  initSocketIO() {
    if (typeof io !== "undefined") {
      this.socket = io();

      // Listen for notification events
      this.socket.on("new_message", (data) => {
        this.handleNewMessage(data);
      });

      this.socket.on("user_online", (data) => {
        this.handleUserOnline(data);
      });

      this.socket.on("user_typing", (data) => {
        this.handleUserTyping(data);
      });

      this.socket.on("virtual_hug", (data) => {
        this.handleVirtualHug(data);
      });

      this.socket.on("mood_update", (data) => {
        this.handleMoodUpdate(data);
      });
    }
  }

  async subscribeToPush() {
    if (!this.registration) return;

    try {
      const subscription = await this.registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(
          "YOUR_VAPID_PUBLIC_KEY"
        ),
      });

      // Send subscription to server
      await fetch("/api/push-subscribe", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(subscription),
      });

      this.isSubscribed = true;
      console.log("Subscribed to push notifications");
    } catch (error) {
      console.error("Failed to subscribe to push notifications:", error);
    }
  }

  async unsubscribeFromPush() {
    if (!this.registration) return;

    try {
      const subscription =
        await this.registration.pushManager.getSubscription();
      if (subscription) {
        await subscription.unsubscribe();

        // Notify server about unsubscription
        await fetch("/api/push-unsubscribe", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ endpoint: subscription.endpoint }),
        });

        this.isSubscribed = false;
        console.log("Unsubscribed from push notifications");
      }
    } catch (error) {
      console.error("Error unsubscribing from push notifications:", error);
    }
  }

  showNotification(title, options = {}) {
    if (this.permission !== "granted") return;

    const defaultOptions = {
      icon: "/static/images/icons/icon-192x192.png",
      badge: "/static/images/icons/badge-72x72.png",
      vibrate: [200, 100, 200],
      requireInteraction: false,
      actions: [
        {
          action: "open",
          title: "Open Chat",
        },
        {
          action: "close",
          title: "Dismiss",
        },
      ],
    };

    const notificationOptions = { ...defaultOptions, ...options };

    const notification = new Notification(title, notificationOptions);

    notification.onclick = function () {
      window.focus();
      notification.close();

      // Navigate to relevant page based on notification
      if (options.data && options.data.url) {
        window.location.href = options.data.url;
      } else {
        window.location.href = "/chat";
      }
    };

    notification.onclose = function () {
      console.log("Notification closed");
    };

    // Auto-close after 5 seconds
    setTimeout(() => {
      notification.close();
    }, 5000);

    return notification;
  }

  handleNewMessage(data) {
    if (document.hidden) {
      this.showNotification(`New message from ${data.sender_name}`, {
        body:
          data.content.length > 100
            ? data.content.substring(0, 100) + "..."
            : data.content,
        icon: `/static/images/avatars/${data.avatar}`,
        data: { url: "/chat" },
        tag: "new-message",
      });

      this.playNotificationSound("message");
    }
  }

  handleUserOnline(data) {
    if (document.hidden) {
      this.showNotification(`${data.user_name} is now online`, {
        body: "Your partner has come online",
        icon: "/static/images/icons/online.png",
        data: { url: "/chat" },
        tag: "user-online",
      });

      this.playNotificationSound("online");
    }
  }

  handleUserTyping(data) {
    // Don't show notification for typing, but you could update UI
    console.log(`${data.user_name} is typing...`);
  }

  handleVirtualHug(data) {
    this.showNotification("Virtual Hug! 💖", {
      body: `${data.from_user_name} sent you a virtual hug!`,
      icon: "/static/images/icons/heart.png",
      data: { url: "/chat" },
      tag: "virtual-hug",
    });

    this.playNotificationSound("hug");
    this.createFloatingHearts(10);
  }

  handleMoodUpdate(data) {
    this.showNotification("Mood Update", {
      body: `${data.user_name} is feeling ${data.mood} ${data.emoji}`,
      icon: "/static/images/icons/mood.png",
      data: { url: "/dashboard" },
      tag: "mood-update",
    });
  }

  playNotificationSound(type = "message") {
    const soundMap = {
      message: "/static/sounds/message.mp3",
      online: "/static/sounds/online.mp3",
      hug: "/static/sounds/hug.mp3",
      general: "/static/sounds/notification.mp3",
    };

    const soundFile = soundMap[type] || soundMap.general;

    try {
      const audio = new Audio(soundFile);
      audio.volume = 0.3;
      audio.play().catch((e) => {
        console.log("Audio play failed:", e);
      });
    } catch (error) {
      console.error("Error playing notification sound:", error);
    }
  }

  createFloatingHearts(count = 5) {
    for (let i = 0; i < count; i++) {
      setTimeout(() => {
        this.createFloatingHeart();
      }, i * 100);
    }
  }

  createFloatingHeart() {
    const heart = document.createElement("div");
    heart.innerHTML = "💖";
    heart.style.position = "fixed";
    heart.style.fontSize = Math.random() * 24 + 16 + "px";
    heart.style.left = Math.random() * 100 + "vw";
    heart.style.top = "100vh";
    heart.style.zIndex = "10000";
    heart.style.pointerEvents = "none";
    heart.style.animation = `floatUp ${
      Math.random() * 3 + 2
    }s ease-in forwards`;
    heart.style.opacity = "0.8";

    document.body.appendChild(heart);

    setTimeout(() => {
      if (heart.parentElement) {
        heart.remove();
      }
    }, 5000);
  }

  // Utility function for VAPID key conversion
  urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding)
      .replace(/\-/g, "+")
      .replace(/_/g, "/");

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  // Custom notification methods
  showCustomNotification(type, data) {
    const notificationTemplates = {
      anniversary: {
        title: "Anniversary Reminder! 🎉",
        body: `Today is your ${data.title}!`,
        icon: "/static/images/icons/anniversary.png",
      },
      streak: {
        title: "Chat Streak! 🔥",
        body: `You've maintained your ${data.days}-day chat streak!`,
        icon: "/static/images/icons/streak.png",
      },
      memory: {
        title: "Memory Alert! 📸",
        body: `On this day ${data.years} years ago...`,
        icon: "/static/images/icons/memory.png",
      },
    };

    const template = notificationTemplates[type];
    if (template) {
      this.showNotification(template.title, {
        body: template.body,
        icon: template.icon,
        data: { url: "/dashboard" },
      });
    }
  }

  // Notification settings
  updateSettings(settings) {
    if (settings.soundsEnabled === false) {
      // Disable sound notifications
      this.playNotificationSound = () => {}; // No-op function
    }

    if (settings.notificationsEnabled === false) {
      // Disable all notifications
      this.showNotification = () => {}; // No-op function
    }
  }
}

// Initialize notification manager
let notificationManager;

document.addEventListener("DOMContentLoaded", function () {
  notificationManager = new NotificationManager();

  // Add CSS for floating animation if not already present
  if (!document.querySelector("#notification-styles")) {
    const style = document.createElement("style");
    style.id = "notification-styles";
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
        `;
    document.head.appendChild(style);
  }
});

// Export for global access
window.NotificationManager = NotificationManager;
window.notificationManager = notificationManager;

// Service Worker for Push Notifications (sw.js)
// This would be a separate file, but here's the content:
const CACHE_NAME = "lunalink-v1";
const urlsToCache = [
  "/",
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/images/icons/icon-192x192.png",
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(urlsToCache);
    })
  );
});

self.addEventListener("fetch", function (event) {
  event.respondWith(
    caches.match(event.request).then(function (response) {
      if (response) {
        return response;
      }
      return fetch(event.request);
    })
  );
});

self.addEventListener("push", function (event) {
  let data = {};
  if (event.data) {
    data = event.data.json();
  }

  const options = {
    body: data.body || "New notification from LunaLink",
    icon: data.icon || "/static/images/icons/icon-192x192.png",
    badge: "/static/images/icons/badge-72x72.png",
    vibrate: [200, 100, 200],
    data: data.data || { url: "/" },
    actions: [
      {
        action: "open",
        title: "Open App",
      },
      {
        action: "close",
        title: "Dismiss",
      },
    ],
  };

  event.waitUntil(
    self.registration.showNotification(data.title || "LunaLink", options)
  );
});

self.addEventListener("notificationclick", function (event) {
  event.notification.close();

  if (event.action === "open") {
    event.waitUntil(
      clients.matchAll({ type: "window" }).then((windowClients) => {
        for (let client of windowClients) {
          if (client.url === "/" && "focus" in client) {
            return client.focus();
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(event.notification.data.url || "/");
        }
      })
    );
  }
});
