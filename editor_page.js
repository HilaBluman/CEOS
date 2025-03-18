let codeEditor;
let isEditorReady = false; // Global flag to track editor readiness

require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.36.1/min/vs' }});
async function initializeEditor() {
    await new Promise((resolve) => {
        require(['vs/editor/editor.main'], function() {
            codeEditor = monaco.editor.create(document.getElementById('editor-container'), {
                value: "",
                language: 'javascript',
                theme: 'vs-dark',
                automaticLayout: true
            });

            // Set the flag to true when the editor is ready
            isEditorReady = true;

            // Register completion provider
            monaco.languages.registerCompletionItemProvider('javascript', {
                provideCompletionItems: () => {
                    return {
                        suggestions: [
                            {
                                label: 'console',
                                kind: monaco.languages.CompletionItemKind.Function,
                                insertText: 'console.',
                                detail: 'Console object',
                            },
                            {
                                label: 'log',
                                kind: monaco.languages.CompletionItemKind.Method,
                                insertText: 'log',
                                detail: 'Log to console',
                            },
                            // Add more suggestions as needed
                        ]
                    };
                }
            });

            // Optionally, trigger a custom event
            const event = new Event('editorReady');
            window.dispatchEvent(event);
            resolve(); // Resolve the promise when the editor is ready
        });
    });
}


// Function to use codeEditor safely
function useCodeEditor(callback) {
    if (isEditorReady) {
        callback(codeEditor);
    } else {
        // Wait for the editor to be ready
        window.addEventListener('editorReady', () => {
            callback(codeEditor);
        });
    }
}


// Flags and Variables
let isResizing = false;
let startX;
let startOutputWidth;
let previousContent = '';
let timeoutId;
let isPasting = false;
let isHighlighted = false;
let isLoaded = false;
let highlightedTxt = {start: -1, end: -1, selectedText: ""}

let user = {       // temporary           
    id: 'user123', 
    name: 'John Doe'
};

// Functionality Constants
const DEBOUNCE_DELAY = 500; // ms
const MIN_WIDTH = 80;
const MAX_WIDTH = window.innerWidth * 0.8;
document.addEventListener('DOMContentLoaded', async () => {
    console.log("works")
    await loadInitialFile();
});

document.addEventListener('mousemove', onDocumentMouseMove);
document.addEventListener('mouseup', onDocumentMouseUp);    
document.addEventListener('keydown', onDocumentKeySave);
document.addEventListener('selectionchange', isTextHighlighted);
window.addEventListener("pagehide", pageHide);



