(function(){
  // admin_chat.js: connect to the order websocket and append messages to #admin-chat-log
  document.addEventListener('DOMContentLoaded', function() {
    const chatLog = document.getElementById('admin-chat-log');
    if (!chatLog) return;
    const orderId = chatLog.getAttribute('data-order-id');
    if (!orderId) return;

    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const chatSocket = new WebSocket(`${wsScheme}://${window.location.host}/ws/orders/${orderId}/`);

    chatSocket.onmessage = function(e) {
      let data;
      try { data = JSON.parse(e.data); } catch (err) { return; }
      const p = document.createElement('p');
      const strong = document.createElement('strong');
      strong.textContent = data.sender + ':';
      const textNode = document.createTextNode(' ' + data.message + ' ');
      const small = document.createElement('small');
      small.className = 'text-muted';
      small.textContent = data.created_at;
      p.appendChild(strong);
      p.appendChild(textNode);
      p.appendChild(small);
      chatLog.appendChild(p);
      chatLog.scrollTop = chatLog.scrollHeight;
    };

    chatSocket.onopen = function() { /* optional visual state */ };
    chatSocket.onclose = function() { console.warn('Admin chat socket closed'); };
    chatSocket.onerror = function(e) { console.error('Admin chat socket error', e); };
  });
})();