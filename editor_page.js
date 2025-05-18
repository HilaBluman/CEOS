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
        codeEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyZ, () => {
            undoTriggered = true;
            console.log('Undo shortcut pressed (Ctrl+Z or Cmd+Z)');
            codeEditor.trigger('keyboard', 'undo', null);
        });
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


let undoTriggered = false;


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



function recognizEnterKey(event) {
    if (event.key === 'Enter') {
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
                const isDelete = changedText === '';                 // Check if the change is a delete operation

                // Get the current content of the editor
                const fullContent = editor.getValue();
                let lines = fullContent.split('\n');

                // Determine the action based on the type of change
                let action  = "update";

                if (undoTriggered){
                    console.log("changes: " + changedText);
                    onKeyZ(change, lines);
                }
                else if (isHighlighted){
                    isHighlighted = false;
                    sendModifiction(endLineNumber, startLineNumber , "delete highlighted", 0 );
                    sendModifiction(lines[startLineNumber - 1] , startLineNumber - 1, "update", 0);
                    console.log("end of highlighted")
                }
                else if (isEnter){
                    isEnter = false;
                    if (lines[startLineNumber] === ""){
                        sendModifiction("",startLineNumber, "insert", lines.length);
                    }
                    else{
                        sendModifiction(lines[startLineNumber] ,startLineNumber, "insert", lines.length);
                        sendModifiction(lines[startLineNumber - 1], startLineNumber - 1, "update", lines.length);
                    }
                }

                else if (isDelete) {
                        // delete in the same line 
                        // Check if the delete is at the start of the row
                        action = 'delete same line';                 
                        lines = lines.map(line => line.replace(/\n$/, ''));
                        if (lines[lines.length - 1] === '') {
                            lines.pop();
                        }
                        console.log(lines.length)
                        await sendModifiction(lines[startLineNumber - 1], startLineNumber - 1, action, lines.length)
                 } 
                else{
                    await sendModifiction(lines[startLineNumber - 1] , startLineNumber - 1, "update", 0);
                }
                
            }
        }
    });
});

async function sendModifiction (content, row, action, linesLength) {
    // First escape any special characters in the content
    const modification = JSON.stringify({
        content: content,
        row: row,
        action: action,
        linesLength: linesLength,
    });
    
    await saveInput(modification);
}

async function handlePaste(event) {
    isPaste = true;    
    const pastedData = (event.clipboardData || window.clipboardData).getData('text');
    let linesArray = pastedData.split('\n');

    const lastLineNumber = codeEditor.getSelection().startLineNumber;
    const lastLineContent = codeEditor.getModel().getLineContent(lastLineNumber)
    const firstLineNumber = lastLineNumber - linesArray.length + 1;
    linesArray.shift();
    linesArray[linesArray.length - 1] = lastLineContent;
    const contentPaste = linesArray.join("\n");
    await sendModifiction(contentPaste, firstLineNumber, "paste", 0);
    //await sendModifiction(contentPaste, codeEditor.getSelection().startLineNumber, "update", 0);
    isPaste = false;
};

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

async function onKeyZ(change, lines) {
    console.log('Undo shortcut pressed (Ctrl+Z or Cmd+Z)');
    console.log(change)
    let changeLines = change["text"].split("\n");
    let startLine = change.range['startLineNumber'] - 1;
    let endLine = changeLines.length + startLine - 1;
    // Handle custom behavior
    if (lines[startLine] !== ""){
        console.log(lines[startLine]);
        changeLines[0] = lines[startLine];
    }
    if(lines[endLine] !== ""){
        console.log(lines[endLine]);
        changeLines[changeLines.length - 1] = lines[endLine];
    }

    let text = changeLines.join("\n");
    sendModifiction(change.range['endLineNumber'], change.range['startLineNumber'], "delete highlighted", 0);
    sendModifiction(text, change.range['startLineNumber'] - 1, "update", 0);
    undoTriggered = false;
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
    const modification = JSON.stringify({ content: code, row: 1, action: 'saveAll', linesLength: code.split("\n").length });
    console.log("saveAll")
    await saveInput(modification)
    Loadeing = false;
}

