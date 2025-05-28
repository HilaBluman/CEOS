let codeEditor;
let isEditorReady = false; 
const host = '192.168.68.54'
const main_url = 'http://'+ host +':8000'

// RSA Encryption Class with better error handling
class ClientEncryption {
    constructor() {
        this.jsencrypt = null;
        this.isReady = false;
        this.encryptionMode = 'none'; // 'rsa', 'fallback', or 'none'
        this.initializeEncryption();
    }

    initializeEncryption() {
        try {
            if (typeof JSEncrypt !== 'undefined') {
                this.jsencrypt = new JSEncrypt();
                this.encryptionMode = 'rsa';
                console.log('✅ JSEncrypt initialized successfully');
            } else {
                console.warn('⚠️ JSEncrypt not available - encryption disabled');
                this.encryptionMode = 'none';
            }
        } catch (error) {
            console.error('❌ Error initializing JSEncrypt:', error);
            this.encryptionMode = 'none';
        }
    }

    base64ToPem(base64Key) {
        const pemHeader = '-----BEGIN PUBLIC KEY-----\n';
        const pemFooter = '\n-----END PUBLIC KEY-----';
        const formatted = base64Key.match(/.{1,64}/g).join('\n');
        return pemHeader + formatted + pemFooter;
    }

    async getPublicKey() {
        if (this.encryptionMode === 'none') {
            console.log('🔓 Running in no-encryption mode');
            return true;
        }

        try {
            const response = await fetch('/get-public-key', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (this.jsencrypt) {
                const pemKey = this.base64ToPem(data.publicKey);
                this.jsencrypt.setPublicKey(pemKey);
                this.isReady = true;
                console.log('🔑 Public key obtained and set successfully');
            }
            
            return true;
        } catch (error) {
            console.error('❌ Error getting public key:', error);
            this.encryptionMode = 'none';
            console.log('🔓 Falling back to no-encryption mode');
            return true; // Continue without encryption
        }
    }

    encrypt(text) {
        if (this.encryptionMode === 'none' || !this.jsencrypt || !this.isReady) {
            return text; // Return unencrypted text
        }

        try {
            const encrypted = this.jsencrypt.encrypt(text);
            if (!encrypted) {
                console.warn('⚠️ Encryption failed - returning original text');
                return text;
            }
            return encrypted;
        } catch (error) {
            console.warn('⚠️ Encryption error - returning original text:', error);
            return text;
        }
    }

    isEncryptionAvailable() {
        return this.encryptionMode === 'rsa' && this.isReady;
    }
}

// Global RSA instance
let clientRSA;

// Improved JSEncrypt waiting function with timeout
function waitForJSEncrypt(timeout = 5000) {
    return new Promise((resolve) => {
        const startTime = Date.now();
        
        const checkJSEncrypt = () => {
            if (typeof JSEncrypt !== 'undefined') {
                console.log('✅ JSEncrypt loaded successfully');
                resolve(true);
            } else if (Date.now() - startTime > timeout) {
                console.warn('⚠️ JSEncrypt loading timeout - continuing without encryption');
                resolve(false);
            } else {
                setTimeout(checkJSEncrypt, 50);
            }
        };
        
        checkJSEncrypt();
    });
}

require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.36.1/min/vs' }});

async function initializeEditor() {
    await new Promise((resolve) => {
        require(['vs/editor/editor.main'], async function () {
    
        // JS compiler setup
        monaco.languages.typescript.javascriptDefaults.setCompilerOptions({
            target: monaco.languages.typescript.ScriptTarget.ES2020,
            allowNonTsExtensions: true,
            checkJs: true,
            noEmit: true,
            strict: true
        });

        // Create editor 
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
let isViewer = false;
let highlightedTxt = {start: -1, end: -1, selectedText: ""}
let pollingInterval;

let fileID = 0;     // changes after pciking a file
let userID = 0;
let username = "";
let lastModID = -1; 

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

// Improved initialization with better error handling
document.addEventListener('DOMContentLoaded', async () => {
    try {
        console.log('🚀 Starting application initialization...');
        
        // Show loading message to user
        showNotification('Loading application...', 'info');
        
        // Wait for JSEncrypt with timeout
        const jsEncryptLoaded = await waitForJSEncrypt(5000);
        
        if (jsEncryptLoaded) {
            console.log('✅ JSEncrypt loaded successfully');
        } else {
            console.log('⚠️ Continuing without JSEncrypt - encryption disabled');
            showNotification('Running in fallback mode (encryption disabled)', 'warning');
        }
        
        // Initialize RSA (will work with or without JSEncrypt)
        clientRSA = new ClientEncryption();
        
        // Initialize Monaco Editor
        console.log('📝 Initializing Monaco Editor...');
        await initializeEditor();
        console.log('✅ Monaco Editor initialized');
        
        // Initialize RSA encryption
        console.log('🔐 Setting up encryption...');
        await clientRSA.getPublicKey();
        
        // Load initial file
        console.log('📂 Loading initial file...');
        await loadInitialFile();
        
        console.log('🎉 Application initialization complete!');
        showNotification('Application loaded successfully!', 'success');
        
    } catch (error) {
        console.error('❌ Error during initialization:', error);
        showNotification('Error loading application: ' + error.message, 'error');
        
        // Try to continue without all features
        try {
            if (!isEditorReady) {
                await initializeEditor();
            }
            clientRSA = new ClientRSA(); // Fallback mode
            await loadInitialFile();
        } catch (fallbackError) {
            console.error('❌ Fallback initialization also failed:', fallbackError);
            showNotification('Critical error - please refresh the page', 'error');
        }
    }
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
        else{
        document.getElementById('file-details').classList.remove('slide-in');
        document.getElementById('versions-details').classList.remove('slide-in');

            for (const change of event.changes) {
                const startLineNumber = change.range.startLineNumber; // Starting line number of the change
                const endLineNumber = change.range.endLineNumber;     // Ending line number of the change
                const changedText = change.text;                      // The new text that was inserted or replaced
                const isDelete = changedText === '';                 // Check if the change is a delete operation

                const fullContent = editor.getValue();
                let lines = fullContent.split('\n');

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
    console.log(userID);
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

async function saveAll() {
    const code = codeEditor.getValue();
    const modification = JSON.stringify({ content: code, row: 1, action: 'saveAll', linesLength: code.split("\n").length });
    console.log("saveAll")
    await saveInput(modification)
    Loadeing = false;
}

async function saveInput(modification) {
    try {
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

// Improved loadFile function with better encryption handling
async function loadFile(fileId) {
    try {
        console.log(`📂 Loading file ${fileId}...`);
        
        let headers = { 'Connection': 'keep-alive' };
        
        if (clientRSA && clientRSA.isEncryptionAvailable()) {
            console.log('🔒 Loading file with RSA encryption...');
            const encryptedFileId = clientRSA.encrypt(fileId.toString());
            headers['fileId'] = encryptedFileId;
            headers['encrypted'] = 'true';
        } else {
            console.log('🔓 Loading file without encryption...');
            headers['fileId'] = fileId.toString();
        }
        
        const response = await fetch('/load', {
            method: 'GET',
            headers: headers
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        if (data.fullContent) {
            Loadeing = true;
            lastModID = data.lastModID;
            console.log("lastModID: " + lastModID);
            codeEditor.setValue(data.fullContent);
            console.log('✅ File loaded successfully');
            startPolling();
        }
        
    } catch (error) {
        console.error('❌ Error loading file:', error);
        showNotification('Error loading file: ' + error.message, 'error');
    }
}

let selectedFileId = null;
let selectedFileName = null;

function selectFile(fileId, filename) {
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

    checkViewerStatus();
}

async function checkViewerStatus() {
    try {
        const response = await fetch('/check-viewer-status', {
            method: 'GET',
            headers: {
                'fileId': selectedFileId,
                'userId': userID
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        isViewer = data.isViewer;
        console.log("isViewer:", isViewer);
        setEditorReadOnly(isViewer); // Disable editing if the user is a viewer
    } catch (error) {
        console.error('Error checking viewer status:', error);
        showNotification('Error checking file permissions', 'error');
    }
}


async function getUserFiles(userId) {
    try {
        console.log(`👤 Getting files for user ${userId}...`);
        
        let headers = {};
        
        if (clientRSA && clientRSA.isEncryptionAvailable()) {
            console.log('🔒 Getting user files with RSA encryption...');
            const encryptedUserId = clientRSA.encrypt(userId.toString());
            headers['userId'] = encryptedUserId;
            headers['encrypted'] = 'true';
        } else {
            console.log('🔓 Getting user files without encryption...');
            headers['userId'] = userId.toString();
        }

        const response = await fetch('/get-user-files', {
            method: 'GET',
            headers: headers
        });

        if (!response.ok) {
            const errorBody = await response.text(); 
            throw new Error(`HTTP error! status: ${response.status}, body: ${errorBody}`);
        }

        const data = await response.json();
        console.log('✅ User files retrieved successfully');
        return {
            fileIds: data.filesId,
            filenames: data.filenames
        };
    } catch (error) {
        console.error('❌ Error fetching user files:', error);
        showNotification('Error fetching files: ' + error.message, 'error');
        return { fileIds: [], filenames: [] };
    }
}

async function loadInitialFile() { 
    username = await get_username(); 
    userID = await get_userID(); 

    const filesInfo = await getUserFiles(userID);

    populateFileLists(filesInfo);

    document.getElementById('file-popup').style.display = 'block';
}

function populateFileLists(filesInfo) {
    const fileList = document.getElementById('file-list');
    const fileTree = document.getElementById('file-tree');

    fileList.innerHTML = '';
    fileTree.innerHTML = '';
    
    if (Array.isArray(filesInfo.fileIds) && Array.isArray(filesInfo.filenames)) {
        filesInfo.filenames.forEach((filename, index) => {
            const fileId = filesInfo.fileIds[index];
            
            const popupListItem = document.createElement('li');
            popupListItem.textContent = filename;
            popupListItem.setAttribute('data-file-id', fileId);
            
            const sidebarListItem = document.createElement('li');
            sidebarListItem.innerHTML = `📄 ${filename}`;
            sidebarListItem.setAttribute('data-file-id', fileId);
            
            const handleFileClick = async () => {
                document.querySelectorAll('#file-list li, #file-tree li').forEach(item => 
                    item.classList.remove('selected')
                );

                popupListItem.classList.add('selected');
                sidebarListItem.classList.add('selected');
                await selectFile(fileId, filename);
                await loadFile(fileId);
                
                document.getElementById('file-popup').style.display = 'none';
                document.getElementById('file-details').classList.remove('slide-in');
                document.getElementById('versions-details').classList.remove('slide-in');
            };
            
            popupListItem.onclick = handleFileClick;
            sidebarListItem.onclick = handleFileClick;
            
            fileList.appendChild(popupListItem);
            fileTree.appendChild(sidebarListItem);
        });
    } else {
        console.error('No files found or invalid response:', filesInfo);
    }
}

// Improved createNewFile function
async function createNewFile(filename) {
    if (!hasValidExtension(filename)) {
        filename = filename.replace(/\..*$/, '.txt');
    } 
    
    try {
        console.log(`📝 Creating new file: ${filename}`);
        
        let headers = {};
        
        if (clientRSA && clientRSA.isEncryptionAvailable()) {
            console.log('🔒 Creating new file with RSA encryption...');
            headers['userId'] = clientRSA.encrypt(userID.toString());
            headers['filename'] = clientRSA.encrypt(filename);
            headers['encrypted'] = 'true';
        } else {
            console.log('🔓 Creating new file without encryption...');
            headers['userId'] = userID.toString();
            headers['filename'] = filename;
        }

        const response = await fetch('/new-file', {
            method: 'GET',
            headers: headers
        });

        const data = await response.json();

        if (response.status === 409) {
            showNotification('A file with this name already exists. Please choose a different name.', 'error');
            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        if (data.fileId !== 0) {
            fileID = data.fileId;
        }

        const fileTree = document.querySelector('.file-tree');
        const newFileItem = document.createElement('li');
        newFileItem.innerHTML = `📄 ${filename}`;
        newFileItem.setAttribute('data-file-id', data.fileId);
        fileTree.appendChild(newFileItem);
        codeEditor.setValue('// New file');
        document.getElementById('file-popup').style.display = 'none';

        await selectFile(data.fileId, filename);
        //await loadFile(data.fileId);
        console.log('✅ New file created successfully');
        showNotification('File created successfully!', 'success');

    } catch (error) {
        console.error('❌ Error creating new file:', error);
        showNotification('Failed to create new file. Please try again.', 'error');
    }
}

// Improved uploadNewFile function
async function uploadNewFile(fileContent, filename) {
    try {
        console.log(`📤 Uploading file: ${filename}`);
        
        let headers = { 'Content-Type': 'application/json' };
        let body = {};
        
        if (clientRSA && clientRSA.isEncryptionAvailable()) {
            console.log('🔒 Uploading file with RSA encryption...');
            headers['filename'] = clientRSA.encrypt(filename);
            headers['userId'] = clientRSA.encrypt(userID.toString());
            headers['encrypted'] = 'true';
            body = {
                content: clientRSA.encrypt(fileContent),
                encrypted: true
            };
        } else {
            console.log('🔓 Uploading file without encryption...');
            headers['filename'] = filename;
            headers['userId'] = userID.toString();
            body = { content: fileContent };
        }

        const response = await fetch('/upload-file', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(body)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('✅ File uploaded successfully:', result);

        const fileTree = document.querySelector('.file-tree');
        const newFileItem = document.createElement('li');
        newFileItem.innerHTML = `📄 ${filename}`;
        newFileItem.setAttribute('data-file-id', result.fileId);
        fileTree.appendChild(newFileItem);
        await selectFile(result.fileId, filename);
        await loadFile(result.fileId);
        showNotification('File uploaded successfully!', 'success');
        
    } catch (error) {
        console.error('❌ Error uploading file:', error);
        showNotification('Failed to upload file: ' + error.message, 'error');
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

        // Temporarily disable read-only mode to apply updates
        const wasReadOnly = codeEditor.getOption(monaco.editor.EditorOption.readOnly);
        if (wasReadOnly) {
            codeEditor.updateOptions({ readOnly: false });
        }

        codeEditor.executeEdits('', [{
            range: range,
            text: content
        }]);
        
        const decorationIds = codeEditor.deltaDecorations([], decorations);
        setTimeout(() => {
            codeEditor.deltaDecorations(decorationIds, []);
        }, 500);

        // Restore read-only mode if it was enabled
        if (wasReadOnly) {
            codeEditor.updateOptions({ readOnly: true });
        }
        
    } catch (error) {
        console.error('Error applying partial update:', error);
    }
    finally {
        isApplyingUpdates = false; 
    }
}

function getRangeAndContent(update) {
    let row = update.row + 1;
    let content = update.content;
    let action = update.action;
    let decorations = [];
    const model = codeEditor.getModel();
    let range;

    if (action === "delete highlighted") { 
        range = new monaco.Range(
            row,            // Convert 0-based to 1-based
            1,              // Start at beginning of line
            content + 1,         // the end of the delete is in content 
            1               // End at beginning of the last line
        );
        content = "";       
    } else if (content.startsWith("\n") && action === "update" && row === model.getLineCount()){
        range = new monaco.Range(
            update.row + 1,  
            1,              
            update.row + 1, 
            1               
        );
        content = "";
    } else if (action === "insert" || action === "paste") {
            if (! content.endsWith("\n")){
                content = content + "\n";
            }

        range = new monaco.Range(
            row,  
            1,             
            row,            
            1               
        );
    } else if (action == "delete"){
        range = new monaco.Range(
            row,  
            1,              
            row + 1,        
            1               
        );
        content = "";       
    } else if (action === "update") {
        range = new monaco.Range(
            row,  
            1,              
            row,            
            model.getLineContent(row).length + 1  
        );
    }else if(action === "saveAll"){
        range = new monaco.Range(
            1,  
            1,              
            model.getLineCount(),            
            model.getLineContent(row).length + 1  
        );
    } else if (action === "update and delete row below") {
        range = new monaco.Range(
            row,            
            1,              
            row + 1,        
            1               
        );
    }else { 
        console.log("action not acceptable.")
    }

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
        if (pollingInterval) {
            setTimeout(pollForUpdates, 200);
        }
    }
}

function startPolling() {
    console.log("in start polling");
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
    document.getElementById('mini-popup').style.display = 'none';
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
            document.body.removeChild(fileInput);
        }
    };

    document.body.appendChild(fileInput);
    fileInput.click();
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

function popFileInfo(popupVariation) {
    if (!fileID || !selectedFileName) {
        showNotification('Please select a file first', 'error');
        return;
    }
    
    let sidePanel = '';
    
    if (popupVariation === "D") {
        sidePanel = document.getElementById('file-details');
        sidePanel.classList.add('open');
        loadFileDetails();
    } else if (popupVariation === "V") {
        sidePanel = document.getElementById('versions-details');
        sidePanel.classList.add('open');
        loadVersionDetails(); 
    } else {
        console.log("The popup variation does not exist!");
    }
    document.getElementById('filename').textContent = selectedFileName;
}

async function loadVersionDetails() {
    try {
        const response = await fetch('/get-version-details', {
            method: 'GET',
            headers: {
                'fileID': fileID
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        const isOwner = data.owner_id === parseInt(userID);
        document.getElementById('filename2').textContent = selectedFileName;

        // Show/hide buttons based on viewer status and ownership
        const deleteVersionBtn = document.getElementById('delete-version-btn');
        const saveVersionBtn = document.getElementById('save-version-btn');
        
        if (isViewer) {
            deleteVersionBtn.style.display = 'none';
            saveVersionBtn.style.display = 'none';
        } else {
            deleteVersionBtn.style.display = isOwner ? 'block' : 'none';
            saveVersionBtn.style.display = 'block';
        }

        const versionsList = document.getElementById('versions-list');
        versionsList.innerHTML = ''; 

        data.versions.forEach(version => {
            const row = document.createElement('tr');
            const versionCell = document.createElement('td');
            versionCell.textContent = version[0];
            const dateCell = document.createElement('td');
            dateCell.textContent = version[1];
            const timeCell = document.createElement('td');
            timeCell.textContent = version[2];

            row.appendChild(versionCell);
            row.appendChild(dateCell);
            row.appendChild(timeCell);
            versionsList.appendChild(row);
        });

        document.getElementById('versions-details').classList.add('slide-in'); 

        document.getElementById('close-panel-V-btn').onclick = () => {
            document.getElementById('versions-details').classList.remove('slide-in');}

    } catch (error) {
        console.error('Error loading version details:', error);
        showNotification('Error loading version details', 'error');
    }
}

function confirmDelete(type) {
    const popup = document.getElementById('delete-confirm-popup');
    document.getElementById('delete-type').value = type;
    popup.style.display = 'flex';
}

function confirmDeleteAction(confirmed) {
    const popup = document.getElementById('delete-confirm-popup');
    const deleteType = document.getElementById('delete-type').value;
    popup.style.display = 'none';
    
    if (confirmed) {
        if (deleteType === 'file') {
            deleteFile();
        } else if (deleteType === 'version') {
            deleteVersion();
        }
    }
}

async function deleteVersion() {
    const version = document.getElementById('input-version-btn').value.trim();
    try {
        const response = await fetch('/delete-version', {
            method: 'DELETE',
            headers: {
                'fileID': fileID,
                'userID': userID,
                'version': version
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        document.getElementById('versions-details').classList.remove('slide-in');
        showNotification('Version deleted successfully', 'success');
        loadVersionDetails(); // Refresh the versions list
    } catch (error) {
        console.error('Error deleting version:', error);
        showNotification('Failed to delete version. Please try again.', 'error');
    }
}

async function deleteFile(){
    try {
        const response = await fetch('/delete-file', {
            method: 'DELETE',
            headers: {
                'fileID': fileID,
                'userID': userID
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        document.getElementById('file-details').classList.remove('slide-in');
        codeEditor.setValue('');
    
        const currentFileTab = document.getElementById('current-file-tab');
        currentFileTab.textContent = '';
        currentFileTab.classList.remove('active-tab');
        
        fileID = 0;
        stopPolling();

        refreshFiles();
        const filePopup = document.getElementById('file-popup');
        filePopup.style.display = 'block';

        showNotification('File deleted successfully', 'success');
    } catch (error) {
        console.error('Error deleting file:', error);
        showNotification('Failed to delete file. Please try again.', 'error');
    }
}

async function loadFileDetails() {
    try {
        const response = await fetch('/get-file-details', {
            method: 'GET',
            headers: {
                'fileID': fileID
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Details data :", JSON.stringify(data));
        document.getElementById('filename').textContent = data.filename;
        const isOwner = data.owner_id === parseInt(userID);
        
        // Show/hide user management controls based on ownership
        const userManagementControls = document.querySelectorAll('#username-action,#role-action, #grant-user-btn, #revoke-user-btn, #delete-file-btn');
        userManagementControls.forEach(control => {
            control.style.display = isOwner ? 'block' : 'none';
        });

        if (Array.isArray(data.users)) {
            const userList = document.getElementById('user-list');
            userList.innerHTML = '';
            
            data.users.forEach((user) => {             
                const row = document.createElement('tr');
                
                const usernameCell = document.createElement('td');
                usernameCell.textContent = user.username;
                
                const roleCell = document.createElement('td');
                roleCell.textContent = user.role || 'user';
                
                row.appendChild(usernameCell);
                row.appendChild(roleCell);
                userList.appendChild(row);
            });
        }
        document.getElementById('file-details').classList.add('slide-in');
        document.getElementById('file-details').classList.add('slide-in');
        document.getElementById('close-panel-D-btn').onclick = () => {
            document.getElementById('file-details').classList.remove('slide-in');
        };

    } catch (error) {
        console.error('Error loading file details:', error);
        showNotification('Error loading file details', 'error');
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

async function accessUser(usernameInput, request, roleInput) {
    const username = document.getElementById('username-action').value.trim();
    const role = document.getElementById('role-action').value.trim().toLowerCase();
    if (!username) {
        showNotification('Please enter a username', 'error');
        return;
    }

    let prompt;
    if (request === "granted") {
        prompt = '/grant-user-to-file';
    } else {
        prompt = '/revoke-user-to-file';
    }

    try {
        const response = await fetch(prompt, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'ownerID': userID,      //if this function is called the user is the owner - just to be safe there is a check on the server side
            },
            body: JSON.stringify({ username, fileID, role }),
        });

        const data = await response.json();

        if (response.ok) {
            showNotification('Access ' + request + ' successfully! The user needs to refresh the files!', 'success');
            usernameInput.value = ''; 
            roleInput.value = '';
            loadFileDetails(); 
        } else {
            console.log(data);
            showNotification(data.message, 'error');
        }
        
    } catch (error) {
        console.error('Error:', error);
        showNotification(error, 'error');
    }
}

// Add event listener for the add user button
document.addEventListener('DOMContentLoaded', () => {
    const grantUserBtn = document.getElementById('grant-user-btn');
    const usernameInput = document.getElementById('username-action');
    const roleInput = document.getElementById('role-action');
    
    if (grantUserBtn && usernameInput && roleInput) {
        grantUserBtn.addEventListener('click', () => accessUser(usernameInput, "granted", roleInput));
    }
});

// Add event listener for the revoke user button
document.addEventListener('DOMContentLoaded', () => {
    const revokeUserBtn = document.getElementById('revoke-user-btn');
    const usernameInput = document.getElementById('username-action');
    const roleInput = document.getElementById('role-action');
    
    if (revokeUserBtn && usernameInput && roleInput) {
        revokeUserBtn.addEventListener('click', () => accessUser(usernameInput, "revoked", roleInput));
    }
});

// Improved showNotification function with better styling
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    
    // Remove existing classes
    notification.className = 'notification';
    
    // Add appropriate class based on type
    switch(type) {
        case 'success':
            notification.className += ' success-notification';
            break;
        case 'error':
            notification.className += ' error-notification';
            break;
        case 'warning':
            notification.className += ' warning-notification';
            break;
        default:
            notification.className += ' info-notification';
    }
    
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

async function saveNewVersion() {
    try {
        const response = await fetch('/save-new-version', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({fileID,userID, content: codeEditor.getValue() })
        });

        if (!response.ok) {
            console.log("error: " + response.json().stringify());
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
            
        showNotification(data, 'success');
        loadVersionDetails();

    } catch (error) {
        console.error('Error saving new version:', error);
        showNotification('Error saving new version', 'error');
    }
}

async function showVersion(){
    isViewer = true;
    const version = document.getElementById('input-version-btn').value.trim();
    try {
        const response = await fetch('/show-version', {
            method: 'GET',
            headers: {
                'fileID': fileID,
                'userID': userID,
                'version': version
            }
        });

        const data = await response.json();
        console.log("data.fullContent: " + data.fullContent)

        if (data.fullContent) {
            Loadeing = true;
            const currentFileTab = document.getElementById('current-file-tab');

            currentFileTab.textContent = selectedFileName + " - V" + version;
            codeEditor.setValue(data.fullContent);
            setEditorReadOnly(true);  // Disable editing in viewer mode
            stopPolling()
        }
    }
    catch (error) {
        console.error('Error saving showing version:', error);
        showNotification('Error saving showing version', 'error');
    }
}

async function refreshFiles(){
    const filesInfo = await getUserFiles(userID);
    populateFileLists(filesInfo);
    
    if (fileID) {
        const currentFileExists = filesInfo.fileIds.includes(parseInt(fileID));
        if (!currentFileExists) {
            showNotification('You no longer have access to this file', 'error');
            codeEditor.setValue('');
            const currentFileTab = document.getElementById('current-file-tab');
            currentFileTab.textContent = '';
            currentFileTab.classList.remove('active-tab');
            fileID = 0;
            stopPolling();
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const refreshBtn = document.getElementById('refresh-files');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            refreshBtn.style.transform = 'rotate(360deg)';
            refreshBtn.style.transition = 'transform 0.5s ease';
            refreshFiles();
        setTimeout(() => {
            refreshBtn.style.transform = '';
        }, 500);
    });
    }
});  

function setEditorReadOnly(isReadOnly) {
    useCodeEditor((editor) => {
        editor.updateOptions({
            readOnly: isReadOnly
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const menuIcon = document.querySelector('.menu-icon');
    const slideMenu = document.getElementById('slide-menu');
    
    menuIcon.addEventListener('click', () => {
        slideMenu.classList.toggle('open');
    });

    // Close menu when clicking outside
    document.addEventListener('click', (event) => {
        if (!slideMenu.contains(event.target) && !menuIcon.contains(event.target)) {
            slideMenu.classList.remove('open');
        }
    });
});

function closeFilePopup() {
    isViewer = true;
    setEditorReadOnly(true);
    document.getElementById('file-popup').style.display = 'none';
}