useCodeEditor((editor) => {
    editor.onDidChangeModelContent((event) => {
        if (isLoaded) {
            isLoaded = false;
            return} 
        event.changes.forEach(change => {
            const startLineNumber = change.range.startLineNumber; // Starting line number of the change
            const endLineNumber = change.range.endLineNumber;     // Ending line number of the change
            const changedText = change.text;                     // The new text that was inserted or replaced
            const isPaste = changedText.includes('\n');          // Check if the change is a paste operation
            const isDelete = changedText === '';                 // Check if the change is a delete operation

            // Log the changes for debugging
            console.log(`Content changed from line ${startLineNumber} to ${endLineNumber}:`);
            console.log(`Changed text: ${changedText}`);

            // Get the current content of the editor
            const fullContent = editor.getValue();
            const lines = fullContent.split('\n');

            

            // Determine the action based on the type of change
            let action;
            if (isDelete) {
                action = 'delete'; // Handle deletion
            } else if (isPaste) {
                action = 'insert'; // Handle pasting (inserting multiple lines)
            } else {
                action = 'update'; // Handle regular updates
            }

            if (isDelete) {
                if (isHighlighted){
                    isHighlighted = false;
                    DeleteHighlighted(startLineNumber -1, endLineNumber - 1,lines.length - 1,lines[startLineNumber - 1])
                }
                const modification = JSON.stringify({
                    content: lines[startLineNumber - 1],                      // The content of the first line
                    row: startLineNumber - 1,               // Convert to 0-based index
                    action: 'update',                       // Action type (update)
                    linesLength: lines.length               // Total number of lines in the editor
                });
                saveInput(modification);

            }
            else if (isPaste) {
                // Handle multi-line pasting (same as before)
                const modifiedLines = changedText.split('\n'); // Get the pasted lines

                // Check if the paste starts in the middle of a line
                const isFirstLineUpdate = change.range.startColumn > 1;
                // Check if the paste ends in the middle of a line
                const isLastLineUpdate = change.range.endColumn < lines[endLineNumber - 1].length + 1;
                const lines2 = editor.getValue().split('\n');

                // Process the first line
                if (isFirstLineUpdate) {
                    // If the paste starts in the middle of a line, update the existing line
                    const modification = JSON.stringify({
                        content: lines2[startLineNumber - 1],          // First line of the pasted content
                        row: startLineNumber - 1,                       // Convert to 0-based index
                        action: 'update',                                // Update the existing line
                        linesLength: lines.length                        // Total number of lines in the editor
                    });
                    // Log the modification for debugging
                    console.log('First Line Modification:', modification);

                    // Call saveInput with the modification
                    saveInput(modification);
                } else {
                    // If the paste starts at the beginning of a line, treat it as an insert
                    const modification = JSON.stringify({
                        content: modifiedLines[0],                     // First line of the pasted content
                        row: startLineNumber,                           // Convert to 0-based index
                        action: 'insert',                               // Insert new line
                        linesLength: lines.length                       // Total number of lines in the editor
                    });
                    // Log the modification for debugging
                    console.log('Insert First Line Modification:', modification);

                    // Call saveInput with the modification
                    saveInput(modification);
                }

                // Remove the first line from modifiedLines since it's already processed
                modifiedLines.shift();

                // Process the middle lines (if any)
                modifiedLines.slice(0, -1).forEach((line, index) => {
                    const modification = JSON.stringify({
                        content: line,                       // The content of the line
                        row: startLineNumber + index,        // Convert to 0-based index
                        action: 'insert',                   // Insert new lines
                        linesLength: lines.length           // Total number of lines in the editor
                    });

                    // Log the modification for debugging
                    console.log('Middle Line Modification:', modification);

                    // Call saveInput with the modification
                    saveInput(modification);
                });

                // Process the last line
                if (isLastLineUpdate && modifiedLines.length > 0) {
                    console.log("lasts paste content: " + modifiedLines[modifiedLines.length - 1])
                    const modification = JSON.stringify({
                        content: lines[endLineNumber], // Last line of the pasted content
                        row: startLineNumber + modifiedLines.length - 1,  // Convert to 0-based index
                        action: 'insert',                                 // Update the existing line
                        linesLength: lines.length                         // Total number of lines in the editor
                    });

                    // Log the modification for debugging
                    console.log('Last Line Modification:', modification);

                    // Call saveInput with the modification
                    saveInput(modification);
                } else if (modifiedLines.length > 0) {
                    // Insert the last line as a new line
                    const modification = JSON.stringify({
                        content: modifiedLines[modifiedLines.length - 1], // Last line of the pasted content
                        row: startLineNumber + modifiedLines.length - 1,  // Convert to 0-based index
                        action: 'insert',                                 // Insert a new line
                        linesLength: lines.length                         // Total number of lines in the editor
                    });

                    // Log the modification for debugging
                    console.log('Last Line Modification:', modification);

                        // Call saveInput with the modification
                        saveInput(modification);
                    }
                }
            else{
                // Handle single-line updates
                const firstline = lines[startLineNumber - 1]; // Lines are 1-indexed in Monaco
                // Create the modification object
                const modification = JSON.stringify({
                    content: firstline,          // The content of the first line of the change
                    row: startLineNumber - 1,   // Convert to 0-based index
                    action: action,             // Action type (update)
                    linesLength: lines.length   // Total number of lines in the editor
                });

                // Log the modification for debugging
                console.log('Modification:', modification);

                // Call saveInput with the modification
                saveInput(modification);
            }
        });
    })
});

document.getElementById('username-display').textContent = get_username();
document.getElementById('username-avater').textContent = get_username().charAt(0).toUpperCase();

function get_username(){
    console.log(sessionStorage.getItem('username'));
    return sessionStorage.getItem('username');}
function get_password(){
    return sessionStorage.getItem('password');}
function get_userID(){
    return sessionStorage.getItem('userId');}

function isTextHighlighted() {
    const selection = codeEditor.getSelection();
    isHighlighted = selection.startLineNumber !== selection.endLineNumber; // Returns true if text is highlighted
}

async function DeleteHighlighted(start, fin, linesLength, firstline ) {  
    console.log("Delete - start: " + start + " fin: " + fin)
    const action = 'delete'
    for(let i = fin; i > start; i--){
        const modification = JSON.stringify({ content: "", row: i, action, linesLength });
        saveInput(modification)   // await saveInput(modification)
    }
    codeEditor.focus();
}
    

// Helper Functions
function pageHide(event){
    console.log("in pageHide")
    if (event.persisted) {
        console.log("Page is being persisted in cache.");
    } else {console.log("Page is being discarded.");}

    fetch('https://127.0.0.1:8000/disconnection', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            userId: userId,
            timestamp: new Date().toISOString()
        })
    });
};