async function saveInput(modification) {

    try {
        // First stringify the modification, then encode it
        const encodedModification = encodeURIComponent(modification);
        const url = "/save?modification=" + encodedModification;
        const response = await fetch(url, {
            method: 'GET',
            headers: { 
                'fileID': fileID,
                "userID": userID,
                'Connection': 'keep-alive'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.text();
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
                showNotification('A file with this name already exists. Please choose a different name.', 'error');
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
            showNotification('Failed to create new file. Please try again.', 'error');
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
    /*if(action == "delete row below"){
       action = "delete";
        row  = row + 1;
    }*/
   const linesCount = model.getLineCount();

    if (action === "delete highlighted") { // must first if
        // For delete highlighted action, we need to create a range that represents the highlighted lines
        // The start is the row, and the end is the last line of the content.
        range = new monaco.Range(
            row,            // Convert 0-based to 1-based
            1,              // Start at beginning of line
            content + 1,         // the end of the delete is in content 
            1               // End at beginning of the last line
        );
        content = "";       // Empty content to remove the lines
    } else if (content.startsWith("\n") && action === "update" && row === model.getLineCount()){
        // Handle new line at the end of file
        range = new monaco.Range(
            update.row + 1,  // Next line
            1,              // Start at beginning of line
            update.row + 1, // Same line
            1               // End at beginning of line
        );
        content = ""; // Empty content for new line
    } else if (action === "insert" || action === "paste") {
        // For insert action, we need to create a range that represents a new line
        // make sure it has a a "\n" at the end.
            if (! content.endsWith("\n")){
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
    } else if (action === "update") {
        // For update action (including deletions within the same row)
        range = new monaco.Range(
            row,  // Convert 0-based to 1-based
            1,              // Start at beginning of line
            row,            // Same line
            model.getLineContent(row).length + 1  // End at end of current line
        );
    }else if(action === "saveAll"){
        range = new monaco.Range(
            1,  // Convert 0-based to 1-based
            1,              // Start at beginning of line
            model.getLineCount(),            // Last line
            model.getLineContent(row).length + 1  // End at end of current line
        );
    } else if (action === "update and delete row below") {
        // Adjust the range to include the next line for deletion
        range = new monaco.Range(
            row,            // Convert 0-based to 1-based
            1,              // Start at beginning of line
            row + 1,        // Next line after the one to be deleted
            1               // Start of the line after the one to be deleted
        );
    }else { //change becuse the action is not the right one
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
            showNotification('File upload completed!','success')
        } catch (error) {
            console.error('Error during file upload:', error);
            showNotification(error.message, 'error');
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
        showNotification('Please select a file first', 'error');
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

        // Check if current user is the owner
        const isOwner = data.owner_id === parseInt(userID);
        
        // Show/hide user management controls based on ownership
        const userManagementControls = document.querySelectorAll('#username-action, #grant-user-btn, #revoke-user-btn');
        userManagementControls.forEach(control => {
            control.style.display = isOwner ? 'block' : 'none';
        });

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
        showNotification(error.message, 'error');
    }
}


function hasValidExtension(filename) {
    if (!filename) return false;
    const validExtensions = [
        '.py', '.js', '.ts', '.html', '.css', '.json', '.java', '.c', '.cpp', '.cs', '.go', '.php', '.r', '.rb', '.sh', '.sql', '.xml', '.yaml', '.md', '.swift', '.dockerfile', '.ini', '.plaintext', '.bat', '.powershell'
    ];
    const extension = filename.substring(filename.lastIndexOf('.'));
    return validExtensions.includes(extension.toLowerCase());
}

async function accessUser(usernameInput,request) {
    const username = usernameInput.value.trim();
    if (!username) {
        showNotification('Please enter a username', 'error');;
        return;
    }
    let prompt;

    if (request === "granted"){
        prompt = '/grant-user-to-file';
    }
    else{
        prompt ='/revoke-user-to-file';
    }

    try {
        // Add user to file
        const response = await fetch(prompt, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, fileID }),
        });

        const data = await response.json();

        if (response.ok) {
            showNotification('Access ' + request + ' successfuly! the user needs to refresh the files!', 'success');
            usernameInput.value = ''; // Clear the input
            loadFileDetails(); // Refresh the user list
        } else {
            showNotification(data.message, 'error');
        }
        
    } catch (error) {
        console.error('Error :', error);
        showNotification(error.message, 'error');
    }
}

// Add event listener for the add user button
document.addEventListener('DOMContentLoaded', () => {
    const grantUserBtn = document.getElementById('grant-user-btn');
    const usernameInput = document.getElementById('username-action');
    
    if (grantUserBtn && usernameInput) {
        grantUserBtn.addEventListener('click', () => accessUser(usernameInput, "granted"));
    }
});

// Add event listener for the add user button
document.addEventListener('DOMContentLoaded', () => {
    const revokeUserBtn = document.getElementById('revoke-user-btn');
    const usernameInput = document.getElementById('username-action');
    
    if (revokeUserBtn && usernameInput) {
        revokeUserBtn.addEventListener('click', () => accessUser(usernameInput, "revoked"));
    }
});


function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.className = `notification ${type === 'success' ? 'success-notification' : 'error-notification'}`;
    notification.innerText = message;
    notification.style.display = 'block';
    notification.style.opacity = '1';

    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            notification.style.display = 'none';
        }, 500);
    }, 3000);
}

// Add event listener for the refresh button
document.addEventListener('DOMContentLoaded', () => {
    const refreshBtn = document.getElementById('refresh-files');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            // Add rotation animation
            refreshBtn.style.transform = 'rotate(360deg)';
            refreshBtn.style.transition = 'transform 0.5s ease';
            
            // Refresh the files list
            const filesInfo = await GetUserFiles(userID);
            populateFileLists(filesInfo);
            
            // Check if current file is still accessible
            if (fileID) {
                const currentFileExists = filesInfo.fileIds.includes(parseInt(fileID));
                if (!currentFileExists) {
                    // User no longer has access to the current file
                    showNotification('You no longer have access to this file', 'error');
                    // Clear the editor
                    codeEditor.setValue('');
                    // Clear the current file tab
                    const currentFileTab = document.getElementById('current-file-tab');
                    currentFileTab.textContent = '';
                    currentFileTab.classList.remove('active-tab');
                    // Reset fileID
                    fileID = 0;
                    // Stop polling for updates
                    stopPolling();
                }
            }
            
            // Reset rotation after animation
            setTimeout(() => {
                refreshBtn.style.transform = '';
            }, 500);
        });
    }
});

