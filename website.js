require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.36.1/min/vs' }});
      require(['vs/editor/editor.main'], function() {
        window.editor = monaco.editor.create(document.getElementById('editor-container'), {
          value: '// Welcome to the code editor\n\nfunction greeting() {\n    console.log("Hello, Developer!");\n}\n\ngreeting();',
          language: 'javascript',
          theme: 'vs-dark',
          automaticLayout: true
        });
      });

// Rest of your code remains the same...

/*function runCode() {
    const code = window.editor.getValue();
    try {
        const output = eval(code);
        document.querySelector('.output-section .output').innerHTML = `<div class="output-title">Output Console</div>${output !== undefined ? output : '// Code executed successfully'}`;
        document.querySelector('.output-section').classList.add('visible');
    } catch (error) {
        document.querySelector('.output-section .output').innerHTML = `<div class="output-title">Output Console</div>Error: ${error.message}`;
        document.querySelector('.output-section').classList.add('visible');
    }
}*/

function newFile() {
    const fileName = prompt("Enter new file name:");
    if (fileName) {
        const fileTree = document.querySelector('.file-tree');
        const newFileItem = document.createElement('li');
        newFileItem.innerHTML = `📄 ${fileName}`;
        fileTree.appendChild(newFileItem);
        window.editor.setValue('// New file');
    }
}

function toggleChat() {
    const chatSection = document.querySelector('.chat-section');
    chatSection.classList.toggle('visible');
}

function toggleOutput() {
    const outputSection = document.querySelector('.output-section');
    outputSection.classList.toggle('visible');
}

function toggleMenu() {
  document.getElementById("menuDropdown").classList.toggle("show");
}

window.onclick = function(event) {
  if (!event.target.matches('.menu-icon')) {
    var dropdowns = document.getElementsByClassName("dropdown-content");
    for (var i = 0; i < dropdowns.length; i++) {
      var openDropdown = dropdowns[i];
      if (openDropdown.classList.contains('show')) {
        openDropdown.classList.remove('show');
      }
    }
  }
}

/*let userCount = 2;
setInterval(() => {
    const users = ['John', 'Sarah', 'Mike', 'Emma'];
    if (Math.random() > 0.7) {
        const user = users[Math.floor(Math.random() * users.length)];
        const messages = [
            'Updated the function parameters',
            'Fixed a bug in the main loop',
            'Added new test cases',
            'Optimized the algorithm'
        ];
        const message = messages[Math.floor(Math.random() * messages.length)];
        
        const chatMessages = document.querySelector('.chat-messages');
        const newMessage = document.createElement('div');
        newMessage.className = 'message';
        newMessage.innerHTML = `<strong>${user}:</strong> ${message}`;
        chatMessages.appendChild(newMessage);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } // );? it does not load the last 3 chars dont know whys
}, 5000);*/
//