/**
 * SecondSpark — Chat & Messaging Engine
 * Real-time polling, auto-scrolling, and asynchronous message dispatch
 */

document.addEventListener('DOMContentLoaded', () => {
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatBox = document.getElementById('chat-messages-box');
  const activeConvId = chatBox ? chatBox.getAttribute('data-conversation-id') : null;

  if (!chatBox || !activeConvId) return;

  // Auto-scroll to bottom of chat
  function scrollToBottom() {
    chatBox.scrollTop = chatBox.scrollHeight;
  }
  scrollToBottom();

  let lastMessageId = parseInt(chatBox.getAttribute('data-last-id') || '0', 10);

  // Send message asynchronously
  if (chatForm && chatInput) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const text = chatInput.value.trim();
      if (!text) return;

      const formData = new FormData();
      formData.append('content', text);

      fetch(`/messages/${activeConvId}/send`, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
      })
        .then(res => res.json())
        .then(data => {
          if (data.success && data.message) {
            appendMessageBubble(data.message, true);
            chatInput.value = '';
            lastMessageId = Math.max(lastMessageId, data.message.id);
            scrollToBottom();
          }
        })
        .catch(err => console.error('Failed to send message', err));
    });
  }

  function appendMessageBubble(msg, isOutgoing) {
    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${isOutgoing ? 'outgoing' : 'incoming'}`;
    bubble.setAttribute('data-id', msg.id);
    bubble.innerHTML = `
      <div class="message-content">${escapeHTML(msg.content)}</div>
      <div class="message-time">${msg.created_at}</div>
    `;
    chatBox.appendChild(bubble);
  }

  function escapeHTML(str) {
    const p = document.createElement('p');
    p.textContent = str;
    return p.innerHTML;
  }

  // Periodic polling for incoming messages every 3 seconds
  function pollIncoming() {
    fetch(`/api/messages/poll?conversation_id=${activeConvId}&last_id=${lastMessageId}`)
      .then(res => res.json())
      .then(data => {
        if (data.messages && data.messages.length > 0) {
          data.messages.forEach(msg => {
            appendMessageBubble(msg, false);
            lastMessageId = Math.max(lastMessageId, msg.id);
          });
          scrollToBottom();
        }
      })
      .catch(() => {});
  }

  const pollInterval = setInterval(pollIncoming, 3000);
  window.addEventListener('beforeunload', () => clearInterval(pollInterval));
});
