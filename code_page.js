const codeEditor = document.getElementById('code-editor');
const lineNumbers = document.querySelector('.line-numbers');
const newFileButton = document.getElementById('new-file-button');
const runButton = document.getElementById('run-button');


document.addEventListener('DOMContentLoaded', () => {
    loadInitialFile();
    updateLineNumbers();
});


// Make the code editor contenteditable
codeEditor.contentEditable = 'true';

// not sure if will detaect deleted rows.
// Function to save the input and the row
function saveInput(event,action) {
    const cursorPosition = getCursorPosition(codeEditor);
    const lines = codeEditor.textContent.split('\n');
    const row = cursorPosition.row
    const currentLine = lines[row];
    
    // Save the input and the row (you can replace this with your saving logic)
    console.log(`Input: ${currentLine} Row: ${cursorPosition.row + 1}`);

    if (!action){
        action = "update"}

    const modificaion = JSON.stringify({currentLine, row, action});
    console.log(`modificaion: ${modificaion}`);
    const filename = document.getElementById('file-name').textContent;

    try {
        const encodedmodficaion = encodeURIComponent(modificaion);
        console.log('encodedmodficaion:', encodedmodficaion);
        const url = `http://127.0.0.1:8000/save?modification=${encodedmodficaion}`;

        const response = fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'filename': filename
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = response.text();
        console.log('Save result:', result);
    } catch (error) {
        console.error('Error saving file:', error);
    }
}

// Function to get the cursor position
function getCursorPosition(element) {
    const selection = window.getSelection();
    const range = selection.getRangeAt(0);
    const preCaretRange = range.cloneRange();
    preCaretRange.selectNodeContents(element);
    preCaretRange.setEnd(range.endContainer, range.endOffset);
    const text = preCaretRange.toString();
    const row = (text.match(/\n/g) || []).length;
    return { row };
}

// Event listener for input changes
codeEditor.addEventListener('input', function(event) {
    updateLineNumbers();
    if(event.data === '\n')
        saveInput(event,'insert');
    saveInput(event);
});


// Add event listeners to update line numbers
//codeEditor.addEventListener('input', updateLineNumbers);
codeEditor.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        requestAnimationFrame(updateLineNumbers);
    }
});

// Add paste event listener
codeEditor.addEventListener('paste', (e) => {
    e.preventDefault();
    const text = e.clipboardData.getData('text/plain');
    const selection = window.getSelection();
    const range = selection.getRangeAt(0);
    range.deleteContents();
    range.insertNode(document.createTextNode(text));
    updateLineNumbers();
});

// Add scroll event listener to synchronize scrolling
codeEditor.addEventListener('scroll', () => {
    lineNumbers.scrollTop = codeEditor.scrollTop;
});

// Add event listeners to buttons
newFileButton.addEventListener('click', () => {
    let newFileName = prompt('Enter file name:', 'untitled.py');

    if (newFileName) {
        // add .py extension if no extension exists
        if (!newFileName.includes('.')) {
            newFileName += '.py';
        }

        const fileNameDisplay = document.getElementById('file-name');
        fileNameDisplay.textContent = newFileName;

        codeEditor.textContent = '';
        updateLineNumbers();
    }
});

document.addEventListener('keydown', function(event) {
    // Check if the user pressed Ctrl + S or Cmd + S
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        saveFile();
    }
});

const resizeHandle = document.getElementById('resize-handle');
const outputContainer = document.querySelector('.output-container');
const editor = document.querySelector('.editor');

let isResizing = false;
let startX;
let startOutputWidth;

resizeHandle.addEventListener('mousedown', (e) => {
    isResizing = true;
    startX = e.pageX;
    startOutputWidth = outputContainer.offsetWidth;
    document.body.classList.add('resizing');
});

document.addEventListener('mousemove', (e) => {
    if (!isResizing) return;

    const moveX = e.pageX - startX;
    const newWidth = startOutputWidth - moveX;

    // Set minimum and maximum widths
    const minWidth = 150;
    const maxWidth = window.innerWidth * 0.8;

    if (newWidth >= minWidth && newWidth <= maxWidth) {
        outputContainer.style.width = `${newWidth}px`;
    }
});

