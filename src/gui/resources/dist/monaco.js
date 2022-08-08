/*
 * This file is part of GumTree.
 *
 * GumTree is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * GumTree is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with GumTree.  If not, see <http://www.gnu.org/licenses/>.
 *
 * Copyright 2011-2015 Jean-Rémy Falleri <jr.falleri@gmail.com>
 * Copyright 2011-2015 Floréal Morandat <florealm@gmail.com>
 */

function getEditorOptions(text) {
    return {
        value: text,
        readOnly: true,
        language: getLanguage(),
        automaticLayout: true,
        scrollBeyondLastLine: false,
        lineDecorationsWidth: 0,
        glyphMargin: false,
        minimap: {
            enabled: false,
        },
    };
}

function getEditorEditableOptions(text){
    return {
        value: text,
        readOnly: false,
        language: getLanguage(),
        automaticLayout: true,
        scrollBeyondLastLine: false,
        lineDecorationsWidth: 0,
        glyphMargin: false,
        minimap: {
            enabled: false,
        },
    };
}

function getLanguage() {
    let extension = config.file.split('.').pop().toLowerCase();
    if (extension == "java")
        return "java";
    else if (extension == "js")
        return "javascript";
    else if (extension == "rb")
        return "ruby";
    else if (extension == "css")
        return "css";
    else if (extension == "py")
        return "python";
    else if (extension == "cs")
        return "csharp";
    else if (extension == "r")
        return "r";
    else if (extension == "php")
        return "php";
    else if (extension == "c" || extension == "h" || extension == "cpp")
        return "cpp";
    else
        return undefined;
}

function getEditColor(edit) {
    if (edit == "inserted") return 'green';
    else if (edit == "deleted") return 'red';
    else if (edit == "updated") return 'yellow';
    else if (edit == "moved") return 'blue';
    else return "black";
}

function getDecoration(range, pos, endPos) {
    return {
        range: new monaco.Range(pos.lineNumber, pos.column, endPos.lineNumber, endPos.column),
        options: {
            className: range.kind,
            zIndex: range.index,
            hoverMessage: {
                value: range.tooltip,
            },
            overviewRuler: {
                color: getEditColor(range.kind),
            },
        },
    };
}

const newUniverseContainer = document.getElementById('new-universe-container');
const oldTemplateContainer = document.getElementById('old-template-container');
const newTemplateContainer = document.getElementById('new-template-container');
const editorContainer = document.getElementById('editor-container')

function installResizeWatcher(el, fn, interval){
    let offset = {width: el.offsetWidth, height: el.offsetHeight}
    setInterval(()=>{
      let newOffset = {width: el.offsetWidth, height: el.offsetHeight}
      if(offset.height!=newOffset.height||offset.width!=newOffset.width){
        offset = newOffset
        fn()
      }
    }, interval)
  }