function onKeyZ(event){
    if (event.metaKey && event.key === 'z') {
        console.log("cmd z")
    }
}
/*async function onCodeEditorInput(event) {
    if (isPasting) return;

    const lines = codeEditor.getValue().split('\n');
    const linesLength = lines.length - 1;
    if (isHighlighted){
        console.log("in isHighlighted");
        if (event.key === 'Backspace' || event.keyCode === 8) {
            const firstline = lines[highlightedTxt.start];
            await DeleteHighhlighted(highlightedTxt.start, highlightedTxt.end, linesLength, firstline);
        }
        isHighlighted = false;
    }
    else{               
        const position = codeEditor.getPosition();
        const row = position.lineNumber - 1;
        const content = lines[row]
        const action = "update";
        const modification = JSON.stringify({ content, row, action, linesLength });
        saveInput(modification);
    }
}*/

function onNewFileButtonClick() {
    let newFileName = prompt('Enter file name:', 'untitled.py');

    if (newFileName) {
        if (!newFileName.includes('.')) {
            newFileName += '.py';
        }

        fileNameDisplay.textContent = newFileName;
        codeEditor.setValue('');
    }
}

function onDocumentMouseMove(e) {
    if (!isResizing) return;

    const moveX = e.pageX - startX;
    const newWidth = startOutputWidth - moveX;

    if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
        outputContainer.style.width = `${newWidth}px`;
    }
}

function onDocumentMouseUp() {
    isResizing = false;
    document.body.classList.remove('resizing');
}

async function onDocumentKeySave(event) {
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        isPasting = true;
        await saveAll();
    }
}

// Core Functions
async function saveAll() {
    const code = codeEditor.getValue();
    const modification = JSON.stringify({ content: code, row: 1, action: 'saveAll', linesLength: code.split("\n").length });
    saveInput(modification)
    isPasting = false;
}

/*async function DeleteHighhlighted(start, fin, linesLength, firstline ) {  
    console.log("Delete - start: " + start + " fin: " + fin)
    const action = 'delete'
    for(let i = fin; i > start; i--){
        const modification = JSON.stringify({ content: "in delete", row: i, action, linesLength });
       await saveInput(modification)
    }
    const modification = JSON.stringify({ content: firstline, row: start , action: 'update', linesLength });
    saveInput(modification)
    codeEditor.focus();
}*/

async function saveInput(modification) {
    const filename = document.getElementById('file-name').textContent;
    //console.log("modification: " + modification);

    try {
        const encodedModification = encodeURIComponent(modification);
        const url = `http://127.0.0.1:8000/save?modification=${encodedModification}`;
        
        const response = await fetch(url, {
            method: 'GET',
            headers: { 'filename': filename,
                'Connection': 'keep-alive'}
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.text();
        console.log('Save result:', result);
    } catch (error) {
        console.error('Error saving file:', error);
        return
    }
}

async function runFile() {
    const filename = document.getElementById('file-name').textContent;
    const outputArea = document.querySelector('.output');

    if (!filename.toLowerCase().endsWith('.py')) {
        outputArea.textContent = 'Error: Only Python files (.py) can be executed';
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:8000/run`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'filename': filename,
                'Connection': 'keep-alive' }
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

async function loadContent(filename) {
    if (!filename.includes('.')) filename += '.py';

    // Check if the 'file-name' element exists
    const fileNameElement = document.getElementById('file-name');
    if (fileNameElement) {
        fileNameElement.textContent = filename;
    } else {
        console.error("Element with id 'file-name' not found.");
    }

    try {
        const response = await fetch(`/load`, {
            method: 'GET',
            headers: { 
                'filename': filename,
                'Connection': 'keep-alive'
            }
        });

        const data = await response.json();
        if (data.fullContent) {
            // Set the content in the Monaco editor
            isLoaded = true
            codeEditor.setValue(data.fullContent);
        }
    } catch (error) {
        console.error('Error loading initial content:', error);
    }
}

async function loadInitialFile() {
    await initializeEditor(); // Ensure the editor is initialized before loading content
    let filename = "hila.js"; // Prompt for the file name if needed
    if (filename) await loadContent(filename);
}

/*async function Get_highlightedText(){
    const selection = codeEditor.getSelection();
    const selectedText = codeEditor.getModel().getValueInRange(selection);
    clearTimeout(timeoutId); 
    timeoutId = setTimeout(function() {
        if(selectedText){
            isHighlighted = true;
            highlightedTxt.start = selection.startLineNumber - 1;
            highlightedTxt.end = selection.endLineNumber - 1;
            highlightedTxt.selectedText = selectedText;
        }
        else{
            isHighlighted = false;
            highlightedTxt.start = -1;
            highlightedTxt.end = - 1;
            highlightedTxt.selectedText = "";
        }  
        console.log("highhlighted flag: " + isHighlighted);      
        codeEditor.focus();
    }, 200);
}*/

function newFile() {
    const fileName = prompt("Enter new file name:");
    if (fileName) {
        const fileTree = document.querySelector('.file-tree');
        const newFileItem = document.createElement('li');
        newFileItem.innerHTML = `📄 ${fileName}`;
        fileTree.appendChild(newFileItem);
        codeEditor.setValue('// New file');
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
  };
}
// end