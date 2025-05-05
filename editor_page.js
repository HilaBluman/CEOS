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
                        // Keywords & Core Syntax
                        { label: 'def', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'def ${1:function_name}(${2:params}):\n\t$0', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: 'class', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'class ${1:ClassName}:\n\tdef __init__(self, $2):\n\t\t$0', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: 'return', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'return $1', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: 'try', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'try:\n\t$1\nexcept ${2:Exception} as ${3:e}:\n\t$0', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: 'except', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'except ${1:Exception} as ${2:e}:\n\t$0', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: 'raise', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'raise ${1:Exception}($2)', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: 'with', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'with ${1:expression} as ${2:var}:\n\t$0', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: 'if', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'if ${1:condition}:\n\t$0', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: 'else', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'else:\n\t$0', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: 'elif', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'elif ${1:condition}:\n\t$0', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: 'for', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'for ${1:item} in ${2:iterable}:\n\t$0', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: 'while', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'while ${1:condition}:\n\t$0', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: 'import', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'import ${1:module}', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: 'from', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'from ${1:module} import ${2:object}', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: 'and', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'and' },
                        { label: 'or', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'or' },
                        { label: 'not', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'not' },
                        { label: 'in', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'in' },
                        { label: 'as', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'as' },
                        { label: 'True', kind: monaco.languages.CompletionItemKind.Constant, insertText: 'True' },
                        { label: 'False', kind: monaco.languages.CompletionItemKind.Constant, insertText: 'False' },
                        { label: 'self', kind: monaco.languages.CompletionItemKind.Variable, insertText: 'self' },
                        { label: '__init__', kind: monaco.languages.CompletionItemKind.Function, insertText: 'def __init__(self, $1):\n\t$0', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: 'finally', kind: monaco.languages.CompletionItemKind.Keyword, insertText: 'finally:\n\t$0', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: "''' '''", kind: monaco.languages.CompletionItemKind.Snippet, insertText: "'''\n$1\n'''", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, documentation: "Multi-line string / comment" },
            
                        // Exceptions
                        { label: 'Exception', kind: monaco.languages.CompletionItemKind.Class, insertText: 'Exception' },
                        { label: 'FileNotFoundError', kind: monaco.languages.CompletionItemKind.Class, insertText: 'FileNotFoundError' },
                        { label: 'ValueError', kind: monaco.languages.CompletionItemKind.Class, insertText: 'ValueError' },
                        { label: 'BrokenPipeError', kind: monaco.languages.CompletionItemKind.Class, insertText: 'BrokenPipeError' },
            
                        // Networking & Threads
                        { label: 'socket', kind: monaco.languages.CompletionItemKind.Module, insertText: 'socket.socket(${1:AF_INET}, ${2:SOCK_STREAM})', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: 'bind', kind: monaco.languages.CompletionItemKind.Method, insertText: 'bind(($1, $2))', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
                        { label: 'listen', kind: monaco.languages.CompletionItemKind.Method, insertText: 'listen(${1:backlog})' },
                        { label: 'accept', kind: monaco.languages.CompletionItemKind.Method, insertText: 'accept()' },
                        { label: 'recv', kind: monaco.languages.CompletionItemKind.Method, insertText: 'recv(${1:bufsize})' },
                        { label: 'decode', kind: monaco.languages.CompletionItemKind.Method, insertText: 'decode(${1:utf-8})' },
                        { label: 'encode', kind: monaco.languages.CompletionItemKind.Method, insertText: 'encode(${1:utf-8})' },
                        { label: 'timeout', kind: monaco.languages.CompletionItemKind.Method, insertText: 'settimeout(${1:seconds})' },
                        { label: 'threading', kind: monaco.languages.CompletionItemKind.Module, insertText: 'import threading' },
                        { label: 'Thread', kind: monaco.languages.CompletionItemKind.Class, insertText: 'threading.Thread(target=${1:func}, args=(${2:args},))' },
                        { label: 'start', kind: monaco.languages.CompletionItemKind.Method, insertText: 'start()' },
            
                        // HTTP-style
                        { label: 'get', kind: monaco.languages.CompletionItemKind.Method, insertText: 'get($1)' },
            
                        // math module
                        ...['ceil','floor','sqrt','log','log10','exp','pow','fabs','factorial','sin','cos','tan','degrees','radians','pi','e'].map(fn => ({
                            label: `math.${fn}`, kind: monaco.languages.CompletionItemKind.Function, insertText: `math.${fn}($1)`, insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        })),
            
                        // re module
                        ...['search','match','findall','sub','split','compile'].map(fn => ({
                            label: `re.${fn}`, kind: monaco.languages.CompletionItemKind.Function, insertText: `re.${fn}($1)`, insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        })),
            
                        // threading module
                        ...['Thread','Lock','Event','Timer','current_thread','enumerate'].map(fn => ({
                            label: `threading.${fn}`, kind: monaco.languages.CompletionItemKind.Function, insertText: `threading.${fn}($1)`, insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        })),
            
                        // os module
                        ...['getcwd','listdir','mkdir','remove','rename','rmdir','system','path','walk','environ'].map(fn => ({
                            label: `os.${fn}`, kind: monaco.languages.CompletionItemKind.Function, insertText: `os.${fn}($1)`, insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        })),
            
                        // json module
                        ...['load','loads','dump','dumps'].map(fn => ({
                            label: `json.${fn}`, kind: monaco.languages.CompletionItemKind.Function, insertText: `json.${fn}($1)`, insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        })),
            
                        // random module
                        ...['random','randint','choice','shuffle','uniform','seed'].map(fn => ({
                            label: `random.${fn}`, kind: monaco.languages.CompletionItemKind.Function, insertText: `random.${fn}($1)`, insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        })),
                        
                        // --- Requests ---
                        ...['get','post','put','delete','head','patch','options','request','Session'].map(fn => ({
                            label: `requests.${fn}`, kind: monaco.languages.CompletionItemKind.Function, insertText: `requests.${fn}($1)`, insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        })),

                        // --- Scrapy (Scrap) ---
                        ...['Spider','Request','Selector','Field','Item','CrawlSpider','Rule'].map(fn => ({
                            label: `scrapy.${fn}`, kind: monaco.languages.CompletionItemKind.Class, insertText: `scrapy.${fn}`, insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        })),

                        // --- Pillow (PIL) ---
                        ...['Image','ImageDraw','ImageFont','ImageFilter','ImageOps'].map(fn => ({
                            label: `PIL.${fn}`, kind: monaco.languages.CompletionItemKind.Class, insertText: `PIL.${fn}`, insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        })),

                        // --- Flask ---
                        ...['Flask','render_template','request','redirect','url_for','session','abort','jsonify'].map(fn => ({
                            label: `flask.${fn}`, kind: monaco.languages.CompletionItemKind.Function, insertText: `flask.${fn}($1)`, insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        })),

                        // --- Pygame ---
                        ...['init','display','Surface','image','event','key','mixer','time','quit'].map(fn => ({
                            label: `pygame.${fn}`, kind: monaco.languages.CompletionItemKind.Function, insertText: `pygame.${fn}($1)`, insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        })),

                        // --- sqlite3 ---
                        ...['connect','Cursor','execute','executemany','fetchall','commit','close'].map(fn => ({
                            label: `sqlite3.${fn}`, kind: monaco.languages.CompletionItemKind.Function, insertText: `sqlite3.${fn}($1)`, insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        }))
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
let isEnter = false;
let isPaste = false;
let Pasting = false;
let isHighlighted = false;
let Loadeing = false;
let isDelete = false;
let highlightedTxt = {start: -1, end: -1, selectedText: ""}
let pollingInterval;

let fileID = 0;     // changes after pciking a file
let userID = 0;
let username = "";
let lastModID = -1; 

// Add these variables at the top of the file with other global variables
let startWidth;
let rightPanel;
let mainSection;



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

// Functisonality Constants
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

async function handlePaste(event) {
    isPaste = true;    
    const pastedData = (event.clipboardData || window.clipboardData).getData('text');
    let linesArray = pastedData.split('\n');

    const lastLineNumber = codeEditor.getSelection().startLineNumber;
    const lastLineContent = codeEditor.getModel().getLineContent(lastLineNumber)
    const firstLineNumber = lastLineNumber - linesArray.length + 1;
    //hendle pasting in line no matter what
    linesArray.shift();
    linesArray[linesArray.length - 1] = lastLineContent;
    const startLineNumber = codeEditor.getSelection().startLineNumber;
    // Log the line number where the paste occurred
    console.log("Pasted at line number:", startLineNumber);
    const contentPaste = linesArray.join("\n");
    await sendModifiction(contentPaste, firstLineNumber, "insert", 0)
    console.log('Pasted data:', linesArray);
    isPaste = false;
};

function recognizEnterKey(event) {
    if (event.key === 'Enter') {
        console.log('Enter key pressed!');
        isEnter = true; 
    }
}

document.addEventListener('paste', handlePaste)
document.addEventListener('keydown', recognizEnterKey);

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
        else if (Loadeing) {
            Loadeing = false;
            return;
        }
       else if (isPaste){
            return;
        }
        // Close file details
        else{
        document.getElementById('file-details').classList.remove('slide-in');

            for (const change of event.changes) {
                const startLineNumber = change.range.startLineNumber; // Starting line number of the change
                const endLineNumber = change.range.endLineNumber;     // Ending line number of the change
                const changedText = change.text;                      // The new text that was inserted or replaced
                //const isPaste = changedText.includes('\n');          // Check if the change is a paste operation
                const isDelete = changedText === '';                 // Check if the change is a delete operation

                // Get the current content of the editor
                const fullContent = editor.getValue();
                const lines = fullContent.split('\n');

                // Determine the action based on the type of change
                let action  = "update";
                
                if (isEnter){
                    console.log("line enter: " + lines[startLineNumber])
                    if (lines[startLineNumber] === ""){
                        console.log("newline")
                        await sendModifiction("",startLineNumber, "insert", lines.length);
                    }
                    else{
                        await sendModifiction(lines[startLineNumber] ,startLineNumber, "insert", lines.length);
                        await sendModifiction(lines[startLineNumber - 1], startLineNumber - 1, "update", lines.length);
                    }
                    isEnter = false;
                }

                else if (isDelete) {
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
        }
    });
});