document.addEventListener('mouseup', () => {
    isResizing = false;
    document.body.classList.remove('resizing');
});

// File name editing functionality
const fileNameDisplay = document.getElementById('file-name');
const fileNameInput = document.getElementById('filename-input');

fileNameDisplay.addEventListener('dblclick', () => {
    fileNameDisplay.classList.add('hidden');
    fileNameInput.classList.remove('hidden');
    fileNameInput.value = fileNameDisplay.textContent;
    fileNameInput.focus();
});

fileNameInput.addEventListener('blur', () => {
    let newFileName = fileNameInput.value.trim() || fileNameDisplay.textContent; // Fallback to current name if empty
    loadContent(newFileName)

});

fileNameInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        fileNameInput.blur();
    }
});

runButton.addEventListener('click', async () => {
    //await saveFile();  
    setTimeout(() => {
        runFile();
    }, 100); 
});

function updateLineNumbers() {
    const codeEditor = document.querySelector('#code-editor');
    const lineNumbersContainer = document.querySelector('.line-numbers');
    
    // Get lines, but remove the last line if it's empty
    let lines = codeEditor.textContent.split('\n');
    if (lines[lines.length - 1] === '') {
        lines.pop();
    }

    const lineCount = Math.max(lines.length, 1);
    lineNumbersContainer.innerHTML = '';

    for (let i = 0; i < lineCount; i++) {
        const lineDiv = document.createElement('div');
        lineDiv.textContent = i + 1;
        lineNumbersContainer.appendChild(lineDiv);
    }
}


function makeEditable(element) {
    const currentText = element.textContent;
    
    // create an input element
    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentText;
    input.className = 'file-name-input';
    
    element.parentNode.replaceChild(input, element);
    input.focus();
    
    // Handle when user is done editing
    input.onblur = function() {
        let newFileName = this.value || currentText;
        

        if (!newFileName.includes('.')) {
            newFileName += '.py';  // add .py extension if no extension exists
        }
        
        const newDiv = document.createElement('div');
        newDiv.textContent = newFileName;
        newDiv.className = 'file-name';
        newDiv.id = 'file-name';
        newDiv.ondblclick = function() { makeEditable(this); };
        this.parentNode.replaceChild(newDiv, this);
    };
    input.onkeydown = function(e) {
        if (e.key === 'Enter') {
            this.blur();
        }
    };
}


async function runFile() {
    const filename = document.getElementById('file-name').textContent;
    const outputArea = document.querySelector('.output');
    
    // Check file extension
    if (!filename.toLowerCase().endsWith('.py')) {
        outputArea.textContent = 'Error: Only Python files (.py) can be executed';
        return;
    }
    
    try {
        const response = await fetch(`http://127.0.0.1:8000/run`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'filename': filename
            }
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || `HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        outputArea.textContent = result.output;
        
    } catch (error) {
        outputArea.textContent = `Error: ${error.message}`;
    }
}



// Modify loadInitialContent to store initial content
async function loadContent(filename) {
    
    // Add .py extension if no extension exists
    if (!filename.includes('.')) {
        filename += '.py';
    }

    document.getElementById('file-name').textContent = filename; // Update filename 
    
    try {
        const response = await fetch(`/load`, {
            method: 'GET',
            headers: {
                'filename': filename
            }
        });
        
        const data = await response.json();
        if (data.fullContent) {
            document.getElementById('code-editor').textContent = data.fullContent;
            previousContent = data.fullContent; // Store initial content
        }
        updateLineNumbers();
    } catch (error) {
        console.error('Error loading initial content:', error);
    }
}


async function loadInitialFile() {
    let filename = prompt('Enter the file name to load:', 'main.py');
    if (!filename) return;
    await loadContent(filename);

}

async function checkForUpdates(filename) {
    try {
        const response = await fetch(`/check-updates`, {
            method: 'GET',
            headers: {
                'filename': filename
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.hasUpdates) {
            await loadContent(filename); // Reload content if there are updates
        }
    } catch (error) {
        console.error('Error checking for updates:', error);
    }
}