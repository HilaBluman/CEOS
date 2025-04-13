let codeEditor;
let isEditorReady = false; // Global flag to track editor readiness
const host = '192.168.68.54'
const main_url = 'http://'+ host +':8000'

require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.36.1/min/vs' }});
async function initializeEditor() {
    await new Promise((resolve) => {
        require(['vs/editor/editor.main'], async function () {
    
        // ✅ JS compiler setup
        monaco.languages.typescript.javascriptDefaults.setCompilerOptions({
            target: monaco.languages.typescript.ScriptTarget.ES2020,
            allowNonTsExtensions: true,
            checkJs: true,
            noEmit: true,
            strict: true
        });

        // 🧠 Create editor 
        codeEditor = monaco.editor.create(document.getElementById('editor-container'), {
            value: '// Start typing...\n',
            language: 'javascript',
            theme: 'vs-dark',
            automaticLayout: true,
            suggestOnTriggerCharacters: true
        });

            // Add Python completion items
        monaco.languages.registerCompletionItemProvider('python', {
            provideCompletionItems: () => {
            const suggestions = [
                { label: 'print', kind: monaco.languages.CompletionItemKind.Function, insertText: 'print($1)', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                { label: 'len', kind: monaco.languages.CompletionItemKind.Function, insertText: 'len($1)' },
                { label: 'range', kind: monaco.languages.CompletionItemKind.Function, insertText: 'range($1)' },
                { label: 'int', kind: monaco.languages.CompletionItemKind.Function, insertText: 'int($1)' },
                { label: 'str', kind: monaco.languages.CompletionItemKind.Function, insertText: 'str($1)' },
            ];
            return { suggestions };
            }
        });

        isEditorReady = true;

        const event = new Event('editorReady');
        window.dispatchEvent(event);
        resolve();
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
let isApplyingUpdates = false;
let isResizing = false;
let startX;
let startOutputWidth;
let previousContent = '';
let timeoutId;
let isPasting = false;
let isHighlighted = false;
let isLoaded = false;
let isDelete = false;
let highlightedTxt = {start: -1, end: -1, selectedText: ""}
let pollingInterval;

let fileID = 0;     // changes after pciking a file
let userID = 0;
let username = "";
let lastModID = -1; 


// Functionality Constants
const DEBOUNCE_DELAY = 500; // ms
const MIN_WIDTH = 80;
const MAX_WIDTH = window.innerWidth * 0.8;
const languageMap = {
    'py': 'python',
    'js': 'javascript',
    'ts': 'typescript',
    'html': 'html',
    'css': 'css',
    'json': 'json',
    'java': 'java',
    'c': 'c',
    'cpp': 'cpp',
    'cs': 'csharp',
    'go': 'go',
    'php': 'php',
    'r': 'r',
    'rb': 'ruby',
    'sh': 'shell',
    'sql': 'sql',
    'xml': 'xml',
    'yaml': 'yaml',
    'md': 'markdown',
    'swift': 'swift',
    'dockerfile': 'dockerfile',
    'ini': 'ini',
    'plaintext': 'plaintext',
    'bat': 'bat',
    'powershell': 'powershell'
};

document.addEventListener('DOMContentLoaded', async () => {
    await initializeEditor();
    await loadInitialFile();
});

document.addEventListener('mousemove', onDocumentMouseMove);
document.addEventListener('mouseup', onDocumentMouseUp);   
document.addEventListener('keydown', onDocumentKeySave);

document.addEventListener('selectionchange', isTextHighlighted);
window.addEventListener("pagehide", pageHide);



useCodeEditor((editor) => {
    editor.onDidChangeModelContent(async (event) => {
        if (isApplyingUpdates) {
            // Skip the logic if updates are being applied
            return;
        }
        if (isLoaded) {
            isLoaded = false;
            return;
        }
        for (const change of event.changes) {
            const startLineNumber = change.range.startLineNumber; // Starting line number of the change
            const endLineNumber = change.range.endLineNumber;     // Ending line number of the change
            const changedText = change.text;                      // The new text that was inserted or replaced
            const isPaste = changedText.includes('\n');          // Check if the change is a paste operation
            const isDelete = changedText === '';                 // Check if the change is a delete operation

            // Get the current content of the editor
            const fullContent = editor.getValue();
            const lines = fullContent.split('\n');

            // Determine the action based on the type of change
            let action  = "update";

            if (isDelete) {
                if (isHighlighted){
                    isHighlighted = false;
                    DeleteHighlighted(startLineNumber -1, endLineNumber - 1)
                }
                // delete in the same line  
                const content = lines[startLineNumber - 1];
                const modification = JSON.stringify({
                    content: content,                      // The content of the first line
                    row: startLineNumber - 1,               // Convert to 0-based index
                    action: 'delete same line',                       // Action type (update)
                    lineLength: content.length               // Total number of lines in the editor
                });
                saveInput(modification);

            } 
            else if (isPaste) {
                // Log the changes for debugging
                console.log(`Content changed from line ${startLineNumber} to ${endLineNumber}:`);
                console.log(`Changed text: ${changedText}`);
                // Handle multi-line pasting
                await handlePaste(editor, startLineNumber, endLineNumber, changedText, lines, change);
            }
            else{
                // Handle single-line updates
                const firstline = lines[startLineNumber - 1]; // Lines are 1-indexed in Monaco
                // Create the modification object
                const modification = JSON.stringify({
                    content: firstline,          // The content of the first line of the change
                    row: startLineNumber - 1,   // Convert to 0-based index
                    action: action,             // Action type (update)
                    lineLength: firstline.length   // Total number of lines in the editor
                });

                // Log the modification for debugging
                console.log('Modification:', modification);

                // Call saveInput with the modification
                saveInput(modification);
            }
        }
    });
});

document.getElementById('username-display').textContent = get_username();
document.getElementById('username-avater').textContent = get_username().charAt(0).toUpperCase();

function get_username(){
    username = sessionStorage.getItem('username')
    return username;}
function get_password(){
    return sessionStorage.getItem('password');}
function get_userID(){
    userID = sessionStorage.getItem('userId');
    return userID}

function isTextHighlighted() {
    const selection = codeEditor.getSelection();
    isHighlighted = selection.startLineNumber !== selection.endLineNumber; // Returns true if text is highlighted
}

function changeEditorLanguage(extension) {    
    const newLanguage = languageMap[extension.toLowerCase()] || 'plaintext';
    const model = codeEditor.getModel();
    if (model) {
        monaco.editor.setModelLanguage(model, newLanguage);
    }
}

async function DeleteHighlighted(start, fin ) {  
    //console.log("Delete - start: " + start + " fin: " + fin)
    const action = 'delete'
    for(let i = fin; i > start; i--){
        const modification = JSON.stringify({ content: "", row: i, action, lineLength: 0 });
        saveInput(modification)   // await saveInput(modification)
    }
    codeEditor.focus();
}


    

// Helper Functions
function pageHide(event){
    console.log("in pageHide")
    if (event.persisted) {
        console.log("Page is being persisted in cache.");
    } else {
        console.log("Page is being discarded.");
        stopPolling();
    }

    fetch('/disconnection', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            userId: userID,
            timestamp: new Date().toISOString()
        })
    });
}

function onKeyZ(event){
    if (event.metaKey && event.key === 'z') {
        console.log("cmd z")
    }
}

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
    const modification = JSON.stringify({ content: code, row: 1, action: 'saveAll', lineLength: code.split("\n").length });
    saveInput(modification)
    isPasting = false;
}

async function saveInput(modification) {

    try {
        const encodedModification = encodeURIComponent(modification);
        const url = "/save?modification=" + encodedModification;
        const response = await fetch(url, {
            method: 'GET',
            headers: { 'fileID': fileID,
                "userID": userID,
                'Connection': 'keep-alive'}
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.text();
        //console.log('Save result:', result);
        await new Promise(resolve => setTimeout(resolve, 1000));
    } catch (error) {
        console.error('Error saving file:', error);
        return
    }
}

async function loadContent(fileId) {
    try {
        const response = await fetch('/load', {
            method: 'GET',
            headers: { 
                'fileId': fileId,
                'Connection': 'keep-alive'
            }
        });
        const data = await response.json();
        if (data.fullContent) {
            // Set the content in the Monaco editor
            isLoaded = true;
            lastModID = data.lastModID;
            console.log("lastModID: " + lastModID);
            codeEditor.setValue(data.fullContent);
        }
        startPolling();
    } catch (error) {
        console.error('Error loading initial content:', error);
    }
}

async function handlePaste(editor, startLineNumber, endLineNumber, changedText, lines, change) {
    const modifiedLines = changedText.split('\n'); // Get the pasted lines

    // Check if the paste starts in the middle of a line
    const isFirstLineUpdate = change.range.startColumn > 1;
    // Check if the paste ends in the middle of a line
    const isLastLineUpdate = change.range.endColumn < lines[endLineNumber - 1].length + 1;
    const lines2 = editor.getValue().split('\n');

    // Process the first line
    if (isFirstLineUpdate) {
        // If the paste starts in the middle of a line, update the existing line
        const content = lines2[startLineNumber - 1];
        const modification = JSON.stringify({
            content: content,          // First line of the pasted content
            row: startLineNumber - 1,                       // Convert to 0-based index
            action: 'update',                                // Update the existing line
            lineLength: content.length                        // Total number of lines in the editor
        });

        // Call saveInput with the modification
        saveInput(modification);
    } else {
        const content = modifiedLines[0] || '\n';
        // If the paste starts at the beginning of a line, treat it as an insert
        const modification = JSON.stringify({
            content: content,              // First line of the pasted content, or newline if empty
            row: startLineNumber,                           // Convert to 0-based index
            action: 'insert',                               // Insert new line
            lineLength: content.length                       // Total number of lines in the editor
        });

        // Call saveInput with the modification
        saveInput(modification);
    }

    // Remove the first line from modifiedLines since it's already processed
    modifiedLines.shift();

    // Process the middle lines (if any)
    for (const line of modifiedLines.slice(0, -1)) {
        const content = line || '\n';
        const modification = JSON.stringify({
            content: content,                          // The content of the line, or newline if empty
            row: startLineNumber + modifiedLines.indexOf(line), // Convert to 0-based index
            action: 'insert',                               // Insert new lines
            lineLength: content.length                       // Total number of lines in the editor
        });

        // Call saveInput with the modification
        await saveInput(modification);
    }

    // Process the last line
    if (isLastLineUpdate && modifiedLines.length > 0) {
        const content = modifiedLines[modifiedLines.length - 1] || '\n';
        const modification = JSON.stringify({
            content: content, // Last line of the pasted content, or newline if empty
            row: startLineNumber + modifiedLines.length - 1,  // Convert to 0-based index
            action: 'insert',                                 // Update the existing line
            lineLength: content.length                         // Total number of lines in the editor
        });

        // Call saveInput with the modification
        saveInput(modification);
    } else if (modifiedLines.length > 0) {
        // Insert the last line as a new line
        const content = modifiedLines[modifiedLines.length - 1] || '\n';
        const modification = JSON.stringify({
            content: content, // Last line of the pasted content, or newline if empty
            row: startLineNumber + modifiedLines.length - 1,  // Convert to 0-based index
            action: 'insert',                                 // Insert a new line
            lineLength: content.length                         // Total number of lines in the editor
        });

        // Call saveInput with the modification
        saveInput(modification);
    }
}

function closeFilePopup() {
    document.getElementById('file-popup').style.display = 'none'; // Hide the popup
}

let selectedFileId = null;
let selectedFileName = null;

function selectFile(fileId, filename) {
    //save file id 
    fileID = fileId;
    selectedFileId = fileId;
    selectedFileName = filename;
    const tab = document.getElementById('current-file-tab');
    tab.textContent = filename || '';
    
    if (filename) {
        tab.classList.add('active-tab');
        const extension = filename.split('.').pop()
        changeEditorLanguage(extension);
    } 
}


async function GetUserFiles(userId) {
    try {
        //console.log('Fetching files for user ID:', userId); // Debugging line
        const response = await fetch('/get-user-files', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'userId': userId
            }
        });

        if (!response.ok) {
            const errorBody = await response.text(); // Log the response body for debugging
            throw new Error(`HTTP error! status: ${response.status}, body: ${errorBody}`);
        }

        const data = await response.json();
        return {
            fileIds: data.filesId,
            filenames: data.filenames
        }; // Return both fileIds and filenames
    } catch (error) {
        console.error('Error fetching user files:', error);
        return [];
    }
}

async function loadInitialFile() { 
    username = await get_username(); // Ensure this is awaited if it's a promise
    userID = await get_userID(); // Ensure this is awaited if it's a promise

    const filesInfo = await GetUserFiles(userID); // Fetch user files
    //console.log('Fetched files:', filesInfo); // Debugging line

    // Populate both the popup and sidebar file lists
    populateFileLists(filesInfo);

    // Show the popup
    document.getElementById('file-popup').style.display = 'block';
}

function populateFileLists(filesInfo) {
    const fileList = document.getElementById('file-list');
    const fileTree = document.getElementById('file-tree');
    
    // Clear existing file lists
    fileList.innerHTML = '';
    fileTree.innerHTML = '';
    
    // Check if fileIds and filenames are arrays before proceeding
    if (Array.isArray(filesInfo.fileIds) && Array.isArray(filesInfo.filenames)) {
        // Populate both lists
        filesInfo.filenames.forEach((filename, index) => {
            const fileId = filesInfo.fileIds[index];
            
            // Create list item for popup
            const popupListItem = document.createElement('li');
            popupListItem.textContent = filename;
            popupListItem.setAttribute('data-file-id', fileId);
            
            // Create list item for sidebar
            const sidebarListItem = document.createElement('li');
            sidebarListItem.innerHTML = `📄 ${filename}`;
            sidebarListItem.setAttribute('data-file-id', fileId);
            
            // Add click events
            const handleFileClick = async () => {
                // Remove 'selected' class from all items in both lists
                document.querySelectorAll('#file-list li, #file-tree li').forEach(item => 
                    item.classList.remove('selected')
                );
                // Add 'selected' class to clicked items
                popupListItem.classList.add('selected');
                sidebarListItem.classList.add('selected');
                // Call the selectFile function
                selectFile(fileId, filename);
                
                // Load the file content
                await loadContent(fileId);
                // Close the popup if it's open
                closeFilePopup();
            };
            
            popupListItem.onclick = handleFileClick;
            sidebarListItem.onclick = handleFileClick;
            
            // Append items to their respective lists
            fileList.appendChild(popupListItem);
            fileTree.appendChild(sidebarListItem);
        });
    } else {
        console.error('No files found or invalid response:', filesInfo);
    }
}

async function newFile() {
    const filename = prompt("Enter new file name:");
    if (filename) {
        try {
            const response = await fetch('/new-file', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'userId': userID,
                    'filename': filename
                }
            });

            const data = await response.json();

            if (response.status === 409) {
                // File already exists
                alert('A file with this name already exists. Please choose a different name.');
                return;
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            
            // Update the file tree
            const fileTree = document.querySelector('.file-tree');
            const newFileItem = document.createElement('li');
            newFileItem.innerHTML = `📄 ${filename}`;
            newFileItem.setAttribute('data-file-id', data.fileId);
            fileTree.appendChild(newFileItem);

            // Update the editor
            codeEditor.setValue('// New file');
            
            // Update the current file tab
            const currentFileTab = document.getElementById('current-file-tab');
            currentFileTab.textContent = filename;
            currentFileTab.classList.add('active-tab');

            // Set the current file ID
            fileID = data.fileId;

            // Close the file popup if it's open
            closeFilePopup();

        } catch (error) {
            console.error('Error creating new file:', error);
            alert('Failed to create new file. Please try again.');
        }
    }
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

async function runFile() {
    const filename = document.getElementById('file-name').textContent;
    const outputArea = document.querySelector('.output');

    if (!filename.toLowerCase().endsWith('.py')) {
        outputArea.textContent = 'Error: Only Python files (.py) can be executed';
        return;
    }

    try {
        const response = await fetch('/run', {
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

async function applyUpdate(update) {
    try {
        isApplyingUpdates = true;
        const model = codeEditor.getModel();
        if (!model) return;

        let { range, content, decorations} = getRangeAndContent(update);

        // Apply the update using the editor's executeEdits method
        codeEditor.executeEdits('', [{
            range: range,
            text: content
        }]);
        
        // Apply decorations and remove them after a short delay
        const decorationIds = codeEditor.deltaDecorations([], decorations);
        setTimeout(() => {
            codeEditor.deltaDecorations(decorationIds, []);
        }, 500);
        
    } catch (error) {
        console.error('Error applying partial update:', error);
    }
    finally {
        isApplyingUpdates = false; // Reset the flag after applying updates
    }
}

function getRangeAndContent(update) {
    let row = update.row + 1;
    let content = update.content;
    let action = update.action;
    let decorations = [];
    const model = codeEditor.getModel();
    let range;

    //checking if a empty line has been deleted
    if(action == "delete row below"){
       action = "delete";
        row  = row + 1;
    }

    // Handle new line at the end of file
    if (content.startsWith("\n") && action === "update" && row === model.getLineCount()){
        range = new monaco.Range(
            update.row + 1,  // Next line
            1,              // Start at beginning of line
            update.row + 1, // Same line
            1               // End at beginning of line
        );
        content = ""; // Empty content for new line
    } else if (action == "insert") {
        // For insert action, we need to create a range that represents a new line
        // saves the spaces is there is.
        if(content.replace(/ /g, "") === ""){
            content = content + "\n";
        }
       
        range = new monaco.Range(
            row,  // Convert 0-based to 1-based
            1,              // Start at beginning of line
            row,            // Same line
            1               // End at beginning of line (empty line)
        );
    } else if (action == "delete"){
        // For delete action when the whole line is being deleted
        range = new monaco.Range(
            row,  // Convert 0-based to 1-based
            1,              // Start at beginning of line
            row + 1,        // Next line
            1               // Start of next line
        );
        content = "";       // Empty content to remove the line
    } else if (action == "update") {
        // For update action (including deletions within the same row)
        range = new monaco.Range(
            row,  // Convert 0-based to 1-based
            1,              // Start at beginning of line
            row,            // Same line
            model.getLineContent(row).length + 1  // End at end of current line
        );
    } else { //change becuse the action is not the right one
        console.log("action not acceptable.")
    }

    // Add cursor line decoration only for update action
    decorations = [{
        range: new monaco.Range(row, content.length + 1, row, content.length + 1),
        options: {
            className: 'cursor-line',
            isWholeLine: false,
            stickiness: monaco.editor.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges
        }
    }];

    return { range, content, decorations };
}

async function pollForUpdates() {
    if (!fileID || !userID) {
        console.log('Skipping poll - no file or user selected');
        return;
    }

    try {
        const response = await fetch('/poll-updates', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'fileID': fileID,
                'userID': userID,
                'lastModID': lastModID,
                'Connection': 'close'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data == "No updates") {
            //console.log('No updates available');
            return;
        }
        else if (Array.isArray(data) && data.length > 0) {
            // Process all updates in order
            for (const update of data) {
                lastModID = update.ModID;
                console.log("modification: " + JSON.stringify(update.modification));
                await applyUpdate(update.modification);
            }
        }
        else {
            console.log('Invalid update format received:', data);
        }

    } catch (error) {
        if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
            console.log('Connection error during polling - will retry next interval');
        } else {
            console.error('Error polling for updates:', error);
        }
    }
}

function startPolling() {
    // Poll every 0.1 seconds
    pollingInterval = setInterval(pollForUpdates, 100);
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}





async function sendToPollingServer(endpoint, method = 'GET', headers = {}, body = null) {
    try {
        const response = await fetch(polling_url + endpoint, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                ...headers
            },
            body: body ? JSON.stringify(body) : null
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error sending request to polling server:', error);
        throw error;
    }
}

// Example usage:
// To send a request to the polling server:
// const result = await sendToPollingServer('/some-endpoint', 'POST', { 'custom-header': 'value' }, { data: 'some data' });

// end