async function sendModifiction (content, row, action, lineLength) {
    const modification = JSON.stringify({
        content: content,          // The content of the first line of the change
        row: row,   // Convert to 0-based index
        action: action,             // Action type (update)
        lineLength: lineLength   // Total number of lines in the editor
    });
    await saveInput(modification);
}

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


async function onDocumentKeySave(event) {
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        Loadeing = true;
        await saveAll();
    }
}

// Core Functions
async function saveAll() {
    const code = codeEditor.getValue();
    const modification = JSON.stringify({ content: code, row: 1, action: 'saveAll', lineLength: code.split("\n").length });
    await saveInput(modification)
    Pasting = false;
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
            Loadeing = true;
            lastModID = data.lastModID;
            console.log("lastModID: " + lastModID);
            codeEditor.setValue(data.fullContent);
        }
        startPolling();
    } catch (error) {
        console.error('Error loading initial content:', error);
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
                // Close file detail if open
                document.getElementById('file-details').classList.remove('slide-in');
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


async function createNewFile(filename) {
    if (!hasValidExtension(filename)) {
            filename = filename.replace(/\..*$/, '.txt');
    }  //fix extenstion ending
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

            // Set the current file ID
            if (data.fileId !== 0) {
                fileID = data.fileId;
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

            // Close the file popup if it's open
            closeFilePopup();

            // Load the new file content
            await loadContent(data.fileId);

        } catch (error) {
            console.error('Error creating new file:', error);
            alert('Failed to create new file. Please try again.');
        }
}

async function uploadNewFile(fileContent, filename) {
    try {
        const response = await fetch('/upload-file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'filename': filename,
                'userId': userID
            },
            body: JSON.stringify({
                content: fileContent
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('File uploaded successfully:', result);

        const fileTree = document.querySelector('.file-tree');
        const newFileItem = document.createElement('li');
        newFileItem.innerHTML = `📄 ${filename}`;
        newFileItem.setAttribute('data-file-id', result.fileId);
        fileTree.appendChild(newFileItem);

        selectFile(result.fileId, filename);
        await loadContent(result.fileId);
    } catch (error) {
        console.error('Error uploading file:', error);
        throw error;
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
    } else if (action === "insert" || action === "paste") {
        // For insert action, we need to create a range that represents a new line
        // saves the spaces is there is.
        if(content.replace(/ /g, "") === "" && content !== "\n"){
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
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data == "No updates") {
            return;
        }
        else if (Array.isArray(data) && data.length > 0) {
            console.log('Received updates:', data);
            // Process all updates in order
            for (const update of data) {
                if(update.ModID > lastModID)
                {
                console.log("Applying update with ModID:", update.ModID);
                lastModID = update.ModID;
                await applyUpdate(update.modification);
                }
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
    } finally {
        // Schedule next poll only after current one completes
        if (pollingInterval) {
            setTimeout(pollForUpdates, 200);
        }
    }
}

function startPolling() {
    // Start the first poll immediately
    pollingInterval = true;
    pollForUpdates();
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

function newFile(event) {
    const popup = document.getElementById('mini-popup');
    const btn = event.currentTarget;
    const rect = btn.getBoundingClientRect();

    popup.style.top = `${rect.top + (rect.height / 2)}px`;
    popup.style.left = `${rect.left + window.scrollX - 130 }px`;
    popup.style.display = 'block';
}

function promptNewFile() {
    const filename = prompt("Enter new file name:");
    if (filename) createNewFile(filename);
    closeMiniPopup();
}

function promptUploadFile() {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '*/*';
    fileInput.style.display = 'none';

    fileInput.onchange = async () => {
        try {
            const file = fileInput.files[0];
            if (!file) {
                console.log('No file selected');
                return;
            }
            
            const filename = file.name;
            console.log('Selected file:', filename);
            
            const content = await file.text();
            console.log('File content loaded, size:', content.length);
            
            await uploadNewFile(content, filename);
            
            console.log('File upload completed:', filename);
        } catch (error) {
            console.error('Error during file upload:', error);
            alert('Error uploading file: ' + error.message);
        } finally {
            // Clean up the file input
            document.body.removeChild(fileInput);
        }
    };

    document.body.appendChild(fileInput);
    fileInput.click();
    closeMiniPopup();
}

function closeMiniPopup() {
    document.getElementById('mini-popup').style.display = 'none';
}

document.addEventListener('click', (e) => {
    const popup = document.getElementById('mini-popup');
    const plusBtn = document.querySelector('button[onclick^="newFile"]');
    
    const clickedInsidePopup = popup.contains(e.target);
    const clickedOnButton = plusBtn.contains(e.target);

    if (!clickedInsidePopup && !clickedOnButton) {
        popup.style.display = 'none';
    }
});


function popFileInfo() {
    if (!fileID || !selectedFileName) {
        alert('Please select a file first');
        return;
    }

    // Open the side panel
    const sidePanel = document.getElementById('file-details');
    sidePanel.classList.add('open');

    // Set the filename
    document.getElementById('filename').textContent = selectedFileName;

    // Load file details
    loadFileDetails();
}

async function loadFileDetails() {
    try {
        // Fetch file details from server
        const response = await fetch('/get-file-details', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'fileID': fileID
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Details data :", JSON.stringify(data));

        // Update the filename
        document.getElementById('filename').textContent = data.filename;

        if (Array.isArray(data.users)) {
            // Clear existing table content
            const userList = document.getElementById('user-list');
            userList.innerHTML = '';
            
            // Populate the table
            data.users.forEach((user) => {             
                // Create table row
                const row = document.createElement('tr');
                
                // Create username cell
                const usernameCell = document.createElement('td');
                usernameCell.textContent = user.username;
                
                // Create role cell
                const roleCell = document.createElement('td');
                roleCell.textContent = user.role || 'user'; // Default to 'user' if role is not specified
                
                // Append cells to row
                row.appendChild(usernameCell);
                row.appendChild(roleCell);
                
                // Append row to table
                userList.appendChild(row);
            });
        }
        // Slide in the details window
        document.getElementById('file-details').classList.add('slide-in');

        // Add event listener for closing the panel
        document.getElementById('close-panel-btn').onclick = () => {
            document.getElementById('file-details').classList.remove('slide-in');
        };

    } catch (error) {
        console.error('Error loading file details:', error);
        alert('Error loading file details');
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

function hasValidExtension(filename) {
    if (!filename) return false;
    const validExtensions = [
        '.py', '.js', '.ts', '.html', '.css', '.json', '.java', '.c', '.cpp', '.cs', '.go', '.php', '.r', '.rb', '.sh', '.sql', '.xml', '.yaml', '.md', '.swift', '.dockerfile', '.ini', '.plaintext', '.bat', '.powershell'
    ];
    const extension = filename.substring(filename.lastIndexOf('.'));
    return validExtensions.includes(extension.toLowerCase());
}



