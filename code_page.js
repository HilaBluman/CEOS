// DOM Elements
const codeEditor = document.getElementById('code-editor');
const lineNumbers = document.querySelector('.line-numbers');
const newFileButton = document.getElementById('new-file-button');
const runButton = document.getElementById('run-button');
const resizeHandle = document.getElementById('resize-handle');
const outputContainer = document.querySelector('.output-container');
const editor = document.querySelector('.editor');
const fileNameDisplay = document.getElementById('file-name');
const fileNameInput = document.getElementById('filename-input');

// Flags and Variables
let isResizing = false;
let startX;
let startOutputWidth;
let previousContent = '';
let timeoutId;
let highlighted_flag = false;
let highlightedTxt = {start: -1, end: -1, selectedText: ""}

// Functionality Constants
const DEBOUNCE_DELAY = 500; // ms
const MIN_WIDTH = 80;
const MAX_WIDTH = window.innerWidth * 0.8;

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadInitialFile();
    updateLineNumbers();
});

codeEditor.addEventListener('paste', onCodeEditorPaste); // handles pasting
codeEditor.addEventListener('scroll', onCodeEditorScroll); // handles scroling
//codeEditor.addEventListener('input', onCodeEditorInput); // handles input saving  

newFileButton.addEventListener('click', onNewFileButtonClick);
runButton.addEventListener('click', onRunButtonClick);

resizeHandle.addEventListener('mousedown', onResizeHandleMouseDown);
document.addEventListener('mousemove', onDocumentMouseMove); //adjusts the output container based on the mouse's horizontal movement while resizing
document.addEventListener('mouseup', onDocumentMouseUp);    
document.addEventListener('keydown', onDocumentKeySave); // handles Ctrl+S or Command+S, prevents the default save action instead calls saveFile
document.addEventListener('keyup', onCodeEditorInput); // handles input saving  
document.addEventListener('selectionchange', Get_highlightedText) // handles input saving  


// Helper Functions

function onCodeEditorPaste(e) {
    e.preventDefault();
    const text = e.clipboardData.getData('text/plain');
    const selection = window.getSelection();
    const range = selection.getRangeAt(0);
    range.deleteContents();
    range.insertNode(document.createTextNode(text));
    updateLineNumbers();
    saveInput();

}

function onCodeEditorScroll() {
    lineNumbers.scrollTop = codeEditor.scrollTop;
}


async function onCodeEditorInput(event) {
    await updateLineNumbers();
    const lines = codeEditor.textContent.split('\n');
    const linesLength = lines.length - 1;
    if (highlighted_flag){
        console.log("in highlighted_flag");
        console.log("event.key: " + event.key)
        if (event.key === 'Backspace' || event.keyCode === 8) {
            const firstline = lines[highlightedTxt.start];
            await DeleteHighhlighted(highlightedTxt.start, highlightedTxt.end, linesLength, firstline);
        }
        // add a paste one
        highlighted_flag = false;
    }
    else{               
        const row = getCursorPosition(codeEditor);
        const currentLine = lines[row]
        const action = "update";
        const modification = JSON.stringify({ currentLine, row, action, linesLength });
        saveInput(modification);
    }
}

function onNewFileButtonClick() {
    let newFileName = prompt('Enter file name:', 'untitled.py');

    if (newFileName) {
        if (!newFileName.includes('.')) {
            newFileName += '.py';
        }

        fileNameDisplay.textContent = newFileName;
        codeEditor.textContent = '';
        updateLineNumbers();
    }
}

async function onRunButtonClick() {
    setTimeout(runFile, 100);
}

function onResizeHandleMouseDown(e) {
    isResizing = true;
    startX = e.pageX;
    startOutputWidth = outputContainer.offsetWidth;
    document.body.classList.add('resizing');
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

function onDocumentKeySave(event) {
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        saveAll();
    }
}

function DeleteHighhlighted(start, fin, linesLength, firstline ) {  
        console.log("Delete - start: " + start + " fin: " + fin)
        const action = 'delete'
        for(let i = fin; i > start; i--){
            const modification = JSON.stringify({ currentLine: "in delete", row: i, action, linesLength });
            saveInput(modification)
        }
        const modification = JSON.stringify({ currentLine: firstline, row: start, action: 'update', linesLength });
        saveInput(modification)
        codeEditor.focus(); // Focus back on the textarea
}


// Core Functions

async function saveInput(modification) {
    const filename = document.getElementById('file-name').textContent;

    console.log("modification: " + modification)

    try {
        const encodedModification = encodeURIComponent(modification);
        const url = `http://127.0.0.1:8000/save?modification=${encodedModification}`;
        
        const response = await fetch(url, {
            method: 'GET',
            headers: { 'filename': filename }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.text();
        console.log('Save result:', result);
    } catch (error) {
        console.error('Error saving file:', error);
    }
}

function getCursorPosition(element) {
     const selection = window.getSelection();
     if (selection.rangeCount === 0) {
         return { row: 0 };
     }
     const range = selection.getRangeAt(0);
     const preCaretRange = range.cloneRange();
     preCaretRange.selectNodeContents(element);
     preCaretRange.setEnd(range.endContainer, range.endOffset);
     const text = preCaretRange.toString();
     const row = (text.match(/\n/g) || []).length;
     return row ;
 }

function updateLineNumbers() {
    const lines = codeEditor.textContent.split('\n');
    if (lines[lines.length - 1] === '') lines.pop();

    const lineCount = Math.max(lines.length, 1);
    lineNumbers.innerHTML = '';

    for (let i = 0; i < lineCount; i++) {
        const lineDiv = document.createElement('div');
        lineDiv.textContent = i + 1;
        lineNumbers.appendChild(lineDiv);
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
            headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'filename': filename }
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
    document.getElementById('file-name').textContent = filename;

    try {
        const response = await fetch(`/load`, {
            method: 'GET',
            headers: { 'filename': filename }
        });

        const data = await response.json();
        if (data.fullContent) {
            document.getElementById('code-editor').textContent = data.fullContent;
            previousContent = data.fullContent;
        }
        updateLineNumbers();
    } catch (error) {
        console.error('Error loading initial content:', error);
    }
}

async function loadInitialFile() {
    let filename = prompt('Enter the file name to load:', 'main.py');
    if (filename) await loadContent(filename);
}


async function Get_highlightedText(){
    const selectedText = window.getSelection().toString();
    clearTimeout(timeoutId); 
    timeoutId = setTimeout(function() {
        if(selectedText){
            highlighted_flag = true;
            highlightedTxt.start = getCursorPosition(codeEditor) - 1;
            highlightedTxt.end = highlightedTxt.start + selectedText.split('\n').length - 1;
            highlightedTxt.selectedText = selectedText;
        }
        else{
            highlighted_flag = false;
            highlightedTxt.start = -1;
            highlightedTxt.end = - 1;
            highlightedTxt.selectedText = "";
        }  
        console.log("highhlighted flag: " + highlighted_flag);      
        codeEditor.focus(); // Focus back on the textarea
    }, 200); // Delay of 200 milliseconds
}