require.config({ paths: { 'vs': '/web/monaco-editor/min/vs' }});
require(['vs/editor/editor.main'], function() {
    Promise.all(
        [
            fetch(config.newUniverse.url)
                .then(result => result.text())
                .then(text => monaco.editor.create(document.getElementById('new-universe-container'), getEditorOptions(text))),
            fetch(config.oldTemplate.url)
                .then(result => result.text())
                .then(text => monaco.editor.create(document.getElementById('old-template-container'), getEditorOptions(text))),
            fetch(config.newTemplate.url)
                .then(result => result.text())
                .then(text => monaco.editor.create(document.getElementById('new-template-container'), getEditorOptions(text))),
            fetch(config.editor.url)
                .then(result => result.text())
                .then(text => monaco.editor.create(document.getElementById('editor-container'), getEditorEditableOptions(text)))
        ]
    ).then(([newUniverseEditor, oldTemplateEditor, newTemplateEditor, editableEditor]) => {
        installResizeWatcher(newUniverseContainer, newUniverseEditor.layout.bind(newUniverseEditor), 15)
        installResizeWatcher(oldTemplateContainer, oldTemplateEditor.layout.bind(oldTemplateEditor), 15)
        installResizeWatcher(newTemplateContainer, newTemplateEditor.layout.bind(newTemplateEditor), 15)
        installResizeWatcher(editorContainer, editableEditor.layout.bind(editableEditor), 15)

        editor = editableEditor
        config.templateMappings = config.templateMappings.map(mapping =>
            [
                monaco.Range.fromPositions(oldTemplateEditor.getModel().getPositionAt(mapping[0]), oldTemplateEditor.getModel().getPositionAt(mapping[1])),
                monaco.Range.fromPositions(newTemplateEditor.getModel().getPositionAt(mapping[2]), newTemplateEditor.getModel().getPositionAt(mapping[3])),
            ]);
        config.newUniTemplateMappings = config.newUniTemplateMappings.map(mapping =>
            [
                monaco.Range.fromPositions(newUniverseEditor.getModel().getPositionAt(mapping[0]), newUniverseEditor.getModel().getPositionAt(mapping[1])),
                monaco.Range.fromPositions(newTemplateEditor.getModel().getPositionAt(mapping[2]), newTemplateEditor.getModel().getPositionAt(mapping[3]))
            ])
        
        const newUniverseDecorations = config.newUniverse.ranges.map(range => getDecoration(
            range,
            newUniverseEditor.getModel().getPositionAt(range.from),
            newUniverseEditor.getModel().getPositionAt(range.to)
       ));
        newUniverseEditor.deltaDecorations([], newUniverseDecorations)
        
        newUniverseEditor.onMouseDown((event) => {
            const allDecorations = newUniverseEditor.getModel().getDecorationsInRange(event.target.range, newUniverseEditor.id, true)
            if (allDecorations.length >= 1) {
                let activatedRange = allDecorations[0].range;
                if (allDecorations.length > 1)  {
                    for (let i = 1; i < allDecorations.length; i = i + 1) {
                        const candidateRange = allDecorations[i].range;
                        if (activatedRange.containsRange(candidateRange))
                            activatedRange = candidateRange;
                    }
                }
                const mapping = config.newUniTemplateMappings.find(mapping => mapping[0].equalsRange(activatedRange))
                newTemplateEditor.revealRangeInCenter(mapping[1]);
            }
        });


        const oldTemplateDecorations = config.oldTemplate.ranges.map(range => getDecoration(
             range,
             oldTemplateEditor.getModel().getPositionAt(range.from),
             oldTemplateEditor.getModel().getPositionAt(range.to)
        ));
        oldTemplateEditor.deltaDecorations([], oldTemplateDecorations);

        oldTemplateEditor.onMouseDown((event) => {
            const allDecorations = oldTemplateEditor.getModel().getDecorationsInRange(event.target.range, oldTemplateEditor.id, true)
                .filter(decoration => decoration.options.className == "updated" || decoration.options.className == "moved");
            if (allDecorations.length >= 1) {
                let activatedRange = allDecorations[0].range;
                if (allDecorations.length > 1)  {
                    for (let i = 1; i < allDecorations.length; i = i + 1) {
                        const candidateRange = allDecorations[i].range;
                        if (activatedRange.containsRange(candidateRange))
                            activatedRange = candidateRange;
                    }
                }
                const mapping = config.templateMappings.find(mapping => mapping[0].equalsRange(activatedRange))
                newTemplateEditor.revealRangeInCenter(mapping[1]);
            }
        });

        const newTemplateDecorations = config.newTemplate.ranges.map(range => getDecoration(  
            range,
            newTemplateEditor.getModel().getPositionAt(range.from),
            newTemplateEditor.getModel().getPositionAt(range.to)
        ));
        newTemplateEditor.deltaDecorations([], newTemplateDecorations); // This part highlights the code into different colors for updated or deleted
        // for more see https://microsoft.github.io/monaco-editor/api/index.html
        // For saving the contents in an editor https://stackoverflow.com/questions/38086013/get-the-value-of-monaco-editor
        // Saving a file needs to be done in html
        newTemplateEditor.onMouseDown((event) => {  // This is the code that does the mouse click and link to the other part in the code.
            const allDecorations = newTemplateEditor.getModel().getDecorationsInRange(event.target.range, newTemplateEditor.id, true)
                .filter(decoration => decoration.options.className == "updated" || decoration.options.className == "moved");
            if (allDecorations.length >= 1) {
                let activatedRange = allDecorations[0].range;
                if (allDecorations.length > 1)  {
                    for (let i = 1; i < allDecorations.length; i = i + 1) {
                        const candidateRange = allDecorations[i].range;
                        if (activatedRange.containsRange(candidateRange)) activatedRange = candidateRange;
                    }
                }
                const mapping = config.templateMappings.find(mapping => mapping[1].equalsRange(activatedRange))
                oldTemplateEditor.revealRangeInCenter(mapping[0]);
            }
        });
    });
});

function bootstrap_alert(elem, message, timeout) {        
    $(elem + " .alertMessage").text(message)  
    $(elem).show().alert()
  
    if (timeout || timeout === 0) {
      setTimeout(function() { 
        $(elem).hide();
      }, timeout);    
    }
  };

function sendDataToBackendAjax(event) {
    
    // create own form in memory
    const formData = new FormData();
    var editorText = editor.getValue()
    // set values in this form
    formData.append("editor_text", editorText)
    fetch("/save-editor", {
        method: "POST",
        body: formData
        //headers: {'Content-Type': 'application/json'},
        //body: JSON.stringify(formData)
    })
    .then(function(response){
        data = response.json();  // get result from server as JSON
        // alert(data);
        return data; 
    })
    .then(function(data){ 
        // alert(data.info);
        $('.toast').toast("show")
        const toastbody = document.getElementById("toast-message")
        toastbody.textContent = data["returnText"]
        console.log(data);
    })
    .catch((error) => {
        console.error('Error:', error);
    });
    
    event.preventDefault(); // don't send in normal way and don't reload page
}


